"""Keeps the Round 4 kit running. Not agent code: the kit is started as shipped.
Restarts the kit when it exits. Two models: the market's model desk, and the OpenAI key in week-08/.env. model.json says
which one is preferred ({"prefer": "own" or "desk", "model": "gpt-4.1"}). After FAILS model errors in a row it switches to
the other (own only if a test call works); an hour later it goes back to the preferred one.
Secrets go to the kit through the environment, never to the command line or a log."""
import json, os, re, socket, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
KIT = REPO / "scripts" / "round4" / "agent_kit.py"
NAME = "로얄 서클(Royal Circle)"
BACKUP = "gpt-4.1"               # default; the kit sends max_tokens, which gpt-5 models refuse
BACKUP_BASE = "https://api.openai.com/v1"
FAILS, BACK = 4, 3600


def say(text):
    with open(ROOT / "logs" / "supervise.log", "a", encoding="utf-8") as f:
        f.write(time.strftime("%m-%d %H:%M:%S ") + text + "\n")


def secrets():
    out = {}
    for line in (ROOT.parent / "week-08" / ".env").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(\w+)\s*=\s*(.*?)\s*$", line)
        if m:
            out[m[1]] = m[2].strip("\"'")
    return out


def config():
    try:
        c = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        c = {}
    return ("backup" if c.get("prefer") == "own" else "desk"), c.get("model") or BACKUP


def backup_works(key):
    body = json.dumps({"model": config()[1], "max_tokens": 5, "messages": [{"role": "user", "content": "ok"}]}).encode()
    req = urllib.request.Request(BACKUP_BASE + "/chat/completions", data=body,
                                 headers={"authorization": "Bearer " + key, "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except Exception as e:
        say(f"backup model not usable: {type(e).__name__} {getattr(e, 'code', '')}")
        return False


def start(mode, sec):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AGENT_LLM_", "OPENAI_", "OPENROUTER_"))}
    env.update(PYTHONUTF8="1", MARKET_OWNER=sec["MARKET_OWNER"],
               PATH=str(Path.home() / "market" / "bin") + os.pathsep + env["PATH"])
    if mode == "desk":
        env["AGENT_LLM_BASE"] = "market"
    else:
        env.update(AGENT_LLM_BASE=BACKUP_BASE, AGENT_LLM_MODEL=config()[1], AGENT_LLM_KEY=sec["OPENAI_API_KEY"])
    say(f"start kit, model: {mode if mode == 'desk' else config()[1]}")
    with open(ROOT / "logs" / "kit.err", "a", encoding="utf-8") as err:
        return subprocess.Popen([sys.executable, str(KIT), "run", "--dir", str(ROOT), "--market",
                                 "https://market.ourolabs.ai", "--name", NAME, "--tunnel", "--app", "8800"],
                                cwd=REPO, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err,
                                creationflags=subprocess.CREATE_NO_WINDOW)


def kill(p):
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    p.wait(timeout=20)


def utf8_stdio():
    """On Windows the kit starts tools with python -I, which ignores PYTHONIOENCODING, so Korean output leaves as cp949
    and the kit cannot decode it. A .pth line in the venv sets UTF-8 for every process; the kit stays unchanged."""
    if os.name == "nt":
        (ROOT / ".venv" / "Lib" / "site-packages" / "zz_utf8_stdio.pth").write_text(
            "import sys; [s.reconfigure(encoding='utf-8') for s in (sys.stdin, sys.stdout, sys.stderr) "
            "if s is not None and hasattr(s, 'reconfigure')]" + chr(10), encoding="utf-8")


def main():
    (ROOT / "logs").mkdir(exist_ok=True)
    utf8_stdio()
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", 8799))          # one supervisor at a time
    except OSError:
        sys.exit("already running")
    logf, mode, wait, next_probe = ROOT / "logs" / "agent-kit.log", config()[0], 15, 0
    while True:
        sec = secrets()
        pos = logf.stat().st_size if logf.exists() else 0
        p, began, fails = start(mode, sec), time.time(), 0
        while p.poll() is None:
            time.sleep(5)
            size = logf.stat().st_size if logf.exists() else 0
            pos = 0 if size < pos else pos      # the kit rotated its log
            if size > pos:
                with open(logf, "rb") as f:
                    f.seek(pos)
                    chunk = f.read()
                pos += len(chunk)
                for line in chunk.decode("utf-8", "replace").splitlines():
                    if "[mind] model call failed" in line:
                        fails += 1
                    elif "[mind]" in line:
                        fails = 0
            if fails >= FAILS and time.time() > next_probe:
                next_probe = time.time() + 600
                if mode == "backup" or backup_works(sec.get("OPENAI_API_KEY", "")):
                    mode = "desk" if mode == "backup" else "backup"
                    say(f"{fails} model errors in a row, switching to {mode}")
                    kill(p)
            elif mode != config()[0] and time.time() - began > BACK and (
                    config()[0] == "desk" or backup_works(sec.get("OPENAI_API_KEY", ""))):
                mode = config()[0]
                say(f"an hour on the other model, back to {mode}")
                kill(p)
        if time.time() - began > 600:
            wait = 15
        say(f"kit ended (code {p.returncode}); again in {wait} s")
        # the kit's own cloudflared would outlive a crash
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        time.sleep(wait)
        wait = min(wait * 2, 300)


main()
