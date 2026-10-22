# Quantitative Trading Pipeline Audit

**Audit date:** 2026-10-22  
**Scope:** Event-driven NSE/BSE filing alerts, target generation, regime controls, price validation, execution filters, and evaluation methodology.  
**Decision:** Do **not** dispatch new directional T+1 alerts until the P0 controls below are deployed and independently validated.

## Executive Result

The current pipeline can convert a regime-vetoed long idea into a dispatched alert, can label end-of-day Yahoo candles as live ticks, and evaluates historical alerts without executable-entry, stop-loss, or gap-risk logic. These are control failures, not ordinary model error.

The October 21-22 failures are consistent with the system treating a broad risk-off event as a minor target adjustment instead of a hard execution veto:

| Symbol | Direction | Stated NIFTY 3-day beta drag | T1 return required | Minimum idiosyncratic alpha required before sector drag/costs |
|---|---:|---:|---:|---:|
| SRF | Long | -3.38% | +1.48% | +4.86% |
| LMW | Long | -3.11% | +1.71% | +4.82% |
| ADOR | Long | -2.97% | +2.85% | +5.82% |

The drag values use the supplied three-day NIFTY move of -2.7% and the beta values currently configured or supplied in the incident: `beta * -2.7%`. They are forensic decompositions, not a forecast rule; production forecasts must use conditional expected market and sector returns.

## P0: Block Live Dispatch

Deploy these changes before the next session.

1. **Make a regime veto terminal.** A signal with `dispatchable=False` must set `is_useful=False`, receive `actionability_status=SUPPRESSED_*`, and never reach email, Telegram, Supabase, or downstream execution consumers.
2. **Remove every synthetic price fallback.** A missing or stale executable quote is a suppression condition. Never use `100.0`, an input-price fallback, a previous expired cache value, or a fabricated company price.
3. **Require a verified pre-open decision for overnight signals.** At 09:08, reject an adverse auction gap and defer all remaining entries until an executable post-open quote is available.
4. **Reject untradeable instruments.** Missing bid/ask, insufficient turnover, circuit restrictions, surveillance restrictions, or unavailable short borrow must suppress the signal.
5. **Fail closed when fundamentals are unknown.** Do not assign synthetic revenue, market cap, ATR, beta, or tier to an unknown company.

## Exact Code Changes

### 1. `services/ingestion/auto_live_stream_worker.py`

#### Replace synthetic prices with a hard failure

Change the fallback at `compute_forward_targets()` and both call sites:

```python
# Remove
safe_ltp = ltp if (ltp and ltp > 0) else 100.0

# Replace with
if ltp is None or not math.isfinite(float(ltp)) or float(ltp) <= 0:
    return {"dispatchable": False, "reason": "UNVERIFIED_LIVE_PRICE"}
safe_ltp = float(ltp)
```

Remove `ltp or 100.0` from the target and position-size calls. Do not fall back to `item["current_base_price_inr"]` unless it is a signed, timestamped quote from an approved market-data source and passes quote-age validation.

#### Make dispatch eligibility explicit

Immediately after target generation:

```python
if not targets.get("dispatchable", True):
    signal_record = {
        "symbol": symbol,
        "headline": headline,
        "predicted_direction": "NEUTRAL",
        "is_useful": False,
        "actionability_status": f"SUPPRESSED_{targets['reason']}",
        "suppression_reason": targets["reason"],
    }
    self._store_suppressed_signal(signal_record)
    return signal_record
```

Then change dispatch to require all conditions:

```python
if (
    signal_record.get("dispatchable") is True
    and signal_record.get("is_useful") is True
    and signal_record.get("conviction_score_pct", 0) >= 70
):
    self._dispatch_instant_alert(signal_record)
```

The existing `suppress_chase_alert` flag must be replaced by a binary execution decision. A label such as `ACCUMULATE_ON_DIP_ONLY` is not a safety control.

#### Replace the illiquidity condition

The current predicate uses `AND`; an instrument can pass if either volume or turnover narrowly exceeds its threshold. Use an `OR` rejection rule and validate book quality:

```python
minimum_price = 50.0
minimum_median_20d_adtv_cr = 2.0
maximum_spread_bps = 25.0

is_untradeable = any((
    quote is None,
    quote.get("quote_age_seconds", float("inf")) > 5,
    ltp < minimum_price,
    quote.get("median_20d_adtv_cr", 0.0) < minimum_median_20d_adtv_cr,
    quote.get("bid", 0.0) <= 0,
    quote.get("ask", 0.0) <= 0,
    quote.get("spread_bps", float("inf")) > maximum_spread_bps,
    quote.get("is_circuit_locked", False),
    quote.get("is_under_surveillance", False),
))
```

For short signals additionally require F&O eligibility and an affirmative stock-borrow/locate result. A cash-equity short alert must not be generated without this evidence.

### 2. `services/ai_pipeline/market_regime_confluence.py`

Replace the positive target floor (`max(0.40, net_t1_pct)`) with a hard long-veto based on an event-alpha lower confidence bound.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MarketState:
    nifty_return_1d: float
    nifty_return_3d: float
    sector_return_1d: float
    india_vix: float
    vix_change_pct: float

class MarketRegimeConfluenceEngine:
    @staticmethod
    def assess_long(
        event_alpha_lcb_pct: float,
        beta_nifty: float,
        beta_sector: float,
        state: MarketState,
        required_target_pct: float,
        execution_cost_pct: float,
    ) -> dict:
        market_contribution = beta_nifty * state.nifty_return_1d
        sector_contribution = beta_sector * state.sector_return_1d
        vix_penalty = max(0.0, state.india_vix - 16.0) * 0.08
        net_expected_pct = (
            event_alpha_lcb_pct
            + market_contribution
            + sector_contribution
            - vix_penalty
        )
        risk_off = (
            state.nifty_return_1d <= -0.80
            or state.nifty_return_3d <= -1.80
            or (state.india_vix >= 16.0 and state.vix_change_pct >= 10.0)
        )
        minimum_return = max(required_target_pct, 1.5 * execution_cost_pct)
        veto = risk_off and (
            event_alpha_lcb_pct < 4.0 or net_expected_pct < minimum_return
        )
        return {
            "dispatchable": not veto,
            "reason": "RISK_OFF_INSUFFICIENT_ALPHA" if veto else None,
            "net_expected_pct": round(net_expected_pct, 2),
            "market_drag_pct": round(market_contribution + sector_contribution, 2),
        }
```

The threshold values are initial priors. Re-estimate them from strictly out-of-sample, event-time-aligned data; do not optimise them on the deployment sample.

### 3. `services/market_data/live_price_provider.py`

The current daily `history(period="5d", interval="1d")` response is not a live quote or a tradable bid/ask. Replace it with an approved, exchange-authorised real-time quote and order-book feed. Until that integration exists:

- Rename `is_live_tick` to `is_delayed_or_eod`.
- Do not dispatch market-hours alerts from the provider.
- Never return an expired cached quote as executable data.
- Return `quote_age_seconds`, `source_timestamp`, `bid`, `ask`, `spread_bps`, cumulative turnover, and a source-health status.
- Mark any provider exception as `source_healthy=False` and force signal suppression.

The defaults `nifty_ltp=25800.0` and `india_vix=14.5` must also be removed. An unavailable regime feed is unknown, not neutral.

### 4. `services/market_data/company_intelligence_provider.py`

Remove unknown-company defaults for revenue, market cap, beta, tier, ATR, and price. Return `profile_verified=False` whenever the company is absent from a verified fundamentals source. A `profile_verified=False` result must allow archival classification but prohibit a T+1 tradable recommendation.

Use rolling, point-in-time beta estimates instead of static mappings. Estimate beta on a 252-trading-day window with a 63-day exponentially weighted update; retain a sector beta only if its estimation quality and sample coverage meet defined thresholds.

### 5. `services/ai_pipeline/jev_classifier.py` and `sentiment_classifier.py`

- Validate the API schema. `act_obj.get("noul", 0.50)` is almost certainly an incorrect field name and silently defaults actionability to 50%.
- Raise the directional-actionability threshold substantially and require calibrated probability, not an LLM self-report.
- Add event archetypes: `ORDER_WIN`, `CAPEX_APPROVAL`, `DIVIDEND`, `CLOSURE_OR_DISPOSAL`, `RATING_ACTION`, `REGULATORY_OR_LEGAL`, and `ROUTINE_COMPLIANCE`.
- Require event-specific materiality evidence. A dividend needs yield surprise and ex-date context; capex needs incremental capacity/EBITDA/ROCE; closure needs affected revenue/EBIT or disposal proceeds.
- Map unknown numeric values to `None`, never to default revenue or materiality denominators.

## Dynamic Stop And Pre-Open Logic

A stop loss does not insure against a gap. It defines a risk budget only after an executable entry exists.

```python
def preopen_execution_gate(
    direction: str,
    prior_close: float,
    indicative_price: float | None,
    atr14_pct: float,
    planned_stop_pct: float,
) -> dict:
    if indicative_price is None or indicative_price <= 0 or prior_close <= 0:
        return {"allow": False, "reason": "MISSING_PREOPEN_QUOTE"}

    opening_return_pct = 100 * (indicative_price / prior_close - 1)
    adverse_gap_pct = (
        -opening_return_pct if direction == "BULLISH" else opening_return_pct
    )
    maximum_gap_pct = min(atr14_pct, 0.75 * planned_stop_pct)

    if adverse_gap_pct >= planned_stop_pct:
        return {"allow": False, "reason": "OPEN_THROUGH_STOP"}
    if adverse_gap_pct >= maximum_gap_pct:
        return {"allow": False, "reason": "ADVERSE_PREOPEN_GAP"}
    return {"allow": True, "reason": None}
```

Use a volatility-adjusted risk distance, then size down rather than simply widening risk:

```text
vix_multiplier = clamp(1 + 0.06 * max(VIX - 14, 0), 1.0, 1.5)
stop_distance_pct = clamp(1.25 * ATR14_pct * vix_multiplier, 1.0, 6.0)
shares = floor(risk_budget_inr / (entry_price * stop_distance_pct / 100))
```

Reject the trade when the target cannot offer at least 1.5 times this risk distance after estimated spread, impact, fees, and taxes.

## Event Materiality Rules

| Archetype | Reject / watch only | Conditional | T+1 eligible evidence |
|---|---|---|---|
| Order/contract | Value <3% of annual revenue | 3-8% revenue | >=8%, margin/timing/counterparty known |
| Capex | Approval with no economics | Capacity or timeline stated | Incremental EBITDA/ROCE and financed execution credible |
| Dividend | Ordinary or anticipated payout | Small surprise | Yield surprise >=1% of spot or statistically material surprise |
| Closure/disposal | Generic disclosure | Revenue/EBIT partly identified | Affected EBIT/revenue or proceeds >=5% and direction supported |
| Credit/rating action | Routine update | Outlook change | Rating/action changes financing or covenant economics |

Contract headline value is not automatically one-year revenue. The model must account for contract duration, cancellation terms, pass-through costs, and margin.

## Backtest And Release Protocol

### Why the existing evidence is insufficient

`data/evaluation_results.json` covers 77 records across four signal dates (2026-09-28 to 2026-10-13). Its reported T+1 hit rate is 38/77 (49.4%). The 45 signals with conviction >=70% produce only 18/45 T+1 hits (40.0%), which demonstrates confidence miscalibration.

The existing combined result is not a tradable result because it:

- Credits a same-day high/low despite after-market alerts that could not have been entered before that movement.
- Does not include stop-loss hits, opening gaps, execution priority, spread, market impact, fees, taxes, or position limits.
- Can award target hit before testing whether a stop was reached during the same session.
- Does not segment results by event archetype, liquidity, market regime, provider health, or short-sale availability.

### Required replay model

1. Store the immutable filing timestamp, exchange receipt timestamp, classification version, quote source, quote timestamp, and all gate decisions.
2. Use one-minute or finer historical bars plus contemporaneous bid/ask where available. Enter at the auction/first executable quote plus half-spread and estimated impact.
3. If the opening price crosses the stop, exit at the opening price, not the stop price.
4. Resolve target-versus-stop sequence chronologically. With only daily candles, use a conservative stop-first assumption and mark the result low confidence.
5. Apply brokerage, exchange costs, taxes, spread, borrow costs, and market impact before calculating returns.
6. Use a purged, chronological walk-forward split. Keep a final untouched holdout period spanning multiple bull, bear, and high-volatility regimes.
7. Report target-first rate, stop-first rate, net expectancy, profit factor, max drawdown, calibration error, coverage, suppression rate, and 95% bootstrap confidence intervals by archetype/regime/liquidity bucket.

### Promotion criteria

Do not promise near-zero false breakouts; that is not attainable or measurable in live markets. Promotion requires all of the following on a frozen out-of-sample dataset:

- Positive net expectancy after all execution costs, with a positive 95% bootstrap lower confidence bound.
- Improved target-first minus stop-first rate versus the current baseline in each eligible regime.
- No failed quote freshness, synthetic-price, or pre-open-gap controls.
- Probability calibration that is monotonic by confidence bucket.
- A documented rejection reason for every suppressed signal.

## Implementation Order

| Priority | Work | Owner outcome |
|---|---|---|
| P0 | Terminal dispatch veto, zero synthetic prices, source-health checks | Unsafe live alerts cannot be sent |
| P0 | Pre-open gap gate and executable-entry rule | Overnight signals cannot assume stop fills |
| P0 | Turnover/spread/borrow/circuit filters | Illiquid and unshortable noise is excluded |
| P1 | Point-in-time fundamentals, ATR, beta, and sector factors | Inputs are auditable and non-fabricated |
| P1 | Archetype-specific classifier and materiality model | Dividends/capex/closures are not generic bullish or bearish events |
| P1 | Event-time, cost-aware replay backtest | Accuracy claims become falsifiable |
| P2 | Probability calibration and monitored canary release | Thresholds adapt only through governed retraining |

## Files Requiring Changes

- `services/ingestion/auto_live_stream_worker.py`
- `services/ai_pipeline/market_regime_confluence.py`
- `services/market_data/live_price_provider.py`
- `services/market_data/company_intelligence_provider.py`
- `services/ai_pipeline/jev_classifier.py`
- `services/ai_pipeline/sentiment_classifier.py`
- `scripts/evaluate_signals.py`
- `services/evaluation/live_accuracy_ledger.py`

No production code was changed by this audit. This document is the implementation specification and release gate.
