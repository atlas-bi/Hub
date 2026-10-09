"""Task processing regression tests."""

from types import SimpleNamespace
from unittest.mock import Mock

from flask import Flask

from runner.scripts import task_runner


def test_url_repository_processing_handles_blank_script_name(tmp_path, monkeypatch) -> None:
    """A cloned URL processor keeps a path fallback for a blank command."""
    processor = Mock()
    processor.run.return_value = None
    processor_class = Mock(return_value=processor)
    monkeypatch.setattr(task_runner, "Cmd", Mock())
    monkeypatch.setattr(task_runner, "PyProcesser", processor_class)
    monkeypatch.setattr(task_runner, "RunnerLog", lambda *args: None)
    monkeypatch.setattr(task_runner, "RunnerException", RuntimeError)

    runner = task_runner.Runner.__new__(task_runner.Runner)
    runner.task = SimpleNamespace(
        processing_type_id=5,
        processing_url="https://example.test/processors.git",
        processing_command="",
    )
    runner.run_id = "run-1"
    runner.temp_path = tmp_path
    runner.source_files = []
    runner.param_loader = Mock()

    app = Flask(__name__)
    with app.app_context():
        runner._Runner__process()

    assert processor_class.call_args.kwargs["script"] == tmp_path.name
