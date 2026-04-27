from __future__ import annotations

from typer.testing import CliRunner

from model_preflight.cli import app

runner = CliRunner()


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


def test_provider_guide_reports_valid_provider_and_env_var():
    result = runner.invoke(app, ["providers", "guide", "openrouter"])

    assert result.exit_code == 0, result.output
    assert "OPENROUTER_API_KEY" in result.output
    assert "mpf doctor --provider openrouter --live" in result.output
