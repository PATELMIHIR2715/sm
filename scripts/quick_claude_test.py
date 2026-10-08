"""
Quick test: Run Claude CLI for 2 events to verify subprocess works, then save results.
"""
import sys, os, json, subprocess, re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

SYSTEM_PROMPT = (
    "You are a senior Indian stock market analyst. "
    "Classify this news event for its stock price impact. "
    "Return ONLY valid JSON: {\"direction\": \"BULLISH\"|\"BEARISH\"|\"NEUTRAL\", \"confidence\": 0-100, \"reasoning\": \"...\"}"
)

def call_claude(headline: str) -> dict:
    full_prompt = f"{SYSTEM_PROMPT}\n\nNews: {headline}"
    try:
        result = subprocess.run(
            ["claude", "-p", "--output-format", "text"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout.strip()
            # Extract JSON from markdown fences if present
            m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
            if m:
                raw = m.group(1).strip()
            return json.loads(raw)
    except Exception as e:
        pass
    return {"direction": "NEUTRAL", "confidence": 0, "reasoning": "CLI call failed"}

test_events = [
    "HAL receives INR 26000 Crore order from IAF for 12 Su-30MKI fighter aircraft",
    "Asian Paints Q3 net profit declines 18% YoY due to crude oil price surge",
]

output_file = "d:/sm/data/backtest_reports/quick_test.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

results = []
for h in test_events:
    print(f"Processing: {h[:50]}...", flush=True)
    r = call_claude(h)
    print(f"  Result: {json.dumps(r)}", flush=True)
    results.append({"headline": h, "result": r})

with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nDone. Saved to {output_file}")
