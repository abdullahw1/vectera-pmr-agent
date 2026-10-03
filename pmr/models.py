"""Bounded, cached API calls. Models select verified quotes and read chart pixels."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from pathlib import Path

from .evidence import digest


class Model:
    def __init__(self, cache: Path, ledger):
        self.cache, self.ledger = cache, ledger
        self.provider = (
            "openai"
            if os.getenv("OPENAI_API_KEY")
            else "anthropic" if os.getenv("ANTHROPIC_API_KEY") else None
        )
        self.name = os.getenv(
            "PMR_MODEL", "gpt-4.1-2025-04-14" if self.provider == "openai" else "claude-sonnet-4-6"
        )
        self.vision_name = os.getenv(
            "PMR_VISION_MODEL", "gpt-4.1-mini-2025-04-14" if self.provider == "openai" else self.name
        )
        self.deadline = time.monotonic() + 600
        self.calls = 0
        self.usage = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.failures = 0
        cache.mkdir(parents=True, exist_ok=True)

    def ask(self, prompt, image=None):
        if not self.provider:
            return None
        model_name = self.vision_name if image else self.name
        key = digest(
            dict(
                provider=self.provider,
                model=model_name,
                prompt=prompt,
                image=base64.b64encode(image).decode() if image else None,
            )
        )
        cached = self.cache / (key + ".json")
        if cached.exists():
            try:
                value = json.loads(cached.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    self.cache_hits += 1
                    return value
            except (ValueError, OSError):
                self.ledger.issue(
                    "invalid_cache", "Unreadable model cache ignored; attempting a fresh request"
                )
        remaining = self.deadline - time.monotonic()
        self.cache_misses += 1
        if remaining <= 0:
            self.ledger.issue(
                "model_budget", "Ten-minute API time budget exhausted; remaining enrichment omitted"
            )
            return None
        if self.provider == "openai":
            content = [{"type": "text", "text": prompt}]
            if image:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + base64.b64encode(image).decode()},
                    }
                )
            body = dict(
                model=model_name,
                temperature=0,
                seed=0,
                messages=[dict(role="user", content=content)],
                response_format={"type": "json_object"},
                max_tokens=3000,
            )
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]}
        else:
            content = []
            if image:
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64.b64encode(image).decode(),
                        },
                    }
                )
            content.append({"type": "text", "text": prompt + " Return only JSON, without Markdown fences."})
            body = dict(
                model=model_name,
                temperature=0,
                max_tokens=3000,
                messages=[dict(role="user", content=content)],
            )
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}
        request = urllib.request.Request(
            url, json.dumps(body).encode(), {**headers, "Content-Type": "application/json"}
        )
        try:
            self.calls += 1
            with urllib.request.urlopen(request, timeout=min(45, remaining)) as response:
                data = json.load(response)
            self.usage.append(data.get("usage", {}))
            text = (
                data["choices"][0]["message"]["content"]
                if self.provider == "openai"
                else "".join(c.get("text", "") for c in data["content"])
            )
            result = json.loads(text)
            if not isinstance(result, dict):
                raise ValueError("Model response must be a JSON object")
            cached.write_text(json.dumps(result, indent=2), encoding="utf-8")
            return result
        except Exception as error:
            self.failures += 1
            # Do not leak headers or keys in diagnostics; failed enrichment must not destroy the draft.
            self.ledger.issue(
                "model_unavailable",
                f"{self.provider} enrichment failed ({type(error).__name__}); source-only draft retained",
            )
            return None


def selected_quotes(text, model):
    result = model.ask(
        "Select up to three complete sentences most useful for investment commentary. "
        "Copy them EXACTLY from the supplied text. Do not calculate, paraphrase, or add claims. "
        'Return JSON {"quotes": ["exact sentence"]}. Source:\n' + text
    )
    if result:
        return [q for q in result.get("quotes", []) if isinstance(q, str) and q in text]
    return []
