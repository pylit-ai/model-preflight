"""ModelPreflight: preflight checks for LLM prototypes."""

from .config import AppConfig, Deployment, RouterSettings, default_config_path, load_config
from .smoke import SmokeCase, SmokeResult, run_smoke_cases

__all__ = [
    "AppConfig",
    "Deployment",
    "RouterSettings",
    "default_config_path",
    "load_config",
    "ModelGateway",
    "pro_mode",
    "SmokeCase",
    "SmokeResult",
    "run_smoke_cases",
]


def __getattr__(name: str):
    if name == "ModelGateway":
        from .router import ModelGateway

        return ModelGateway
    if name == "pro_mode":
        from .pro_mode import pro_mode

        return pro_mode
    raise AttributeError(name)
