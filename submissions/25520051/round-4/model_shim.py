"""A local /chat/completions for the kit (127.0.0.1 only). The kit sends max_tokens, which newer models refuse; this
passes it on as max_completion_tokens and tries the next model when one fails. logs/model.log keeps counts, never content."""
import json, secrets, threading, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOTAL = 165         # seconds per request; the kit gives up at 180, or after 60 silent ones, so spaces go out every 10 s
UPSTREAM = "https://api.openai.com/v1/chat/completions"


def serve(get_key, get_models, log_file, port=8798):
    token = secrets.token_hex(16)

    def ask(model, body, key, timeout):
        out = {"model": model, "messages": body["messages"], "max_completion_tokens": 12000}
        if model.startswith(("gpt-5", "gpt-6", "o")):
            out["reasoning_effort"] = "low"
        req = urllib.request.Request(UPSTREAM, data=json.dumps(out).encode(), headers={
            "authorization": "Bearer " + key, "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        if not d["choices"][0]["message"].get("content"):
            raise ValueError("empty answer")
        return d

    def answer(body, box):
        end, why, models = time.time() + TOTAL, [], get_models()
        box["out"] = {"error": "no model answered"}
        for i, m in enumerate(models):
            left = end - time.time()
            if left < 4:
                break
            t = time.time()
            try:
                d = ask(m, body, get_key(), left if i == len(models) - 1 else min(left, 110 if i == 0 else 40))
                u = d.get("usage", {})
                why.append(f"{m} ok {time.time() - t:.0f}s in={u.get('prompt_tokens')} out={u.get('completion_tokens')}")
                box["out"] = d
                break
            except urllib.error.HTTPError as e:
                why.append(f"{m} HTTP {e.code}")
            except Exception as e:
                why.append(f"{m} {type(e).__name__}")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(time.strftime("%m-%d %H:%M:%S ") + "; ".join(why) + chr(10))

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.headers.get("authorization") != "Bearer " + token:
                self.send_error(401)
                return
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", "0"))))
            box = {}
            t = threading.Thread(target=answer, args=(body, box), daemon=True)
            t.start()
            try:
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.end_headers()                  # no length: HTTP/1.0, the body ends when the connection closes
                while True:
                    t.join(10)
                    if not t.is_alive():
                        break
                    self.wfile.write(b" ")
                    self.wfile.flush()
                self.wfile.write(json.dumps(box["out"]).encode())
            except OSError:
                pass

        def log_message(self, *a):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/v1", token
