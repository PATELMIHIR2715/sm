import json
import os

nifty500_sample = [
    {"symbol": "RELIANCE", "bse_code": "500325", "isin": "INE002A01018", "company_name": "Reliance Industries Ltd", "sector": "Energy & Petrochemicals", "market_cap_cr": 1950000.0, "annual_revenue_cr": 890000.0, "atr_percentage": 1.8},
    {"symbol": "TCS", "bse_code": "532540", "isin": "INE467B01029", "company_name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "market_cap_cr": 1420000.0, "annual_revenue_cr": 240000.0, "atr_percentage": 1.5},
    {"symbol": "HDFCBANK", "bse_code": "500180", "isin": "INE040A01034", "company_name": "HDFC Bank Ltd", "sector": "Banking & Financials", "market_cap_cr": 1280000.0, "annual_revenue_cr": 205000.0, "atr_percentage": 1.7},
    {"symbol": "INFY", "bse_code": "500209", "isin": "INE009A01021", "company_name": "Infosys Ltd", "sector": "Information Technology", "market_cap_cr": 780000.0, "annual_revenue_cr": 153000.0, "atr_percentage": 2.0},
    {"symbol": "ICICIBANK", "bse_code": "532174", "isin": "INE090A01021", "company_name": "ICICI Bank Ltd", "sector": "Banking & Financials", "market_cap_cr": 850000.0, "annual_revenue_cr": 160000.0, "atr_percentage": 1.9},
    {"symbol": "BHARTIARTL", "bse_code": "532454", "isin": "INE397D01024", "company_name": "Bharti Airtel Ltd", "sector": "Telecommunications", "market_cap_cr": 920000.0, "annual_revenue_cr": 150000.0, "atr_percentage": 2.1},
    {"symbol": "LTI", "bse_code": "540005", "isin": "INE214T01019", "company_name": "LTIMindtree Ltd", "sector": "Information Technology", "market_cap_cr": 175000.0, "annual_revenue_cr": 35000.0, "atr_percentage": 2.4},
    {"symbol": "LT", "bse_code": "500510", "isin": "INE018A01030", "company_name": "Larsen & Toubro Ltd", "sector": "Capital Goods & Engineering", "market_cap_cr": 510000.0, "annual_revenue_cr": 221000.0, "atr_percentage": 2.0},
    {"symbol": "HAL", "bse_code": "541154", "isin": "INE066F01020", "company_name": "Hindustan Aeronautics Ltd", "sector": "Defense & Aerospace", "market_cap_cr": 310000.0, "annual_revenue_cr": 30000.0, "atr_percentage": 3.2},
    {"symbol": "MAZDOCK", "bse_code": "543237", "isin": "INE249Z01012", "company_name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defense & Shipbuilding", "market_cap_cr": 95000.0, "annual_revenue_cr": 9400.0, "atr_percentage": 3.8},
    {"symbol": "BEL", "bse_code": "500049", "isin": "INE263A01024", "company_name": "Bharat Electronics Ltd", "sector": "Defense & Aerospace", "market_cap_cr": 215000.0, "annual_revenue_cr": 20000.0, "atr_percentage": 2.8},
    {"symbol": "ASIANPAINT", "bse_code": "500820", "isin": "INE021A01026", "company_name": "Asian Paints Ltd", "sector": "Paints & Consumer", "market_cap_cr": 280000.0, "annual_revenue_cr": 35000.0, "atr_percentage": 2.2},
    {"symbol": "BERGEPAINT", "bse_code": "509480", "isin": "INE463A01038", "company_name": "Berger Paints India Ltd", "sector": "Paints & Consumer", "market_cap_cr": 60000.0, "annual_revenue_cr": 10500.0, "atr_percentage": 2.5},
    {"symbol": "TATASTEEL", "bse_code": "500470", "isin": "INE081A01020", "company_name": "Tata Steel Ltd", "sector": "Metals & Mining", "market_cap_cr": 190000.0, "annual_revenue_cr": 230000.0, "atr_percentage": 2.9},
    {"symbol": "JSWSTEEL", "bse_code": "500228", "isin": "INE019A01038", "company_name": "JSW Steel Ltd", "sector": "Metals & Mining", "market_cap_cr": 230000.0, "annual_revenue_cr": 175000.0, "atr_percentage": 2.7},
    {"symbol": "TATAMOTORS", "bse_code": "500570", "isin": "INE155A01022", "company_name": "Tata Motors Ltd", "sector": "Automotive", "market_cap_cr": 340000.0, "annual_revenue_cr": 430000.0, "atr_percentage": 2.8},
    {"symbol": "M&M", "bse_code": "500520", "isin": "INE101A01026", "company_name": "Mahindra & Mahindra Ltd", "sector": "Automotive", "market_cap_cr": 380000.0, "annual_revenue_cr": 140000.0, "atr_percentage": 2.4},
    {"symbol": "MARUTI", "bse_code": "532500", "isin": "INE585B01010", "company_name": "Maruti Suzuki India Ltd", "sector": "Automotive", "market_cap_cr": 390000.0, "annual_revenue_cr": 141000.0, "atr_percentage": 2.1},
    {"symbol": "SUNPHARMA", "bse_code": "524715", "isin": "INE044A01036", "company_name": "Sun Pharmaceutical Industries Ltd", "sector": "Pharmaceuticals", "market_cap_cr": 420000.0, "annual_revenue_cr": 4800.0, "atr_percentage": 2.0},
    {"symbol": "DRREDDY", "bse_code": "500124", "isin": "INE089A01023", "company_name": "Dr. Reddy's Laboratories Ltd", "sector": "Pharmaceuticals", "market_cap_cr": 110000.0, "annual_revenue_cr": 28000.0, "atr_percentage": 2.1}
]

os.makedirs("d:/sm/data", exist_ok=True)
with open("d:/sm/data/nifty500_master.json", "w") as f:
    json.dump(nifty500_sample, f, indent=2)

print(f"Successfully generated seed file with {len(nifty500_sample)} key Nifty 500 company records.")
