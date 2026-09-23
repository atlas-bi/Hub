"""Test Python script dependency installation."""

from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import ClassVar, List

from runner.scripts import em_python


class RecordingCmd:
    """Record shell commands instead of running them."""

    commands: ClassVar[List[str]] = []

    def __init__(
        self,
        task: object,
        run_id: str,
        cmd: str,
        success_msg: str,
        error_msg: str,
    ) -> None:
        """Store the command passed by the production code."""
        self.command = cmd

    def shell(self) -> str:
        """Record the command and return empty module-list output."""
        self.commands.append(self.command)
        return (
            "Please wait a moment while I gather a list of all available modules..."
            "\nEnter any module name to get more help."
        )


def make_processor(job_path: Path) -> em_python.PyProcesser:
    """Create a processor instance without running its full constructor."""
    processor = em_python.PyProcesser.__new__(em_python.PyProcesser)
    processor.task = SimpleNamespace()
    processor.run_id = "job-1"
    processor.job_path = job_path
    processor.env_name = "job-1_env"
    processor.env_path = str(job_path / processor.env_name)
    return processor


def test_pyproject_with_project_metadata_uses_uv(tmp_path, monkeypatch) -> None:
    """Modern pyproject.toml jobs should install with uv into the job env."""
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo-job"
version = "0.1.0"
dependencies = ["requests"]
""",
        encoding="utf8",
    )
    RecordingCmd.commands = []
    monkeypatch.setattr(em_python, "Cmd", RecordingCmd)

    make_processor(tmp_path)._PyProcesser__pip_install()

    assert RecordingCmd.commands == [
        f'cd "{tmp_path}" && UV_PROJECT_ENVIRONMENT="{tmp_path / "job-1_env"}" '
        "uv sync --no-dev --no-install-project"
    ]


def test_poetry_only_pyproject_keeps_poetry_fallback(tmp_path, monkeypatch) -> None:
    """Legacy Poetry-only jobs should keep the existing Poetry install path."""
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.poetry]
name = "demo-job"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.0"
""",
        encoding="utf8",
    )
    RecordingCmd.commands = []
    monkeypatch.setattr(em_python, "Cmd", RecordingCmd)

    make_processor(tmp_path)._PyProcesser__pip_install()

    assert len(RecordingCmd.commands) == 2
    assert "virtualenv poetry_env" in RecordingCmd.commands[0]
    assert "poetry_env/bin/poetry lock" in RecordingCmd.commands[0]
    assert f'. "{Path("job-1_env")}/bin/activate"' in RecordingCmd.commands[1]
    assert "poetry_env/bin/poetry install" in RecordingCmd.commands[1]


def test_comma_separated_imports_are_installed_individually(tmp_path, monkeypatch) -> None:
    """Comma-separated imports should become separate package arguments."""
    (tmp_path / "script.py").write_text("import smtplib, ssl\n", encoding="utf8")
    RecordingCmd.commands = []
    monkeypatch.setattr(em_python, "Cmd", RecordingCmd)

    make_processor(tmp_path)._PyProcesser__pip_install()

    assert set(RecordingCmd.commands[-1].rsplit(" ", 2)[-2:]) == {"smtplib", "ssl"}


def test_failed_import_install_uses_unique_pypi_candidate(tmp_path, monkeypatch) -> None:
    """Retry a failed import install with a unique PyPI search result."""
    (tmp_path / "script.py").write_text("import PIL\n", encoding="utf8")
    commands = []

    class SearchCmd(RecordingCmd):
        def shell(self) -> str:
            commands.append(self.command)
            if "help('modules')" in self.command:
                return (
                    "Please wait a moment while I gather a list of all available modules..."
                    "\nEnter any module name to get more help."
                )
            if self.command.endswith(" PIL"):
                raise subprocess.CalledProcessError(1, self.command)
            return ""

    monkeypatch.setattr(em_python, "Cmd", SearchCmd)
    monkeypatch.setattr(em_python, "RunnerLog", lambda *args: None)
    monkeypatch.setattr(
        em_python,
        "requests",
        SimpleNamespace(
            get=lambda *args, **kwargs: SimpleNamespace(
                status_code=200,
                text='<a href="/project/Pillow/">Pillow</a>',
            )
        ),
        raising=False,
    )

    processor = make_processor(tmp_path)
    processor.task.id = 1
    processor._PyProcesser__pip_install()

    assert commands[-1].endswith(" Pillow")
