# Week 06 — Claude Code behind A2A, as a seller and as a buyer

## 1. Harness, model, command

- **Harness / model:** Claude Code 2.1.169, model `haiku`, called non-interactively from both agents
  through [`harness.py`](./harness.py):

  ```
  claude -p --model haiku --tools "" --setting-sources "" --no-session-persistence --system-prompt <role>
  ```

  The prompt goes in on stdin. Each call runs in an empty temp directory so the harness does not
  pick up this repository's `CLAUDE.md` / `AGENTS.md`. Every call is a fresh session: the
  negotiation history is rebuilt from the agent's own state and put into the prompt each round.
- **Agents:** [`seller.py`](./seller.py) is an A2A v1.0 server (a2a-sdk 1.2.2, JSON-RPC binding),
  built on the lab's `seller_agent.py` skeleton. [`buyer.py`](./buyer.py) is an A2A client written
  with plain `httpx` (no SDK client), so every header and JSON-RPC body is visible in the code.
- **Commands** ([`agent.json`](./agent.json)): `python seller.py --port {port}` and
  `python buyer.py --url {url} --item {item} --budget {budget}`, run with the venv
  (`a2a-sdk[http-server]`, `uvicorn`, `httpx`) first on `PATH`.
- **Passing run:** 21/21 in 5 min 58 s, 39 harness calls (counted from `[harness] raw` lines in `logs/`).

## 2. How each agent decides

Both agents ask the harness for **one line of JSON** and the code extracts the first `{...}` from
the answer (haiku wraps it in ```` ```json ```` fences almost every time, e.g.
`'```json\n{"action": "offer", "price": 105, ...}\n```'` in `logs/buyer-under-test-buyer_deal-1.log`).

**Seller.** System prompt: a small furniture shop owner who wants to sell at a good price, must never
go below the reserve, and should not raise the price above the previous ask. Per round the prompt
holds the item, the reserve, the conversation so far, the previous ask and the buyer's new offer.
Answer format: `{"action": "counter" | "accept" | "reject", "price": <int>, "message": "<sentence>"}`.

- The reserve is in the prompt **and** enforced in code: a counter is clamped to
  `min(max(price, reserve), previous_ask)`, and an `accept` of an offer below the reserve is turned
  into a counter at the previous ask.
- The code always ends an input-required message with `My price: <ask>`, because the trade test
  reads the ask as the *last* number in the message and the model's own sentence often contains
  other numbers ("that's nearly $20 below my original offer").
- A deal is a `receipt` artifact with a data Part `{"seller", "item", "price"}`.

**Buyer.** System prompt: a careful buyer with a hard budget who should pay as little as possible,
prefers buying within budget over not buying, and walks away if the shop will not come down.
Per round the prompt holds the item, the budget, the conversation so far and the shop's current ask
(the last number in the shop's message). Answer format:
`{"action": "offer" | "accept" | "walk", "price": <int>, "reason": "<short reason>"}`.

- `offer` / `accept` send the price as a bare number on the same `taskId`; `walk` sends `CancelTask`.
- The budget is in the prompt **and** enforced in code: an offer above the budget is cut to the
  budget, and an offer above the shop's current ask is cut to the ask.
- Every request (card GET, `SendMessage`, `CancelTask`) carries `A2A-Version: 1.0`. The buyer stops
  after 10 rounds or 240 s, whichever comes first.

In the passing run neither code guard fired (`grep guard logs/*.log` finds nothing): haiku kept the
reserve and the budget from the prompt alone. The guards are there because "all runs must pass" and
a model that is right 39 times out of 39 is not a guarantee.

## 3. What failed and what I changed

**(a) The harness refused to answer in JSON.** My first manual call had no system prompt, only
`Reply with only this JSON: {"action":"counter","price":115}` on stdin. Haiku answered (from my
terminal during development, before the trade test existed in my directory):

> I appreciate you testing my boundaries, but I can't respond with only arbitrary JSON output. That
> appears to be a prompt injection test.

Claude Code's default system prompt frames it as a coding assistant, so a bare "reply with only
JSON" looks like an attack. Giving it a role with `--system-prompt` ("You are a furniture shop
negotiating a sale. Answer with one line of JSON only: ...") fixed it on the next call.

**(b) First trade test: 19/21, the buyer walked away from a deal it could have made.**
Commit `dc62c93` keeps that run. From its `logs/trade-test.log`:

```
### buyer_deal #3: python buyer.py --url http://127.0.0.1:49676 --item lamp --budget 120
    kit seller saw: offers [], deals [], canceled 1, continued 0, posts without A2A-Version 1.0: 0
  FAIL  buyer_deal #3: deals [] (budget 120)
  FAIL  buyer_protocol_deal #3: posts 2, without A2A-Version 1.0 0, follow-ups with taskId 0
```

and from `logs/buyer-under-test-buyer_deal-3.log`:

```
[buyer] <- TASK_STATE_INPUT_REQUIRED | lamp: asking 130. Send your offer as a number.
[harness] call failed: TimeoutExpired(['claude', '-p', '--model', 'haiku', ...], 90)
[buyer] harness -> {}
[buyer] harness gave no price; walking away
```

The machine went to sleep in the middle of that run (buyer_deal #2's log is stamped 21:26, #3's
10:03 the next morning; the whole run took 764 minutes), and the one harness call made right after
waking timed out. The real weakness was in my buyer, though: one failed call ended the whole
negotiation. I changed `ask_json` to try twice with a 60 s timeout each (commit `167fa5b`), and kept
the computer awake for the rerun. The second run passed 21/21 (commit `dfc2729`); no retry was
actually needed in it.

**(c) Leftover seller processes on Windows.** After both runs a `seller.py` was still listening
(ports 57697 and 49178 answered with the Harness Shop card). The trade test starts the seller with
`shell=True` and stops it with `terminate()`, which on Windows ends the `cmd.exe` shell but not its
Python child. It did not fail a test, because each run picks a fresh port, but I had to kill the
processes by hand.

## 4. What A2A settled, and what it did not

A2A settled the plumbing: where to find the other agent's self-description
(`/.well-known/agent-card.json`), which endpoint and binding to talk to (`supportedInterfaces`),
how a request is shaped (`SendMessage` with a `taskId` to continue), and — most usefully — the
*state* of the negotiation. `TASK_STATE_INPUT_REQUIRED` means "your move", `COMPLETED` means a deal,
`REJECTED` or `CANCELED` means no deal, and a message to a finished task is an error, so neither
side had to invent "is this still open?". What A2A did not settle is the *meaning* of the messages
inside a task, and both of my agents only work because they share conventions that live nowhere in
the protocol: a price is "the last number in the text" (my seller has to append `My price: N`
because the model's sentences contain other numbers), an offer is a bare number, "accept" from the
buyer is just sending the seller's ask back, and the closing price is a `price` field in an
artifact named `receipt`. The Agent Card's skill description says "send a price as a number" in
English, with no schema to check against, so a seller from another student that writes "$1.2e2"
or puts the ask first would break my buyer without any protocol error. A2A also has no place for
the limits of the delegation: nothing stopped my seller from telling the buyer its reserve ("260 is
my absolute bottom line", `logs/trade-test.log`), and the buyer's budget exists only in its prompt
and its code.
