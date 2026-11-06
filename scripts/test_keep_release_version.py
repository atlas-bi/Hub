"""Target-branch version wins when a promotion hits a release conflict."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from keep_release_version import keep_ours


def test_keep_ours_replaces_conflict_with_target_version() -> None:
    conflict = (
        "<<<<<<< HEAD\n"
        '  "version": "2.14.0"\n'
        "=======\n"
        '  "version": "2.14.0-alpha.2"\n'
        ">>>>>>> origin/alpha\n"
    )

    assert keep_ours(conflict) == '  "version": "2.14.0"\n'


def test_keep_ours_leaves_unconflicted_text() -> None:
    assert keep_ours("2.14.0\n") == "2.14.0\n"
