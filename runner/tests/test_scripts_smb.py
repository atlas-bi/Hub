"""Test SMB file loading."""

from io import BytesIO
from types import SimpleNamespace

from runner.scripts import em_smb


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
