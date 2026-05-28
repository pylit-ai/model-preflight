#!/usr/bin/env python3
"""Generate dependency license inventory and a minimal CycloneDX SBOM."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

DENY_LICENSE_RE = re.compile(r"\b(AGPL|GPL|LGPL|SSPL|BUSL|PROPRIETARY)\b", re.IGNORECASE)
UNKNOWN_LICENSES = {"", "UNKNOWN", "UNKNOWN LICENSE", "N/A", "NONE"}


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def project_dependencies(pyproject: Path) -> set[str]:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
        print("Python 3.11+ is required for tomllib", file=sys.stderr)
        raise SystemExit(2) from None

    data = tomllib.loads(pyproject.read_text())
    deps = set()
    for dep in data.get("project", {}).get("dependencies", []):
        name = re.split(r"[<>=!~;,\[\]\s]", dep, maxsplit=1)[0]
        if name:
            deps.add(normalize_name(name))
    return deps


def license_text(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    license_value = (meta.get("License") or "").strip()
    expressions = [value.strip() for value in meta.get_all("License-Expression") or []]
    classifiers = [
        value.rsplit("::", 1)[-1].strip()
        for value in meta.get_all("Classifier") or []
        if value.startswith("License ::")
    ]
    values = [license_value, *expressions, *classifiers]
    return " OR ".join(value for value in values if value).strip()


def package_url(name: str, version: str) -> str:
    return f"pkg:pypi/{normalize_name(name)}@{version}"


def inventory(include_all: bool, pyproject: Path) -> list[dict[str, str]]:
    direct = project_dependencies(pyproject)
    rows = []

    distributions = sorted(
        metadata.distributions(),
        key=lambda item: normalize_name(item.metadata["Name"]),
    )
    for dist in distributions:
        name = dist.metadata["Name"]
        normalized = normalize_name(name)
        if not include_all and normalized not in direct and normalized != "model-preflight":
            continue
        version = dist.version
        license_value = license_text(dist)
        rows.append(
            {
                "name": name,
                "normalized_name": normalized,
                "version": version,
                "license": license_value,
                "package_url": package_url(name, version),
                "direct": normalized in direct,
            }
        )

    return rows


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def sbom(rows: list[dict[str, str]]) -> dict[str, object]:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": [
                {
                    "vendor": "ModelPreflight",
                    "name": "dependency_license_audit.py",
                    "version": "1",
                }
            ],
            "component": {
                "type": "application",
                "name": "model-preflight",
            },
        },
        "components": [
            {
                "type": "library",
                "name": row["name"],
                "version": row["version"],
                "purl": row["package_url"],
                "licenses": [{"license": {"name": row["license"] or "UNKNOWN"}}],
            }
            for row in rows
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument(
        "--license-output",
        type=Path,
        default=Path("build/dependency-licenses.json"),
    )
    parser.add_argument("--sbom-output", type=Path, default=Path("build/sbom.cdx.json"))
    parser.add_argument("--include-all", action="store_true")
    args = parser.parse_args()

    rows = inventory(include_all=args.include_all, pyproject=args.pyproject)
    failures = []
    for row in rows:
        license_value = row["license"].strip()
        if license_value.upper() in UNKNOWN_LICENSES:
            failures.append(f"{row['name']} {row['version']}: missing license metadata")
        elif DENY_LICENSE_RE.search(license_value):
            failures.append(
                f"{row['name']} {row['version']}: denied license metadata {license_value!r}"
            )

    write_json(args.license_output, {"dependencies": rows})
    write_json(args.sbom_output, sbom(rows))

    if failures:
        print("dependency license audit failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"wrote {args.license_output}")
    print(f"wrote {args.sbom_output}")
    print(f"audited {len(rows)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
