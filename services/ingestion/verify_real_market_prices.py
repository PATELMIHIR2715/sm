import yfinance as yf
import json
import sys

tickers = [
    "HAL.NS",
    "BHARTIARTL.NS",
    "TCS.NS",
    "M&M.NS",
    "ICICIBANK.NS",
    "RELIANCE.NS",
    "ASIANPAINT.NS",
    "JSWSTEEL.NS",
    "LT.NS",
    "TATASTEEL.NS"
]

results = {}

for t in tickers:
    try:
        tk = yf.Ticker(t)
        hist = tk.history(period="5d", interval="1d")
        if not hist.empty:
            last_row = hist.iloc[-1]
            prev_row = hist.iloc[-2] if len(hist) > 1 else last_row
            last_close = round(float(last_row["Close"]), 2)
            prev_close = round(float(prev_row["Close"]), 2)
            chg_pct = round(((last_close - prev_close) / prev_close) * 100, 2)
            results[t] = {
                "symbol": t.replace(".NS", ""),
                "latest_market_price": last_close,
                "prev_close": prev_close,
                "day_change_pct": chg_pct,
                "high": round(float(last_row["High"]), 2),
                "low": round(float(last_row["Low"]), 2),
                "volume": int(last_row["Volume"]),
                "last_trading_date": str(last_row.name.date())
            }
            print(f"{t.replace('.NS', '')}: INR {last_close} ({chg_pct:+0.2f}%) on {last_row.name.date()}", flush=True)
        else:
            print(f"{t}: No data returned", flush=True)
    except Exception as e:
        print(f"Error {t}: {e}", flush=True)

with open("d:/sm/data/verified_market_live_prices.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("Saved to d:/sm/data/verified_market_live_prices.json", flush=True)
