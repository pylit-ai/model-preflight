from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from litellm import Router

from .config import AppConfig, Deployment


def _deployment_to_litellm(dep: Deployment) -> dict[str, Any]:
    params: dict[str, Any] = {"model": dep.model}
    if dep.api_key_env:
        api_key = os.getenv(dep.api_key_env)
        if api_key:
            params["api_key"] = api_key
    if dep.api_base:
        params["api_base"] = dep.api_base
    row: dict[str, Any] = {
        "model_name": dep.group,
        "litellm_params": params,
        "metadata": {"deployment_name": dep.name, "tier": dep.tier},
    }
    if dep.rpm is not None:
        row["rpm"] = dep.rpm
    if dep.tpm is not None:
        row["tpm"] = dep.tpm
    return row


class ModelGateway:
    """Small wrapper around LiteLLM Router with audit logging and stable group aliases."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        model_list = [_deployment_to_litellm(d) for d in config.deployments if d.enabled]
        if not model_list:
            raise ValueError("No enabled deployments in ModelPreflight config")
        self.router = Router(
            model_list=model_list,
            num_retries=config.router.num_retries,
            timeout=config.router.timeout_seconds,
        )

    def completion(
        self,
        messages: list[dict[str, str]],
        *,
        group: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        n: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        model_group = group or self.config.router.default_group
        started = time.perf_counter()
        response = self.router.completion(
            model=model_group,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            n=n,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        self._audit(
            {
                "ts": time.time(),
                "group": model_group,
                "latency_ms": latency_ms,
                "metadata": metadata or {},
                "response_id": getattr(response, "id", None),
                "model": getattr(response, "model", None),
                "usage": getattr(response, "usage", None),
            }
        )
        return response

    def text(self, prompt: str, *, group: str | None = None, **kwargs: Any) -> str:
        resp = self.completion(
            [{"role": "user", "content": prompt}],
            group=group,
            **kwargs,
        )
        return resp.choices[0].message.content or ""

    def _audit(self, row: dict[str, Any]) -> None:
        path = self.config.router.audit_jsonl
        if path is None:
            return
        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str, sort_keys=True) + "\n")
