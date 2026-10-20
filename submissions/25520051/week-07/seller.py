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
import hashlib
import hmac
import json
import os
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
SHOP_NAME = "moss-and-oak"                 # the nickname the kit registers this shop under
KEY_PATH = Path(__file__).with_name("shop_key.pem")
BRAND = ("Moss & Oak: simple, well-made furniture with only the parts you need, at fair prices. "
         "Eco-friendly materials, an inclusive workshop, every receipt signed.")


def canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_receipt(receipt: dict, key_path: Path = KEY_PATH) -> dict:
    """Add sig_seller: base64 Ed25519 over canon({shop, item, price, task}), price as a whole number."""
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    body = {"shop": receipt["shop"], "item": receipt["item"], "price": int(receipt["price"]), "task": receipt["task"]}
    receipt["price"] = body["price"]
    receipt["sig_seller"] = base64.b64encode(key.sign(canon(body))).decode()
    return receipt

# Opening asks; the reserves stay. Challenge 1: tune_prices.py rewrites prices.json from our trades and
# reviews, and every new negotiation reads it, so a change needs no restart.
ASK = {"lamp": 130, "chair": 234, "bookshelf": 338}
MAX_OFFERS = 6                               # numeric offers per negotiation; buyers are told how many remain
STEP = [0.25, 0.35, 0.5, 0.7, 1.0]           # share of the remaining (ask - reserve) given up per counter
PRICES = Path(__file__).with_name("prices.json")
LINE = {"lamp": "Fern desk lamp", "chair": "Oak-ply chair", "bookshelf": "Moss modular bookshelf"}


def prices() -> tuple[dict, list]:
    try:
        p = json.loads(PRICES.read_text(encoding="utf-8"))
        return {**ASK, **p.get("ask", {})}, p.get("step") or STEP
    except (OSError, ValueError):
        return ASK, STEP
WORDS = ["no", "one", "two", "three", "four", "five", "six"]
ACCEPT = re.compile(r"^\W*(yes|ok|okay|deal|accept|accepted|agreed|i accept|i agree|i'?ll take it|sold)\b", re.I)
HELP = re.compile(r"\b(help|support|how does|rules?)\b", re.I)
MEMBER = re.compile(r"\bMOSS-([A-Z]{4})([A-Z]{4})\b")
MEMBER_ASK = 0.92                            # members open lower ...
MEMBER_STEP = [0.4, 0.5, 0.7, 1.0]           # ... and reach the reserve sooner


def _secret() -> bytes:
    return hashlib.sha256(KEY_PATH.read_bytes()).digest()


def _letters(b: bytes, n: int) -> str:
    return "".join(chr(65 + x % 26) for x in b[:n])


def member_code(task_id: str) -> str:
    """Letters only (the price stays the only number in a reply); checked by recomputing, nothing stored."""
    nonce = _letters(hashlib.sha256(task_id.encode()).digest(), 4)
    return f"MOSS-{nonce}{_letters(hmac.new(_secret(), nonce.encode(), 'sha256').digest(), 4)}"


def is_member(text: str) -> bool:
    m = MEMBER.search(text.upper())
    return bool(m) and hmac.compare_digest(_letters(hmac.new(_secret(), m.group(1).encode(), "sha256").digest(), 4),
                                           m.group(2))

# Every reply is written for any buyer model, large or small:
# - the current price is the only digit in the text, and it comes last ("Counteroffer: 115.")
# - "Final price" means it will not go lower; the offers left are spelled out, never digits
# - the same facts ride along as a data Part {ask, final, offers_left} for buyers that read data
PITCH_SYSTEM = f"""You greet buyers for this furniture shop. {BRAND}
Write ONE short, warm sentence greeting a buyer who asked for an item, mentioning one of those facts.
No numbers, no prices, no instructions to the buyer. Reply with JSON: {{"message": "<sentence>"}}"""


def pitch(item: str, member: bool) -> str:
    who = "a returning member" if member else "a new buyer"
    ans = ask_json(PITCH_SYSTEM, f"{who} asked for a {item}; this season's model is the {LINE[item]}.",
                   timeout=20, attempts=1) or {}
    text = re.sub(r"\d+", "", str(ans.get("message") or "")).strip()   # the ask must stay the only number
    text = text[:160] or f"Welcome to Moss & Oak; our {item} is simple, sturdy and made from eco-friendly materials."
    return text + (" Welcome back: member pricing applies." if member else "")


def next_ask(deal: dict) -> int:
    steps = MEMBER_STEP if deal.get("member") else deal["step"]
    k = min(deal["offers"] - 1, len(steps) - 1)
    return max(deal["reserve"], round(deal["ask"] - (deal["ask"] - deal["reserve"]) * steps[k]))


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
            member = is_member(text)
            asks, step = prices()
            ask = round(asks[item] * MEMBER_ASK) if member else asks[item]
            deal = {"item": item, "reserve": RESERVE[item], "ask": max(ask, RESERVE[item]), "offers": 0,
                    "member": member, "list": asks[item], "step": step}
            self.open[task.id] = deal
            hello = await asyncio.to_thread(pitch, item, member)
            await self.reply(up, deal, f"{hello} Send your offer as a number, or reply 'accept' to buy now. "
                                       f"{item.capitalize()}: asking {deal['ask']}.")
            return

        if not deal["member"] and is_member(text):                       # a code given after the opening
            deal["member"] = True
            deal["ask"] = max(deal["reserve"], min(deal["ask"], round(deal["list"] * MEMBER_ASK)))
            if not re.search(r"\d", MEMBER.sub("", text.upper())):
                await self.reply(up, deal, f"Welcome back, member pricing applies. Current price: {deal['ask']}.")
                return
            text = MEMBER.sub("", text.upper())
        if HELP.search(text) and not re.search(r"\d", text):              # A/S: explain, never punish a question
            left = MAX_OFFERS - deal["offers"]
            await self.reply(up, deal, f"Send a whole number as your offer, or reply 'accept' to buy at the current "
                                       f"price. {WORDS[left].capitalize()} offers left; 'Final price' means we cannot "
                                       f"go lower. Current price: {deal['ask']}.")
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
            f"Deal: {deal['item']} at {price}. Signed receipt attached. Your Moss & Oak member code is "
            f"{member_code(task_id)}; include it when you ask next time for member pricing.")]))
        print(f"[seller] -> deal at {price} ({deal['item']}, opened {deal['list']}"
              f"{', member' if deal['member'] else ''})", flush=True)
        del self.open[task_id]

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        self.open.pop(task.id, None)
        await TaskUpdater(event_queue=event_queue, task_id=task.id, context_id=task.context_id).cancel()


def build(port: int):
    url = f"http://127.0.0.1:{port}/"
    card = AgentCard(
        name=SHOP_NAME,
        description=BRAND + " Desk lamps, chairs and bookshelves. Receipts: Ed25519 sig_seller over "
                    "{shop, item, price, task}. Each reply ends with our current price as its only number; "
                    "'Final price' means we cannot go lower. Up to six offers, and we say how many remain. "
                    "Reply 'accept' to buy at the current price, 'help' for the rules. Every buyer gets a member "
                    "code with the receipt; members get lower prices next time.",
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


def app_from_env():
    return build(int(os.environ["SELLER_PORT"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9999)
    args = ap.parse_args()
    if os.environ.get("SELLER_RELOAD") == "1":
        # In the market: a restarted kit gets a new tunnel URL, and buyers holding the old one leave
        # "shop did not answer" reviews (8 of our 10 listed reviews at 20:45). The kit forwards to this
        # port, so reloading the seller in place keeps the public URL; only seller code triggers it.
        os.environ["SELLER_PORT"] = str(args.port)
        uvicorn.run("seller:app_from_env", factory=True, host="127.0.0.1", port=args.port, log_level="warning",
                    reload=True, reload_dirs=[str(Path(__file__).parent)],
                    reload_excludes=["buyer.py", "market_buyer.py", "a2a_trade.py", "tune_prices.py",
                                     "shop_report.py", "*.json", "logs/*", ".market/*"])
    else:
        uvicorn.run(build(args.port), host="127.0.0.1", port=args.port, log_level="warning")
