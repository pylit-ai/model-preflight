from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .config import (
    AppConfig,
    Deployment,
    load_config,
    missing_env_vars,
    selected_deployments,
    write_default_config,
)
from .preset_registry import PROVIDERS, available_presets
from .pro_mode import pro_mode as run_pro_mode
from .router import ModelGateway
from .smoke import SmokeCase, run_smoke_cases

app = typer.Typer(no_args_is_help=True, help="Preflight checks for LLM prototypes.")
providers_app = typer.Typer(no_args_is_help=True, help="Provider setup helpers.")
app.add_typer(providers_app, name="providers")
console = Console()


SMOKE_PATH = Path("evals/smoke.jsonl")
PROJECT_README = Path(".model-preflight/README.md")
ARTIFACT_IGNORE = ".model-preflight/artifacts/"


def _deployment_table(
    cfg: AppConfig,
    *,
    title: str = "ModelPreflight deployments",
    group: str | None = None,
    provider: str | None = None,
) -> Table:
    table = Table(title=title)
    for col in [
        "enabled",
        "required",
        "provider",
        "name",
        "group",
        "tier",
        "model",
        "api_key_env",
        "env",
        "status",
    ]:
        table.add_column(col)
    for dep in selected_deployments(cfg, group=group, provider=provider, include_disabled=True):
        env_status = _env_status(dep)
        table.add_row(
            str(dep.enabled),
            str(dep.required),
            dep.provider or "",
            dep.name,
            dep.group,
            dep.tier,
            dep.model,
            dep.api_key_env or "",
            env_status,
            dep.status,
        )
    return table


def _env_status(dep: Deployment) -> str:
    if not dep.api_key_env:
        return "not-needed"
    if os.getenv(dep.api_key_env):
        return "ok"
    if not dep.enabled:
        return "disabled"
    return "missing" if dep.required else "optional-missing"


def _parse_cases(path: Path) -> list[SmokeCase]:
    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [SmokeCase.model_validate(row) for row in raw]


def _default_smoke_cases() -> str:
    return (
        '{"id":"basic-route","prompt":"Return only: ok","expected_substrings":["ok"]}\n'
        '{"id":"json-format","prompt":"Return JSON only: {\\"ok\\": true}",'
        '"expected_substrings":["ok"],"forbidden_substrings":["```"]}\n'
    )


@app.command()
def init(
    path: Annotated[Path | None, typer.Option("--config")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
    provider: Annotated[str | None, typer.Option("--provider")] = None,
    preset: Annotated[str | None, typer.Option("--preset")] = None,
) -> None:
    """Create the machine-local ModelPreflight config."""
    if provider and preset:
        raise typer.BadParameter("use either --provider or --preset, not both")
    out = write_default_config(path, overwrite=overwrite, preset=preset, provider=provider)
    console.print(f"wrote config: {out}")
    if provider:
        info = PROVIDERS.get(provider)
        if info:
            env_vars = ", ".join(info.env_vars)
            console.print(f"provider: {info.name}")
            console.print(f"set env var: {env_vars}")
    console.print("next: mpf doctor --live")


@app.command()
def doctor(
    path: Annotated[Path | None, typer.Option("--config")] = None,
    group: Annotated[str | None, typer.Option("--group")] = None,
    provider: Annotated[str | None, typer.Option("--provider")] = None,
    live: Annotated[bool, typer.Option("--live")] = False,
) -> None:
    """Validate config/env and optionally run a tiny live provider check."""
    cfg = load_config(path)
    console.print(_deployment_table(cfg, group=group, provider=provider))
    selected = selected_deployments(cfg, group=group, provider=provider)
    if not selected:
        console.print("no matching enabled deployments")
        raise typer.Exit(code=2)
    missing = missing_env_vars(cfg, group=group, provider=provider, required_only=True)
    if missing:
        console.print(f"missing required env vars: {', '.join(missing)}")
        for env_var in missing:
            console.print(f"next: export {env_var}=...")
        raise typer.Exit(code=2)
    optional_missing = missing_env_vars(cfg, group=group, provider=provider, required_only=False)
    optional_missing = [env for env in optional_missing if env not in missing]
    if optional_missing:
        console.print(f"optional env vars not set: {', '.join(optional_missing)}")
    if live:
        _doctor_live(cfg, group=group, provider=provider)


def _doctor_live(cfg: AppConfig, *, group: str | None = None, provider: str | None = None) -> None:
    selected = selected_deployments(cfg, group=group, provider=provider)
    live_group = group or (selected[0].group if selected else cfg.router.default_group)
    started = time.perf_counter()
    try:
        text = ModelGateway(cfg).text(
            "Return only: ok",
            group=live_group,
            temperature=0,
            metadata={"phase": "doctor_live", "provider": provider, "group": live_group},
        )
    except Exception as exc:  # noqa: BLE001 - provider exceptions need human-readable recovery.
        console.print(f"live check failed for group {live_group!r}: {exc}")
        raise typer.Exit(code=2) from exc
    latency = time.perf_counter() - started
    if "ok" not in text.lower():
        console.print(f"live check failed for group {live_group!r}: response did not contain 'ok'")
        raise typer.Exit(code=2)
    console.print(f"live check ok: group={live_group} latency={latency:.2f}s")
    if cfg.router.audit_jsonl:
        console.print(f"audit log: {cfg.router.audit_jsonl}")


@app.command()
def models(path: Annotated[Path | None, typer.Option("--config")] = None) -> None:
    """List configured provider/model deployments."""
    cfg = load_config(path)
    console.print(_deployment_table(cfg, title="Configured deployments"))


@app.command()
def run(
    cases: Annotated[Path | None, typer.Argument(help="JSONL smoke cases")] = None,
    path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Run project-local smoke cases."""
    cases_path = cases or SMOKE_PATH
    if not cases_path.exists():
        console.print(f"no smoke cases found at {cases_path}")
        console.print("next: mpf init-project")
        raise typer.Exit(code=2)
    parsed = _parse_cases(cases_path)
    results = run_smoke_cases(ModelGateway(load_config(path)), parsed)
    console.print_json(json.dumps([r.model_dump() for r in results], indent=2))
    if not all(r.passed for r in results):
        raise typer.Exit(code=1)


@app.command()
def demo(path: Annotated[Path | None, typer.Option("--config")] = None) -> None:
    """Run a packaged no-project smoke demo."""
    cfg = load_config(path)
    cases = [
        SmokeCase(
            id="demo-ok",
            prompt="Return only: ok",
            expected_substrings=["ok"],
            forbidden_substrings=["```"],
        )
    ]
    results = run_smoke_cases(ModelGateway(cfg), cases)
    console.print_json(json.dumps([r.model_dump() for r in results], indent=2))
    if not all(r.passed for r in results):
        raise typer.Exit(code=1)


@app.command("init-project")
def init_project(
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    """Create project-local smoke case starter files."""
    SMOKE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROJECT_README.parent.mkdir(parents=True, exist_ok=True)
    if SMOKE_PATH.exists() and not overwrite:
        console.print(f"kept existing {SMOKE_PATH}")
    else:
        SMOKE_PATH.write_text(_default_smoke_cases(), encoding="utf-8")
        console.print(f"wrote {SMOKE_PATH}")
    readme_text = (
        "# ModelPreflight project files\n\n"
        "- `evals/smoke.jsonl` contains project-local smoke cases.\n"
        "- `.model-preflight/artifacts/` is for generated local evidence "
        "and should stay out of git.\n"
    )
    if PROJECT_README.exists() and not overwrite:
        console.print(f"kept existing {PROJECT_README}")
    else:
        PROJECT_README.write_text(readme_text, encoding="utf-8")
        console.print(f"wrote {PROJECT_README}")
    gitignore = Path(".gitignore")
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if ARTIFACT_IGNORE not in existing:
        suffix = "" if existing.endswith("\n") or not existing else "\n"
        gitignore.write_text(f"{existing}{suffix}{ARTIFACT_IGNORE}\n", encoding="utf-8")
        console.print("updated .gitignore")
    console.print("next: mpf run")


@app.command()
def pro(
    prompt: str,
    n: Annotated[int, typer.Option("--n", min=1, max=100)] = 8,
    sample_group: Annotated[str, typer.Option("--sample-group")] = "free_fast",
    judge_group: Annotated[str, typer.Option("--judge-group")] = "free_reasoning",
    path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Run fanout + synthesis for a one-off prototype prompt."""
    gw = ModelGateway(load_config(path))
    result = run_pro_mode(gw, prompt, n=n, sample_group=sample_group, judge_group=judge_group)
    console.print_json(json.dumps(result, default=str))


@providers_app.command("list")
def providers_list(path: Annotated[Path | None, typer.Option("--config")] = None) -> None:
    """List known provider setup metadata."""
    configured: AppConfig | None = None
    try:
        configured = load_config(path)
    except FileNotFoundError:
        configured = None
    table = Table(title="ModelPreflight providers")
    for col in ["provider", "preset", "env_vars", "configured", "setup_url", "best_for"]:
        table.add_column(col)
    for info in PROVIDERS.values():
        is_configured = "no"
        if configured and any(dep.provider == info.id for dep in configured.deployments):
            is_configured = "yes"
        table.add_row(
            info.id,
            info.preset,
            ", ".join(info.env_vars),
            is_configured,
            info.setup_url,
            info.best_for,
        )
    console.print(table)
    console.print(f"presets: {', '.join(available_presets())}")


@providers_app.command("guide")
def providers_guide(provider: str) -> None:
    """Show setup steps for one provider."""
    info = PROVIDERS.get(provider)
    if info is None:
        valid = ", ".join(sorted(PROVIDERS))
        raise typer.BadParameter(f"unknown provider {provider!r}; valid providers: {valid}")
    console.print(f"# {info.name}")
    console.print(f"Best for: {info.best_for}")
    console.print(f"Setup: {info.setup_url}")
    console.print(f"Env var: {', '.join(info.env_vars)}")
    console.print("")
    console.print(f"mpf init --provider {info.id}")
    console.print(f"export {info.env_vars[0]}=...")
    console.print(f"mpf doctor --provider {info.id} --live")


@providers_app.command("test")
def providers_test(
    provider: str,
    path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Run a live doctor check for one provider."""
    doctor(path=path, provider=provider, live=True)
