from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that a release tag matches pyproject.toml project.version."
    )
    parser.add_argument("tag", help="Release tag, for example v0.1.3")
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to pyproject.toml",
    )
    args = parser.parse_args()

    tag_version = args.tag.removeprefix("refs/tags/").removeprefix("v")
    pyproject_path = Path(args.pyproject)
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project_version = data["project"]["version"]

    if tag_version != project_version:
        print(
            f"version mismatch: tag {args.tag!r} implies {tag_version!r}, "
            f"but {pyproject_path} declares {project_version!r}",
            file=sys.stderr,
        )
        return 1

    print(f"version ok: {project_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
