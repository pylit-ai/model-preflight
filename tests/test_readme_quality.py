from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CONFIGURATION_DOC = ROOT / "docs" / "configuration.md"
AGENT_OPERATIONS_DOC = ROOT / "docs" / "agent-operations.md"


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_surfaces_first_useful_prompt_above_endpoint_map() -> None:
    readme = _readme()

    first_run = readme.index("## Ask your first prompt")
    endpoint_map = readme.index("## Free endpoint map")

    assert first_run < endpoint_map
    assert "mpf ask" in readme[first_run:endpoint_map]
    assert "mpf init --preset minimal" in readme[first_run:endpoint_map]
    assert "The `minimal` preset is intentionally boring" in readme[first_run:endpoint_map]
    assert "mpf doctor --live" in readme[first_run:endpoint_map]
    assert "Want an agent to initialize this repo?" in readme[first_run:endpoint_map]
    assert "Initialize ModelPreflight in this repository" in readme[first_run:endpoint_map]


def test_readme_has_agent_workflow_and_verification_guidance() -> None:
    readme = _readme()

    assert "## Agent operations" in readme
    agent_section = readme[readme.index("## Agent operations") :]
    assert "docs/agent-operations.md" in agent_section
    assert "docs/agent-specs/setup-model-preflight.md" in agent_section
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


def test_readme_explains_pro_mode_and_non_python_paths() -> None:
    readme = _readme()

    pro_section = readme[readme.index("## Fan out with Pro Mode") :]
    assert "Self-Consistency Improves Chain of Thought Reasoning" in pro_section
    assert "`-n 8` means" in pro_section
    assert "There is no TypeScript SDK yet" in readme
    assert "examples/node_hook_example.mjs" in readme


def test_verbose_configuration_and_agent_details_live_in_docs() -> None:
    readme = _readme()
    configuration = CONFIGURATION_DOC.read_text(encoding="utf-8")
    agent_operations = AGENT_OPERATIONS_DOC.read_text(encoding="utf-8")

    assert "## Configuration and secrets" in readme
    assert "## Config shape" not in readme
    assert "## Config shape" in configuration
    assert "Provider selection" in configuration
    assert "Copy-paste prompt: set up ModelPreflight" in agent_operations
    assert "Copy-paste prompt: prompt-based init" in agent_operations
    assert "OpenAI Symphony spec" in agent_operations
