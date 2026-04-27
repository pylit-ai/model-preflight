from __future__ import annotations

from typing import Any

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
