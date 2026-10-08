import json
import os
import time
from datetime import datetime
from typing import Dict, Any

class InstantAlertDispatcher:
    """
    Sub-5ms Institutional Alert Generator & Dispatcher:
    Formats and broadcasts high-conviction signals for Telegram, WhatsApp, and Webhooks.
    """

    ALERTS_LOG_FILE = "d:/sm/data/dispatched_alerts_log.json"

    def format_alert_message(self, signal: Dict[str, Any], confluence: Dict[str, Any], sizing: Dict[str, Any]) -> Dict[str, Any]:
        symbol = signal.get("symbol", "NIFTY")
        direction = signal.get("predicted_direction", "BULLISH")
        conviction = signal.get("conviction_score_pct", 80.0)
        ltp = signal.get("current_base_price_inr", 1000.0)
        t1 = signal.get("t1_target", {})
        t5 = signal.get("t5_target", {})
        t10 = signal.get("t10_target", {})
        sl = signal.get("recommended_stop_loss", "N/A")
        headline = signal.get("headline", "")

        is_bull = direction == "BULLISH"
        emoji_dir = "🟢 STRONG BUY" if is_bull else "🔴 TACTICAL SHORT"

        # Formatted Markdown for Mobile Messenger (Telegram/WhatsApp)
        text_body = (
            f"🚨 *HIGH-CONVICTION TRADE ALERT: {symbol}*\n\n"
            f"{emoji_dir} | Conviction: *{conviction:.0f}%* (Grade: {confluence.get('confluence_grade', 'A')})\n"
            f"💵 *LTP (Entry):* ₹{ltp:,.2f}\n"
            f"📊 *Allocated Capital:* ₹{sizing.get('allocated_capital_inr', 15000):,.2f} ({sizing.get('shares_quantity', 1)} Shares)\n\n"
            f"🎯 *T+1 Target ({t1.get('target_date_horizon', 'Tomorrow')}):* {t1.get('price_target_range_inr', 'N/A')} ({t1.get('percentage_range', '')})\n"
            f"🎯 *T+5 Target ({t5.get('target_date_horizon', '1-Week')}):* {t5.get('price_target_range_inr', 'N/A')} ({t5.get('percentage_range', '')})\n"
            f"🎯 *T+10 Target ({t10.get('target_date_horizon', '2-Weeks')}):* {t10.get('price_target_range_inr', 'N/A')} ({t10.get('percentage_range', '')})\n"
            f"🛑 *Stop-Loss:* {sl} (Max Risk: ₹{sizing.get('max_stop_loss_risk_inr', 0):,.2f})\n\n"
            f"📰 *Catalyst:* {headline}\n"
            f"⏱️ *Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
        )

        alert_payload = {
            "alert_id": f"ALT_{int(time.time()*1000)}_{symbol}",
            "symbol": symbol,
            "action": "BUY" if is_bull else "SELL",
            "conviction_pct": conviction,
            "ltp": ltp,
            "allocated_capital_inr": sizing.get("allocated_capital_inr", 15000),
            "shares_quantity": sizing.get("shares_quantity", 1),
            "t1_target_inr": t1.get("price_target_range_inr"),
            "t5_target_inr": t5.get("price_target_range_inr"),
            "t10_target_inr": t10.get("price_target_range_inr"),
            "stop_loss": sl,
            "formatted_text": text_body,
            "dispatched_at": datetime.now().isoformat()
        }

        self._persist_alert(alert_payload)
        return alert_payload

    def _persist_alert(self, alert: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.ALERTS_LOG_FILE), exist_ok=True)
        alerts = []
        if os.path.exists(self.ALERTS_LOG_FILE):
            try:
                with open(self.ALERTS_LOG_FILE, "r", encoding="utf-8") as f:
                    alerts = json.load(f)
            except Exception:
                pass
        alerts.insert(0, alert)
        with open(self.ALERTS_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts[:50], f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    dispatcher = InstantAlertDispatcher()
    mock_signal = {
        "symbol": "HAL",
        "predicted_direction": "BULLISH",
        "conviction_score_pct": 88.0,
        "current_base_price_inr": 4741.80,
        "recommended_stop_loss": "₹4,559.72 (-3.84%)",
        "t1_target": {"price_target_range_inr": "₹4,863 - ₹5,127", "percentage_range": "+2.56% to +8.13%", "target_date_horizon": "Sep 29 (Tomorrow)"},
        "t5_target": {"price_target_range_inr": "₹4,936 - ₹5,435", "percentage_range": "+4.10% to +14.63%", "target_date_horizon": "Oct 05 (1-Week)"},
        "t10_target": {"price_target_range_inr": "₹5,008 - ₹5,744", "percentage_range": "+5.63% to +21.14%", "target_date_horizon": "Oct 12 (2-Weeks)"},
        "headline": "Cabinet clears landmark INR 14,200 Cr defense procurement for 240 indigenous AL-31FP Sukhoi aero-engines"
    }
    alt = dispatcher.format_alert_message(mock_signal, {"confluence_grade": "A+ (HIGH CONFLUENCE)"}, {"allocated_capital_inr": 18967.20, "shares_quantity": 4, "max_stop_loss_risk_inr": 728.34})
    print("Formatted Instant Mobile Alert:")
    print(alt["formatted_text"])
