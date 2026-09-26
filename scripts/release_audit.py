"""Classify release commits with TypeSafe Jev and emit CSV."""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from urllib import error, request

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"
HTTP_TIMEOUT = 30
MAX_ATTEMPTS = 3
MAX_BACKOFF = 30
HEADER = [
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
CRITERIA = {
    "behavior": (
        "Handwritten runtime behavior, including features, fixes, authentication, UI, "
        "scheduler, runner, and migrations. Prefer this when runtime impact is plausible."
    ),
    "dependency": (
        "Package or action version updates only, with no handwritten runtime behavior."
    ),
    "build-tooling": (
        "CI, packaging, Docker, lint, format, or release tooling with no runtime behavior."
    ),
    "version-release": "Generated release or version metadata.",
    "tests-docs-style": (
        "Tests, documentation, style-only changes, or static assets with no runtime behavior."
    ),
}


def request_payload(commits):
    """Build independent Choice questions over one structured commit batch."""
    questions = {}
    for index in range(len(commits)):
        questions[f"commit_{index}"] = {
            "type": "choice",
            "instructions": (
                f"Classify `commits[{index}]` from both its subject and paths. "
                "Choose behavior conservatively whenever runtime impact is plausible."
            ),
            "criteria": CRITERIA,
        }
    return {"state": {"commits": commits}, "model": MODEL, "questions": questions}


def classify_batch(commits, confidence_threshold=0.70, urlopen=None, sleep=None):
    """Return Jev category, confidence, model, and review flag for each commit."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is required")

    api_request = request.Request(  # noqa: S310 - API_URL is a fixed HTTPS endpoint.
        API_URL,
        data=json.dumps(request_payload(commits)).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    opener = urlopen or request.urlopen
    sleeper = sleep or time.sleep
    for attempt in range(MAX_ATTEMPTS):
        try:
            with opener(api_request, timeout=HTTP_TIMEOUT) as response:  # noqa: S310
                result = json.loads(response.read())
            break
        except error.HTTPError as exc:
            if exc.code not in (429, 529):
                raise RuntimeError(
                    f"TypeSafe classification failed: HTTP {exc.code} {exc.reason}"
                ) from exc
            if attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(
                    f"TypeSafe classification failed: HTTP {exc.code} after "
                    f"{MAX_ATTEMPTS} attempts"
                ) from exc
            try:
                delay = float((exc.headers or {}).get("Retry-After", 2**attempt))
                if not delay >= 0:
                    raise ValueError
            except (TypeError, ValueError):
                delay = 2**attempt
            sleeper(min(delay, MAX_BACKOFF))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(f"TypeSafe classification failed: {exc}") from exc

    try:
        model = result["model"]
        return [
            (
                result["answers"][f"commit_{index}"]["choice"],
                result["answers"][f"commit_{index}"]["confidence"],
                model,
                "yes"
                if result["answers"][f"commit_{index}"]["confidence"] < confidence_threshold
                else "no",
            )
            for index in range(len(commits))
        ]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"TypeSafe classification failed: {exc}") from exc


def git(*args):
    """Run Git and return standard output."""
    command = ["git", *args]
    try:
        return subprocess.run(  # noqa: S603
            command,  # noqa: S607
            check=True,
            text=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or f"exit status {exc.returncode}"
        raise RuntimeError(f"{' '.join(exc.cmd)} failed: {detail}") from exc


def commits(revision_range):
    """Read commit metadata and changed paths from Git."""
    found = []
    log = git(
        "log",
        "--no-merges",
        "--format=%H%x09%ad%x09%s",
        "--date=short",
        "--end-of-options",
        revision_range,
    )
    for line in log.splitlines():
        sha, date, subject = line.split("\t", 2)
        paths = git("show", "--format=", "--name-only", sha).splitlines()
        found.append({"sha": sha, "date": date, "subject": subject, "paths": paths})
    return found


def subsystem(paths):
    """Return the deterministic subsystem represented by paths."""
    if any("/migrations/" in f"/{path}" for path in paths):
        return "migration"
    areas = {path.split("/", 1)[0] for path in paths} & {"web", "runner", "scheduler"}
    if len(areas) > 1:
        return "cross-cutting"
    return next(iter(areas), "repository")


def risk(subject, category, area):
    """Return the audit risk level for a classified commit."""
    if area == "migration":
        return "high"
    if category != "behavior":
        return "low"
    if any(term in subject.lower() for term in ("auth", "security", "delete", "credential")):
        return "high"
    return "medium"


def rows(revision_range, confidence_threshold=0.70, batch_size=10):
    """Yield classified audit rows in bounded Jev batches."""
    all_commits = commits(revision_range)
    for start in range(0, len(all_commits), batch_size):
        batch = all_commits[start : start + batch_size]
        for commit, prediction in zip(
            batch, classify_batch(batch, confidence_threshold), strict=True
        ):
            category, confidence, model, review_required = prediction
            area = subsystem(commit["paths"])
            yield [
                commit["sha"],
                commit["date"],
                commit["subject"],
                category,
                confidence,
                model,
                review_required,
                area,
                risk(commit["subject"], category, area),
                "unreviewed" if category == "behavior" else "not-required",
                "no",
            ]


def write_csv(output, audit_rows):
    """Write the audit header and rows as CSV."""
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(audit_rows)


def main(argv=None):
    """Run the release audit command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision_range", nargs="?", default="v2.12.3..origin/dev")
    parser.add_argument("--confidence-threshold", type=float, default=0.70)
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args(argv)
    if not 0 <= args.confidence_threshold <= 1:
        parser.error("--confidence-threshold must be between 0 and 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    try:
        audit_rows = list(rows(args.revision_range, args.confidence_threshold, args.batch_size))
        write_csv(sys.stdout, audit_rows)
    except RuntimeError as exc:
        parser.exit(1, f"release audit: {exc}\n")


if __name__ == "__main__":
    main()
