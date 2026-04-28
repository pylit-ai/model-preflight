from __future__ import annotations

import os

import yaml

from model_preflight.config import (
    AppConfig,
    load_config,
    missing_env_vars,
    write_default_config,
)
from model_preflight.preset_registry import available_presets, preset_text

PROVIDER_ENV_VARS = [
    "OPENROUTER_API_KEY",
    "NVIDIA_NIM_API_KEY",
    "GROQ_API_KEY",
    "CEREBRAS_API_KEY",
    "MISTRAL_API_KEY",
]


def test_all_packaged_presets_parse():
    assert {"minimal", "nvidia", "openrouter", "multi-free-dev"}.issubset(
        set(available_presets())
    )
    for preset in available_presets():
        AppConfig.model_validate(yaml.safe_load(preset_text(preset)))


def test_provider_init_writes_one_required_nvidia_deployment(tmp_path):
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path, provider="nvidia")

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert len(enabled) == 1
    assert enabled[0].provider == "nvidia"
    assert enabled[0].required
    assert enabled[0].api_key_env == "NVIDIA_NIM_API_KEY"
    assert enabled[0].model == "nvidia_nim/nvidia/nemotron-3-super-120b-a12b"


def test_default_init_uses_openrouter_fallback_when_no_key_visible(tmp_path, monkeypatch):
    for env_var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path)

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert len(enabled) == 1
    assert enabled[0].provider == "openrouter"
    assert enabled[0].api_key_env == "OPENROUTER_API_KEY"


def test_default_init_uses_visible_nvidia_key(tmp_path, monkeypatch):
    for env_var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "test")
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path)

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert len(enabled) == 1
    assert enabled[0].provider == "nvidia"
    assert cfg.router.default_group == "free_reasoning"


def test_default_init_prefers_openrouter_when_multiple_keys_visible(tmp_path, monkeypatch):
    for env_var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "test")
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path)

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert len(enabled) == 1
    assert enabled[0].provider == "openrouter"


def test_provider_init_writes_one_required_openrouter_deployment(tmp_path):
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path, provider="openrouter")

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert len(enabled) == 1
    assert enabled[0].provider == "openrouter"
    assert enabled[0].required
    assert enabled[0].api_key_env == "OPENROUTER_API_KEY"
    assert enabled[0].model == "openrouter/nvidia/nemotron-3-super-120b-a12b:free"


def test_provider_init_writes_one_required_groq_deployment(tmp_path):
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path, provider="groq")

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert len(enabled) == 1
    assert enabled[0].provider == "groq"
    assert enabled[0].required
    assert enabled[0].api_key_env == "GROQ_API_KEY"
    assert enabled[0].group == "free_fast"
    assert cfg.router.default_group == "free_fast"


def test_minimal_preset_has_no_missing_required_env(tmp_path):
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path, preset="minimal")

    assert missing_env_vars(load_config(cfg_path)) == []


def test_doctor_missing_env_respects_required_and_provider_filter(tmp_path, monkeypatch):
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path, preset="multi-free-dev")
    cfg = load_config(cfg_path)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    assert missing_env_vars(cfg) == ["OPENROUTER_API_KEY"]
    assert missing_env_vars(cfg, provider="groq") == []

    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    assert "OPENROUTER_API_KEY" in os.environ
    assert missing_env_vars(cfg) == []
