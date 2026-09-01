#!/usr/bin/env python3
"""Ownership check for PRs: every changed file must belong to the PR author.

Usage: python scripts/check_pr_paths.py <actor> <changed-file> [<changed-file> ...]

Allowed changes:
  roster/<student-id>.md            if the file's `github:` value == actor
  submissions/<student-id>/**       if roster/<student-id>.md maps to actor
"""
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^\d{6,10}$")


def roster_owner(student_id: str) -> str | None:
    f = Path("roster") / f"{student_id}.md"
    source = f if f.is_file() else None
    if source is None:
        return None
    m = re.search(r"github:\s*@?([A-Za-z0-9-]+)", source.read_text(encoding="utf-8"))
    return m.group(1).lower() if m else None


def github_value_in(path: Path) -> str | None:
    m = re.search(r"github:\s*@?([A-Za-z0-9-]+)", path.read_text(encoding="utf-8"))
    return m.group(1).lower() if m else None


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    actor = sys.argv[1].lower()
    errors = []

    for changed in sys.argv[2:]:
        parts = Path(changed).parts

        if parts[0] == "roster" and len(parts) == 2 and changed.endswith(".md"):
            sid = Path(changed).stem
            if not ID_RE.match(sid):
                errors.append(f"{changed}: filename must be your student id (digits only)")
                continue
            p = Path(changed)
            if not p.is_file():
                errors.append(f"{changed}: deleting roster files is not allowed")
                continue
            owner = github_value_in(p)
            if owner != actor:
                errors.append(f"{changed}: 'github: {owner}' does not match PR author @{actor}")
            continue

        if parts[0] == "submissions" and len(parts) >= 3:
            sid = parts[1]
            if not ID_RE.match(sid):
                errors.append(f"{changed}: submissions/<student-id>/... — '{sid}' is not a student id")
                continue
            owner = roster_owner(sid)
            if owner is None:
                errors.append(f"{changed}: no roster/{sid}.md — submit your roster PR first")
            elif owner != actor:
                errors.append(f"{changed}: directory belongs to @{owner}, but PR author is @{actor}")
            continue

        errors.append(f"{changed}: outside your territory (only roster/<id>.md and submissions/<id>/** may change)")

    if errors:
        print("ownership check failed:\n")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"ownership check passed for @{actor} ({len(sys.argv) - 2} file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
