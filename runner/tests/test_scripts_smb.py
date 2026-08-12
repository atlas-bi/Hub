"""Test SMB file loading."""

from io import BytesIO
from types import SimpleNamespace

from runner.scripts import em_smb


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

    result = smb._Smb__load_file("input.txt", 1, 1)

    assert (tmp_path / "input.txt").read_bytes() == b"one,two\r\nthree,four\r\n"
    assert result.name == str(tmp_path / "input.txt")
