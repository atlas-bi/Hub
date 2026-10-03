"""Tests for the TypeSafe-backed release audit inventory."""

# ruff: noqa: D101,D102,D103,D105,D107

import csv
import io
import json
import subprocess
import urllib.error
from unittest.mock import Mock

import pytest
import release_audit

COMMITS = [
    {"sha": "abc", "date": "2026-01-01", "subject": "fix auth", "paths": ["web/auth.py"]},
    {"sha": "def", "date": "2026-01-02", "subject": "docs", "paths": ["docs/use.md"]},
]


class Response:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.body


def test_request_uses_pinned_model_and_choice_criteria():
    payload = release_audit.request_payload(COMMITS)

    assert payload["model"] == "jev-1.13.0"
    assert payload["state"] == {"commits": COMMITS}
    assert len(payload["questions"]) == 2
    for index, question in enumerate(payload["questions"].values()):
        assert question["type"] == "choice"
        assert set(question["criteria"]) == {
            "behavior",
            "dependency",
            "build-tooling",
            "version-release",
            "tests-docs-style",
        }
        assert f"`commits[{index}]`" in question["instructions"]


def test_classify_batch_preserves_predictions_and_flags_confidence(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret")
    answers = {
        "commit_0": {"type": "choice", "choice": "behavior", "confidence": 0.69},
        "commit_1": {"type": "choice", "choice": "tests-docs-style", "confidence": 0.70},
    }
    seen = {}

    def urlopen(request, timeout=None):
        seen["request"] = request
        seen["timeout"] = timeout
        return Response({"model": "jev-1.13.0", "answers": answers})

    assert release_audit.classify_batch(COMMITS, 0.70, urlopen) == [
        ("behavior", 0.69, "jev-1.13.0", "yes"),
        ("tests-docs-style", 0.70, "jev-1.13.0", "no"),
    ]
    assert seen["request"].get_header("Authorization") == "Bearer secret"
    assert seen["timeout"] == release_audit.HTTP_TIMEOUT


def test_classify_batch_requires_api_key(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="TYPESAFE_API_KEY"):
        release_audit.classify_batch(COMMITS)


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["web/migrations/0012_add.py"], "migration"),
        (["runner/runner.py"], "runner"),
        (["scheduler/tasks.py", "web/views.py"], "cross-cutting"),
    ],
)
def test_subsystem(paths, expected):
    assert release_audit.subsystem(paths) == expected


@pytest.mark.parametrize(
    ("subject", "category", "area", "expected"),
    [
        ("add field", "behavior", "migration", "high"),
        ("fix auth check", "behavior", "web", "high"),
        ("fix display", "behavior", "web", "medium"),
        ("update docs", "tests-docs-style", "repository", "low"),
    ],
)
def test_risk(subject, category, area, expected):
    assert release_audit.risk(subject, category, area) == expected


def test_write_csv_header_and_rows():
    output = io.StringIO()
    release_audit.write_csv(
        output,
        [
            [
                "abc",
                "2026-01-01",
                "fix auth",
                "behavior",
                0.9,
                "jev-1.13.0",
                "no",
                "web",
                "high",
                "unreviewed",
                "no",
            ]
        ],
    )

    rows = list(csv.reader(io.StringIO(output.getvalue())))
    assert rows[0] == [
        "sha",
        "date",
        "subject",
        "category",
        "confidence",
        "model",
        "review_required",
        "subsystem",
        "risk",
        "evidence",
        "human_reviewed",
    ]
    assert rows[1][0:4] == ["abc", "2026-01-01", "fix auth", "behavior"]


def test_rows_to_csv_batches_git_commits_through_jev(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret")
    git_results = {
        (
            "log",
            "--no-merges",
            "--format=%H%x09%ad%x09%s",
            "--date=short",
            "--stdin",
            "--end-of-options",
        ): ("abc\t2026-01-01\tfix auth\ndef\t2026-01-02\tdocs update\n"),
        ("show", "--format=", "--name-only", "abc"): "web/auth.py\n",
        ("show", "--format=", "--name-only", "def"): "docs/use.md\n",
    }
    git_inputs = []

    def fake_git(*args, input_text=None):
        git_inputs.append(input_text)
        return git_results[args]

    monkeypatch.setattr(release_audit, "git", fake_git)
    calls = []

    def urlopen(api_request, timeout=None):
        commit = json.loads(api_request.data)["state"]["commits"][0]
        calls.append(commit["sha"])
        answer = (
            {"choice": "behavior", "confidence": 0.69}
            if commit["sha"] == "abc"
            else {"choice": "tests-docs-style", "confidence": 0.90}
        )
        return Response(
            {
                "model": "jev-1.13.0",
                "answers": {"commit_0": {"type": "choice", **answer}},
            }
        )

    monkeypatch.setattr(release_audit.request, "urlopen", urlopen)
    output = io.StringIO()
    release_audit.write_csv(output, release_audit.rows("base..head", batch_size=1))

    assert calls == ["abc", "def"]
    assert git_inputs == ["base..head\n", None, None]
    assert list(csv.reader(io.StringIO(output.getvalue()))) == [
        release_audit.HEADER,
        [
            "abc",
            "2026-01-01",
            "fix auth",
            "behavior",
            "0.69",
            "jev-1.13.0",
            "yes",
            "web",
            "high",
            "unreviewed",
            "no",
        ],
        [
            "def",
            "2026-01-02",
            "docs update",
            "tests-docs-style",
            "0.9",
            "jev-1.13.0",
            "no",
            "repository",
            "low",
            "not-required",
            "no",
        ],
    ]


def test_main_reports_git_error_without_traceback(monkeypatch, capsys):
    def fail(*_args, **_kwargs):
        raise subprocess.CalledProcessError(
            128,
            ["git", "log", "--no-merges", "--stdin", "--end-of-options"],
            stderr="fatal: bad revision",
        )

    monkeypatch.setattr(release_audit.subprocess, "run", fail)

    with pytest.raises(SystemExit) as exit_info:
        release_audit.main(["missing..origin/dev"])

    assert exit_info.value.code == 1
    error = capsys.readouterr().err
    assert "git log --no-merges --stdin --end-of-options" in error
    assert "fatal: bad revision" in error
    assert "Traceback" not in error


def test_main_rejects_malformed_revision_range_without_running_git(monkeypatch, capsys):
    run = Mock()
    monkeypatch.setattr(release_audit.subprocess, "run", run)

    with pytest.raises(SystemExit) as exit_info:
        release_audit.main(["bad-range"])

    assert exit_info.value.code == 1
    assert "revision range must contain two plain refs" in capsys.readouterr().err
    run.assert_not_called()


def test_main_writes_nothing_when_a_later_batch_fails(monkeypatch, capsys):
    def partial_rows(*_args, **_kwargs):
        yield [
            "abc",
            "2026-01-01",
            "fix",
            "behavior",
            0.9,
            release_audit.MODEL,
            "no",
            "web",
            "medium",
            "unreviewed",
            "no",
        ]
        raise RuntimeError("batch 2 failed")

    monkeypatch.setattr(release_audit, "rows", partial_rows)

    with pytest.raises(SystemExit):
        release_audit.main(["range"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "batch 2 failed" in captured.err


def http_error(status, retry_after=None):
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return urllib.error.HTTPError(release_audit.API_URL, status, f"status {status}", headers, None)


def test_classify_retries_429_and_honors_retry_after(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret")
    calls = []
    sleeps = []

    def urlopen(_request, timeout=None):
        calls.append(timeout)
        if len(calls) == 1:
            raise http_error(429, "0.25")
        return Response(
            {
                "model": "jev-1.13.0",
                "answers": {
                    "commit_0": {
                        "type": "choice",
                        "choice": "behavior",
                        "confidence": 0.8,
                    }
                },
            }
        )

    release_audit.classify_batch(COMMITS[:1], urlopen=urlopen, sleep=sleeps.append)

    assert calls == [release_audit.HTTP_TIMEOUT, release_audit.HTTP_TIMEOUT]
    assert sleeps == [0.25]


@pytest.mark.parametrize("retry_after", ["-1", "nan", "inf", "invalid"])
def test_classify_uses_backoff_for_invalid_retry_after(monkeypatch, retry_after):
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret")
    calls = 0
    sleeps = []

    def urlopen(_request, timeout=None):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise http_error(429, retry_after)
        return Response(
            {
                "model": "jev-1.13.0",
                "answers": {
                    "commit_0": {
                        "type": "choice",
                        "choice": "behavior",
                        "confidence": 0.8,
                    }
                },
            }
        )

    release_audit.classify_batch(COMMITS[:1], urlopen=urlopen, sleep=sleeps.append)

    assert sleeps == [1]


def test_classify_uses_bounded_backoff_then_fails_usefully(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret")
    sleeps = []
    calls = 0

    def urlopen(_request, timeout=None):
        nonlocal calls
        calls += 1
        raise http_error(529)

    with pytest.raises(RuntimeError, match=r"HTTP 529.*3 attempts"):
        release_audit.classify_batch(COMMITS[:1], urlopen=urlopen, sleep=sleeps.append)

    assert calls == 3
    assert sleeps == [1, 2]


def test_classify_does_not_retry_authentication_errors(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret")
    calls = 0

    def urlopen(_request, timeout=None):
        nonlocal calls
        calls += 1
        raise http_error(401)

    with pytest.raises(RuntimeError, match="HTTP 401"):
        release_audit.classify_batch(COMMITS[:1], urlopen=urlopen, sleep=lambda _delay: None)

    assert calls == 1


@pytest.mark.parametrize("ref", ["v2.12.3", "origin/dev", "refs/heads/release-1", "a" * 40])
def test_validate_revision_range_accepts_plain_refs(ref):
    assert release_audit.validate_revision_range(f"{ref}..{ref}") == f"{ref}..{ref}"


@pytest.mark.parametrize(
    "revision_range",
    [
        "--upload-pack=touch /tmp/pwned..HEAD",
        "v2.12.3..origin/dev;touch /tmp/pwned",
        "HEAD~1..origin/dev",
        "base...head",
        "base..--exec=sh",
        "base..origin//dev",
    ],
)
def test_commits_rejects_unsafe_revision_range_before_git(monkeypatch, revision_range):
    run = Mock()
    monkeypatch.setattr(release_audit.subprocess, "run", run)

    with pytest.raises(RuntimeError, match="revision range must contain two plain refs"):
        release_audit.commits(revision_range)

    run.assert_not_called()


def test_commits_passes_validated_revision_range_through_stdin(monkeypatch):
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="", stderr=""))
    monkeypatch.setattr(release_audit.subprocess, "run", run)

    assert release_audit.commits("v2.12.3..origin/dev") == []

    command = run.call_args.args[0]
    assert "--stdin" in command
    assert "v2.12.3..origin/dev" not in command
    assert run.call_args.kwargs["input"] == "v2.12.3..origin/dev\n"
