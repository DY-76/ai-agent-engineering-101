# CLAUDE.md

@AGENTS.md

All repository rules live in AGENTS.md. Below is Claude Code specific advice only.

- Commit after every unit of work — do not wait until the end of the session. One-line commit messages are enough. When committing a failed attempt, say what failed and why in one line (e.g. `wip: fetch tool hangs without a timeout`).
- To capture an agent run log: `python first_agent.py 2>&1 | tee logs/run-$(date +%m%d-%H%M).txt`
- Plan mode is rarely worth it here. Assignments are small; just start working.
