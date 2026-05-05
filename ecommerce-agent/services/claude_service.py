"""Claude API service wrapper with caching for the Marketing AI Agent."""

import json
import time

try:
    from anthropic import Anthropic, AnthropicError
except ImportError:
    Anthropic = None
    AnthropicError = Exception


class ClaudeService:
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._cache = {}
        if Anthropic and api_key:
            self._client = Anthropic(api_key=api_key)

    @property
    def available(self) -> bool:
        return self._client is not None

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        if not self._client:
            return self._mock_complete(system_prompt, user_prompt)

        cache_key = hash(system_prompt + user_prompt)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = resp.content[0].text
            self._cache[cache_key] = text
            return text
        except AnthropicError as e:
            return f"[API Error: {e}]"

    def analyze_sentiment_batch(self, texts: list[str]) -> list[dict]:
        if not texts:
            return []

        joined = "\n---\n".join(
            f"[{i}] {t[:300]}" for i, t in enumerate(texts)
        )
        system = (
            "You are a sentiment analyst for e-commerce reviews. "
            "For each review (marked [N]), output a JSON object with: "
            '{"index": N, "sentiment": "positive"|"negative"|"neutral", '
            '"score": 0.0-1.0 (1.0=very positive), "issues": [string], '
            '"key_phrase": "short summary"}. '
            "Return a valid JSON array only, no other text."
        )
        result = self.complete(system, joined, max_tokens=2048)
        try:
            parsed = json.loads(self._extract_json(result))
            return parsed if isinstance(parsed, list) else [parsed]
        except (json.JSONDecodeError, ValueError):
            return self._mock_sentiment(texts)

    def generate_copy(
        self, product_title: str, features: list[str], tone: str, content_type: str, market: str
    ) -> str:
        system = (
            f"You are an expert e-commerce copywriter for {market} market. "
            f"Write compelling {content_type} copy. Tone: {tone}. "
            "Optimize for conversion. Keep to platform character limits."
        )
        prompt = (
            f"Product: {product_title}\n"
            f"Key Features: {', '.join(features)}\n"
            f"Generate {content_type} copy."
        )
        return self.complete(system, prompt, max_tokens=800, temperature=0.7)

    def generate_decision(
        self, context: str, options: list[str]
    ) -> str:
        system = (
            "You are a strategic pricing and bidding advisor for e-commerce. "
            "Analyze the context, evaluate each option, then recommend the best one "
            "with concise reasoning (2-3 sentences)."
        )
        prompt = f"Context:\n{context}\n\nOptions:\n" + "\n".join(
            f"- {o}" for o in options
        )
        return self.complete(system, prompt, max_tokens=600, temperature=0.4)

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        return text

    def _mock_complete(self, system_prompt: str, user_prompt: str) -> str:
        time.sleep(0.05)
        return "[Mock] Claude API not configured — placeholder response."

    def _mock_sentiment(self, texts: list[str]) -> list[dict]:
        import random
        results = []
        negative_triggers = [
            "broke", "poor", "terrible", "disappointed", "waste", "cheap",
            "stopped working", "bad", "awful", "returned", "defective",
            "battery life is", "fell apart", "not worth", "arrived damaged",
        ]
        for i, text in enumerate(texts):
            txt_lower = text.lower()
            is_neg = any(t in txt_lower for t in negative_triggers)
            score = random.uniform(0.1, 0.4) if is_neg else random.uniform(0.55, 0.95)
            label = "negative" if score < 0.4 else ("positive" if score > 0.6 else "neutral")
            issues = (
                [random.choice(["quality", "durability", "packaging", "battery", "accuracy"])]
                if label == "negative"
                else []
            )
            results.append({
                "index": i,
                "sentiment": label,
                "score": round(score, 2),
                "issues": issues,
                "key_phrase": txt_lower[:40] + "...",
            })
        return results
