"""Tests for command execution compatibility."""

from pathlib import Path
from unittest.mock import Mock

from runner.scripts import em_cmd


def test_shell_globs_preserve_pathname_expansion(tmp_path: Path, monkeypatch) -> None:
    """Wildcard commands still expand paths after shell invocation was hardened."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(em_cmd, "RunnerLog", Mock())
    for filename in ("alpha.csv", "beta.csv", "report1.csv", "report2.csv", "a.txt", "b.txt"):
        (tmp_path / filename).touch()

    commands = {
        "echo *.csv": ["alpha.csv", "beta.csv", "report1.csv", "report2.csv"],
        "echo report?.csv": ["report1.csv", "report2.csv"],
        "echo [ab].txt": ["a.txt", "b.txt"],
    }
    for command, expected in commands.items():
        output = em_cmd.Cmd(None, None, command, "ok", "error").shell()
        assert sorted(output.split()) == expected


def test_shell_metacharacters_use_explicit_shell_with_shell_false(monkeypatch) -> None:
    command = "printf ok | tr o O"
    check_output = Mock(return_value=b"OK")
    monkeypatch.setattr(em_cmd.subprocess, "check_output", check_output)
    monkeypatch.setattr(em_cmd, "RunnerLog", Mock())

    result = em_cmd.Cmd(None, None, command, "ok", "error").shell()

    assert result == "OK"
    assert check_output.call_args.args[0] == ["/bin/sh", "-c", command]
    assert check_output.call_args.kwargs["shell"] is False
