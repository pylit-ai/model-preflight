from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .router import ModelGateway, TextResult


class SmokeCase(BaseModel):
    id: str
    prompt: str
    expected_substrings: list[str] = Field(default_factory=list)
    forbidden_substrings: list[str] = Field(default_factory=list)
    group: str | None = None
    temperature: float = 0.0
    reasoning: dict[str, Any] | None = None
    include_reasoning: bool | None = None


class SmokeResult(BaseModel):
    id: str
    passed: bool
    text: str
    failures: list[str] = Field(default_factory=list)
    reasoning: str | None = None
    reasoning_details: Any | None = None
    reasoning_summary: Any | None = None
    usage: Any | None = None
    model: str | None = None
    response_id: str | None = None
    error: str | None = None


def score_case(case: SmokeCase, result: str | TextResult) -> SmokeResult:
    if isinstance(result, TextResult):
        text = result.text
        reasoning = result.reasoning
        reasoning_details = result.reasoning_details
        reasoning_summary = result.reasoning_summary
        usage = result.usage
        model = result.model
        response_id = result.response_id
    else:
        text = result
        reasoning = None
        reasoning_details = None
        reasoning_summary = None
        usage = None
        model = None
        response_id = None
    failures: list[str] = []
    lowered = text.lower()
    for expected in case.expected_substrings:
        if expected.lower() not in lowered:
            failures.append(f"missing expected substring: {expected!r}")
    for forbidden in case.forbidden_substrings:
        if forbidden.lower() in lowered:
            failures.append(f"contains forbidden substring: {forbidden!r}")
    return SmokeResult(
        id=case.id,
        passed=not failures,
        text=text,
        failures=failures,
        reasoning=reasoning,
        reasoning_details=reasoning_details,
        reasoning_summary=reasoning_summary,
        usage=usage,
        model=model,
        response_id=response_id,
    )


def run_smoke_cases(gateway: ModelGateway, cases: list[SmokeCase]) -> list[SmokeResult]:
    results: list[SmokeResult] = []
    for case in cases:
        kwargs: dict[str, Any] = {
            "group": case.group,
            "temperature": case.temperature,
            "metadata": {
                "runner": "smoke",
                "case_id": case.id,
                "case_group": case.group,
            },
        }
        if case.reasoning is not None:
            kwargs["reasoning"] = case.reasoning
        if case.include_reasoning is not None:
            kwargs["include_reasoning"] = case.include_reasoning
        try:
            if hasattr(gateway, "text_result"):
                result = gateway.text_result(case.prompt, **kwargs)
            else:
                result = gateway.text(case.prompt, **kwargs)
        except Exception as exc:  # noqa: BLE001 - preserve provider-route failures as evidence
            results.append(
                SmokeResult(
                    id=case.id,
                    passed=False,
                    text="",
                    failures=[f"provider exception: {type(exc).__name__}: {exc}"],
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        results.append(score_case(case, result))
    return results
