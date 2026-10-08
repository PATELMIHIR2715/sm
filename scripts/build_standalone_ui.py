import json
import os

with open("d:/sm/data/backtest_reports/2026_10day_trading_sim_results.json", "r", encoding="utf-8") as f:
    data_10day = json.load(f)

with open("d:/sm/data/backtest_reports/2026_5day_full_results.json", "r", encoding="utf-8") as f:
    data_5day = json.load(f)

with open("d:/sm/apps/web/index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Replace initial state placeholders
json_10_str = json.dumps(data_10day)
json_5_str = json.dumps(data_5day)

injected_script = f"""
        const INITIAL_10DAY_DATA = {json_10_str};
        const INITIAL_5DAY_DATA = {json_5_str};
        const {{ useState, useEffect }} = React;

        function App() {{
            const [selectedWindow, setSelectedWindow] = useState("10day");
            const [activeTab, setActiveTab] = useState("table3");
            const [searchQuery, setSearchQuery] = useState("");
            const [data10Day, setData10Day] = useState(INITIAL_10DAY_DATA);
            const [data5Day, setData5Day] = useState(INITIAL_5DAY_DATA);
"""

# Inject into index.html
if "const { useState, useEffect } = React;" in html_content:
    html_content = html_content.replace(
        "const { useState, useEffect } = React;\n\n        function App() {\n            const [selectedWindow, setSelectedWindow] = useState(\"10day\");",
        injected_script.strip()
    )

with open("d:/sm/apps/web/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Successfully injected instant preloaded dataset into apps/web/index.html!")
