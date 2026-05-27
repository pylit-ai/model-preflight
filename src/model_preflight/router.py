from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import AppConfig, Deployment, resolve_secret


def _deployment_to_litellm(dep: Deployment, config: AppConfig) -> dict[str, Any]:
    params: dict[str, Any] = {"model": dep.model}
    if dep.api_key_env:
        api_key = resolve_secret(config, dep.api_key_env)
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
        self.enabled_deployments = [d for d in config.deployments if d.enabled]
        if not self.enabled_deployments:
            raise ValueError("No enabled deployments in ModelPreflight config")
        self.router: Any | None = None
        if any(d.provider != "offline" for d in self.enabled_deployments):
            from litellm import Router

            model_list = [_deployment_to_litellm(d, config) for d in self.enabled_deployments]
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
        stream: bool | None = None,
        reasoning: dict[str, Any] | None = None,
        include_reasoning: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        model_group = group or self.config.router.default_group
        offline_dep = self._offline_deployment(model_group)
        if offline_dep is not None:
            prompt = "\n".join(m["content"] for m in messages if m.get("role") == "user")
            text = prompt or "ok"
            self._audit(
                {
                    "ts": time.time(),
                    "group": model_group,
                    "latency_ms": 0.0,
                    "metadata": metadata or {},
                    "response_id": None,
                    "model": offline_dep.model,
                    "usage": None,
                }
            )
            return _OfflineResponse(text=text, model=offline_dep.model)
        if self.router is None:
            raise ValueError(f"No live deployment configured for group {model_group!r}")
        started = time.perf_counter()
        completion_kwargs: dict[str, Any] = {
            "model": model_group,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "n": n,
            "stream": stream,
        }
        if reasoning is not None:
            completion_kwargs["reasoning"] = reasoning
        if include_reasoning is not None:
            completion_kwargs["include_reasoning"] = include_reasoning
        response = self.router.completion(**completion_kwargs)
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
        return self.text_result(prompt, group=group, **kwargs).text

    def text_result(self, prompt: str, *, group: str | None = None, **kwargs: Any) -> TextResult:
        resp = self.completion(
            [{"role": "user", "content": prompt}],
            group=group,
            **kwargs,
        )
        return _text_result_from_response(resp)

    def stream_text(self, prompt: str, *, group: str | None = None, **kwargs: Any) -> Any:
        resp = self.completion(
            [{"role": "user", "content": prompt}],
            group=group,
            stream=True,
            **kwargs,
        )
        if isinstance(resp, _OfflineResponse):
            yield resp.choices[0].message.content or ""
            return
        for chunk in resp:
            text = _stream_delta_text(chunk)
            if text:
                yield text

    def _offline_deployment(self, group: str) -> Deployment | None:
        for dep in self.enabled_deployments:
            if dep.group == group and dep.provider == "offline":
                return dep
        return None

    def _audit(self, row: dict[str, Any]) -> None:
        path = self.config.router.audit_jsonl
        if path is None:
            return
        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str, sort_keys=True) + "\n")


class _OfflineMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _OfflineChoice:
    def __init__(self, text: str) -> None:
        self.message = _OfflineMessage(text)


class _OfflineResponse:
    id = None
    usage = None

    def __init__(self, *, text: str, model: str) -> None:
        self.model = model
        self.choices = [_OfflineChoice(text)]


def _stream_delta_text(chunk: Any) -> str:
    try:
        return chunk.choices[0].delta.content or ""
    except AttributeError:
        pass
    try:
        return chunk["choices"][0]["delta"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        return ""


@dataclass(frozen=True)
class TextResult:
    text: str
    reasoning: str | None = None
    reasoning_details: Any | None = None
    reasoning_summary: Any | None = None
    usage: Any | None = None
    model: str | None = None
    response_id: str | None = None


def _field(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return _jsonable(value.dict())
    if hasattr(value, "__dict__"):
        return _jsonable(vars(value))
    return str(value)


def _first_choice(response: Any) -> Any:
    choices = _field(response, "choices") or []
    return choices[0] if choices else None


def _choice_message(choice: Any) -> Any:
    return _field(choice, "message") if choice is not None else None


def _text_result_from_response(response: Any) -> TextResult:
    choice = _first_choice(response)
    message = _choice_message(choice)
    reasoning = (
        _field(message, "reasoning")
        or _field(message, "reasoning_content")
        or _field(message, "thinking")
    )
    reasoning_summary = (
        _field(message, "reasoning_summary")
        or _field(message, "summary")
        or _field(response, "reasoning_summary")
        or _field(response, "summary")
    )
    return TextResult(
        text=_field(message, "content") or "",
        reasoning=reasoning,
        reasoning_details=_jsonable(_field(message, "reasoning_details")),
        reasoning_summary=_jsonable(reasoning_summary),
        usage=_jsonable(_field(response, "usage")),
        model=_field(response, "model"),
        response_id=_field(response, "id"),
    )
