from __future__ import annotations

import os

import yaml

from model_preflight.config import AppConfig, load_config, missing_env_vars, write_default_config
from model_preflight.preset_registry import available_presets, preset_text


def test_all_packaged_presets_parse():
    assert {"minimal", "openrouter", "multi-free-dev"}.issubset(set(available_presets()))
    for preset in available_presets():
        AppConfig.model_validate(yaml.safe_load(preset_text(preset)))


def test_provider_init_writes_one_required_openrouter_deployment(tmp_path):
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path, provider="openrouter")

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert len(enabled) == 1
    assert enabled[0].provider == "openrouter"
    assert enabled[0].required
    assert enabled[0].api_key_env == "OPENROUTER_API_KEY"


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
