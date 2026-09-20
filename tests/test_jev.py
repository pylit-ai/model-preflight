from __future__ import annotations

import io
import json

import pytest
from typer.testing import CliRunner

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
            return io.BytesIO(json.dumps(body).encode())

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
    runner = CliRunner(mix_stderr=False)
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
