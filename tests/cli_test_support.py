"""Keep CLI stream assertions portable across supported Click versions."""

from inspect import signature

from typer.testing import CliRunner


def separate_stream_runner() -> CliRunner:
    # Click 8.2+ always captures stderr separately and removed this argument.
    if "mix_stderr" in signature(CliRunner).parameters:
        return CliRunner(mix_stderr=False)
    return CliRunner()
