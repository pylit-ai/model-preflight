from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console
from rich.table import Table

from .config import (
    AppConfig,
    Deployment,
    default_config_path,
    deployment_is_ready,
    detect_provider_from_env,
    link_dotenv_secret_source,
    load_config,
    missing_env_vars,
    secret_source_status,
    selected_deployments,
    write_config,
    write_default_config,
)
from .preset_registry import PROVIDERS, available_presets
from .pro_mode import pro_mode as run_pro_mode
from .router import ModelGateway
from .smoke import SmokeCase, run_smoke_cases

app = typer.Typer(no_args_is_help=True, help="Preflight checks for LLM prototypes.")
providers_app = typer.Typer(no_args_is_help=True, help="Provider setup helpers.")
secrets_app = typer.Typer(no_args_is_help=True, help="Machine-local secret source helpers.")
app.add_typer(providers_app, name="providers")
app.add_typer(secrets_app, name="secrets")
console = Console()
err_console = Console(stderr=True)


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
        env_status = _env_status(cfg, dep)
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


def _env_status(cfg: AppConfig, dep: Deployment) -> str:
    if not dep.api_key_env:
        return "not-needed"
    if not dep.enabled:
        return "disabled"
    if deployment_is_ready(cfg, dep):
        return "ok"
    if os.getenv(dep.api_key_env):
        return "ok"
    return "missing" if dep.required else "optional-missing"


def _enabled_groups(cfg: AppConfig) -> list[str]:
    return sorted({dep.group for dep in cfg.deployments if dep.enabled})


def _route_metadata(cfg: AppConfig, group: str) -> list[dict[str, str]]:
    routes = []
    for dep in selected_deployments(cfg, group=group):
        routes.append(
            {
                "provider": dep.provider or "unknown",
                "model": dep.model,
            }
        )
    return routes


def _ask_status(message: str, *, style: str = "dim") -> None:
    if err_console.is_terminal:
        err_console.print("[mpf] " + message, style=style)
        return
    err_console.print(f"[mpf] {message}", markup=False)


def _status(message: str, *, style: str = "dim") -> None:
    if err_console.is_terminal:
        err_console.print("[mpf] " + message, style=style)
        return
    err_console.print(f"[mpf] {message}", markup=False)


def _required_env_vars(deployments: list[Deployment]) -> list[str]:
    return sorted({dep.api_key_env for dep in deployments if dep.required and dep.api_key_env})


def _disabled_matching_deployments(
    cfg: AppConfig,
    *,
    group: str | None = None,
    provider: str | None = None,
) -> list[Deployment]:
    return [
        dep
        for dep in selected_deployments(
            cfg,
            group=group,
            provider=provider,
            include_disabled=True,
        )
        if not dep.enabled
    ]


def _doctor_diagnostic(
    cfg: AppConfig,
    *,
    group: str | None = None,
    provider: str | None = None,
) -> dict[str, object]:
    selected = selected_deployments(cfg, group=group, provider=provider)
    selected_group = group or (selected[0].group if selected else cfg.router.default_group)
    disabled_matching = _disabled_matching_deployments(cfg, group=group, provider=provider)
    required_env = _required_env_vars(selected)
    ready = [dep for dep in selected if deployment_is_ready(cfg, dep)]
    blocked = [dep for dep in selected if not deployment_is_ready(cfg, dep)]
    missing = missing_env_vars(cfg, group=group, provider=provider, required_only=True)
    next_commands: list[str] = []
    warnings: list[str] = []
    error_code: str | None = None

    if not selected:
        if disabled_matching:
            error_code = "GROUP_DISABLED"
            next_commands.append("enable a matching deployment in the ModelPreflight config")
        else:
            error_code = "GROUP_NOT_FOUND"
            next_commands.append("mpf models")
    elif not ready:
        if len(selected) == 1 and missing:
            error_code = "MISSING_REQUIRED_ENV"
            next_commands.extend(f"export {env_var}=..." for env_var in missing)
        else:
            error_code = "NO_READY_DEPLOYMENT"
            next_commands.extend(f"export {env_var}=..." for env_var in missing)
            next_commands.append("model-preflight secrets link /path/to/private/.env")
    elif blocked:
        warnings.append(
            "At least one deployment is ready, but some enabled deployments are missing secrets."
        )
    elif missing:
        error_code = "MISSING_REQUIRED_ENV"
        next_commands.extend(f"export {env_var}=..." for env_var in missing)

    return {
        "status": "error" if error_code else "ok",
        "error_code": error_code,
        "config_path": str(cfg.config_path) if cfg.config_path is not None else None,
        "selected_group": selected_group,
        "selected_provider": provider or (selected[0].provider if selected else None),
        "enabled_groups": _enabled_groups(cfg),
        "required_env_vars": required_env,
        "missing_env_vars": missing if selected else [],
        "ready_deployments": [dep.name for dep in ready],
        "blocked_deployments": [dep.name for dep in blocked],
        "disabled_matching_providers": sorted(
            {
                dep.provider
                for dep in disabled_matching
                if dep.provider is not None
            }
        ),
        "secret_sources": secret_source_status(cfg),
        "warnings": warnings,
        "next_commands": next_commands,
    }


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
    fallback: Annotated[str | None, typer.Option("--fallback")] = None,
    preset: Annotated[str | None, typer.Option("--preset")] = None,
) -> None:
    """Create the machine-local ModelPreflight config."""
    if provider and preset:
        raise typer.BadParameter("use either --provider or --preset, not both")
    if fallback and not provider:
        raise typer.BadParameter("--fallback requires --provider")
    if fallback and preset:
        raise typer.BadParameter("use --fallback only with --provider")
    detected_provider = None if provider or preset else detect_provider_from_env()
    out = write_default_config(
        path,
        overwrite=overwrite,
        preset=preset,
        provider=provider,
        fallback_provider=fallback,
    )
    console.print(f"wrote config: {out}")
    if provider:
        info = PROVIDERS.get(provider)
        if info:
            env_vars = ", ".join(info.env_vars)
            console.print(f"provider: {info.name}")
            console.print(f"set env var: {env_vars}")
        if fallback:
            fallback_info = PROVIDERS.get(fallback)
            if fallback_info:
                console.print(f"fallback: {fallback_info.name}")
    elif detected_provider:
        info = PROVIDERS[detected_provider]
        console.print(f"provider: {info.name} (auto-detected from {info.env_vars[0]})")
    elif preset is None:
        console.print("no supported provider key visible; wrote OpenRouter starter config")
        console.print("next: export OPENROUTER_API_KEY=...")
    console.print("next: mpf doctor --live")


@app.command()
def setup(
    path: Annotated[Path | None, typer.Option("--config")] = None,
    provider: Annotated[str, typer.Option("--provider")] = "nvidia",
    fallback: Annotated[str | None, typer.Option("--fallback")] = "openrouter",
    env_file: Annotated[Path | None, typer.Option("--env-file", dir_okay=False)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Set up local routing, optional fallback, and a private dotenv source."""
    out = write_default_config(
        path,
        overwrite=True,
        provider=provider,
        fallback_provider=fallback,
    )
    cfg = load_config(out)
    linked_env_file = env_file or (Path.cwd() / ".env" if (Path.cwd() / ".env").exists() else None)
    if linked_env_file is not None:
        link_dotenv_secret_source(cfg, linked_env_file)
        write_config(cfg, out)
        cfg = load_config(out)
    diagnostic = _doctor_diagnostic(cfg, group=cfg.router.default_group)
    if json_output:
        typer.echo(json.dumps(diagnostic, indent=2))
        if diagnostic["status"] != "ok":
            raise typer.Exit(code=2)
        return
    console.print(f"updated config: {out}")
    console.print(f"provider: {PROVIDERS[provider].name}")
    if fallback:
        console.print(f"fallback: {PROVIDERS[fallback].name}")
    if linked_env_file is not None:
        console.print(f"linked dotenv secret source: {linked_env_file.expanduser()}")
    else:
        console.print("no dotenv file linked")
        console.print("next: mpf secrets link /path/to/private/.env")
    ready = cast(list[str], diagnostic["ready_deployments"])
    blocked = cast(list[str], diagnostic["blocked_deployments"])
    console.print(f"ready deployments: {', '.join(ready) or 'none'}")
    console.print(f"blocked deployments: {', '.join(blocked) or 'none'}")
    console.print("next: mpf doctor --group free_reasoning --json")
    if diagnostic["status"] != "ok":
        raise typer.Exit(code=2)


@app.command()
def paths() -> None:
    """Print machine-local ModelPreflight paths."""
    cfg = AppConfig()
    console.print(f"config: {default_config_path()}")
    console.print(f"artifacts: {cfg.artifacts_dir}")


@app.command()
def doctor(
    path: Annotated[Path | None, typer.Option("--config")] = None,
    group: Annotated[str | None, typer.Option("--group")] = None,
    provider: Annotated[str | None, typer.Option("--provider")] = None,
    live: Annotated[bool, typer.Option("--live")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate config/env and optionally run a tiny live provider check."""
    cfg = load_config(path)
    diagnostic = _doctor_diagnostic(cfg, group=group, provider=provider)
    if json_output:
        typer.echo(json.dumps(diagnostic, indent=2))
        if diagnostic["status"] != "ok":
            raise typer.Exit(code=2)
        if live:
            _doctor_live(cfg, group=group, provider=provider)
        return

    console.print(_deployment_table(cfg, group=group, provider=provider))
    console.print(f"selected group: {diagnostic['selected_group']}")
    console.print(f"selected provider: {diagnostic['selected_provider'] or 'any'}")
    enabled_groups = cast(list[str], diagnostic["enabled_groups"])
    console.print(f"enabled groups: {', '.join(enabled_groups) or 'none'}")
    required_env = cast(list[str], diagnostic["required_env_vars"])
    if required_env:
        console.print(f"required env vars: {', '.join(required_env)}")
    disabled_matching = cast(list[str], diagnostic["disabled_matching_providers"])
    if disabled_matching:
        console.print(f"disabled matching providers: {', '.join(disabled_matching)}")
    selected = selected_deployments(cfg, group=group, provider=provider)
    if not selected:
        if diagnostic["error_code"] == "GROUP_DISABLED":
            console.print("matching provider or group exists but is disabled")
        else:
            console.print("no matching enabled deployments")
        for command in cast(list[str], diagnostic["next_commands"]):
            console.print(f"next: {command}")
        raise typer.Exit(code=2)
    missing = missing_env_vars(cfg, group=group, provider=provider, required_only=True)
    if diagnostic["status"] != "ok" and missing:
        console.print(f"missing required env vars: {', '.join(missing)}")
        for command in cast(list[str], diagnostic["next_commands"]):
            console.print(f"next: {command}")
        raise typer.Exit(code=2)
    if diagnostic["status"] != "ok":
        console.print(str(diagnostic["error_code"]))
        for command in cast(list[str], diagnostic["next_commands"]):
            console.print(f"next: {command}")
        raise typer.Exit(code=2)
    warnings = cast(list[str], diagnostic["warnings"])
    for warning in warnings:
        console.print(f"warning: {warning}")
    optional_missing = missing_env_vars(cfg, group=group, provider=provider, required_only=False)
    optional_missing = [env for env in optional_missing if env not in missing]
    if optional_missing:
        console.print(f"optional env vars not set: {', '.join(optional_missing)}")
    if live:
        _doctor_live(cfg, group=group, provider=provider)


@secrets_app.command("link")
def secrets_link(
    env_file: Annotated[Path, typer.Argument(exists=False, dir_okay=False)],
    path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Link a machine-local dotenv file as a secret source."""
    cfg = load_config(path)
    link_dotenv_secret_source(cfg, env_file)
    out = write_config(cfg, path)
    console.print(f"linked dotenv secret source: {env_file.expanduser()}")
    console.print(f"updated config: {out}")
    console.print("next: model-preflight secrets doctor")


@secrets_app.command("doctor")
def secrets_doctor(
    path: Annotated[Path | None, typer.Option("--config")] = None,
    group: Annotated[str | None, typer.Option("--group")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Report secret source readiness without printing secret values."""
    cfg = load_config(path)
    diagnostic = _doctor_diagnostic(cfg, group=group)
    if json_output:
        typer.echo(json.dumps(diagnostic, indent=2))
        if diagnostic["status"] != "ok":
            raise typer.Exit(code=2)
        return
    for source in cast(list[dict[str, object]], diagnostic["secret_sources"]):
        if source["kind"] == "env":
            console.print("secret source: env")
        else:
            console.print(
                "secret source: dotenv "
                f"path={source.get('path')} exists={source.get('exists')} "
                f"readable={source.get('readable')}"
            )
    ready = cast(list[str], diagnostic["ready_deployments"])
    blocked = cast(list[str], diagnostic["blocked_deployments"])
    console.print(f"ready deployments: {', '.join(ready) or 'none'}")
    console.print(f"blocked deployments: {', '.join(blocked) or 'none'}")
    if diagnostic["status"] != "ok":
        for command in cast(list[str], diagnostic["next_commands"]):
            console.print(f"next: {command}")
        raise typer.Exit(code=2)


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


@app.command()
def ask(
    prompt: str,
    group: Annotated[str | None, typer.Option("--group")] = None,
    path: Annotated[Path | None, typer.Option("--config")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    stream: Annotated[bool, typer.Option("--stream/--no-stream")] = True,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
    hide_route: Annotated[bool, typer.Option("--hide-route")] = False,
) -> None:
    """Ask one prompt through one configured model group."""
    cfg = load_config(path)
    selected_group = group or cfg.router.default_group
    routes = _route_metadata(cfg, selected_group)
    gateway = ModelGateway(cfg)
    if json_output:
        text = gateway.text(
            prompt,
            group=selected_group,
            metadata={"runner": "ask", "group": selected_group, "stream": False},
        )
        payload: dict[str, object] = {"group": selected_group, "text": text}
        if not hide_route:
            payload["routes"] = routes
        console.print_json(json.dumps(payload, indent=2))
        return
    if not quiet and not hide_route:
        _ask_status(f"route {selected_group}", style="dim cyan")
        for route in routes:
            _ask_status(f"  {route['provider']}: {route['model']}", style="dim cyan")
    if stream:
        if not quiet:
            _ask_status(
                f"waiting for first token from {selected_group}...",
                style="yellow",
            )
            err_console.print()
        for chunk in gateway.stream_text(
            prompt,
            group=selected_group,
            metadata={"runner": "ask", "group": selected_group, "stream": True},
        ):
            console.print(chunk, end="")
        console.print()
        return
    text = gateway.text(
        prompt,
        group=selected_group,
        metadata={"runner": "ask", "group": selected_group, "stream": False},
    )
    console.print(text)


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
    n: Annotated[int, typer.Option("--n", "-n", min=1, max=100)] = 8,
    sample_group: Annotated[str | None, typer.Option("--sample-group")] = None,
    judge_group: Annotated[str | None, typer.Option("--judge-group")] = None,
    path: Annotated[Path | None, typer.Option("--config")] = None,
    artifact: Annotated[Path | None, typer.Option("--artifact", dir_okay=False)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run fanout + synthesis for a one-off prototype prompt."""
    cfg = load_config(path)
    effective_sample_group = sample_group or cfg.router.default_group
    effective_judge_group = judge_group or cfg.router.default_group
    _status(
        "pro fanout "
        f"n={n} sample_group={effective_sample_group} judge_group={effective_judge_group}",
        style="dim cyan",
    )
    for route in _route_metadata(cfg, effective_sample_group):
        _status(f"sample {route['provider']}: {route['model']}", style="dim cyan")
    if effective_judge_group != effective_sample_group:
        for route in _route_metadata(cfg, effective_judge_group):
            _status(f"judge {route['provider']}: {route['model']}", style="dim cyan")
    gw = ModelGateway(cfg)
    result = run_pro_mode(
        gw,
        prompt,
        n=n,
        sample_group=effective_sample_group,
        judge_group=effective_judge_group,
    )
    artifact_payload = {
        "prompt": prompt,
        "sample_group": effective_sample_group,
        "judge_group": effective_judge_group,
        "routes": {
            "sample": _route_metadata(cfg, effective_sample_group),
            "judge": _route_metadata(cfg, effective_judge_group),
        },
        "result": result,
    }
    if artifact is not None:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(artifact_payload, indent=2, default=str), encoding="utf-8")
        _status(f"artifact {artifact}", style="dim")
    candidates = cast(list[dict[str, object]], result.get("candidates", []))
    ok_count = sum(1 for candidate in candidates if candidate.get("ok"))
    _status(f"pro candidates ok={ok_count}/{len(candidates)}", style="dim")
    if not result.get("final"):
        _status("all candidate generations failed or returned empty text", style="red")
        for candidate in candidates[:5]:
            if candidate.get("ok"):
                continue
            _status(
                f"candidate {candidate.get('index')} error: {candidate.get('error')}",
                style="red",
            )
        raise typer.Exit(code=2)
    if json_output:
        console.print_json(json.dumps(result, default=str))
        return
    console.print(str(result.get("final", "")))


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
        if configured and any(
            dep.provider == info.id and dep.enabled for dep in configured.deployments
        ):
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
