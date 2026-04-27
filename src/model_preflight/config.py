from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from platformdirs import user_cache_path, user_config_path
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "model-preflight"

DEFAULT_CONFIG_TEXT = """version: "1"
router:
  num_retries: 1
  timeout_seconds: 60
  default_group: free_reasoning
  audit_jsonl: null
artifacts_dir: ~/.cache/model-preflight/artifacts

deployments:
  # Exact model ids change. Pin these after checking each provider's current catalog.
  - name: openrouter_gpt_oss_120b_free
    group: free_reasoning
    model: openrouter/openai/gpt-oss-120b:free
    api_key_env: OPENROUTER_API_KEY
    rpm: 18
    tier: reasoning

  - name: groq_gpt_oss_120b
    group: free_fast
    model: groq/openai/gpt-oss-120b
    api_key_env: GROQ_API_KEY
    rpm: 10
    tier: fast

  - name: cerebras_gpt_oss_120b
    group: free_fast
    model: cerebras/gpt-oss-120b
    api_key_env: CEREBRAS_API_KEY
    rpm: 10
    tier: fast

  - name: mistral_large_experiment
    group: free_reasoning
    model: mistral/mistral-large-latest
    api_key_env: MISTRAL_API_KEY
    rpm: 5
    tier: reasoning

  # Confirm current NVIDIA NIM LiteLLM model prefix/catalog slug before enabling.
  - name: nvidia_nim_gpt_oss_120b
    enabled: false
    group: free_reasoning
    model: nvidia_nim/openai/gpt-oss-120b
    api_key_env: NVIDIA_NIM_API_KEY
    rpm: 5
    tier: reasoning
"""


class Deployment(BaseModel):
    """One concrete provider/model deployment exposed under a logical group."""

    name: str
    group: str = "free_reasoning"
    model: str
    api_key_env: str | None = None
    api_base: str | None = None
    rpm: int | None = None
    tpm: int | None = None
    enabled: bool = True
    tier: Literal["reasoning", "fast", "baseline", "judge"] = "reasoning"

    @field_validator("name", "group", "model")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class RouterSettings(BaseModel):
    num_retries: int = 1
    timeout_seconds: float = 60
    default_group: str = "free_reasoning"
    audit_jsonl: Path | None = None


class AppConfig(BaseModel):
    version: str = "1"
    router: RouterSettings = Field(default_factory=RouterSettings)
    deployments: list[Deployment] = Field(default_factory=list)
    artifacts_dir: Path = Field(default_factory=lambda: user_cache_path(APP_NAME) / "artifacts")

    @field_validator("deployments")
    @classmethod
    def at_least_one_enabled(cls, value: list[Deployment]) -> list[Deployment]:
        if value and not any(d.enabled for d in value):
            raise ValueError("at least one deployment must be enabled")
        return value


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODEL_PREFLIGHT_", extra="ignore")
    config: Path | None = None


def default_config_path() -> Path:
    env = EnvSettings()
    if env.config:
        return env.config.expanduser()
    return user_config_path(APP_NAME) / "config.yaml"


def load_config(path: Path | str | None = None) -> AppConfig:
    cfg_path = Path(path).expanduser() if path is not None else default_config_path()
    if not cfg_path.exists():
        raise FileNotFoundError(f"No config at {cfg_path}; run `mpf init` first")
    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg = AppConfig.model_validate(data)
    if cfg.router.audit_jsonl is None:
        cfg.router.audit_jsonl = cfg.artifacts_dir / "audit.jsonl"
    return cfg


def write_default_config(path: Path | str | None = None, *, overwrite: bool = False) -> Path:
    out = Path(path).expanduser() if path is not None else default_config_path()
    if out.exists() and not overwrite:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    return out


def missing_env_vars(config: AppConfig) -> list[str]:
    missing: list[str] = []
    for dep in config.deployments:
        if dep.enabled and dep.api_key_env and not os.getenv(dep.api_key_env):
            missing.append(dep.api_key_env)
    return sorted(set(missing))
