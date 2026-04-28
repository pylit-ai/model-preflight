from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "onepassword_env_secrets.py"
SPEC = importlib.util.spec_from_file_location("onepassword_env_secrets", SCRIPT)
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_parse_env_skips_comments_and_unquotes_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "OPENROUTER_API_KEY='abc'",
                'GROQ_API_KEY="def"',
                "LOCAL_PROVIDER_IDS=ollama,lmstudio",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert mod.parse_env(env_file) == {
        "OPENROUTER_API_KEY": "abc",
        "GROQ_API_KEY": "def",
        "LOCAL_PROVIDER_IDS": "ollama,lmstudio",
    }


def test_ordered_values_preserves_example_order_then_env_then_existing(tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    env = tmp_path / ".env"
    example.write_text("OPENROUTER_API_KEY=\nLOCAL_PROVIDER_IDS=\n", encoding="utf-8")
    env.write_text("LOCAL_PROVIDER_IDS=ollama\nGROQ_API_KEY=secret\n", encoding="utf-8")

    values = mod.ordered_values(
        env_file=env,
        example_file=example,
        existing={"CEREBRAS_API_KEY": "old"},
    )

    assert values == [
        ("OPENROUTER_API_KEY", ""),
        ("LOCAL_PROVIDER_IDS", "ollama"),
        ("GROQ_API_KEY", "secret"),
        ("CEREBRAS_API_KEY", "old"),
    ]


def test_item_template_uses_concealed_for_api_keys() -> None:
    template = mod.item_template(
        "env",
        [("OPENROUTER_API_KEY", "secret"), ("LOCAL_PROVIDER_IDS", "ollama")],
    )
    fields = {field["label"]: field for field in template["fields"]}

    assert template["title"] == "env"
    assert fields["OPENROUTER_API_KEY"]["type"] == "CONCEALED"
    assert fields["LOCAL_PROVIDER_IDS"]["type"] == "STRING"


def test_format_env_value_quotes_spaces_and_empty_values() -> None:
    assert mod.format_env_value("abc-123") == "abc-123"
    assert mod.format_env_value("hello world") == '"hello world"'
    assert mod.format_env_value("") == '""'


def test_is_service_account_email() -> None:
    assert mod.is_service_account_email("abc@1passwordserviceaccounts.com")
    assert mod.is_service_account_email("svc@serviceaccounts.com")
    assert not mod.is_service_account_email("person@example.com")
