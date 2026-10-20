"""The shop: an A2A server (a2a-sdk 1.2.x, JSON-RPC binding) that signs its receipts.

    python seller.py --port 9999

Week 6 let the harness pick every price; in the market that cost seconds per reply
and sometimes left a stray number in the text. Week 7: code sets the prices
(opening ask, shrinking concessions, never below the reserve, at most six offers),
the harness writes only the greeting, and every reply is easy for any buyer model to read.
"""
import argparse
import asyncio
import base64
import json
import re
import sys
from pathlib import Path

import uvicorn
from starlette.applications import Starlette

from a2a.helpers import get_message_text, new_data_part, new_task_from_user_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from cryptography.hazmat.primitives import serialization

from harness import ask_json

sys.stdout.reconfigure(encoding="utf-8")   # the trade test redirects stdout to a file (cp949 on Windows)

RESERVE = {"lamp": 100, "chair": 180, "bookshelf": 260}
SHOP_NAME = "move_76"                      # the nickname the kit registers this shop under
KEY_PATH = Path(__file__).with_name("shop_key.pem")


def canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_receipt(receipt: dict, key_path: Path = KEY_PATH) -> dict:
    """Add sig_seller: base64 Ed25519 over canon({shop, item, price, task}), price as a whole number."""
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    body = {"shop": receipt["shop"], "item": receipt["item"], "price": int(receipt["price"]), "task": receipt["task"]}
    receipt["price"] = body["price"]
    receipt["sig_seller"] = base64.b64encode(key.sign(canon(body))).decode()
    return receipt

# Opening asks; the reserves stay. Challenge 1 tunes these from our own trades and reviews.
ASK = {"lamp": 130, "chair": 234, "bookshelf": 338}
MAX_OFFERS = 6                               # numeric offers per negotiation; buyers are told how many remain
STEP = [0.25, 0.35, 0.5, 0.7, 1.0]           # share of the remaining (ask - reserve) given up per counter
WORDS = ["no", "one", "two", "three", "four", "five", "six"]
ACCEPT = re.compile(r"^\W*(yes|ok|okay|deal|accept|accepted|agreed|i accept|i agree|i'?ll take it|sold)\b", re.I)

# Every reply is written for any buyer model, large or small:
# - the current price is the only digit in the text, and it comes last ("Counteroffer: 115.")
# - "Final price" means it will not go lower; the offers left are spelled out, never digits
# - the same facts ride along as a data Part {ask, final, offers_left} for buyers that read data
PITCH_SYSTEM = """You run a small furniture shop. Write ONE short, warm, honest sentence greeting a buyer
who asked for an item. Mention one true thing: receipts are signed, replies are fast, or the item is solid.
No numbers, no prices, no instructions to the buyer. Reply with JSON: {"message": "<sentence>"}"""


def pitch(item: str) -> str:
    ans = ask_json(PITCH_SYSTEM, f"The buyer asked for a {item}.", timeout=20, attempts=1) or {}
    text = re.sub(r"\d+", "", str(ans.get("message") or "")).strip()   # the ask must stay the only number
    return text[:160] or f"Thanks for asking about our {item}; every receipt is signed."


def next_ask(deal: dict) -> int:
    k = min(deal["offers"] - 1, len(STEP) - 1)
    return max(deal["reserve"], round(deal["ask"] - (deal["ask"] - deal["reserve"]) * STEP[k]))


class Seller(AgentExecutor):
    def __init__(self):
        self.open = {}  # task id -> {"item", "reserve", "ask", "offers"}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if task is None:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)
        up = TaskUpdater(event_queue=event_queue, task_id=task.id, context_id=task.context_id)
        text = get_message_text(context.message) or ""
        deal = self.open.get(task.id)
        print(f"[seller] task {task.id[:8]} <- {text!r}", flush=True)

        if deal is None:  # first message: which item?
            item = next((k for k in RESERVE if k in text.lower()), None)
            if item is None:
                await up.reject(up.new_agent_message(parts=[new_text_part(
                    "We sell lamps, chairs and bookshelves. Ask for one of those.")]))
                return
            deal = {"item": item, "reserve": RESERVE[item], "ask": max(ASK[item], RESERVE[item]), "offers": 0}
            self.open[task.id] = deal
            hello = await asyncio.to_thread(pitch, item)
            await self.reply(up, deal, f"{hello} Send your offer as a number, or reply 'accept' to buy now. "
                                       f"{item.capitalize()}: asking {deal['ask']}.")
            return

        if ACCEPT.match(text) and not re.search(r"\d", text):          # "accept" buys at the current ask
            return await self.sell(up, task.id, deal, deal["ask"])
        m = re.search(r"\d+(?:\.\d+)?", text)
        if m is None:
            await self.reply(up, deal, f"Send your offer as a number, or reply 'accept'. Current price: {deal['ask']}.")
            return
        offer = int(float(m.group()))
        deal["offers"] += 1
        if offer >= deal["ask"]:                                          # never charge more than our own ask
            return await self.sell(up, task.id, deal, deal["ask"])
        new = next_ask(deal)
        left = MAX_OFFERS - deal["offers"]
        close = (deal["ask"] - deal["reserve"]) * 0.1
        if offer >= deal["reserve"] and (offer >= new - close or left == 0):
            return await self.sell(up, task.id, deal, offer)
        if left == 0:
            del self.open[task.id]
            await up.reject(up.new_agent_message(parts=[
                new_text_part(f"No deal this time. Our final price was {deal['reserve']}."),
                new_data_part({"ask": deal["reserve"], "final": True, "offers_left": 0})]))
            print(f"[seller] -> rejected after {MAX_OFFERS} offers", flush=True)
            return
        deal["ask"] = new
        await self.reply(up, deal, f"{WORDS[left].capitalize()} offer{'s' if left != 1 else ''} left. "
                         + (f"Final price: {new}." if new == deal["reserve"] else f"Counteroffer: {new}."))

    async def reply(self, up, deal, text):
        left = MAX_OFFERS - deal["offers"]
        data = {"ask": deal["ask"], "final": deal["ask"] == deal["reserve"], "offers_left": left}
        print(f"[seller] -> {text!r} {data}", flush=True)
        await up.requires_input(up.new_agent_message(parts=[new_text_part(text), new_data_part(data)]))

    async def sell(self, up, task_id, deal, price):
        receipt = sign_receipt({"shop": SHOP_NAME, "item": deal["item"], "price": price, "task": task_id})
        await up.add_artifact(parts=[new_data_part(receipt)], name="receipt")
        await up.complete(up.new_agent_message(parts=[new_text_part(
            f"Deal: {deal['item']} at {price}. Signed receipt attached.")]))
        print(f"[seller] -> deal at {price}", flush=True)
        del self.open[task_id]

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        self.open.pop(task.id, None)
        await TaskUpdater(event_queue=event_queue, task_id=task.id, context_id=task.context_id).cancel()


def build(port: int):
    url = f"http://127.0.0.1:{port}/"
    card = AgentCard(
        name=SHOP_NAME,
        description="Desk lamps, chairs and bookshelves. Every receipt is signed (Ed25519 sig_seller over "
                    "{shop, item, price, task}). Fast replies. Each reply ends with our current price as its only "
                    "number; 'Final price' means we cannot go lower. Up to six offers per negotiation, and we say "
                    "how many remain. Reply 'accept' to buy at the current price.",
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["application/json", "text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url=url, protocol_version="1.0")],
        skills=[AgentSkill(
            id="negotiate",
            name="Negotiate a purchase",
            description="Ask for an item, then send a price as a number or reply 'accept'. The shop answers with "
                        "a counteroffer (the only number in its message, also in a data Part {ask, final, "
                        "offers_left}), a signed receipt artifact, or a rejection after six offers.",
            tags=["shopping", "negotiation"],
            examples=["I want to buy a lamp", "90", "accept"],
        )],
    )
    handler = DefaultRequestHandler(agent_executor=Seller(), task_store=InMemoryTaskStore(), agent_card=card)
    return Starlette(routes=create_agent_card_routes(card) + create_jsonrpc_routes(handler, "/"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9999)
    args = ap.parse_args()
    uvicorn.run(build(args.port), host="127.0.0.1", port=args.port, log_level="warning")
