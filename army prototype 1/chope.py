#!/usr/bin/env python3
"""Chope.  Five commands, no framework, no dependencies outside stdlib.
    chope.py check   -> proves the token and chat id work, posts nothing
    chope.py open    -> posts the anonymous poll                (cron, 0700)
    chope.py lock    -> stops the poll, locks the board number  (cron, cook cutoff)
    chope.py key N   -> after service: FIRST what was actually cooked, THEN what
                        was left.  Two numbers, dispatched on the board state, so
                        the state lives in board.js and a keypad restart mid-entry
                        cannot desync them.                     (called by keypad.py)
    chope.py listen  -> answers /commands in the group, runs /demo (systemd, chope-listen)
                        Outbound long-poll only: no port opens.  The poll stays anonymous;
                        a command arrives with a user id, which is read past and never kept.
Token comes from the environment, never the repo.
"""
import json, os, random, sys, time, urllib.request
import forecast as F, game as G

TOKEN   = os.environ["CHOPE_TOKEN"]          # export CHOPE_TOKEN=... in /etc/chope.env
CHAT    = int(os.environ["CHOPE_CHAT"])      # the unit's existing group
STRENGTH = int(os.environ.get("CHOPE_STRENGTH") or 0)  # 0 = ask Telegram; "" counts as 0
CUTOFF  = os.environ.get("CHOPE_CUTOFF", "")  # "HH:MM", set by install.sh from LOCK_AT --
                                               # the open-screen countdown target, nothing else
HERE    = os.path.dirname(os.path.abspath(__file__))
BOARD   = os.path.join(HERE, "board.js")     # .js, not .json: the kiosk page is file://
LOG     = os.path.join(HERE, "meals.csv")
COLS    = "when,eat,notc,unconf,board,cooked,left,taken,r,slack,buffer_pct\n"
# /demo: a 90-strong unit in 45 s.  Seeded votes sit ONE short of a Goal Day
# (61 + 10 = 71, need 72), so the visitor's own tap is the one that earns the point.
DEMO_N, DEMO_EAT, DEMO_NOTC, DEMO_SECS = 90, 61, 10, 45


def tg(method, **p):
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/%s" % (TOKEN, method),
        json.dumps(p).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=30))
    if not r.get("ok"):
        raise RuntimeError(r)
    return r["result"]


def board(**kw):
    kw["d"] = time.strftime("%F")             # the guard below reads this
    kw["t"] = time.strftime("%a %d %b %H:%M")
    open(BOARD + ".tmp", "w").write("B=" + json.dumps(kw))
    os.replace(BOARD + ".tmp", BOARD)         # atomic: the browser never sees half a file


def read_board(want_state=None):
    """Stale-board guard. Without it, a morning where `open` failed leaves yesterday's
    numbers in place and `lock`/`left` score today's meal against them -- silently."""
    b = json.loads(open(BOARD).read()[2:])    # strip the "B=" the browser needs
    if b["d"] != time.strftime("%F"):
        sys.exit("board.js is from %s, not today. Refusing." % b["d"])
    if want_state and b["state"] != want_state:
        sys.exit("board is '%s', expected '%s'. Refusing." % (b["state"], want_state))
    return b


def strength(demo=False):
    return DEMO_N if demo else STRENGTH or tg("getChatMemberCount", chat_id=CHAT) - 1  # -1: the bot


def cmd_check():
    me = tg("getMe")
    n  = tg("getChatMemberCount", chat_id=CHAT)
    s  = F.load()
    print("bot @%s ok | chat %d has %d members | strength=%s | r=%.2f margin=%d "
          "slack=%d after %d meals (%d ran short)"
          % (me["username"], CHAT, n, STRENGTH or "(ask Telegram)", s["r"],
             F.margin(s), s["slack"], s["n"], s["stockouts"]))
    for name in G.PACKS:          # the only check the stickers get before the booth
        try:
            print("sticker pack %s: %d stickers"
                  % (name, len(tg("getStickerSet", name=name)["stickers"])))
        except Exception as e:
            print("sticker pack %s: MISSING (%s) -- messages still send without it" % (name, e))


def menu():
    tg("sendPoll", chat_id=CHAT, question="🍽 Champion's special — what do you want?",
       options=["🍔 Western", "🌶 Mala", "🥩 Korean BBQ", "🍕 Pizza"], is_anonymous=True)


def month_end(new):
    """Crown, reset, open the menu vote.  Real: the first poll of a new month.
    Demo: /demo monthend.  No-op if the month has not changed."""
    text = G.rollover(G.load(), new)
    if text:
        tg("sendMessage", chat_id=CHAT, text=text)
        G.sticker(tg, CHAT, "win")
        menu()


def cmd_open(demo=False):
    if not demo:
        month_end(time.strftime("%Y-%m"))   # before the poll, so today counts for the new month
    tg("sendMessage", chat_id=CHAT, text=G.morning(G.load(), strength(demo)))
    m = tg("sendPoll", chat_id=CHAT, question="🍛 Lunch today?",
           options=["Eating", "Not eating"], is_anonymous=True)   # anonymous is the default
    now = time.time()
    board(state="open", msg=m["message_id"], pid=m.get("poll", {}).get("id"), demo=demo,
          cutoff=time.strftime("%H:%M:%S", time.localtime(now + DEMO_SECS)) if demo else CUTOFF,
          opened=int(now) if demo else 0)


def cmd_lock():
    b = read_board("open")
    p = tg("stopPoll", chat_id=CHAT, message_id=b["msg"])   # returns the FINAL counts
    eat, notc = (o["voter_count"] for o in p["options"])
    if b.get("demo"):
        eat, notc = eat + DEMO_EAT, notc + DEMO_NOTC
    n = strength(b.get("demo"))
    if eat + notc > n:        # otherwise unconf is 0 forever, r never learns, silently
        print("WARNING: %d votes but strength is %d. CHOPE_STRENGTH is wrong -- nobody "
              "is being counted as silent." % (eat + notc, n), file=sys.stderr)
    unconf = max(0, n - eat - notc)
    s = F.load()
    cooked = F.cook(s, eat, unconf, notc)
    F.save(s)
    board(state="cook", msg=b["msg"], cook=cooked, eat=eat, notc=notc, unconf=unconf,
          r=round(s["r"], 2), margin=cooked - s["base"], slack=s["slack"])
                        # margin is the APPLIED one, not margin(s): the cap can cut it
                        # and the board must show what was actually cooked
    g = G.load()                 # the old rule cooks for everyone who didn't decline
    goal, lead = G.record(g, eat + notc, n, eat + unconf - cooked)
    tg("sendMessage", chat_id=CHAT, text=G.locked(eat + notc, n, cooked, goal, lead))
    G.sticker(tg, CHAT, "win" if lead else "hype" if goal else "sad")


def cmd_cooked(actual):
    """First keypad number: what the kitchen ACTUALLY cooked, not what the board said.

    This is not bureaucracy and it is not optional.  The kitchen cooks above the
    number it is given -- "if you put 100, they will cook 110" [T5].  Score the
    model against the board's own number and `left` is measured against a pan that
    is 10% bigger, so `taken` reads 10% low EVERY meal: r collapses from 0.72 to
    0.42 (measured), the board number sinks, and NOBODY EVER SEES IT FAIL because
    the kitchen's own buffer quietly covers the shortfall it caused.

    It is also the instrument: actual/board is the kitchen buffer, K1, the biggest
    unknown in the project -- measured every lunch, logged, for free."""
    b = read_board("cook")
    if actual < 0:
        sys.exit("cooked=%d. Refusing." % actual)
    board(state="cooked", cook=b["cook"], actual=actual, eat=b["eat"],
          notc=b["notc"], unconf=b["unconf"])


def cmd_left(left):
    b = read_board("cooked")
    n, actual = b["eat"] + b["notc"] + b["unconf"], b["actual"]
    if not 0 <= left <= actual:          # fat finger on the keypad: 100 instead of 10
        sys.exit("left=%d but only %d were cooked. Refusing." % (left, actual))
    if actual - left > n:                # derived bound, not a magic number: you
        sys.exit("that says %d ate, but the unit is %d strong. Refusing."
                 % (actual - left, n))   # cannot feed more people than exist
    if actual == left and b["eat"]:      # the same number keyed twice
        sys.exit("left=%d of %d cooked says nobody ate, but %d said they would. "
                 "Refusing." % (left, actual, b["eat"]))
    s = F.load()
    F.score(s, b["eat"], b["unconf"], actual, left)   # ACTUAL, never b["cook"]
    F.save(s)
    taken, buf = actual - left, 100.0 * (actual - b["cook"]) / max(1, b["cook"])
    new = not os.path.exists(LOG)
    with open(LOG, "a") as f:
        if new:
            f.write(COLS)
        f.write("%s,%d,%d,%d,%d,%d,%d,%d,%.3f,%d,%.1f\n"
                % (time.strftime("%F %T"), b["eat"], b["notc"], b["unconf"],
                   b["cook"], actual, left, taken, s["r"], s["slack"], buf))
    board(state="done", cook=b["cook"], actual=actual, left=left, taken=taken,
          r=round(s["r"], 2), buf=round(buf))
    # The kitchen's buffer stays in meals.csv and off the group: a performance number
    # about kitchen staff does not belong in a chat full of NSFs (00-master-plan §4.1).
    text, mood = G.scorecard(G.load(), left, taken)
    tg("sendMessage", chat_id=CHAT, text=text)
    G.sticker(tg, CHAT, mood)


def cmd_key(n):
    """One keypad command, two numbers.  WHICH one depends on the board, not on the
    keypad process -- so restarting chope-keypad between the two entries cannot
    desync them, and the operator just types the two numbers the screen asks for."""
    st = json.loads(open(BOARD).read()[2:])["state"]
    if st not in ("cook", "cooked"):
        sys.exit("board is '%s' -- nothing to key in." % st)
    (cmd_cooked if st == "cook" else cmd_left)(n)


def say(text):
    tg("sendMessage", chat_id=CHAT, text=text)


def cmd_today(live):
    try:
        b = read_board("open")
    except SystemExit:
        return say("No poll open now. Next one tomorrow morning — don't siam ah.")
    p = live.get(b.get("pid"), {"options": [{"voter_count": 0}] * 2})
    replied = sum(o["voter_count"] for o in p["options"])
    if b.get("demo"):
        replied += DEMO_EAT + DEMO_NOTC
    n = strength(b.get("demo"))
    say("📊 %d/%d replied so far. Goal Day needs %d%s. Cutoff %s."
        % (replied, n, G.need(n), " ✅" if replied >= G.need(n) else "", b["cutoff"]))


def auto_key():
    """/demo auto stands in for the kitchen: cooks ~10% over the board like the real
    one [T5] and leaves a few -- never more eaten than the unit is strong."""
    actual = round(read_board("cook")["cook"] * 1.1)
    cmd_key(actual)
    cmd_key(max(0, actual - DEMO_N) + random.randint(3, 8))


def command(cmd, arg, live):
    """One /command.  Returns (when a /demo locks, auto-key?) or None."""
    g = G.load()
    if cmd == "leaderboard":
        say(G.leaderboard(g))
    elif cmd == "progress":
        say(G.progress(g))
    elif cmd == "saved":
        say(G.saved(g))
    elif cmd == "today":
        cmd_today(live)
    elif cmd == "menu":
        menu()
    elif cmd == "excuse":
        say("📝 Official reason for not eating:\n" + random.choice(G.EXCUSES))
        G.sticker(tg, CHAT, "think")
    elif cmd == "8ball":
        say("🎱 %s\n%s" % (" ".join(arg) or "Will lunch be good today?",
                           random.choice(G.EIGHTBALL)))
        G.sticker(tg, CHAT, "think")
    elif cmd == "demo" and arg[:1] == ["monthend"]:
        say("⏩ DEMO — fast-forward to the last lunch of %s…" % G.month_name(g["month"]))
        month_end(G.next_month(g["month"]))
    elif cmd == "demo" and arg[:1] == ["reset"]:
        G.seed()
        say("🔄 Demo reset. %s back to %d pts, tied for first." % (G.HOME, G.SEED[G.HOME][0]))
    elif cmd == "demo":
        say("🎬 DEMO — a full lunch in %d s. Vote in the poll below!" % DEMO_SECS)
        cmd_open(demo=True)
        return time.time() + DEMO_SECS, arg[:1] == ["auto"]
    elif cmd in ("help", "start"):
        say("🍛 Chope — tap the lunch poll, earn Goal Days, win %s.\n\n" % G.PRIZE
            + "\n".join("/%s — %s" % c for c in G.HELP))


def cmd_listen():
    tg("setMyCommands", commands=[{"command": c, "description": d} for c, d in G.HELP])
    off, due, auto, live = 0, None, False, {}
    while True:
        # 25 s cap: must stay under tg()'s 30 s urlopen timeout
        wait = 25 if due is None else max(0, min(25, int(due - time.time())))
        try:
            ups = tg("getUpdates", offset=off, timeout=wait, allowed_updates=["message", "poll"])
        except Exception as e:
            print("getUpdates:", e, file=sys.stderr)
            time.sleep(5)
            ups = []
        for u in ups:
            off = u["update_id"] + 1
            if "poll" in u:          # anonymous poll state: counts only, no voter
                live[u["poll"]["id"]] = u["poll"]
                continue
            m = u.get("message") or {}
            text = m.get("text", "")
            # The trust boundary: only the unit's own group drives the bot, so a stranger
            # DMing /demo cannot post into it.  Checked by chat id, never user id.
            if m.get("chat", {}).get("id") != CHAT or not text.startswith("/"):
                continue
            cmd, *arg = text.split()
            try:
                r = command(cmd[1:].split("@")[0].lower(), arg, live)
                if r:
                    due, auto = r
            except (Exception, SystemExit) as e:     # cmd_* refuse with sys.exit
                print(cmd, e, file=sys.stderr)
                say("⚠️ %s" % e)
        if due is not None and time.time() >= due:
            due = None
            try:
                cmd_lock()
                if auto:
                    auto_key()
            except (Exception, SystemExit) as e:
                print("demo:", e, file=sys.stderr)
                say("⚠️ %s" % e)


if __name__ == "__main__":
    {"check": cmd_check, "open": cmd_open, "lock": cmd_lock, "listen": cmd_listen,
     "key": lambda: cmd_key(int(sys.argv[2]))}[sys.argv[1]]()
