#!/usr/bin/env python3
"""Chope.  Four commands, no daemon, no framework, no dependencies outside stdlib.
    chope.py check   -> proves the token and chat id work, posts nothing
    chope.py open    -> posts the anonymous poll                (cron, 0700)
    chope.py lock    -> stops the poll, locks the board number  (cron, cook cutoff)
    chope.py left N  -> scores the meal                         (called by keypad.py)
Token comes from the environment, never the repo.
"""
import json, os, sys, time, urllib.request
import forecast as F

TOKEN   = os.environ["CHOPE_TOKEN"]          # export CHOPE_TOKEN=... in /etc/chope.env
CHAT    = int(os.environ["CHOPE_CHAT"])      # the unit's existing group
STRENGTH = int(os.environ.get("CHOPE_STRENGTH") or 0)  # 0 = ask Telegram; "" counts as 0
HERE    = os.path.dirname(os.path.abspath(__file__))
BOARD   = os.path.join(HERE, "board.js")     # .js, not .json: the kiosk page is file://
LOG     = os.path.join(HERE, "meals.csv")
COLS    = "when,eat,unconf,cooked,left,taken,r\n"


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


def cmd_check():
    me = tg("getMe")
    n  = tg("getChatMemberCount", chat_id=CHAT)
    s  = F.load()
    print("bot @%s ok | chat %d has %d members | strength=%s | r=%.2f margin=%d after %d meals"
          % (me["username"], CHAT, n, STRENGTH or "(ask Telegram)", s["r"], F.margin(s), s["n"]))


def cmd_open():
    m = tg("sendPoll", chat_id=CHAT, question="Lunch today?",
           options=["Eating", "Not eating"], is_anonymous=True)   # anonymous is the default
    board(state="open", msg=m["message_id"])


def cmd_lock():
    b = read_board("open")
    p = tg("stopPoll", chat_id=CHAT, message_id=b["msg"])   # returns the FINAL counts
    eat, notc = (o["voter_count"] for o in p["options"])
    n = STRENGTH or tg("getChatMemberCount", chat_id=CHAT) - 1   # -1: the bot is a member
    unconf = max(0, n - eat - notc)
    s = F.load()
    cooked = F.cook(s, eat, unconf)
    F.save(s)
    board(state="cook", msg=b["msg"], cook=cooked, eat=eat, notc=notc, unconf=unconf,
          r=round(s["r"], 2), margin=F.margin(s))
    tg("sendMessage", chat_id=CHAT,
       text="Cook %d.  %d said eating, %d not, %d silent (counted at r=%.2f)."
            % (cooked, eat, notc, unconf, s["r"]))


def cmd_left(left):
    b = read_board("cook")
    if not 0 <= left <= b["cook"]:       # fat finger on the keypad: 100 instead of 10
        sys.exit("left=%d but only %d were cooked. Refusing." % (left, b["cook"]))
    s = F.load()
    F.score(s, b["eat"], b["unconf"], b["cook"], left)
    F.save(s)
    taken = b["cook"] - left
    new = not os.path.exists(LOG)
    with open(LOG, "a") as f:
        if new:
            f.write(COLS)
        f.write("%s,%d,%d,%d,%d,%d,%.3f\n" % (time.strftime("%F %T"), b["eat"],
                b["unconf"], b["cook"], left, taken, s["r"]))
    board(state="done", cook=b["cook"], left=left, taken=taken, r=round(s["r"], 2))
    tg("sendMessage", chat_id=CHAT,
       text="Cooked %d, %d left, %d eaten. Next forecast trusts %d%% of the silent."
            % (b["cook"], left, taken, round(s["r"] * 100)))


if __name__ == "__main__":
    {"check": cmd_check, "open": cmd_open, "lock": cmd_lock,
     "left": lambda: cmd_left(int(sys.argv[2]))}[sys.argv[1]]()
