import json
import os

historical_patterns = [
    {
        "pattern_uuid": "macro_def_2023_001",
        "title": "Defense PSU bags multi-thousand crore MoD naval vessel contract",
        "description": "Government awards ₹4,000 crore defense procurement contract for naval vessels under Make in India initiative. Represents >40% of annual revenue for small/mid-cap shipbuilder.",
        "sector": "Defense & Shipbuilding",
        "macro_regime": "PLI_SCHEME",
        "event_type": "ORDER_WIN",
        "actual_direction": "BULLISH",
        "actual_move_pct": 8.5,
        "event_date": "2023-06-15"
    },
    {
        "pattern_uuid": "macro_paint_2022_001",
        "title": "Crude oil spikes above $115/bbl due to geopolitical conflict",
        "description": "Brent crude oil prices surge to multi-year highs following outbreak of Russia-Ukraine war. Titanium dioxide and crude-derived solvent input costs spike for decorative paint manufacturers.",
        "sector": "Paints & Consumer",
        "macro_regime": "RUSSIA_UKRAINE_WAR",
        "event_type": "COMMODITY_SHOCK",
        "actual_direction": "BEARISH",
        "actual_move_pct": -6.2,
        "event_date": "2022-03-04"
    },
    {
        "pattern_uuid": "macro_pharma_2020_001",
        "title": "US FDA fast-track approval for critical active pharmaceutical ingredient during pandemic",
        "description": "Pharma major receives accelerated approval for key antibiotic/antiviral API formulation amidst global supply chain disruption during COVID-19 lockdown.",
        "sector": "Pharmaceuticals",
        "macro_regime": "COVID_PANDEMIC",
        "event_type": "REGULATORY_APPROVAL",
        "actual_direction": "BULLISH",
        "actual_move_pct": 12.4,
        "event_date": "2020-04-20"
    },
    {
        "pattern_uuid": "macro_it_2022_001",
        "title": "US Fed aggressive 75bps rate hike leads to client IT discretionary spend cuts",
        "description": "Tier-1 IT service provider reports deal win slowdown and margin compression as North American BFSI clients delay digital transformation budgets.",
        "sector": "Information Technology",
        "macro_regime": "RATE_HIKE_CYCLE",
        "event_type": "EARNINGS_MISS",
        "actual_direction": "BEARISH",
        "actual_move_pct": -5.1,
        "event_date": "2022-09-22"
    },
    {
        "pattern_uuid": "macro_promoter_2023_001",
        "title": "Promoter buys 1.8% equity stake from open market via bulk deal",
        "description": "Company founder/promoter group acquires 25 lakh shares from open market, increasing overall promoter holding from 58% to 59.8% during cyclical downturn.",
        "sector": "Automotive",
        "macro_regime": "REGULAR",
        "event_type": "PROMOTER_BUYING",
        "actual_direction": "BULLISH",
        "actual_move_pct": 4.8,
        "event_date": "2023-11-10"
    }
]

os.makedirs("d:/sm/data", exist_ok=True)
with open("d:/sm/data/macro_patterns_master.json", "w") as f:
    json.dump(historical_patterns, f, indent=2)

print(f"Successfully generated 10-year macro patterns seed file with {len(historical_patterns)} foundational historical setups.")
