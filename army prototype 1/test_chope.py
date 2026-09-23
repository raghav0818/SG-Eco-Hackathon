#!/usr/bin/env python3
"""One check for the plumbing forecast.py's self-check cannot see: the board.js
round-trip, the stale-board guards, and the CSV header.  `python test_chope.py`.
No Telegram, no network -- tg() is replaced."""
import json, os, tempfile

os.environ.update(CHOPE_TOKEN="x", CHOPE_CHAT="-100", CHOPE_STRENGTH="100")
tmp = tempfile.mkdtemp()
os.environ["CHOPE_STATE"] = os.path.join(tmp, "state.json")
import chope as K
K.BOARD, K.LOG = os.path.join(tmp, "board.js"), os.path.join(tmp, "meals.csv")

sent = []
K.tg = lambda m, **p: (sent.append(m), {
    "sendPoll":    {"message_id": 42},
    "stopPoll":    {"options": [{"voter_count": 60}, {"voter_count": 12}]},
    "sendMessage": {},
}[m])[1]


def board_js():
    """What the kiosk page actually evaluates -- B={...} , not bare JSON."""
    raw = open(K.BOARD).read()
    assert raw.startswith("B={"), raw[:20]
    return json.loads(raw[2:])


K.cmd_open()
assert board_js()["state"] == "open"

K.cmd_lock()
b = board_js()
# 100 strength - 60 eating - 12 not = 28 silent, trusted at r=1.0 on day one, margin 0.
# Day one is exactly the indent, and the 12 who said "not eating" are never cooked for.
assert (b["state"], b["eat"], b["notc"], b["unconf"]) == ("cook", 60, 12, 28), b
assert b["cook"] == 60 + 28, b["cook"]
assert b["r"] == 1.0 and b["margin"] == 0 and b["slack"] == 0, b
assert b["eat"] <= b["cook"] <= b["eat"] + b["unconf"] + b["slack"], b

# --- the two-number entry. The kitchen cooks ABOVE the board number [T5], so the
# meal MUST be scored against the pan (97) and never against the board (88).
K.cmd_key(97)                                    # first number: actually cooked
b = board_js()
assert (b["state"], b["actual"], b["cook"]) == ("cooked", 97, 88), b

K.cmd_key(18)                                    # second number: portions left
b = board_js()
assert (b["state"], b["taken"], b["left"], b["buf"]) == ("done", 79, 18, 10), b
rows = open(K.LOG).read().splitlines()
assert rows[0] == K.COLS.strip() and len(rows) == 2, rows       # header written once
#            board cooked left taken            buffer_pct
assert rows[1].split(",")[4:8] == ["88", "97", "18", "79"], rows[1]
assert rows[1].split(",")[10] == "10.2", rows[1]                # K1, measured, logged
r_honest = json.load(open(os.environ["CHOPE_STATE"]))["r"]
assert r_honest < 1.0, r_honest                                 # scored, r came down
# 79 of 88 taken, 60 said yes, 28 silent -> obs = 19/28 = 0.679, not (88-18-60)/28
assert abs(r_honest - (1.0 + 0.25 * (19 / 28.0 - 1.0))) < 1e-9, r_honest

# --- the guards. Both of these silently corrupted a meal before they existed. ---
def refuses(fn, why):
    try:
        fn()
    except SystemExit:
        return
    raise AssertionError(why)

refuses(lambda: K.cmd_key(5), "keyed a number in while the board said 'done'")


def reopen(state, **kw):
    """Put the board back into a mid-meal state.  The 'done' board is terminal and
    does not carry the headcounts, so they go back in explicitly."""
    b = board_js()
    b.update(state=state, eat=60, notc=12, unconf=28, cook=88)
    b.update(kw)
    open(K.BOARD, "w").write("B=" + json.dumps(b))


reopen("cooked", actual=97)
refuses(lambda: K.cmd_left(98), "accepted more left over than was ever cooked")
# The same number keyed twice -- the failure the old "Cooked?" prompt invited on the
# SECOND number. taken=0 is silent: it passes every other guard and floors r.
refuses(lambda: K.cmd_left(97), "accepted 97 cooked / 97 left while 60 said eating")
# 97 cooked, 2 left => 95 ate, but the unit is only 100 strong and 12 declined.
reopen("cooked", actual=997)
refuses(lambda: K.cmd_left(0), "accepted more eaten than the unit has people")

reopen("cook")
stale = board_js()
stale["d"] = "2020-01-01"
open(K.BOARD, "w").write("B=" + json.dumps(stale))
refuses(K.cmd_lock, "locked against a board from a different day")
refuses(lambda: K.cmd_key(5), "scored against a board from a different day")

assert sent == ["sendPoll", "stopPoll", "sendMessage", "sendMessage"], sent
print("ok  |  two-number entry scores the PAN not the board, K1 logged, plus "
      "board.js round-trip, header, stale-day, wrong-state, over-count, "
      "double-key guards")
