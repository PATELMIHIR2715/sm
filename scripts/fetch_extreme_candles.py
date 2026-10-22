import yfinance as yf
import pandas as pd

tickers = {
    'ZEEL': ('2024-01-19', '2024-01-26'),
    'KOTAKBANK': ('2024-04-23', '2024-04-29'),
    'PAYTM': ('2024-01-30', '2024-02-06'),
    'POLYCAB': ('2024-01-09', '2024-01-15'),
    'ADANIENT': ('2023-03-01', '2023-03-08'),
    'BHEL': ('2024-06-03', '2024-06-07'),
    'BANDHANBNK': ('2024-04-04', '2024-04-10'),
    'LUPIN': ('2023-11-20', '2023-11-27'),
    'RELIANCE': ('2024-09-04', '2024-09-10')
}

for sym, (s_date, e_date) in tickers.items():
    try:
        tk = yf.Ticker(f'{sym}.NS')
        df = tk.history(start=s_date, end=e_date)
        if df.empty:
            tk = yf.Ticker(f'{sym}.BO')
            df = tk.history(start=s_date, end=e_date)
        print(f"=== {sym} ({len(df)} candles) ===")
        for idx, row in df.iterrows():
            d_str = idx.strftime('%Y-%m-%d')
            print(f"  {d_str}: O={row['Open']:.2f}, H={row['High']:.2f}, L={row['Low']:.2f}, C={row['Close']:.2f}, Vol={int(row['Volume'])}")
    except Exception as e:
        print(f"{sym} Error: {e}")
