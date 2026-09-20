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
# 100 strength - 60 eating - 12 not = 28 silent, trusted at r=1.0 on day one, +3 margin
assert (b["state"], b["eat"], b["notc"], b["unconf"]) == ("cook", 60, 12, 28), b
assert b["cook"] == 60 + 28 + 3, b["cook"]
assert b["r"] == 1.0 and b["margin"] == 3, b

K.cmd_left(9)
b = board_js()
assert (b["state"], b["taken"], b["left"]) == ("done", b["cook"] - 9, 9), b
rows = open(K.LOG).read().splitlines()
assert rows[0] == K.COLS.strip() and len(rows) == 2, rows       # header written once
assert rows[1].split(",")[3:6] == ["91", "9", "82"], rows[1]
assert json.load(open(os.environ["CHOPE_STATE"]))["r"] < 1.0    # scored, r came down

# --- the guards. Both of these silently corrupted a meal before they existed. ---
def refuses(fn, why):
    try:
        fn()
    except SystemExit:
        return
    raise AssertionError(why)

refuses(lambda: K.cmd_left(5), "scored a meal while the board said 'done', not 'cook'")

back = board_js()                                  # re-open the board to test the range guard
back["state"] = "cook"
open(K.BOARD, "w").write("B=" + json.dumps(back))
refuses(lambda: K.cmd_left(back["cook"] + 1), "accepted more left over than was ever cooked")

stale = board_js()
stale["d"] = "2020-01-01"
open(K.BOARD, "w").write("B=" + json.dumps(stale))
refuses(K.cmd_lock, "locked against a board from a different day")
refuses(lambda: K.cmd_left(5), "scored against a board from a different day")

assert sent == ["sendPoll", "stopPoll", "sendMessage", "sendMessage"], sent
print("ok  |  board.js round-trip, header, stale-day, wrong-state, over-count guards")
