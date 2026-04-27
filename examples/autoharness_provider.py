"""Drop-in adapter idea for autoharness.providers.* without forking provider routing.

Copy into the AutoHarness repo, then add `kind: model-preflight` to its ProviderConfig
or instantiate this class from its provider factory for provider-backed probes.
"""

from __future__ import annotations

from pathlib import Path

from autoharness.providers.base import GenerationConfig, Provider, ProviderResult
from model_preflight import ModelGateway, load_config


class ModelPreflightProvider(Provider):
    def __init__(self, *, group: str = "free_reasoning", config_path: str | None = None) -> None:
        self.group = group
        self.gateway = ModelGateway(load_config(None if config_path is None else Path(config_path)))

    def generate(self, prompt: str) -> ProviderResult:
        return self.generate_candidates(prompt)[0]

    def generate_candidates(
        self, prompt: str, generation_config: GenerationConfig | None = None
    ) -> list[ProviderResult]:
        n = generation_config.candidate_count if generation_config else 1
        temp = generation_config.temperature if generation_config else None
        results = []
        for i in range(n):
            text = self.gateway.text(prompt, group=self.group, temperature=temp)
            results.append(
                ProviderResult(
                    text=text,
                    provider="model-preflight",
                    model=self.group,
                    metadata={"candidate_index": i},
                )
            )
        return results
