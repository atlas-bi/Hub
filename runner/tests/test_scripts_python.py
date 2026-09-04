"""Test Python script dependency installation."""

from pathlib import Path
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
        """Record the command and return empty command output."""
        self.commands.append(self.command)
        return ""


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
