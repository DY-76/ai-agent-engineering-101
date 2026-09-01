# Week 01 — First Agent: add a third tool

**Due: before the start of the week-02 class.** The deadline is judged by the PR open timestamp.

## Background

In the lab you built a twenty-line loop that turns a model into an agent, with two tools: `calculator` and `read_file`. The starter code in `starter/` is that agent.

## Assignment

Add **one more tool** to the agent (three tools total), then use the agent to solve a real task of your choosing. Any tool is fine — `fetch` to pull text from the web, `clock` to tell the current time, `write_note` to append a memo to a file. Observe how the model's tool selection behavior changes once a third tool exists.

## What to submit

Everything goes in `submissions/<student-id>/week-01/`:

| File | Contents |
|---|---|
| `first_agent.py` | The working agent with three tools. |
| `TOOLS.md` | One paragraph: why you described your new tool the way you did. The description is the interface — defend your wording. |
| `notes.txt` | The input file your agent reads (or whatever input your task uses). |
| `logs/` | At least one console capture of a full agent run. `python first_agent.py 2>&1 | tee logs/run-01.txt` |

## Grading

- **Half: reproducibility.** Someone else must be able to get the same result from your code and settings alone. State everything except the API key: model name, tool schemas, how to run.
- **Half: honest process.** What you tried and what you discarded must be visible in the commit history and logs. Do not squash. A messy history is evidence, not a penalty.

## Checks

CI verifies structure only: `first_agent.py` parses, defines three tools, `TOOLS.md` and `logs/` exist, and your PR touches only your own directory. Run it locally first:

```bash
python scripts/check_week01.py submissions/<student-id>/week-01
```

## Using an OpenRouter free model

If you do not have an Anthropic or OpenAI key, use `starter/first_agent_openai.py` — it speaks the OpenAI-compatible API, so pointing it at OpenRouter is two environment variables:

```bash
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
export OPENAI_API_KEY=<your openrouter key>
python first_agent.py "read notes.txt and sum the numbers in it"
```

Free-tier models vary in tool-calling quality. If your model keeps failing to call tools, that observation itself belongs in your logs — it is exactly the kind of process evidence this course grades.
