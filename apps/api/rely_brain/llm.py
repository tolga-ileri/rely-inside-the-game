"""AI provider abstraction.

AI_PROVIDER=none (default)          -> deterministic templates only, no network.
AI_PROVIDER=microsoft_foundry       -> Azure AI Foundry model inference via `azure-ai-inference`
                                       (FOUNDRY_ENDPOINT, FOUNDRY_API_KEY, FOUNDRY_MODEL).
Providers return parsed JSON objects (structured output via response_format="json_object").
Streaming is exposed where the SDK supports it (`stream=True` on ChatCompletionsClient.complete).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable, Iterator
from typing import Any, Protocol


class ProviderError(RuntimeError):
    pass


class LLMProvider(Protocol):
    name: str
    model: str | None
    supports_stream: bool

    def complete_json(self, system: str, user: str) -> dict[str, Any]: ...

    def stream_text(self, system: str, user: str) -> Iterator[str]: ...


class NoProvider:
    name = "none"
    model: str | None = None
    supports_stream = False

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        raise ProviderError("AI provider disabled (AI_PROVIDER=none)")

    def stream_text(self, system: str, user: str) -> Iterator[str]:
        raise ProviderError("AI provider disabled (AI_PROVIDER=none)")


class FoundryProvider:
    """Azure AI Foundry chat completions through the azure-ai-inference SDK.

    `client_factory` is injectable so tests can run without credentials or network.
    """

    name = "microsoft_foundry"
    supports_stream = True

    def __init__(self, endpoint: str | None = None, api_key: str | None = None, model: str | None = None,
                 timeout: float | None = None, client_factory: Callable[[], Any] | None = None):
        self.endpoint = endpoint or os.getenv("FOUNDRY_ENDPOINT", "")
        self._key = api_key or os.getenv("FOUNDRY_API_KEY", "")
        self.model = model or os.getenv("FOUNDRY_MODEL", "gpt-4o-mini")
        self.timeout = timeout or float(os.getenv("FOUNDRY_TIMEOUT_SECONDS", "12"))
        self._factory = client_factory
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            if self._factory is not None:
                self._client = self._factory()
            else:
                if not self.endpoint or not self._key:
                    raise ProviderError("FOUNDRY_ENDPOINT / FOUNDRY_API_KEY not configured")
                from azure.ai.inference import ChatCompletionsClient
                from azure.core.credentials import AzureKeyCredential

                self._client = ChatCompletionsClient(endpoint=self.endpoint, credential=AzureKeyCredential(self._key))
        return self._client

    @staticmethod
    def _messages(system: str, user: str) -> list[dict[str, str]]:
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        try:
            resp = self._get_client().complete(messages=self._messages(system, user), model=self.model,
                                               response_format="json_object", temperature=0.2, max_tokens=700,
                                               connection_timeout=self.timeout, read_timeout=self.timeout)
            content = resp.choices[0].message.content
        except ProviderError:
            raise
        except Exception as exc:  # network, auth, timeout, content filter
            raise ProviderError(f"Foundry call failed: {type(exc).__name__}") from exc
        try:
            data = json.loads(content)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ProviderError("Foundry returned non-JSON content") from exc
        if not isinstance(data, dict):
            raise ProviderError("Foundry returned a non-object JSON value")
        return data

    def stream_text(self, system: str, user: str) -> Iterator[str]:
        try:
            updates = self._get_client().complete(messages=self._messages(system, user), model=self.model, stream=True,
                                                  temperature=0.2, max_tokens=700)
            for upd in updates:
                if upd.choices and upd.choices[0].delta and upd.choices[0].delta.content:
                    yield upd.choices[0].delta.content
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Foundry stream failed: {type(exc).__name__}") from exc


def get_provider() -> LLMProvider:
    kind = os.getenv("AI_PROVIDER", "none").strip().lower()
    if kind == "microsoft_foundry":
        return FoundryProvider()
    return NoProvider()


class ResponseCache:
    """In-memory cache keyed by state hash + moment + persona + locale + model."""

    def __init__(self, max_items: int = 512):
        self._d: dict[str, tuple[float, Any]] = {}
        self.max_items = max_items
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(state_hash: str, moment_id: str, persona: str, locale: str, model: str | None) -> str:
        return hashlib.sha256(f"{state_hash}|{moment_id}|{persona}|{locale}|{model}".encode()).hexdigest()

    def get(self, key: str) -> Any:
        hit = self._d.get(key)
        if hit is None:
            self.misses += 1
            return None
        self.hits += 1
        return hit[1]

    def put(self, key: str, value: Any) -> None:
        if len(self._d) >= self.max_items:
            oldest = min(self._d, key=lambda k: self._d[k][0])
            del self._d[oldest]
        self._d[key] = (time.time(), value)


CACHE = ResponseCache()
