from __future__ import annotations

import json

from typer.testing import CliRunner

from model_preflight.cli import app

runner = CliRunner()

PROVIDER_ENV_VARS = [
    "OPENROUTER_API_KEY",
    "NVIDIA_NIM_API_KEY",
    "GROQ_API_KEY",
    "CEREBRAS_API_KEY",
    "MISTRAL_API_KEY",
]


def test_init_minimal_demo_init_project_and_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "config.yaml"

    init_result = runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])
    assert init_result.exit_code == 0, init_result.output
    assert "next: mpf doctor --live" in init_result.output

    doctor_result = runner.invoke(app, ["doctor", "--config", str(cfg), "--live"])
    assert doctor_result.exit_code == 0, doctor_result.output
    assert "live check ok" in doctor_result.output

    demo_result = runner.invoke(app, ["demo", "--config", str(cfg)])
    assert demo_result.exit_code == 0, demo_result.output
    assert '"passed": true' in demo_result.output

    project_result = runner.invoke(app, ["init-project"])
    assert project_result.exit_code == 0, project_result.output
    assert (tmp_path / "evals/smoke.jsonl").exists()
    assert (tmp_path / ".model-preflight/README.md").exists()
    assert ".model-preflight/artifacts/" in (tmp_path / ".gitignore").read_text()

    run_result = runner.invoke(app, ["run", "--config", str(cfg)])
    assert run_result.exit_code == 0, run_result.output
    assert '"id": "basic-route"' in run_result.output


def test_run_without_default_cases_points_to_init_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    result = runner.invoke(app, ["run", "--config", str(cfg)])

    assert result.exit_code == 2
    assert "next: mpf init-project" in result.output


def test_openrouter_doctor_missing_key_is_actionable(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--provider", "openrouter", "--config", str(cfg)])

    result = runner.invoke(app, ["doctor", "--config", str(cfg)])

    assert result.exit_code == 2
    assert "missing required env vars: OPENROUTER_API_KEY" in result.output
    assert "next: export OPENROUTER_API_KEY=..." in result.output


def test_init_without_visible_keys_reports_openrouter_fallback(tmp_path, monkeypatch):
    for env_var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    cfg = tmp_path / "config.yaml"

    result = runner.invoke(app, ["init", "--config", str(cfg)])

    assert result.exit_code == 0, result.output
    assert "no supported provider key visible" in result.output
    assert "OPENROUTER_API_KEY" in result.output


def test_doctor_json_missing_env_has_stable_error(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--provider", "openrouter", "--config", str(cfg)])

    result = runner.invoke(
        app,
        ["doctor", "--config", str(cfg), "--group", "free_reasoning", "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["error_code"] == "MISSING_REQUIRED_ENV"
    assert payload["selected_group"] == "free_reasoning"
    assert payload["enabled_groups"] == ["free_reasoning"]
    assert payload["missing_env_vars"] == ["OPENROUTER_API_KEY"]
    assert payload["next_commands"] == ["export OPENROUTER_API_KEY=..."]


def test_doctor_json_group_not_found_has_stable_error(tmp_path):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--provider", "openrouter", "--config", str(cfg)])

    result = runner.invoke(
        app,
        ["doctor", "--config", str(cfg), "--group", "local_fast", "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["error_code"] == "GROUP_NOT_FOUND"
    assert payload["selected_group"] == "local_fast"
    assert payload["enabled_groups"] == ["free_reasoning"]
    assert payload["missing_env_vars"] == []


def test_secrets_link_and_doctor_json_report_ready_deployment(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text('OPENROUTER_API_KEY="secret-value"\n', encoding="utf-8")
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--provider", "openrouter", "--config", str(cfg)])

    link_result = runner.invoke(app, ["secrets", "link", str(env_path), "--config", str(cfg)])
    assert link_result.exit_code == 0, link_result.output
    assert "secret-value" not in link_result.output

    result = runner.invoke(app, ["secrets", "doctor", "--config", str(cfg), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["ready_deployments"] == ["openrouter_nemotron_3_super_free"]
    assert payload["secret_sources"][1]["kind"] == "dotenv"
    assert payload["secret_sources"][1]["exists"] is True
    assert "secret-value" not in result.output


def test_init_provider_with_fallback_and_doctor_json_warns_when_primary_missing(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text('OPENROUTER_API_KEY="fallback-secret"\n', encoding="utf-8")
    cfg = tmp_path / "config.yaml"

    init_result = runner.invoke(
        app,
        [
            "init",
            "--provider",
            "nvidia",
            "--fallback",
            "openrouter",
            "--config",
            str(cfg),
        ],
    )
    assert init_result.exit_code == 0, init_result.output
    runner.invoke(app, ["secrets", "link", str(env_path), "--config", str(cfg)])

    result = runner.invoke(
        app,
        ["doctor", "--config", str(cfg), "--group", "free_reasoning", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["error_code"] is None
    assert payload["ready_deployments"] == ["openrouter_nemotron_3_super_free"]
    assert payload["blocked_deployments"] == ["nvidia_nim_nemotron_3_super"]
    assert payload["missing_env_vars"] == ["NVIDIA_NIM_API_KEY"]
    assert payload["warnings"]
    assert "fallback-secret" not in result.output


def test_doctor_json_returns_no_ready_deployment_when_fallback_group_has_no_keys(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cfg = tmp_path / "config.yaml"
    runner.invoke(
        app,
        [
            "init",
            "--provider",
            "nvidia",
            "--fallback",
            "openrouter",
            "--config",
            str(cfg),
        ],
    )

    result = runner.invoke(
        app,
        ["doctor", "--config", str(cfg), "--group", "free_reasoning", "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["error_code"] == "NO_READY_DEPLOYMENT"
    assert payload["missing_env_vars"] == ["NVIDIA_NIM_API_KEY", "OPENROUTER_API_KEY"]


def test_setup_writes_primary_fallback_links_env_file_and_reports_ready(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text(
        'NVIDIA_NIM_API_KEY="primary-secret"\nOPENROUTER_API_KEY="fallback-secret"\n',
        encoding="utf-8",
    )
    cfg = tmp_path / "config.yaml"

    result = runner.invoke(
        app,
        [
            "setup",
            "--config",
            str(cfg),
            "--env-file",
            str(env_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["ready_deployments"] == [
        "nvidia_nim_nemotron_3_super",
        "openrouter_nemotron_3_super_free",
    ]
    assert "primary-secret" not in result.output
    assert "fallback-secret" not in result.output


def test_paths_reports_config_and_artifacts():
    result = runner.invoke(app, ["paths"])

    assert result.exit_code == 0, result.output
    assert "config:" in result.output
    assert "config.yaml" in result.output
    assert "artifacts:" in result.output


def test_provider_guide_reports_valid_provider_and_env_var():
    result = runner.invoke(app, ["providers", "guide", "openrouter"])

    assert result.exit_code == 0, result.output
    assert "OPENROUTER_API_KEY" in result.output
    assert "mpf doctor --provider openrouter --live" in result.output
