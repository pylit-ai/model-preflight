from __future__ import annotations

from types import SimpleNamespace

from model_preflight.config import AppConfig, Deployment
from model_preflight.router import ModelGateway


def test_stream_text_yields_litellm_delta_chunks(monkeypatch):
    cfg = AppConfig(
        deployments=[
            Deployment(
                name="live",
                provider="openrouter",
                group="free_reasoning",
                model="openrouter/test-model",
                api_key_env=None,
            )
        ]
    )
    gateway = ModelGateway(cfg)

    def fake_completion(**kwargs):
        assert kwargs["stream"] is True
        yield {
            "choices": [
                {
                    "delta": {
                        "content": "hello",
                    }
                }
            ]
        }
        yield SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=" world"),
                )
            ]
        )

    monkeypatch.setattr(gateway.router, "completion", fake_completion)

    assert list(gateway.stream_text("ignored", group="free_reasoning")) == ["hello", " world"]


def test_text_result_extracts_reasoning_fields(monkeypatch):
    cfg = AppConfig(
        deployments=[
            Deployment(
                name="live",
                provider="openrouter",
                group="free_reasoning",
                model="openrouter/test-model",
                api_key_env=None,
            )
        ]
    )
    gateway = ModelGateway(cfg)
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            id="resp-1",
            model="openrouter/test-model",
            usage=SimpleNamespace(completion_tokens=4, reasoning_tokens=2),
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="answer",
                        reasoning="visible reasoning",
                        reasoning_details=[{"type": "reasoning.text", "text": "detail"}],
                    )
                )
            ],
        )

    monkeypatch.setattr(gateway.router, "completion", fake_completion)

    result = gateway.text_result(
        "ignored",
        group="free_reasoning",
        reasoning={"enabled": True, "exclude": False},
        include_reasoning=True,
    )

    assert calls[0]["reasoning"] == {"enabled": True, "exclude": False}
    assert calls[0]["include_reasoning"] is True
    assert result.text == "answer"
    assert result.reasoning == "visible reasoning"
    assert result.reasoning_details == [{"type": "reasoning.text", "text": "detail"}]
    assert result.usage == {"completion_tokens": 4, "reasoning_tokens": 2}
    assert result.model == "openrouter/test-model"
    assert result.response_id == "resp-1"
