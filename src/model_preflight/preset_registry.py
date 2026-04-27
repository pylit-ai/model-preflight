from __future__ import annotations

from dataclasses import dataclass
from importlib import resources

PROVIDER_TO_PRESET = {
    "minimal": "minimal",
    "openrouter": "openrouter",
    "groq": "multi-free-dev",
    "cerebras": "multi-free-dev",
    "mistral": "multi-free-dev",
}


@dataclass(frozen=True)
class ProviderInfo:
    id: str
    name: str
    preset: str
    env_vars: tuple[str, ...]
    setup_url: str
    best_for: str


PROVIDERS: dict[str, ProviderInfo] = {
    "openrouter": ProviderInfo(
        id="openrouter",
        name="OpenRouter",
        preset="openrouter",
        env_vars=("OPENROUTER_API_KEY",),
        setup_url="https://openrouter.ai/docs/api-reference/authentication",
        best_for="One-key first run with broad model access.",
    ),
    "groq": ProviderInfo(
        id="groq",
        name="GroqCloud",
        preset="multi-free-dev",
        env_vars=("GROQ_API_KEY",),
        setup_url="https://console.groq.com/docs/quickstart",
        best_for="Fast repeated calls after first-run setup is working.",
    ),
    "cerebras": ProviderInfo(
        id="cerebras",
        name="Cerebras",
        preset="multi-free-dev",
        env_vars=("CEREBRAS_API_KEY",),
        setup_url="https://inference-docs.cerebras.ai",
        best_for="Fast inference experiments when current dev-tier limits fit.",
    ),
    "mistral": ProviderInfo(
        id="mistral",
        name="Mistral",
        preset="multi-free-dev",
        env_vars=("MISTRAL_API_KEY",),
        setup_url="https://docs.mistral.ai",
        best_for="First-party Mistral model-family smoke checks.",
    ),
}


def available_presets() -> list[str]:
    root = resources.files("model_preflight.presets")
    return sorted(
        path.name.removesuffix(".yaml") for path in root.iterdir() if path.name.endswith(".yaml")
    )


def preset_text(name: str) -> str:
    normalized = name.strip().lower()
    if normalized not in available_presets():
        valid = ", ".join(available_presets())
        raise ValueError(f"unknown preset {name!r}; valid presets: {valid}")
    return resources.files("model_preflight.presets").joinpath(f"{normalized}.yaml").read_text(
        encoding="utf-8"
    )


def preset_for_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in PROVIDER_TO_PRESET:
        valid = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"unknown provider {provider!r}; valid providers: {valid}")
    return PROVIDER_TO_PRESET[normalized]
