from dataclasses import dataclass
from pathlib import Path
import os
import yaml


@dataclass
class LLMSettings:
    provider: str
    model: str
    api_base: str | None = None
    api_key_env: str | None = None
    temperature: float = 0.1
    embedding_model: str | None = None
    top_k: int = 5
    timeout_s: int = 60
    extra: dict | None = None


def load_settings() -> LLMSettings:
    profile = os.getenv("SC_PROFILE", "local")
    settings_file = Path(f"settings-{profile}.yaml")
    if not settings_file.exists():
        raise FileNotFoundError(f"Missing settings file: {settings_file}")
    data = yaml.safe_load(settings_file.read_text(encoding="utf-8")) or {}
    return LLMSettings(
        provider=data.get("provider", profile),
        model=data.get("model", ""),
        api_base=data.get("api_base"),
        api_key_env=data.get("api_key_env"),
        temperature=float(data.get("temperature", 0.1)),
        embedding_model=data.get("embedding_model"),
        top_k=int(data.get("top_k", 5)),
        timeout_s=int(data.get("timeout_s", 60)),
        extra=data.get("extra", {}) or {},
    )
