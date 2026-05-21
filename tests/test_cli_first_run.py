from __future__ import annotations

import json

from rich.console import Console
from typer.testing import CliRunner

from model_preflight import cli
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


def test_ask_sends_one_prompt_to_default_group(tmp_path):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    result = runner.invoke(
        app,
        [
            "ask",
            "Write a poem about how ModelPreflight makes free LLM endpoints easy.",
            "--config",
            str(cfg),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Write a poem about how ModelPreflight makes free LLM endpoints easy." in result.output
    assert '"passed"' not in result.output


def test_ask_json_reports_group_and_text(tmp_path):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    result = runner.invoke(
        app,
        [
            "ask",
            "Return only: ok",
            "--config",
            str(cfg),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {
        "group": "offline_echo",
        "routes": [
            {
                "provider": "offline",
                "model": "offline/echo",
            }
        ],
        "text": "Return only: ok",
    }


def test_ask_json_can_hide_route_metadata(tmp_path):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    result = runner.invoke(
        app,
        [
            "ask",
            "Return only: ok",
            "--config",
            str(cfg),
            "--json",
            "--hide-route",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {
        "group": "offline_echo",
        "text": "Return only: ok",
    }


def test_ask_streams_text_output_by_default(tmp_path, monkeypatch):
    from model_preflight import cli

    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])
    calls = []

    class FakeGateway:
        def __init__(self, config):
            calls.append(("init", config.router.default_group))

        def stream_text(self, prompt, *, group=None, metadata=None):
            calls.append(("stream", prompt, group, metadata))
            yield "alpha"
            yield " beta"

    monkeypatch.setattr(cli, "ModelGateway", FakeGateway)

    result = runner.invoke(
        app,
        ["ask", "stream please", "--config", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert result.stdout == "alpha beta\n"
    assert "[mpf] route offline_echo" in result.stderr
    assert "[mpf]   offline: offline/echo" in result.stderr
    assert "[mpf] waiting for first token from offline_echo" in result.stderr
    assert result.stderr.endswith("\n\n")
    assert calls[1] == (
        "stream",
        "stream please",
        "offline_echo",
        {"runner": "ask", "group": "offline_echo", "stream": True},
    )


def test_ask_no_stream_uses_buffered_text(tmp_path, monkeypatch):
    from model_preflight import cli

    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])
    calls = []

    class FakeGateway:
        def __init__(self, config):
            pass

        def text(self, prompt, *, group=None, metadata=None):
            calls.append(("text", prompt, group, metadata))
            return "buffered"

    monkeypatch.setattr(cli, "ModelGateway", FakeGateway)

    result = runner.invoke(
        app,
        ["ask", "buffer please", "--config", str(cfg), "--no-stream"],
    )

    assert result.exit_code == 0, result.output
    assert result.stdout == "buffered\n"
    assert "[mpf] route offline_echo" in result.stderr
    assert calls == [
        (
            "text",
            "buffer please",
            "offline_echo",
            {"runner": "ask", "group": "offline_echo", "stream": False},
        )
    ]


def test_ask_quiet_keeps_stderr_clean(tmp_path, monkeypatch):
    from model_preflight import cli

    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    class FakeGateway:
        def __init__(self, config):
            pass

        def stream_text(self, prompt, *, group=None, metadata=None):
            yield "clean"

    monkeypatch.setattr(cli, "ModelGateway", FakeGateway)

    result = runner.invoke(
        app,
        ["ask", "quiet please", "--config", str(cfg), "--quiet"],
    )

    assert result.exit_code == 0, result.output
    assert result.stdout == "clean\n"
    assert result.stderr == ""


def test_ask_show_model_reports_model_on_stderr(tmp_path):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    result = runner.invoke(
        app,
        ["ask", "Return only: ok", "--config", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert result.stdout == "Return only: ok\n"
    assert "[mpf] route offline_echo" in result.stderr
    assert "[mpf]   offline: offline/echo" in result.stderr
    assert result.stderr.endswith("\n\n")


def test_pro_accepts_short_n_and_defaults_to_ready_group(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])
    calls = []

    def fake_run_pro_mode(gateway, prompt, **kwargs):
        calls.append({"prompt": prompt, **kwargs})
        return {"final": "final", "candidates": [], "group_winners": []}

    monkeypatch.setattr(cli, "run_pro_mode", fake_run_pro_mode)

    result = runner.invoke(
        app,
        ["pro", "prompt", "-n", "2", "--config", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert result.stdout == "final\n"
    assert calls == [
        {
            "prompt": "prompt",
            "n": 2,
            "sample_group": "offline_echo",
            "judge_group": "offline_echo",
        }
    ]
    assert "[mpf] pro fanout n=2 sample_group=offline_echo judge_group=offline_echo" in (
        result.stderr
    )


def test_pro_writes_diagnostic_artifact(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])
    artifact = tmp_path / "pro.json"

    def fake_run_pro_mode(gateway, prompt, **kwargs):
        return {
            "final": "final",
            "candidates": [{"index": 0, "ok": True, "text": "candidate", "error": None}],
            "group_winners": ["winner"],
        }

    monkeypatch.setattr(cli, "run_pro_mode", fake_run_pro_mode)

    result = runner.invoke(
        app,
        ["pro", "prompt", "--config", str(cfg), "--artifact", str(artifact)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["prompt"] == "prompt"
    assert payload["result"]["final"] == "final"


def test_pro_json_outputs_full_payload(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    def fake_run_pro_mode(gateway, prompt, **kwargs):
        return {
            "final": "final",
            "candidates": [{"index": 0, "ok": True, "text": "candidate", "error": None}],
            "group_winners": [],
        }

    monkeypatch.setattr(cli, "run_pro_mode", fake_run_pro_mode)

    result = runner.invoke(
        app,
        ["pro", "prompt", "--config", str(cfg), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["final"] == "final"
    assert payload["candidates"][0]["text"] == "candidate"


def test_pro_reports_candidate_errors_when_all_samples_fail(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    runner.invoke(app, ["init", "--preset", "minimal", "--config", str(cfg)])

    def fake_run_pro_mode(gateway, prompt, **kwargs):
        return {
            "final": "",
            "candidates": [
                {"index": 0, "ok": False, "text": "", "error": "No deployment for free_fast"},
                {"index": 1, "ok": False, "text": "", "error": "No deployment for free_fast"},
            ],
            "group_winners": [],
        }

    monkeypatch.setattr(cli, "run_pro_mode", fake_run_pro_mode)

    result = runner.invoke(
        app,
        [
            "pro",
            "prompt",
            "--config",
            str(cfg),
            "--sample-group",
            "free_fast",
            "--judge-group",
            "offline_echo",
        ],
    )

    assert result.exit_code == 2
    assert "all candidate generations failed or returned empty text" in result.stderr
    assert "No deployment for free_fast" in result.stderr


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
    monkeypatch.setenv("MODEL_PREFLIGHT_CONFIG", str(tmp_path / "default.yaml"))
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


def test_doctor_json_warns_when_custom_config_omits_default_dotenv(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    default_cfg = tmp_path / "default.yaml"
    custom_cfg = tmp_path / "custom.yaml"
    env_path = tmp_path / "private.env"
    env_path.write_text("OPENROUTER_API_KEY=secret-value\n", encoding="utf-8")
    monkeypatch.setenv("MODEL_PREFLIGHT_CONFIG", str(default_cfg))

    default_init = runner.invoke(app, ["init", "--provider", "openrouter"])
    assert default_init.exit_code == 0, default_init.output
    link_result = runner.invoke(app, ["secrets", "link", str(env_path)])
    assert link_result.exit_code == 0, link_result.output
    custom_init = runner.invoke(
        app,
        ["init", "--provider", "openrouter", "--config", str(custom_cfg)],
    )
    assert custom_init.exit_code == 0, custom_init.output

    result = runner.invoke(
        app,
        ["doctor", "--config", str(custom_cfg), "--group", "free_reasoning", "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["error_code"] == "MISSING_REQUIRED_ENV"
    assert payload["missing_env_vars"] == ["OPENROUTER_API_KEY"]
    assert payload["warnings"] == [
        "Custom config does not include default dotenv secret source(s) "
        "that can satisfy missing required env vars. Custom configs do not "
        "inherit global credentials; link the dotenv source explicitly."
    ]
    assert payload["next_commands"] == [
        "export OPENROUTER_API_KEY=...",
        f"model-preflight secrets link {env_path} --config {custom_cfg}",
    ]
    assert "secret-value" not in result.output


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


def test_providers_list_counts_only_enabled_deployments_as_configured(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "console", Console(width=240, color_system=None))
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

    result = runner.invoke(app, ["providers", "list", "--config", str(cfg)])

    assert result.exit_code == 0, result.output
    assert "│ nvidia     │ nvidia         │ NVIDIA_NIM_API_KEY │ yes" in result.output
    assert "│ openrouter │ openrouter     │ OPENROUTER_API_KEY │ yes" in result.output
    assert "│ groq       │ multi-free-dev │ GROQ_API_KEY       │ no" in result.output
    assert "│ cerebras   │ multi-free-dev │ CEREBRAS_API_KEY   │ no" in result.output
    assert "│ mistral    │ multi-free-dev │ MISTRAL_API_KEY    │ no" in result.output
