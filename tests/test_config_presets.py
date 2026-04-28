from __future__ import annotations

import os

import yaml

from model_preflight.config import (
    AppConfig,
    Deployment,
    SecretSource,
    SecretsSettings,
    load_config,
    missing_env_vars,
    resolve_secret,
    write_default_config,
)
from model_preflight.preset_registry import available_presets, preset_text
from model_preflight.router import _deployment_to_litellm

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


def test_dotenv_secret_source_resolves_without_mutating_environment(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        'NVIDIA_NIM_API_KEY="from-dotenv"\nOPENROUTER_API_KEY="fallback"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    cfg = AppConfig(
        secrets=SecretsSettings(
            sources=[
                SecretSource(kind="env"),
                SecretSource(kind="dotenv", path=env_path),
            ]
        ),
        deployments=[
            Deployment(
                name="nvidia",
                provider="nvidia",
                model="nvidia/model",
                api_key_env="NVIDIA_NIM_API_KEY",
            )
        ],
    )

    assert resolve_secret(cfg, "NVIDIA_NIM_API_KEY") == "from-dotenv"
    assert "NVIDIA_NIM_API_KEY" not in os.environ
    assert missing_env_vars(cfg) == []


def test_process_env_overrides_dotenv_secret_source(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text('NVIDIA_NIM_API_KEY="from-dotenv"\n', encoding="utf-8")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "from-env")
    cfg = AppConfig(
        secrets=SecretsSettings(
            sources=[
                SecretSource(kind="env"),
                SecretSource(kind="dotenv", path=env_path),
            ]
        ),
    )

    assert resolve_secret(cfg, "NVIDIA_NIM_API_KEY") == "from-env"


def test_missing_dotenv_secret_source_does_not_break_config_load(tmp_path):
    cfg_path = tmp_path / "mpf.yaml"
    cfg_path.write_text(
        "\n".join(
            [
                'version: "1"',
                "secrets:",
                "  sources:",
                "    - kind: env",
                "    - kind: dotenv",
                f"      path: {tmp_path / 'missing.env'}",
                "deployments:",
                "  - name: offline",
                "    provider: offline",
                "    group: free_reasoning",
                "    model: offline/echo",
                "    api_key_env: null",
            ]
        ),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)

    assert cfg.secrets.sources[1].kind == "dotenv"
    assert cfg.secrets.sources[1].path == tmp_path / "missing.env"


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


def test_provider_init_with_fallback_writes_two_enabled_deployments(tmp_path):
    cfg_path = tmp_path / "mpf.yaml"
    write_default_config(cfg_path, provider="nvidia", fallback_provider="openrouter")

    cfg = load_config(cfg_path)

    enabled = [dep for dep in cfg.deployments if dep.enabled]
    assert [dep.provider for dep in enabled] == ["nvidia", "openrouter"]
    assert [dep.group for dep in enabled] == ["free_reasoning", "free_reasoning"]
    assert all(dep.required for dep in enabled)


def test_router_uses_dotenv_resolved_secret(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text('OPENROUTER_API_KEY="from-dotenv"\n', encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cfg = AppConfig(
        secrets=SecretsSettings(
            sources=[
                SecretSource(kind="env"),
                SecretSource(kind="dotenv", path=env_path),
            ]
        ),
        deployments=[
            Deployment(
                name="openrouter",
                provider="openrouter",
                model="openrouter/model",
                api_key_env="OPENROUTER_API_KEY",
            )
        ],
    )

    row = _deployment_to_litellm(cfg.deployments[0], cfg)

    assert row["litellm_params"]["api_key"] == "from-dotenv"
