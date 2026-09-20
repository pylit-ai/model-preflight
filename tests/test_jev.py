from __future__ import annotations

import io
import json
from urllib.error import HTTPError, URLError

import pytest
import yaml
from cli_test_support import separate_stream_runner

from model_preflight import jev
from model_preflight.cli import app
from model_preflight.pro_mode import pro_mode


class Gateway:
    def __init__(self):
        self.synthesis = 0

    def text(self, prompt, **kwargs):
        if kwargs["metadata"]["phase"] == "fanout":
            return f"  answer {kwargs['metadata']['candidate_index']}\n"
        self.synthesis += 1
        return "synthesized"


def response(choice="candidate_1", confidence=0.95):
    keys = ["candidate_0", "candidate_1", "needs_synthesis", "none_adequate"]
    return {
        "model": "jev-1.13.0",
        "usage": {"input_tokens": 100, "output_tokens": 12},
        "answers": {
            "answer": {
                "type": "choice",
                "choice": choice,
                "confidence": confidence,
                "probabilities": {k: 1 if k == choice else 0 for k in keys},
            }
        },
    }


def transport(monkeypatch, body):
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            if isinstance(body, Exception):
                raise body
            return io.BytesIO(body if isinstance(body, bytes) else json.dumps(body).encode())

    monkeypatch.setenv("TYPESAFE_API_KEY", "test-only")
    monkeypatch.setattr(jev, "build_opener", lambda *args: Opener())
    return calls


def test_opt_in_exact_copy_and_metadata(monkeypatch):
    calls = transport(monkeypatch, response())
    gateway = Gateway()
    result = pro_mode(gateway, "prompt", n=2, jev_select=True)
    assert result["final"] == "  answer 1\n"
    assert gateway.synthesis == 0
    assert result["selection"]["returned_model"] == "jev-1.13.0"
    assert result["selection"]["usage"]["input_tokens"] == 100
    assert result["selection"]["attempts"] == 1
    assert result["selection"]["elapsed_seconds"] >= 0
    assert len(calls) == 1 and calls[0][1] == 10
    payload = json.loads(calls[0][0].data)
    assert payload["state"]["candidates"]["candidate_1"] == result["final"]


@pytest.mark.parametrize(
    "body",
    [
        response(confidence=0.1),
        response("needs_synthesis"),
        response("none_adequate"),
        response("unknown"),
        response(confidence=float("nan")),
        response(confidence=True),
        {},
        TimeoutError("secret error must not leak"),
    ],
)
def test_fallback(monkeypatch, body):
    calls = transport(monkeypatch, body)
    gateway = Gateway()
    result = pro_mode(gateway, "prompt", n=2, jev_select=True)
    assert result["final"] == "synthesized"
    assert gateway.synthesis == 1 and len(calls) == 1
    assert "secret" not in json.dumps(result)
    assert result["selection"]["status"] == "fallback"
    assert result["selection"]["attempts"] == 1
    assert result["selection"]["elapsed_seconds"] >= 0


@pytest.mark.parametrize(
    "mutation",
    [
        lambda b: b["answers"]["answer"].update(type="score"),
        lambda b: b["answers"]["answer"]["probabilities"].update(candidate_0=float("inf")),
        lambda b: b["answers"]["answer"]["probabilities"].pop("none_adequate"),
        lambda b: b["answers"]["answer"]["probabilities"].update(candidate_1=0.3),
        lambda b: b["usage"].update(input_tokens=True),
        lambda b: b.update(model=None),
    ],
)
def test_schema_rejected(monkeypatch, mutation):
    body = response()
    mutation(body)
    transport(monkeypatch, body)
    assert pro_mode(Gateway(), "prompt", n=2, jev_select=True)["final"] == "synthesized"


def test_default_no_egress_and_missing_key(monkeypatch):
    calls = transport(monkeypatch, response())
    assert "selection" not in pro_mode(Gateway(), "prompt", n=2)
    monkeypatch.delenv("TYPESAFE_API_KEY")
    result = pro_mode(Gateway(), "prompt", n=2, jev_select=True)
    assert result["selection"]["reason"] == "missing_key"
    assert result["selection"]["attempts"] == 0
    assert result["selection"]["elapsed_seconds"] >= 0
    assert not calls


def test_pinned_model_mismatch_falls_back_with_usage(monkeypatch):
    body = response()
    body["model"] = "jev-1.14.0"
    transport(monkeypatch, body)
    result = pro_mode(Gateway(), "prompt", n=2, jev_select=True)
    assert result["final"] == "synthesized"
    assert result["selection"]["reason"] == "model_mismatch"
    assert result["selection"]["returned_model"] == "jev-1.14.0"
    assert result["selection"]["usage"]["input_tokens"] == 100


@pytest.mark.parametrize("alias", ["jev-latest", "jev-preview"])
def test_explicit_model_alias_accepts_returned_version(monkeypatch, alias):
    transport(monkeypatch, response())
    result = pro_mode(Gateway(), "prompt", n=2, jev_select=True, jev_model=alias)
    assert result["final"] == "  answer 1\n"
    assert result["selection"]["requested_model"] == alias
    assert result["selection"]["returned_model"] == "jev-1.13.0"


def test_cli_real_entrypoint(monkeypatch, tmp_path):
    import model_preflight.cli as cli

    calls = transport(monkeypatch, response())
    monkeypatch.setattr(cli, "ModelGateway", lambda cfg: Gateway())
    runner = separate_stream_runner()
    config = tmp_path / "config.yaml"
    assert (
        runner.invoke(app, ["init", "--preset", "minimal", "--config", str(config)]).exit_code == 0
    )
    result = runner.invoke(
        app, ["pro", "prompt", "--n", "2", "--jev-select", "--config", str(config), "--json"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["final"] == "  answer 1\n"
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("scenario", "body", "reason", "attempts"),
    [
        ("available", response(), "complete_answer", 1),
        ("disabled", response(), None, 0),
        ("no_key", response(), "missing_key", 0),
        (
            "unauthorized",
            HTTPError("https://api.typesafe.ai/v1/systemone", 401, "private failure", {}, None),
            "request_or_schema_failure",
            1,
        ),
        (
            "rate_limited",
            HTTPError(
                "https://api.typesafe.ai/v1/systemone",
                429,
                "private failure",
                {"Retry-After": "120"},
                None,
            ),
            "request_or_schema_failure",
            1,
        ),
        ("unreachable", URLError("private failure"), "request_or_schema_failure", 1),
        ("timeout", TimeoutError("private failure"), "request_or_schema_failure", 1),
        ("malformed_json", b"private failure: not JSON", "request_or_schema_failure", 1),
        ("malformed_schema", {}, "request_or_schema_failure", 1),
    ],
)
def test_real_cli_availability_preserves_baseline(
    monkeypatch, tmp_path, scenario, body, reason, attempts
):
    """Exercise actual CLI, fanout, adapter and gateway synthesis; mock only Jev transport."""
    calls = transport(monkeypatch, body)
    runner = separate_stream_runner()
    config = tmp_path / "config.yaml"
    assert (
        runner.invoke(app, ["init", "--preset", "minimal", "--config", str(config)]).exit_code == 0
    )
    data = yaml.safe_load(config.read_text())
    audit = tmp_path / "audit.jsonl"
    data["router"]["audit_jsonl"] = str(audit)
    config.write_text(yaml.safe_dump(data))
    args = ["pro", "availability prompt", "--n", "2", "--config", str(config), "--json"]
    baseline = runner.invoke(app, args)
    assert baseline.exit_code == 0, baseline.output
    baseline_payload = json.loads(baseline.stdout)
    assert not calls
    audit.write_text("")
    if scenario == "no_key":
        monkeypatch.delenv("TYPESAFE_API_KEY")
    if scenario != "disabled":
        args.append("--jev-select")
    actual = runner.invoke(app, args)
    assert actual.exit_code == 0, actual.output
    payload = json.loads(actual.stdout)
    assert payload["final"] == (
        "availability prompt" if scenario == "available" else baseline_payload["final"]
    )
    assert payload["candidates"] == baseline_payload["candidates"]
    phases = [json.loads(row)["metadata"]["phase"] for row in audit.read_text().splitlines()]
    assert phases.count("fanout") == 2
    assert phases.count("synthesis") == (0 if scenario == "available" else 1)
    assert len(calls) == attempts
    assert "private failure" not in actual.stdout + actual.stderr
    if reason is None:
        assert "selection" not in payload
    else:
        assert payload["selection"]["status"] == (
            "selected" if scenario == "available" else "fallback"
        )
        assert payload["selection"]["reason"] == reason
        assert payload["selection"]["attempts"] == attempts
        assert payload["selection"]["elapsed_seconds"] >= 0
        if scenario == "available":
            assert payload["selection"]["usage"]["input_tokens"] == 100
        else:
            assert "usage" not in payload["selection"]
