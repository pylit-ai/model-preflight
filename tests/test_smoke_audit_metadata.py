from __future__ import annotations

from typing import Any

from model_preflight.router import TextResult
from model_preflight.smoke import SmokeCase, run_smoke_cases


class RecordingGateway:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def text(self, prompt: str, *, group: str | None = None, **kwargs: Any) -> str:
        self.calls.append({"prompt": prompt, "group": group, **kwargs})
        return "ok"


def test_smoke_runner_passes_case_metadata_to_gateway():
    gateway = RecordingGateway()
    cases = [SmokeCase(id="case-1", prompt="Return only: ok", expected_substrings=["ok"])]

    results = run_smoke_cases(gateway, cases)  # type: ignore[arg-type]

    assert results[0].passed
    assert gateway.calls[0]["metadata"] == {
        "runner": "smoke",
        "case_id": "case-1",
        "case_group": None,
    }


class ReasoningGateway:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def text_result(self, prompt: str, *, group: str | None = None, **kwargs: Any) -> TextResult:
        self.calls.append({"prompt": prompt, "group": group, **kwargs})
        return TextResult(
            text="ok",
            reasoning="visible provider reasoning",
            reasoning_details=[{"type": "reasoning.text", "text": "detail"}],
            reasoning_summary=[{"text": "summary"}],
            usage={"completion_tokens": 4, "reasoning_tokens": 2},
            model="openrouter/test-reasoning",
            response_id="resp-1",
        )


def test_smoke_runner_preserves_reasoning_artifacts():
    gateway = ReasoningGateway()
    cases = [
        SmokeCase(
            id="case-1",
            prompt="Return only: ok",
            expected_substrings=["ok"],
            reasoning={"enabled": True, "exclude": False},
            include_reasoning=True,
        )
    ]

    results = run_smoke_cases(gateway, cases)  # type: ignore[arg-type]

    assert gateway.calls[0]["reasoning"] == {"enabled": True, "exclude": False}
    assert gateway.calls[0]["include_reasoning"] is True
    assert results[0].passed
    assert results[0].reasoning == "visible provider reasoning"
    assert results[0].reasoning_details == [{"type": "reasoning.text", "text": "detail"}]
    assert results[0].reasoning_summary == [{"text": "summary"}]
    assert results[0].usage == {"completion_tokens": 4, "reasoning_tokens": 2}
    assert results[0].model == "openrouter/test-reasoning"
    assert results[0].response_id == "resp-1"


class FailingGateway:
    def text_result(self, prompt: str, *, group: str | None = None, **kwargs: Any) -> TextResult:
        raise RuntimeError("provider route failed")


def test_smoke_runner_preserves_provider_exceptions_as_results():
    cases = [SmokeCase(id="case-1", prompt="Return only: ok", expected_substrings=["ok"])]

    results = run_smoke_cases(FailingGateway(), cases)  # type: ignore[arg-type]

    assert not results[0].passed
    assert results[0].text == ""
    assert results[0].failures == ["provider exception: RuntimeError: provider route failed"]
    assert results[0].error == "RuntimeError: provider route failed"
