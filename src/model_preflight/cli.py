from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .config import load_config, missing_env_vars, write_default_config
from .pro_mode import pro_mode as run_pro_mode
from .router import ModelGateway
from .smoke import SmokeCase, run_smoke_cases

app = typer.Typer(no_args_is_help=True, help="Preflight checks for LLM prototypes.")
console = Console()


def _deployment_table(cfg, *, title: str = "ModelPreflight deployments") -> Table:
    table = Table(title=title)
    for col in ["enabled", "name", "group", "tier", "model", "api_key_env", "env_ok", "rpm"]:
        table.add_column(col)
    missing = set(missing_env_vars(cfg))
    for dep in cfg.deployments:
        env_ok = "yes"
        if dep.api_key_env and dep.api_key_env in missing:
            env_ok = "missing"
        table.add_row(
            str(dep.enabled),
            dep.name,
            dep.group,
            dep.tier,
            dep.model,
            dep.api_key_env or "",
            env_ok,
            str(dep.rpm or ""),
        )
    return table


@app.command()
def init(
    path: Annotated[Path | None, typer.Option("--config")] = None,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
) -> None:
    """Create the machine-local ModelPreflight config."""
    out = write_default_config(path, overwrite=overwrite)
    console.print(f"wrote config: {out}")


@app.command()
def doctor(path: Annotated[Path | None, typer.Option("--config")] = None) -> None:
    """Validate config and required provider environment variables."""
    cfg = load_config(path)
    console.print(_deployment_table(cfg))
    missing = missing_env_vars(cfg)
    if missing:
        console.print(f"missing env vars: {', '.join(missing)}")
        raise typer.Exit(code=2)


@app.command()
def models(path: Annotated[Path | None, typer.Option("--config")] = None) -> None:
    """List configured provider/model deployments."""
    cfg = load_config(path)
    console.print(_deployment_table(cfg, title="ModelPreflight model groups"))


@app.command()
def run(
    cases: Annotated[Path, typer.Argument(exists=True, readable=True, help="JSONL smoke cases")],
    path: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    """Run project-local smoke cases."""
    raw = [json.loads(line) for line in cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    parsed = [SmokeCase.model_validate(row) for row in raw]
    results = run_smoke_cases(ModelGateway(load_config(path)), parsed)
    console.print_json(json.dumps([r.model_dump() for r in results], indent=2))
    if not all(r.passed for r in results):
        raise typer.Exit(code=1)


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
