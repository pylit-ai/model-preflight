from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .router import ModelGateway


def fanout(
    gateway: ModelGateway,
    prompt: str,
    *,
    group: str,
    n: int,
    temperature: float = 0.9,
    max_workers: int = 16,
    max_tokens: int | None = None,
) -> list[str]:
    results = [""] * n
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
            results[idx] = fut.result()
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
    candidates = fanout(
        gateway,
        prompt,
        group=sample_group,
        n=n,
        max_workers=max_workers,
        max_tokens=max_tokens,
    )
    nonempty = [c for c in candidates if c.strip()]
    if not nonempty:
        raise RuntimeError("all candidate generations were empty")
    if len(nonempty) <= tournament_group_size:
        final = synthesize(gateway, prompt, nonempty, group=judge_group, max_tokens=max_tokens)
        return {"final": final, "candidates": candidates, "group_winners": []}
    winners = []
    for i in range(0, len(nonempty), tournament_group_size):
        winners.append(
            synthesize(gateway, prompt, nonempty[i : i + tournament_group_size], group=judge_group)
        )
    final = synthesize(gateway, prompt, winners, group=judge_group, max_tokens=max_tokens)
    return {"final": final, "candidates": candidates, "group_winners": winners}
