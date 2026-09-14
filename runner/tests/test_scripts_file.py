"""Test local file output."""

import csv
from types import SimpleNamespace

from runner.scripts import em_file


def test_quote_none_preserves_literal_quotes_and_empty_rows(tmp_path, monkeypatch) -> None:
    """Quote-free output keeps data quotes and supports empty records."""
    source = tmp_path / "source.csv"
    with source.open("w", newline="") as stream:
        csv.writer(stream).writerows([['"', '"asdf"', "''"], [""]])

    task = SimpleNamespace(
        destination_file_name="output",
        destination_file_type_id=1,
        destination_ignore_delimiter=0,
        destination_file_delimiter=",",
        destination_quote_level_id=1,
        destination_file_line_terminator=None,
        destination_create_zip=0,
        file_type=SimpleNamespace(ext="csv"),
        file_gpg=0,
    )
    params = SimpleNamespace(insert_file_params=lambda value: value)
    monkeypatch.setattr(em_file, "RunnerLog", lambda *args: None)

    with source.open() as stream:
        em_file.File(task, None, stream, params).save()

    assert (tmp_path / "output.csv").read_bytes() == b'","asdf",\'\'\r\n\r\n'
