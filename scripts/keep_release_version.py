"""Keep the target side of release-version merge conflicts.

Promotion merges (dev -> alpha -> main) only conflict on the files semantic-release
writes. The destination branch's version stays in place; the release job retags
after the merge.
"""

import re
import sys
from pathlib import Path

PATTERN = re.compile(r"^<<<<<<< .*?\n(.*?)=======\n.*?^>>>>>>> .*?\n", re.M | re.S)


def keep_ours(text: str) -> str:
    """Replace conflict markers with the target-branch side."""
    resolved = PATTERN.sub(r"\1", text)
    if "<<<<<<<" in resolved or ">>>>>>>" in resolved:
        raise SystemExit(f"unresolved conflict markers remain:\n{resolved}")
    return resolved


def main() -> None:
    """Resolve the version files passed on the command line."""
    for name in sys.argv[1:]:
        path = Path(name)
        path.write_text(keep_ours(path.read_text()))


if __name__ == "__main__":
    main()
