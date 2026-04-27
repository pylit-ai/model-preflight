from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from platformdirs import user_cache_path, user_config_path
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .preset_registry import preset_for_provider, preset_text

APP_NAME = "model-preflight"

DEFAULT_PRESET = "openrouter"


class Deployment(BaseModel):
    """One concrete provider/model deployment exposed under a logical group."""

    name: str
    provider: str | None = None
    group: str = "free_reasoning"
    model: str
    api_key_env: str | None = None
    api_base: str | None = None
    rpm: int | None = None
    tpm: int | None = None
    enabled: bool = True
    required: bool = True
    status: Literal["required", "optional", "best_effort", "offline"] = "required"
    setup_url: str | None = None
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


def write_default_config(
    path: Path | str | None = None,
    *,
    overwrite: bool = False,
    preset: str | None = None,
    provider: str | None = None,
) -> Path:
    out = Path(path).expanduser() if path is not None else default_config_path()
    if out.exists() and not overwrite:
        return out
    preset_name = preset_for_provider(provider) if provider else (preset or DEFAULT_PRESET)
    text = preset_text(preset_name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def selected_deployments(
    config: AppConfig,
    *,
    group: str | None = None,
    provider: str | None = None,
    include_disabled: bool = False,
) -> list[Deployment]:
    selected: list[Deployment] = []
    effective_group = group
    if effective_group is None and provider is None:
        effective_group = config.router.default_group
    for dep in config.deployments:
        if not include_disabled and not dep.enabled:
            continue
        if effective_group is not None and dep.group != effective_group:
            continue
        if provider is not None and dep.provider != provider:
            continue
        selected.append(dep)
    return selected


def missing_env_vars(
    config: AppConfig,
    *,
    group: str | None = None,
    provider: str | None = None,
    required_only: bool = True,
) -> list[str]:
    missing: list[str] = []
    for dep in selected_deployments(config, group=group, provider=provider):
        if required_only and not dep.required:
            continue
        if dep.api_key_env and not os.getenv(dep.api_key_env):
            missing.append(dep.api_key_env)
    return sorted(set(missing))
