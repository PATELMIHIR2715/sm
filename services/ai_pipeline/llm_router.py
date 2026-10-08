import os
import json
import subprocess
import urllib.request
import urllib.error
import re

class LLMRouter:
    """
    Unified LLM router supporting:
    1. Claude CLI (claude -p) — Primary for local dev/testing, uses your existing Claude subscription
    2. Local Ollama (CPU-optimized, $0 cost)
    3. DeepSeek / OpenAI / Anthropic / Groq (Cloud APIs for production)
    4. Comprehensive Financial Rule Engine (Fallback when all else is offline)
    """

    SYSTEM_PROMPT = (
        "You are a senior Indian stock market analyst with 15 years of experience covering NSE/BSE. "
        "You specialize in corporate event impact analysis, order book materiality assessment, "
        "promoter activity interpretation, and credit rating implications. "
        "You must return ONLY valid JSON with these exact fields:\n"
        "- direction: BULLISH or BEARISH or NEUTRAL\n"
        "- confidence: number from 0 to 100\n"
        "- reasoning: 1-2 sentence explanation\n"
        "No markdown, no code fences, no extra text. Just raw JSON."
    )

    def __init__(self, provider: str = None, model: str = None, ollama_host: str = "http://localhost:11434"):
        self.provider = provider or os.getenv("LLM_PROVIDER", "claude_cli")
        self.model = model or os.getenv("LLM_MODEL", "")
        self.ollama_host = ollama_host.rstrip("/")

    def call_llm(self, prompt: str, system_prompt: str = None) -> str:
        sys_prompt = system_prompt or self.SYSTEM_PROMPT

        if self.provider == "claude_cli":
            return self._call_claude_cli(prompt, sys_prompt)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, sys_prompt)
        elif self.provider in ["openai", "deepseek", "groq"]:
            return self._call_openai_compatible(prompt, sys_prompt)
        else:
            return self._fallback_rule_engine(prompt)

    def _call_claude_cli(self, prompt: str, system_prompt: str) -> str:
        """Call Claude via the local CLI (claude -p) — uses existing subscription, no API key needed"""
        full_prompt = f"{system_prompt}\n\nAnalyze this: {prompt}"
        try:
            result = subprocess.run(
                ["claude", "-p", "--output-format", "text"],
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0 and result.stdout.strip():
                raw_output = result.stdout.strip()
                # Extract JSON from potential markdown code fences
                json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_output, re.DOTALL)
                if json_match:
                    raw_output = json_match.group(1).strip()
                # Validate it's parseable JSON
                try:
                    json.loads(raw_output)
                    return raw_output
                except json.JSONDecodeError:
                    # Try to find JSON object in the output
                    obj_match = re.search(r'\{[^{}]*"direction"[^{}]*\}', raw_output, re.DOTALL)
                    if obj_match:
                        return obj_match.group(0)
                    return self._fallback_rule_engine(prompt)
            else:
                return self._fallback_rule_engine(prompt)
        except subprocess.TimeoutExpired:
            return self._fallback_rule_engine(prompt)
        except Exception as e:
            return self._fallback_rule_engine(prompt)

    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model or "qwen2.5:3b-instruct-q4_K_M",
            "prompt": f"System: {system_prompt}\nUser: {prompt}",
            "stream": False,
            "options": {"temperature": 0.1}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "")
        except Exception:
            return self._fallback_rule_engine(prompt)

    def _call_openai_compatible(self, prompt: str, system_prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return self._fallback_rule_engine(prompt)

        base_url = "https://api.deepseek.com/v1" if self.provider == "deepseek" else "https://api.openai.com/v1"
        url = f"{base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result["choices"][0]["message"]["content"]
        except Exception:
            return self._fallback_rule_engine(prompt)

    def _fallback_rule_engine(self, prompt: str) -> str:
        """Deterministic Financial NLP Rule Engine — fallback when Claude CLI / APIs are offline"""
        text = prompt.upper()

        bullish_high = [
            "ORDER WIN", "BAGS ORDER", "BAGS INR", "BAGS CONTRACT", "AWARDED CONTRACT",
            "RECEIVES ORDER", "WINS ORDER", "PROMOTER BUYS", "PROMOTER BUY",
            "ACQUIRES SHARES", "OPEN MARKET PURCHASE", "REVOKES PLEDGE",
            "REVOKE PLEDGE", "PLEDGE REVOCATION", "RATING UPGRADE", "UPGRADES RATING",
            "UPGRADED TO", "CABINET APPROVES", "PLI SCHEME", "GEM TENDER"
        ]
        bullish_med = [
            "ORDER", "CONTRACT", "BAGS", "AWARDED", "BUYS", "BUY", "ACQUIRES",
            "ACQUISITION", "UPGRADES", "UPGRADE", "APPROVES", "PROCUREMENT",
            "PARTNERSHIP", "PROFIT UP", "REVENUE UP", "EXPANSION",
            "PAT UP", "OUTLOOK POSITIVE", "BLOCK DEAL", "CAPACITY EXPANSION"
        ]
        bearish_high = [
            "RATING DOWNGRADE", "DOWNGRADES RATING", "DEFAULTS ON", "LOAN DEFAULT",
            "AUDITOR RESIGNS", "CFO RESIGNS", "PENALTY IMPOSED", "SEBI PENALTY",
            "PROMOTER SELLS", "PROMOTER PLEDGE INCREASE", "ADDED TO ASM",
            "ADDED TO GSM", "PROFIT DOWN", "NET LOSS", "SLUMP IN REVENUE"
        ]
        bearish_med = [
            "PENALTY", "RESIGNS", "RESIGNATION", "DOWNGRADE", "DOWNGRADES",
            "LOSS", "DEFAULT", "DEFAULTS", "PLEDGES SHARES", "PROBE",
            "INVESTIGATION", "SURVEILLANCE", "REVENUE DOWN", "MARGIN DROP",
            "SLUMP", "AUDITOR EXIT", "COST INFLATION", "DOWN YOY", "CRASH"
        ]

        if any(w in text for w in bullish_high):
            return json.dumps({"direction": "BULLISH", "confidence": 90.0,
                               "reasoning": "Strong bullish signal from high-impact corporate event."})
        elif any(w in text for w in bearish_high):
            return json.dumps({"direction": "BEARISH", "confidence": 88.0,
                               "reasoning": "Strong bearish signal from high-impact negative event."})
        elif any(w in text for w in bullish_med):
            return json.dumps({"direction": "BULLISH", "confidence": 78.0,
                               "reasoning": "Moderate bullish corporate event detected."})
        elif any(w in text for w in bearish_med):
            return json.dumps({"direction": "BEARISH", "confidence": 75.0,
                               "reasoning": "Moderate bearish corporate event detected."})
        else:
            return json.dumps({"direction": "NEUTRAL", "confidence": 45.0,
                               "reasoning": "Mixed or low-impact news headline — insufficient conviction."})


if __name__ == "__main__":
    router = LLMRouter()
    print(f"Provider: {router.provider}")
    res = router.call_llm("CRISIL upgrades debt rating for Berger Paints India Ltd to AAA Stable from AA+")
    print("Test Output:", res)
