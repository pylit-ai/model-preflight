from __future__ import annotations

from typing import Any

from model_preflight.pro_mode import pro_mode


class FlakyGateway:
    def __init__(self, *, fail_all: bool = False) -> None:
        self.fail_all = fail_all
        self.calls: list[dict[str, Any]] = []

    def text(self, prompt: str, *, group: str | None = None, **kwargs: Any) -> str:
        self.calls.append({"prompt": prompt, "group": group, **kwargs})
        metadata = kwargs.get("metadata") or {}
        if metadata.get("phase") == "fanout":
            idx = metadata["candidate_index"]
            if self.fail_all or idx == 1:
                raise RuntimeError(f"candidate {idx} failed")
            return f"candidate {idx} ok"
        return "final ok"


def test_pro_mode_synthesizes_from_successful_partial_fanout():
    gateway = FlakyGateway()

    result = pro_mode(gateway, "prompt", n=3, sample_group="sample", judge_group="judge")

    assert result["final"] == "final ok"
    assert result["candidates"][0]["ok"] is True
    assert result["candidates"][1]["ok"] is False
    assert "candidate 1 failed" in result["candidates"][1]["error"]
    synthesis_calls = [
        call for call in gateway.calls if (call["metadata"] or {}).get("phase") == "synthesis"
    ]
    assert len(synthesis_calls) == 1
    assert "candidate 0 ok" in synthesis_calls[0]["prompt"]
    assert "candidate 1 failed" not in synthesis_calls[0]["prompt"]


def test_pro_mode_returns_candidate_errors_when_all_candidates_fail():
    result = pro_mode(FlakyGateway(fail_all=True), "prompt", n=2, sample_group="sample")

    assert result["final"] == ""
    assert result["group_winners"] == []
    assert result["candidates"][0]["ok"] is False
    assert "candidate 0 failed" in result["candidates"][0]["error"]
