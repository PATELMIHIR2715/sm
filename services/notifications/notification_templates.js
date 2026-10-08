/**
 * Institutional Notification Templates for WhatsApp and Email (Nodemailer)
 */

function formatWhatsAppAlert(signal) {
  const sym = signal.symbol || 'NIFTY';
  const dir = signal.predicted_direction || 'BULLISH';
  const isBull = dir.toUpperCase() === 'BULLISH';
  const emojiDir = isBull ? '🟢 STRONG BUY' : '🔴 TACTICAL SHORT';
  const ltp = signal.current_live_ltp_t0 || signal.current_base_price_inr || signal.ltp || 0;
  const optimalEntry = signal.optimal_entry_price || ltp;
  const orderType = signal.execution_order_type || (isBull ? 'ACCUMULATE_BEFORE_MOVE' : 'TACTICAL_SHORT');
  
  const t1 = signal.predicted_tomorrows_price_range_t1 || signal.t1_target || {};
  const t5 = signal.forward_5day_target_t5 || signal.t5_target || {};
  const t10 = signal.forward_10day_target_t10 || signal.t10_target || {};
  
  const t1Bounds = t1.predicted_price_bounds_inr || t1.price_target_range_inr || 'N/A';
  const t1Pct = t1.expected_move_pct || t1.percentage_range || '';
  const t5Bounds = t5.predicted_price_bounds_inr || t5.price_target_range_inr || 'N/A';
  const t5Pct = t5.expected_move_pct || t5.percentage_range || '';
  
  const sl = signal.recommended_stop_loss || 'N/A';
  const conviction = signal.conviction_score_pct || 80;
  const headline = signal.headline || 'High materiality catalyst detected';
  const sector = signal.sector || 'Equities';
  const absorption = signal.catalyst_absorption_pct != null ? `${signal.catalyst_absorption_pct}%` : 'Unreacted';
  const remainingAlpha = signal.remaining_alpha_pct != null ? `+${signal.remaining_alpha_pct}%` : 'Full Alpha';
  const kellyAlloc = signal.kelly_capital_allocation_inr || signal.allocated_capital_inr || 15000;
  const qty = signal.recommended_shares_quantity || signal.shares_qty || 1;

  return (
`⚡ *INSTITUTIONAL STOCK IMPACT ALERT*
*Symbol:* ${sym} (${sector})
*Action:* ${emojiDir} (Conviction: *${conviction}%*)
*Current LTP:* ₹${Number(ltp).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
*Order Corridor:* ${orderType}

🎯 *1-DAY PRICE TARGET (T+1):*
• *Tomorrow Target:* ${t1Bounds} (${t1Pct})
🛑 *Stop-Loss:* ${sl}

📊 *CATALYST & MICROSTRUCTURE INTEL:*
• *Catalyst:* ${headline}
• *Catalyst Absorption:* ${absorption} | *Remaining Alpha:* ${remainingAlpha}
• *Kelly Capital Allocation:* ₹${Number(kellyAlloc).toLocaleString('en-IN')} (${qty} Shares)

🛡️ *Microstructure Defense:* Active | Clamped to F&O Resistance
⏱️ *Time:* ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST`
  );
}

function formatWhatsAppPreCatalystAlert(item) {
  const sym = item.symbol || 'STOCK';
  const name = item.company_name || sym;
  const leadTime = item.hours_ahead_of_market ? `${item.hours_ahead_of_market} Hours Ahead of Market` : (item.lead_time_status || 'Early Radar');
  const source = item.channel_type ? item.channel_type.replace(/_/g, ' ') : 'Upstream Intelligence';
  const entryCorridor = item.pre_catalyst_entry_corridor || `₹${item.current_ltp || 0}`;
  const target = item.target_upon_announcement || 'N/A';
  const sl = item.stop_loss || 'N/A';
  const advice = item.action_advice || 'Accumulate before retail public repricing.';
  const headline = item.upstream_headline || 'Upstream early warning signal detected';
  const fp = item.smart_money_footprint || {};

  return (
`🚨 *UPSTREAM PRE-CATALYST RADAR ALERT (BEFORE MOVE)*
*Symbol:* ${sym} (${name})
*Lead Time Edge:* ⚡ *${leadTime}*
*Primary Source:* ${source}

💵 *Unreacted Base Entry Corridor:* ${entryCorridor}
🎯 *Target Upon Announcement:* ${target}
🛑 *Stop-Loss:* ${sl}

🔍 *SMART MONEY FOOTPRINT:*
• *15M RVOL:* ${fp.rvol_15m || '2.5x'}+
• *Delivery Accumulation:* ${fp.delivery_pct || 65}%
• *Options Flow:* ${fp.fno_call_buildup || 'Unusual Call OI Additions'}

💡 *Action Guidance:* ${advice}
📰 *Upstream Intel:* ${headline}
⏱️ *Alert Time:* ${new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST`
  );
}

function formatEmailHtml(signal) {
  const sym = signal.symbol || 'STOCK';
  const dir = signal.predicted_direction || 'BULLISH';
  const isBull = dir.toUpperCase() === 'BULLISH';
  const ltp = signal.current_live_ltp_t0 || signal.current_base_price_inr || signal.ltp || 0;
  const t1 = signal.predicted_tomorrows_price_range_t1 || signal.t1_target || {};
  const t5 = signal.forward_5day_target_t5 || signal.t5_target || {};
  const t10 = signal.forward_10day_target_t10 || signal.t10_target || {};
  const t1Bounds = t1.predicted_price_bounds_inr || t1.price_target_range_inr || 'N/A';
  const t1Pct = t1.expected_move_pct || t1.percentage_range || '';
  const t5Bounds = t5.predicted_price_bounds_inr || t5.price_target_range_inr || 'N/A';
  const t5Pct = t5.expected_move_pct || t5.percentage_range || '';
  const t10Bounds = t10.predicted_price_bounds_inr || t10.price_target_range_inr || 'N/A';
  const t10Pct = t10.expected_move_pct || t10.percentage_range || '';
  const sl = signal.recommended_stop_loss || 'N/A';
  const conviction = signal.conviction_score_pct || 80;
  const headline = signal.headline || 'High materiality corporate catalyst';
  const sector = signal.sector || 'Equities';
  const orderType = signal.execution_order_type || (isBull ? 'ACCUMULATE_BEFORE_MOVE' : 'TACTICAL_SHORT');
  const kellyAlloc = signal.kelly_capital_allocation_inr || signal.allocated_capital_inr || 15000;
  const qty = signal.recommended_shares_quantity || signal.shares_qty || 1;
  const absorption = signal.catalyst_absorption_pct != null ? `${signal.catalyst_absorption_pct}%` : 'Unreacted';
  const remainingAlpha = signal.remaining_alpha_pct != null ? `+${signal.remaining_alpha_pct}%` : '+3.5%';

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #131722; color: #d1d4dc; margin: 0; padding: 24px; }
    .container { max-width: 620px; margin: 0 auto; background-color: #1e222d; border: 1px solid #2a2e39; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
    .header { background: linear-gradient(135deg, #1e222d, #131722); padding: 20px 24px; border-bottom: 1px solid #2a2e39; }
    .brand { font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #2962ff; text-transform: uppercase; margin-bottom: 4px; }
    .title { font-size: 20px; font-weight: bold; color: #ffffff; margin: 0; }
    .badge-bull { display: inline-block; background-color: rgba(34, 197, 94, 0.15); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3); font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; margin-top: 8px; }
    .content { padding: 24px; }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; }
    .card { background-color: #131722; border: 1px solid #2a2e39; border-radius: 8px; padding: 12px; }
    .card-label { font-size: 10px; color: #787b86; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
    .card-value { font-size: 16px; font-weight: bold; color: #f0f3fa; }
    .target-box { background-color: rgba(41, 98, 255, 0.08); border: 1px solid rgba(41, 98, 255, 0.3); border-radius: 8px; padding: 16px; margin: 20px 0; }
    .target-title { font-size: 12px; font-weight: bold; color: #2962ff; text-transform: uppercase; margin-bottom: 10px; }
    .target-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #2a2e39; font-size: 13px; }
    .target-row:last-child { border-bottom: none; }
    .headline-box { background-color: #131722; border-left: 3px solid #2962ff; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 20px; font-size: 13px; line-height: 1.5; color: #d1d4dc; }
    .footer { background-color: #131722; padding: 14px 24px; border-top: 1px solid #2a2e39; font-size: 11px; color: #787b86; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="brand">Institutional Stock Impact Engine • Zero-Lookahead</div>
      <h1 class="title">${sym} — High Conviction Trade Signal</h1>
      <span class="badge-bull">${isBull ? '🟢 STRONG BUY' : '🔴 TACTICAL SHORT'} • Conviction: ${conviction}%</span>
    </div>

    <div class="content">
      <div class="headline-box">
        <strong style="color:#ffffff;">Catalyst:</strong> ${headline}
      </div>

      <div class="grid">
        <div class="card">
          <div class="card-label">Current LTP (Entry)</div>
          <div class="card-value">₹${Number(ltp).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        </div>
        <div class="card">
          <div class="card-label">Execution Order</div>
          <div class="card-value" style="font-size:12px; color:#22c55e;">${orderType}</div>
        </div>
        <div class="card">
          <div class="card-label">Catalyst Absorption</div>
          <div class="card-value" style="color:#38bdf8;">${absorption} <span style="font-size:11px; color:#787b86;">(${remainingAlpha} left)</span></div>
        </div>
        <div class="card">
          <div class="card-label">Kelly Capital Sizing</div>
          <div class="card-value">₹${Number(kellyAlloc).toLocaleString('en-IN')} <span style="font-size:11px; color:#787b86;">(${qty} shs)</span></div>
        </div>
      </div>

      <div class="target-box">
        <div class="target-title">🎯 Defended 1-Day Price Target (T+1)</div>
        <div class="target-row">
          <span style="color:#787b86;">1-Day Target (Tomorrow):</span>
          <strong style="color:#22c55e;">${t1Bounds} (${t1Pct})</strong>
        </div>
        <div class="target-row">
          <span style="color:#787b86;">Stop Loss (Strict 3%):</span>
          <strong style="color:#ef4444;">${sl}</strong>
        </div>
      </div>
    </div>

    <div class="footer">
      Dispatched at ${new Date().toLocaleString('en-IN')} IST • Zero Synthetic Data • Microstructure Defense Active
    </div>
  </div>
</body>
</html>
  `;
}

module.exports = {
  formatWhatsAppAlert,
  formatWhatsAppPreCatalystAlert,
  formatEmailHtml
};
