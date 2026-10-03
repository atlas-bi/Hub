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
    """Shell syntax uses an explicit shell process without shell=True."""
    command = "printf ok | tr o O"
    check_output = Mock(return_value=b"OK")
    monkeypatch.setattr(em_cmd.subprocess, "check_output", check_output)
    monkeypatch.setattr(em_cmd, "RunnerLog", Mock())

    result = em_cmd.Cmd(None, None, command, "ok", "error").shell()

    assert result == "OK"
    assert check_output.call_args.args[0] == ["/bin/sh", "-c", command]
    assert check_output.call_args.kwargs["shell"] is False


def test_shell_plain_command_uses_argv_with_shell_false(monkeypatch) -> None:
    """Plain shell commands are passed as argv without invoking a shell."""
    command = "echo plain command"
    check_output = Mock(return_value=b"plain command\n")
    monkeypatch.setattr(em_cmd.subprocess, "check_output", check_output)
    monkeypatch.setattr(em_cmd, "RunnerLog", Mock())

    result = em_cmd.Cmd(None, None, command, "ok", "error").shell()

    assert result == "plain command\n"
    assert check_output.call_args.args[0] == ["echo", "plain", "command"]
    assert check_output.call_args.kwargs["shell"] is False


def test_run_plain_command_uses_argv_with_shell_false(monkeypatch) -> None:
    """Plain run commands are passed as argv and return stdout."""
    command = "echo plain command"
    run = Mock(return_value=em_cmd.subprocess.CompletedProcess(command, 0, "plain command\n", ""))
    monkeypatch.setattr(em_cmd.subprocess, "run", run)
    # The exact pre-fix implementation uses os.popen; keep its red test process-free.
    monkeypatch.setattr(
        em_cmd.os, "popen", Mock(return_value=Mock(read=Mock(return_value="plain command\n")))
    )
    monkeypatch.setattr(em_cmd, "RunnerLog", Mock())

    result = em_cmd.Cmd(None, None, command, "ok", "error").run()

    assert result == "plain command\n"
    assert run.call_args.args[0] == ["echo", "plain", "command"]
    assert run.call_args.kwargs["shell"] is False


def test_run_shell_syntax_uses_explicit_shell_with_shell_false(monkeypatch) -> None:
    """Run preserves shell stdout-then-stderr output for shell syntax."""
    command = "printf out; printf err >&2"
    run = Mock(return_value=em_cmd.subprocess.CompletedProcess(command, 0, "stdout", "stderr"))
    monkeypatch.setattr(em_cmd.subprocess, "run", run)
    # The exact pre-fix implementation uses os.popen; keep its red test process-free.
    monkeypatch.setattr(
        em_cmd.os, "popen", Mock(return_value=Mock(read=Mock(return_value="stdoutstderr")))
    )
    monkeypatch.setattr(em_cmd, "RunnerLog", Mock())

    result = em_cmd.Cmd(None, None, command, "ok", "error").run()

    assert result == "stdoutstderr"
    assert run.call_args.args[0] == ["/bin/sh", "-c", command]
    assert run.call_args.kwargs["shell"] is False
