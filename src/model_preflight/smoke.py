from __future__ import annotations

from pydantic import BaseModel, Field

from .router import ModelGateway


class SmokeCase(BaseModel):
    id: str
    prompt: str
    expected_substrings: list[str] = Field(default_factory=list)
    forbidden_substrings: list[str] = Field(default_factory=list)
    group: str | None = None
    temperature: float = 0.0


class SmokeResult(BaseModel):
    id: str
    passed: bool
    text: str
    failures: list[str] = Field(default_factory=list)


def score_case(case: SmokeCase, text: str) -> SmokeResult:
    failures: list[str] = []
    lowered = text.lower()
    for expected in case.expected_substrings:
        if expected.lower() not in lowered:
            failures.append(f"missing expected substring: {expected!r}")
    for forbidden in case.forbidden_substrings:
        if forbidden.lower() in lowered:
            failures.append(f"contains forbidden substring: {forbidden!r}")
    return SmokeResult(id=case.id, passed=not failures, text=text, failures=failures)


def run_smoke_cases(gateway: ModelGateway, cases: list[SmokeCase]) -> list[SmokeResult]:
    results: list[SmokeResult] = []
    for case in cases:
        text = gateway.text(case.prompt, group=case.group, temperature=case.temperature)
        results.append(score_case(case, text))
    return results
