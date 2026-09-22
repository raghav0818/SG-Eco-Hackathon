#!/usr/bin/env python3
"""Chope.  Four commands, no daemon, no framework, no dependencies outside stdlib.
    chope.py check   -> proves the token and chat id work, posts nothing
    chope.py open    -> posts the anonymous poll                (cron, 0700)
    chope.py lock    -> stops the poll, locks the board number  (cron, cook cutoff)
    chope.py key N   -> after service: FIRST what was actually cooked, THEN what
                        was left.  Two numbers, dispatched on the board state, so
                        the state lives in board.js and a keypad restart mid-entry
                        cannot desync them.                     (called by keypad.py)
Token comes from the environment, never the repo.
"""
import json, os, sys, time, urllib.request
import forecast as F

TOKEN   = os.environ["CHOPE_TOKEN"]          # export CHOPE_TOKEN=... in /etc/chope.env
CHAT    = int(os.environ["CHOPE_CHAT"])      # the unit's existing group
STRENGTH = int(os.environ.get("CHOPE_STRENGTH") or 0)  # 0 = ask Telegram; "" counts as 0
CUTOFF  = os.environ.get("CHOPE_CUTOFF", "")  # "HH:MM", set by install.sh from LOCK_AT --
                                               # the open-screen countdown target, nothing else
HERE    = os.path.dirname(os.path.abspath(__file__))
BOARD   = os.path.join(HERE, "board.js")     # .js, not .json: the kiosk page is file://
LOG     = os.path.join(HERE, "meals.csv")
COLS    = "when,eat,notc,unconf,board,cooked,left,taken,r,slack,buffer_pct\n"


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
    print("bot @%s ok | chat %d has %d members | strength=%s | r=%.2f margin=%d "
          "slack=%d after %d meals (%d ran short)"
          % (me["username"], CHAT, n, STRENGTH or "(ask Telegram)", s["r"],
             F.margin(s), s["slack"], s["n"], s["stockouts"]))


def cmd_open():
    m = tg("sendPoll", chat_id=CHAT, question="Lunch today?",
           options=["Eating", "Not eating"], is_anonymous=True)   # anonymous is the default
    board(state="open", msg=m["message_id"], cutoff=CUTOFF)


def cmd_lock():
    b = read_board("open")
    p = tg("stopPoll", chat_id=CHAT, message_id=b["msg"])   # returns the FINAL counts
    eat, notc = (o["voter_count"] for o in p["options"])
    n = STRENGTH or tg("getChatMemberCount", chat_id=CHAT) - 1   # -1: the bot is a member
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
    tg("sendMessage", chat_id=CHAT,
       text="Cook %d.  %d said eating, %d not, %d silent (counted at r=%.2f). "
            "Never below %d, never above %d."
            % (cooked, eat, notc, unconf, s["r"], eat, eat + unconf + s["slack"]))


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
    tg("sendMessage", chat_id=CHAT,
       text="Board said %d, kitchen cooked %d (+%d%%), %d left, %d eaten. "
            "Next forecast trusts %d%% of the silent."
            % (b["cook"], actual, round(buf), left, taken, round(s["r"] * 100)))


def cmd_key(n):
    """One keypad command, two numbers.  WHICH one depends on the board, not on the
    keypad process -- so restarting chope-keypad between the two entries cannot
    desync them, and the operator just types the two numbers the screen asks for."""
    st = json.loads(open(BOARD).read()[2:])["state"]
    if st not in ("cook", "cooked"):
        sys.exit("board is '%s' -- nothing to key in." % st)
    (cmd_cooked if st == "cook" else cmd_left)(n)


if __name__ == "__main__":
    {"check": cmd_check, "open": cmd_open, "lock": cmd_lock,
     "key": lambda: cmd_key(int(sys.argv[2]))}[sys.argv[1]]()
