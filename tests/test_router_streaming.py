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
