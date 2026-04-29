from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Any

from .router import ModelGateway


@dataclass(frozen=True)
class CandidateResult:
    index: int
    ok: bool
    text: str = ""
    error: str | None = None


def fanout(
    gateway: ModelGateway,
    prompt: str,
    *,
    group: str,
    n: int,
    temperature: float = 0.9,
    max_workers: int = 16,
    max_tokens: int | None = None,
) -> list[CandidateResult]:
    results: list[CandidateResult] = [CandidateResult(index=i, ok=False) for i in range(n)]
    workers = min(max_workers, n)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(
                gateway.text,
                prompt,
                group=group,
                temperature=temperature,
                max_tokens=max_tokens,
                metadata={"phase": "fanout", "candidate_index": i},
            ): i
            for i in range(n)
        }
        for fut in as_completed(futs):
            idx = futs[fut]
            try:
                results[idx] = CandidateResult(index=idx, ok=True, text=fut.result())
            except Exception as exc:  # noqa: BLE001 - preserve provider failure detail for callers.
                results[idx] = CandidateResult(index=idx, ok=False, error=str(exc))
    return results


def synthesize(
    gateway: ModelGateway,
    prompt: str,
    candidates: list[str],
    *,
    group: str,
    max_tokens: int | None = None,
) -> str:
    numbered = "\n\n".join(
        f"<candidate index={i}>\n{c}\n</candidate>" for i, c in enumerate(candidates) if c.strip()
    )
    synthesis_prompt = f"""You are a strict research-eval judge/synthesizer.
Given the original prompt and candidate outputs, return the single best answer.
Preserve correct reasoning, remove contradictions, and do not mention the candidate process.

<original_prompt>
{prompt}
</original_prompt>

{numbered}
"""
    return gateway.text(
        synthesis_prompt,
        group=group,
        temperature=0.2,
        max_tokens=max_tokens,
        metadata={"phase": "synthesis", "candidate_count": len(candidates)},
    )


def pro_mode(
    gateway: ModelGateway,
    prompt: str,
    *,
    n: int = 8,
    sample_group: str = "free_fast",
    judge_group: str = "free_reasoning",
    tournament_group_size: int = 10,
    max_workers: int = 16,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    candidate_results = fanout(
        gateway,
        prompt,
        group=sample_group,
        n=n,
        max_workers=max_workers,
        max_tokens=max_tokens,
    )
    nonempty = [c.text for c in candidate_results if c.ok and c.text.strip()]
    if not nonempty:
        return {
            "final": "",
            "candidates": [asdict(c) for c in candidate_results],
            "group_winners": [],
        }
    if len(nonempty) <= tournament_group_size:
        final = synthesize(gateway, prompt, nonempty, group=judge_group, max_tokens=max_tokens)
        return {
            "final": final,
            "candidates": [asdict(c) for c in candidate_results],
            "group_winners": [],
        }
    winners = []
    for i in range(0, len(nonempty), tournament_group_size):
        winners.append(
            synthesize(gateway, prompt, nonempty[i : i + tournament_group_size], group=judge_group)
        )
    final = synthesize(gateway, prompt, winners, group=judge_group, max_tokens=max_tokens)
    return {
        "final": final,
        "candidates": [asdict(c) for c in candidate_results],
        "group_winners": winners,
    }
