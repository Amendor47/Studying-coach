"""Unified adapter for various LLM backends.

Supports local providers (Ollama, GPT4All) and OpenAI-compatible
servers such as LM Studio or llama.cpp. A mock client is also provided
for tests.
"""
from __future__ import annotations

import os
from typing import List, Tuple
import requests

from .config import LLMSettings


class LLMClient:
    def __init__(self, settings: LLMSettings):
        self.s = settings

    @staticmethod
    def from_settings(settings: LLMSettings) -> "LLMClient":
        provider = settings.provider.lower()
        if provider == "ollama":
            return OllamaClient(settings)
        if provider in {"lmstudio", "llamacpp", "vllm", "openai", "azure"}:
            return OpenAICompatClient(settings)
        if provider == "gpt4all":
            return GPT4AllClient(settings)
        if provider == "mock":
            return MockClient(settings)
        return MockClient(settings)

    # default implementations
    def chat(self, messages: List[dict], stream: bool = False):
        raise NotImplementedError

    def complete(self, prompt: str, stream: bool = False):
        raise NotImplementedError

    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def healthcheck(self) -> Tuple[bool, str]:
        try:
            self.embed(["ping"])
            return True, "ok"
        except Exception as e:  # pragma: no cover
            return False, str(e)


class OllamaClient(LLMClient):
    """Client for the Ollama HTTP API."""

    def _host(self) -> str:
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def chat(self, messages: List[dict], stream: bool = False):
        url = self._host() + "/api/chat"
        payload = {"model": self.s.model, "messages": messages, "stream": stream}
        r = requests.post(url, json=payload, timeout=self.s.timeout_s)
        r.raise_for_status()
        return r.json()

    def complete(self, prompt: str, stream: bool = False):
        url = self._host() + "/api/generate"
        payload = {"model": self.s.model, "prompt": prompt, "stream": stream}
        r = requests.post(url, json=payload, timeout=self.s.timeout_s)
        r.raise_for_status()
        return r.json()

    def embed(self, texts: List[str]) -> List[List[float]]:
        url = self._host() + "/api/embeddings"
        out = []
        model = self.s.embedding_model or "nomic-embed-text"
        for t in texts:
            r = requests.post(url, json={"model": model, "prompt": t}, timeout=self.s.timeout_s)
            r.raise_for_status()
            out.append(r.json()["embedding"])
        return out


class OpenAICompatClient(LLMClient):
    """For servers exposing an OpenAI-compatible REST API."""

    def _headers(self):
        key = os.getenv(self.s.api_key_env, "") if self.s.api_key_env else ""
        return {"Authorization": f"Bearer {key}"} if key else {}

    def _base(self) -> str:
        return self.s.api_base or "http://localhost:1234/v1"

    def chat(self, messages: List[dict], stream: bool = False):
        url = self._base() + "/chat/completions"
        payload = {
            "model": self.s.model,
            "messages": messages,
            "temperature": self.s.temperature,
            "stream": stream,
        }
        r = requests.post(url, json=payload, headers=self._headers(), timeout=self.s.timeout_s)
        r.raise_for_status()
        return r.json()

    def complete(self, prompt: str, stream: bool = False):
        url = self._base() + "/completions"
        payload = {"model": self.s.model, "prompt": prompt, "temperature": self.s.temperature}
        r = requests.post(url, json=payload, headers=self._headers(), timeout=self.s.timeout_s)
        r.raise_for_status()
        return r.json()

    def embed(self, texts: List[str]) -> List[List[float]]:
        url = self._base() + "/embeddings"
        model = self.s.embedding_model or self.s.model
        payload = {"model": model, "input": texts}
        r = requests.post(url, json=payload, headers=self._headers(), timeout=self.s.timeout_s)
        r.raise_for_status()
        data = r.json().get("data", [])
        return [d.get("embedding", []) for d in data]


class GPT4AllClient(LLMClient):
    """Lightweight local model via gpt4all package."""

    def __init__(self, settings: LLMSettings):
        super().__init__(settings)
        from gpt4all import GPT4All

        self.llm = GPT4All(settings.model)

    def chat(self, messages: List[dict], stream: bool = False):  # pragma: no cover
        prompt = "\n".join(m.get("content", "") for m in messages)
        return {"text": self.llm.generate(prompt, temp=self.s.temperature)}

    def complete(self, prompt: str, stream: bool = False):  # pragma: no cover
        return {"text": self.llm.generate(prompt, temp=self.s.temperature)}

    def embed(self, texts: List[str]) -> List[List[float]]:
        from .embeddings import local_embed

        return local_embed(texts, self.s)


class MockClient(LLMClient):
    """Simple mock used for tests."""

    def chat(self, messages: List[dict], stream: bool = False):
        return {"choices": [{"message": {"content": "MOCK"}}]}

    def complete(self, prompt: str, stream: bool = False):
        return {"text": "MOCK"}

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 3 for _ in texts]
