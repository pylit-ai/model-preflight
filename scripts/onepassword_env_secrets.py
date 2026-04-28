#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

DEFAULT_VAULT = "model-preflight"
DEFAULT_ITEM = "env"
STRING_FIELDS = frozenset(
    {
        "MODEL_PREFLIGHT_CONFIG",
        "PROVIDER_PRESETS",
        "LOCAL_PROVIDER_IDS",
        "OLLAMA_BASE_URL",
        "LMSTUDIO_BASE_URL",
        "LLAMACPP_BASE_URL",
    }
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


ROOT = repo_root()


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"').strip("'")
    return values


def format_env_value(value: str) -> str:
    safe = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:/,@")
    if value and all(ch in safe for ch in value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def is_service_account_email(email: str) -> bool:
    return email.endswith("@1passwordserviceaccounts.com") or "serviceaccounts.com" in email


def op_run(args: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=dict(os.environ),
    )


def ensure_op_auth(*, allow_service_account: bool) -> dict[str, object]:
    proc = op_run(["op", "whoami", "--format", "json"])
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip() or "unknown 1Password auth error"
        raise SystemExit(
            "1Password CLI is not ready in this shell.\n"
            "Run this command from a terminal where `op vault list` works.\n\n"
            f"op error: {msg}"
        )
    whoami = json.loads(proc.stdout)
    email = str(whoami.get("email", ""))
    if is_service_account_email(email) and not allow_service_account:
        raise SystemExit(
            "Refusing service-account auth by default.\n"
            "Unset `OP_SERVICE_ACCOUNT_TOKEN` and rerun from a human-authenticated shell, "
            "or pass `--allow-service-account` intentionally."
        )
    return whoami


def field_type(key: str) -> str:
    return "STRING" if key in STRING_FIELDS else "CONCEALED"


def ordered_values(
    env_file: Path,
    example_file: Path,
    existing: dict[str, str],
) -> list[tuple[str, str]]:
    env_values = parse_env(env_file)
    example_values = parse_env(example_file)
    merged = dict(existing)
    merged.update(example_values)
    merged.update(env_values)

    ordered: list[str] = []
    for source in (tuple(example_values), tuple(env_values), tuple(existing)):
        for key in source:
            if key not in ordered:
                ordered.append(key)
    return [(key, merged.get(key, "")) for key in ordered]


def item_template(title: str, values: list[tuple[str, str]]) -> dict[str, object]:
    fields: list[dict[str, object]] = [
        {
            "id": "notesPlain",
            "type": "STRING",
            "purpose": "NOTES",
            "label": "notesPlain",
            "value": "Managed by model-preflight 1Password helper. Field labels map to env vars.",
        }
    ]
    for idx, (key, value) in enumerate(values, start=1):
        fields.append(
            {
                "id": f"field_{idx:03d}",
                "section": {"id": "Section_env"},
                "type": field_type(key),
                "label": key,
                "value": value,
            }
        )
    return {
        "title": title,
        "category": "SECURE_NOTE",
        "sections": [{"id": "Section_env"}],
        "fields": fields,
    }


def ensure_vault(vault: str) -> str:
    existing = op_run(["op", "vault", "get", vault, "--format", "json"])
    if existing.returncode == 0:
        return "exists"
    created = op_run(
        [
            "op",
            "vault",
            "create",
            vault,
            "--description",
            "ModelPreflight local secrets",
        ]
    )
    if created.returncode != 0:
        msg = created.stderr.strip() or created.stdout.strip()
        raise SystemExit(f"failed to create vault {vault}: {msg}")
    return "created"


def existing_item_values(vault: str, title: str) -> dict[str, str]:
    current = op_run(
        ["op", "item", "get", title, "--vault", vault, "--format", "json", "--reveal"]
    )
    if current.returncode != 0:
        return {}
    item = json.loads(current.stdout)
    return {
        str(field["label"]): str(field.get("value", ""))
        for field in item.get("fields", [])
        if field.get("label") and field.get("label") != "notesPlain"
    }


def push(vault: str, title: str, env_file: Path, example_file: Path) -> tuple[str, int]:
    existing = existing_item_values(vault, title)
    values = ordered_values(env_file=env_file, example_file=example_file, existing=existing)
    template = item_template(title, values)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
        json.dump(template, handle)
        temp_path = handle.name
    try:
        current = op_run(["op", "item", "get", title, "--vault", vault, "--format", "json"])
        if current.returncode == 0:
            proc = op_run(["op", "item", "edit", title, "--vault", vault, "--template", temp_path])
            action = "updated"
        else:
            proc = op_run(["op", "item", "create", "--vault", vault, "--template", temp_path])
            action = "created"
        if proc.returncode != 0:
            msg = proc.stderr.strip() or proc.stdout.strip()
            raise SystemExit(f"failed to {action} {title} in {vault}: {msg}")
    finally:
        Path(temp_path).unlink(missing_ok=True)
    return action, len(values)


def pull(vault: str, title: str, env_file: Path, example_file: Path) -> tuple[Path, int]:
    proc = op_run(["op", "item", "get", title, "--vault", vault, "--format", "json", "--reveal"])
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip()
        raise SystemExit(f"failed to read {title} from {vault}: {msg}")
    item = json.loads(proc.stdout)
    values = {
        str(field["label"]): str(field.get("value", ""))
        for field in item.get("fields", [])
        if field.get("label") and field.get("label") != "notesPlain"
    }
    ordered_keys = [key for key, _ in parse_env(example_file).items()]
    for key in values:
        if key not in ordered_keys:
            ordered_keys.append(key)
    env_file.write_text(
        "\n".join(f"{key}={format_env_value(values.get(key, ''))}" for key in ordered_keys)
        + "\n",
        encoding="utf-8",
    )
    return env_file, len(ordered_keys)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("push", "pull"))
    parser.add_argument("--vault", default=DEFAULT_VAULT)
    parser.add_argument("--item", default=DEFAULT_ITEM)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--example-file", default=".env.example")
    parser.add_argument("--allow-service-account", action="store_true")
    args = parser.parse_args(argv)

    whoami = ensure_op_auth(allow_service_account=args.allow_service_account)
    print(f"1Password auth: {whoami.get('email', '<unknown>')} @ {whoami.get('url', '<unknown>')}")
    if args.command == "push":
        vault_state = ensure_vault(args.vault)
        action, count = push(args.vault, args.item, ROOT / args.env_file, ROOT / args.example_file)
        print(f"{args.vault}: vault {vault_state}; {args.item} {action}; {count} managed fields")
    else:
        dest, count = pull(args.vault, args.item, ROOT / args.env_file, ROOT / args.example_file)
        print(f"{dest.name}: wrote {count} fields from {args.vault}/{args.item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
