"""Test SMB file loading."""

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

from runner.scripts import em_smb


def test_backup_save_includes_configured_subfolder(tmp_path, monkeypatch) -> None:
    """Default SMB backups retain the configured subfolder hierarchy."""
    (tmp_path / "report.csv").write_text("patient_id,status\n", encoding="utf8")
    connection = Mock()
    connection.storeFile.return_value = 18
    monkeypatch.setattr(em_smb, "RunnerLog", lambda *args: None)
    monkeypatch.setattr(em_smb, "RunnerException", RuntimeError)

    smb = em_smb.Smb.__new__(em_smb.Smb)
    smb.task = SimpleNamespace(
        project=SimpleNamespace(name="Hospital Reports"),
        name="Patient Export",
        last_run_job_id="run-1",
    )
    smb.run_id = "run-1"
    smb.dir = tmp_path
    smb.connection = None
    smb.conn = connection
    smb.share_name = "backups"
    smb.subfolder = "hospital-data"

    destination = smb.save(overwrite=1, file_name="report.csv")

    assert destination == "hospital-data/Hospital Reports/Patient Export/run-1/report.csv"
    assert connection.storeFile.call_args.args[:2] == ("backups", destination)


def test_load_file_includes_connection_path(tmp_path, monkeypatch) -> None:
    """SMB downloads include the configured connection path."""
    opened_urls = []

    class FakeOpener:
        def open(self, url):
            opened_urls.append(url)
            return BytesIO(b"data")

    monkeypatch.setattr(em_smb.urllib.request, "build_opener", lambda _handler: FakeOpener())
    monkeypatch.setattr(em_smb, "em_decrypt", lambda value, _key: value)
    monkeypatch.setattr(em_smb, "RunnerLog", lambda *args: None)
    monkeypatch.setattr(em_smb, "app", SimpleNamespace(config={"PASS_KEY": "key"}))

    smb = em_smb.Smb.__new__(em_smb.Smb)
    smb.task = SimpleNamespace(source_smb_ignore_delimiter=1, source_smb_delimiter=None)
    smb.run_id = None
    smb.dir = tmp_path
    smb.username = "user"
    smb.password = None
    smb.server_name = "server"
    smb.server_ip = "127.0.0.1"
    smb.share_name = "share"
    smb.connection = SimpleNamespace(path="folder")

    smb._Smb__load_file("input.txt", 1, 1)

    assert opened_urls == ["smb://user:None@server,127.0.0.1/share/folder/input.txt"]


def test_read_converts_binary_delimited_smb_data(tmp_path, monkeypatch) -> None:
    """Delimited SMB data opened as bytes is converted to a text file."""

    class FakeOpener:
        def open(self, _url):
            return BytesIO(b"one|two\nthree|four\n")

    monkeypatch.setattr(em_smb.urllib.request, "build_opener", lambda _handler: FakeOpener())
    monkeypatch.setattr(em_smb, "em_decrypt", lambda value, _key: value)
    monkeypatch.setattr(em_smb, "RunnerLog", lambda *args: None)
    monkeypatch.setattr(em_smb, "app", SimpleNamespace(config={"PASS_KEY": "key"}))

    smb = em_smb.Smb.__new__(em_smb.Smb)
    smb.task = SimpleNamespace(source_smb_ignore_delimiter=0, source_smb_delimiter="|")
    smb.run_id = None
    smb.dir = tmp_path
    smb.username = "user"
    smb.password = None
    smb.server_name = "server"
    smb.server_ip = "127.0.0.1"
    smb.share_name = "share"
    smb.connection = None

    result = smb._Smb__load_file("input.txt", 1, 1)

    assert (tmp_path / "input.txt").read_bytes() == b"one,two\r\nthree,four\r\n"
    assert result.name == str(tmp_path / "input.txt")
