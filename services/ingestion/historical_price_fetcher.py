import os
import json
from datetime import datetime, timedelta
import yfinance as yf

class HistoricalPriceFetcher:
    """
    Automated Real Historical Price & Return Calculator:
    Fetches real daily OHLC price candles from NSE/BSE and calculates:
    - 1-Day Return % (T+1 Close vs T-0 Close)
    - 1-Day Open Gap % (T+1 Open vs T-0 Close)
    - Peak Favorable Move % (T+1 High/Low vs T-0 Close)
    - 5-Day Return % (T+5 Close vs T-0 Close)
    - 20-Day Return % (T+20 Close vs T-0 Close)
    """

    def __init__(self, cache_dir="d:/sm/data/price_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cached_series = {}

    def calculate_event_return(self, symbol: str, event_date_str: str) -> dict:
        symbol_clean = symbol.upper().replace(".NS", "").replace(".BO", "")
        cache_key = f"{symbol_clean}_{event_date_str}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        try:
            ed = datetime.strptime(event_date_str[:10], "%Y-%m-%d")
        except Exception:
            return {"status": "INVALID_DATE", "actual_direction": "NEUTRAL", "return_1d_pct": 0.0}

        start = (ed - timedelta(days=6)).strftime("%Y-%m-%d")
        end = (ed + timedelta(days=25)).strftime("%Y-%m-%d")

        hist = None
        for suffix in [".NS", ".BO"]:
            try:
                t = yf.Ticker(f"{symbol_clean}{suffix}")
                h = t.history(start=start, end=end)
                if h is not None and len(h) >= 2:
                    hist = h
                    break
            except Exception:
                continue

        if hist is None or len(hist) < 2:
            return {
                "status": "NO_PRICE_DATA",
                "t0_date": event_date_str,
                "t0_close": 0.0,
                "return_1d_pct": 0.0,
                "return_5d_pct": 0.0,
                "actual_direction": "NEUTRAL"
            }

        h_on_or_before = hist[hist.index <= ed.strftime("%Y-%m-%d")]
        h_after = hist[hist.index > ed.strftime("%Y-%m-%d")]

        if len(h_on_or_before) == 0 or len(h_after) == 0:
            return {
                "status": "INSUFFICIENT_DATA",
                "t0_date": event_date_str,
                "t0_close": 0.0,
                "return_1d_pct": 0.0,
                "return_5d_pct": 0.0,
                "actual_direction": "NEUTRAL"
            }

        t0_close = round(float(h_on_or_before.iloc[-1]["Close"]), 2)
        t1_open = round(float(h_after.iloc[0]["Open"]), 2)
        t1_high = round(float(h_after.iloc[0]["High"]), 2)
        t1_low = round(float(h_after.iloc[0]["Low"]), 2)
        t1_close = round(float(h_after.iloc[0]["Close"]), 2)

        t5_close = round(float(h_after.iloc[min(4, len(h_after)-1)]["Close"]), 2) if len(h_after) >= 3 else t1_close
        t20_close = round(float(h_after.iloc[-1]["Close"]), 2)

        if t0_close > 0:
            ret_1d = round(((t1_close - t0_close) / t0_close) * 100, 2)
            gap_pct = round(((t1_open - t0_close) / t0_close) * 100, 2)
            high_move = round(((t1_high - t0_close) / t0_close) * 100, 2)
            low_move = round(((t1_low - t0_close) / t0_close) * 100, 2)
            ret_5d = round(((t5_close - t0_close) / t0_close) * 100, 2)
            ret_20d = round(((t20_close - t0_close) / t0_close) * 100, 2)
        else:
            ret_1d, gap_pct, high_move, low_move, ret_5d, ret_20d = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        if ret_1d >= 1.2 or high_move >= 2.0:
            dir_label = "BULLISH"
        elif ret_1d <= -1.2 or low_move <= -2.0:
            dir_label = "BEARISH"
        else:
            dir_label = "NEUTRAL"

        res = {
            "status": "SUCCESS",
            "t0_date": str(h_on_or_before.index[-1].date()),
            "t0_close": t0_close,
            "t1_date": str(h_after.index[0].date()),
            "t1_open": t1_open,
            "t1_high": t1_high,
            "t1_low": t1_low,
            "t1_close": t1_close,
            "gap_pct": gap_pct,
            "return_1d_pct": ret_1d,
            "max_high_pct": high_move,
            "max_low_pct": low_move,
            "return_5d_pct": ret_5d,
            "return_20d_pct": ret_20d,
            "actual_direction": dir_label
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(res, f)
        except Exception:
            pass

        return res

if __name__ == "__main__":
    fetcher = HistoricalPriceFetcher()
    res = fetcher.calculate_event_return("MAZDOCK", "2023-06-15")
    print("Verified Historical Price Return for Mazagon Dock (2023-06-15):")
    print(json.dumps(res, indent=2))
