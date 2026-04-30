from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_surfaces_first_successful_path_above_endpoint_map() -> None:
    readme = _readme()

    first_run = readme.index("## First green check")
    endpoint_map = readme.index("## Free endpoint map")

    assert first_run < endpoint_map
    assert "uvx model-preflight --help" in readme[first_run:endpoint_map]
    assert "mpf init --preset minimal" in readme[first_run:endpoint_map]
    assert '"passed": true' in readme[first_run:endpoint_map]


def test_readme_has_agent_workflow_and_verification_guidance() -> None:
    readme = _readme()

    assert "## For coding agents" in readme
    agent_section = readme[readme.index("## For coding agents") :]
    assert "README verification" in agent_section
    assert "uv run pytest tests/test_readme_quality.py" in agent_section
    assert "Do not copy private" in agent_section


def test_readme_media_and_claims_are_registry_safe() -> None:
    readme = _readme()

    assert "raw.githubusercontent.com/pylit-ai/model-preflight/main/docs/assets/hero.png" in readme
    assert (
        "raw.githubusercontent.com/pylit-ai/model-preflight/main/docs/assets/readme-icons/preflight.svg"
        in readme
    )
    assert "<!-- TODO: Add terminal demo GIF showing" in readme
    assert "<!-- TODO: Add product screenshot showing" in readme
    assert "<!-- TODO: Add 60-second setup video link." in readme
    assert "Provider notes last reviewed: 2026-04-30." in readme
