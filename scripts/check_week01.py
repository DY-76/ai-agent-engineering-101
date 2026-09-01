#!/usr/bin/env python3
"""Structural checks for the week-01 submission. CI runs exactly this.

Usage: python scripts/check_week01.py submissions/<student-id>/week-01
"""
import ast
import sys
from pathlib import Path

REQUIRED_TOOLS = 3


def fail(msg: str):
    print(f"FAIL  {msg}")
    fail.count += 1


fail.count = 0


def ok(msg: str):
    print(f"ok    {msg}")


def count_tools(tree: ast.Module) -> tuple[int, int]:
    """Return (len of TOOLS list literal, len of TOOLS_IMPL dict literal)."""
    tools, impl = -1, -1
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "TOOLS" and isinstance(node.value, ast.List):
                        tools = len(node.value.elts)
                    if target.id == "TOOLS_IMPL" and isinstance(node.value, ast.Dict):
                        impl = len(node.value.keys)
    return tools, impl


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    sub = Path(sys.argv[1])

    if not sub.is_dir():
        fail(f"{sub} is not a directory")
        return 1

    agent = sub / "first_agent.py"
    if not agent.is_file():
        fail("first_agent.py is missing")
    else:
        try:
            tree = ast.parse(agent.read_text(encoding="utf-8"))
            ok("first_agent.py parses")
            tools, impl = count_tools(tree)
            if tools < 0:
                fail("no TOOLS list found (keep the starter's TOOLS variable)")
            elif tools < REQUIRED_TOOLS:
                fail(f"TOOLS defines {tools} tools; the assignment requires {REQUIRED_TOOLS}")
            else:
                ok(f"TOOLS defines {tools} tools")
            if impl < 0:
                fail("no TOOLS_IMPL dict found (keep the starter's TOOLS_IMPL variable)")
            elif impl < REQUIRED_TOOLS:
                fail(f"TOOLS_IMPL maps {impl} tools; the assignment requires {REQUIRED_TOOLS}")
            else:
                ok(f"TOOLS_IMPL maps {impl} tools")
        except SyntaxError as e:
            fail(f"first_agent.py has a syntax error: {e}")

    tools_md = sub / "TOOLS.md"
    if not tools_md.is_file():
        fail("TOOLS.md is missing (one paragraph on why you described your new tool that way)")
    elif len(tools_md.read_text(encoding="utf-8").strip()) < 100:
        fail("TOOLS.md looks empty; write a real paragraph")
    else:
        ok("TOOLS.md present")

    logs = sub / "logs"
    log_files = [p for p in logs.iterdir() if p.is_file()] if logs.is_dir() else []
    if not log_files:
        fail("logs/ has no run capture (tee your console output into logs/)")
    else:
        ok(f"logs/ contains {len(log_files)} file(s)")

    # naive key scan: better to catch the obvious leak here than in a public PR
    for p in sub.rglob("*"):
        if p.is_file() and p.stat().st_size < 1_000_000:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for marker in ("sk-ant-", "sk-or-v1-", "sk-proj-"):
                if marker in text:
                    fail(f"{p} appears to contain an API key ({marker}...) — remove it and rotate the key")

    if fail.count:
        print(f"\n{fail.count} check(s) failed")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
