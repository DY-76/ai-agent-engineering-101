"""Owner's reminders to the agent through its own app chat (127.0.0.1:8800). Not agent code: it only says when it is time;
the agent decides and acts with its own tools. Sends only while the agent sleeps (its last log line), because a message
that reaches it in the middle of a run is lost. Counts go to logs/remind.log."""
import json, socket, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKET = "https://market.ourolabs.ai"
POST_EVERY, CLEAR_EVERY = 10 * 60, 60 * 60
POST = "가게 주인입니다. 글 올릴 때입니다. 다른 조회 없이 post_stock을 인자 없이 한 번 부르고 바로 주무세요. 429면 다시 부르지 마세요."
CLEAR = "가게 주인입니다. 임박 특가 글을 올릴 때입니다. post_clearance를 한 번 부르고 바로 주무세요. 429면 다시 부르지 마세요."
BUY = "가게 주인입니다. 재입고 창이 열렸습니다. 다른 조회 없이 top_sellers를 부르고, items가 있으면 그대로 buy_batch에 넣고 바로 주무세요. 없으면 바로 주무세요."


def say(t):
    with open(ROOT / "logs" / "remind.log", "a", encoding="utf-8") as f:
        f.write(time.strftime("%m-%d %H:%M:%S ") + t + "\n")


def paused():
    """The owner is giving the agent a longer instruction: .kit/pause was touched in the last 6 minutes."""
    try:
        return time.time() - (ROOT / ".kit" / "pause").stat().st_mtime < 360
    except OSError:
        return False


def asleep():
    with open(ROOT / "logs" / "agent-kit.log", "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 4000))
        lines = f.read().decode("utf-8", "replace").strip().splitlines()
    return bool(lines) and "[mind] sleeps" in lines[-1]


def tell(text):
    for _ in range(20):
        if asleep() and not paused():
            break
        time.sleep(6)
    else:
        return False
    req = urllib.request.Request("http://127.0.0.1:8800/api/chat", headers={"content-type": "application/json"},
                                 data=json.dumps({"text": text, "user": "가게 주인"}).encode())
    try:
        urllib.request.urlopen(req, timeout=85).read()
    except Exception:
        pass                                # the answer may take longer than the wait; the message is in
    return True


def main():
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", 8797))
    except OSError:
        sys.exit("already running")
    post, clear, window = 0.0, time.time() - CLEAR_EVERY + 300, 0
    while True:
        try:
            with urllib.request.urlopen(MARKET + "/api/restock", timeout=15) as r:
                w = json.load(r)
            if w["open"] and w["closes_at"] != window and w["closes_at"] - w["now"] > 45:
                if tell(BUY):
                    window = w["closes_at"]
                    say("buy")
            elif time.time() - post > POST_EVERY and (w["open"] or w["opens_at"] - w["now"] > 40):
                if tell(POST):
                    post = time.time()
                    say("post")
            elif time.time() - clear > CLEAR_EVERY and time.time() - post > 310:
                if tell(CLEAR):
                    clear = time.time()
                    say("clear")
        except Exception as e:
            say(f"{type(e).__name__}")
        time.sleep(10)


if __name__ == "__main__":
    main()
