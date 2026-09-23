#!/usr/bin/env python3
"""One check for the plumbing forecast.py's self-check cannot see: the board.js
round-trip, the stale-board guards, and the CSV header.  `python test_chope.py`.
No Telegram, no network -- tg() is replaced."""
import json, os, tempfile, time

os.environ.update(CHOPE_TOKEN="x", CHOPE_CHAT="-100", CHOPE_STRENGTH="100")
tmp = tempfile.mkdtemp()
os.environ["CHOPE_STATE"] = os.path.join(tmp, "state.json")
os.environ["CHOPE_UNITS"] = os.path.join(tmp, "units.json")
import chope as K
K.BOARD, K.LOG = os.path.join(tmp, "board.js"), os.path.join(tmp, "meals.csv")

sent = []
K.tg = lambda m, **p: (sent.append(m), {
    "sendPoll":    {"message_id": 42},
    "stopPoll":    {"options": [{"voter_count": 60}, {"voter_count": 12}]},
}.get(m, {}))[1]          # getStickerSet -> {} : no packs, stickers skip


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

assert [m for m in sent if m != "getStickerSet"] == [
    "sendMessage", "sendPoll", "stopPoll", "sendMessage", "sendMessage"], sent  # stickers skipped, not crashed

# --- the game.  72/100 replied, need 80: no Goal Day.  Old rule cooks 88, board 88: 0 saved.
import game as G
g = G.load()
assert g["pts"][G.HOME] == G.SEED[G.HOME][0] and g["played"] == 18 and g["last_left"] == 18, g
# /demo arithmetic: the seeded 71 are one short, the visitor's tap makes 72 of 90.
assert not G.record(G.seed(), K.DEMO_EAT + K.DEMO_NOTC, K.DEMO_N, 5)[0]
g = G.seed()
assert G.record(g, K.DEMO_EAT + K.DEMO_NOTC + 1, K.DEMO_N, 5) == (True, True)  # tied -> sole lead
assert G.rank(g) == 1 and g["saved"][G.HOME] == G.SEED[G.HOME][1] + 5
assert "👈" in G.leaderboard(g) and "15 pts" in G.progress(g)
print("ok  |  game: Goal Day at 80%, demo vote tips it, lead change  |  two-number entry scores the PAN not the board, K1 logged, plus "
      "board.js round-trip, header, stale-day, wrong-state, over-count, "
      "double-key guards")

# --- month end.  Crown by points (ties -> portions saved), zero everyone, keep the champion.
g = G.seed()
g["pts"]["Bravo Coy"] = g["pts"][G.HOME]                       # tie on points ...
assert g["saved"][G.HOME] < g["saved"]["Bravo Coy"]             # ... Bravo saved more
nxt = G.next_month(g["month"])
text = G.rollover(g, nxt)
assert "CHAMPION: BRAVO COY" in text and "finished #2" in text, text
assert set(g["pts"].values()) == {0} and g["played"] == 0 and g["month"] == nxt, g
assert g["champions"][-1][1] == "Bravo Coy" and "Last month: 🏆 Bravo Coy" in G.leaderboard(g)
assert G.rollover(g, nxt) is None and G.rollover(g, "2020-01") is None   # never twice, never back
assert G.next_month("2026-12") == "2027-01"
g = G.seed(); g["pts"] = dict.fromkeys(g["pts"], 0)
assert "No winner" in G.rollover(g, nxt) and g["champions"] == []
# the real path: the first poll of a new month announces BEFORE the poll goes out
g = G.seed(); g["month"] = "2020-01"; G.save(g)
del sent[:]
K.cmd_open()
assert [m for m in sent if m not in ("getStickerSet", "sendSticker")] == [
    "sendMessage", "sendPoll", "sendMessage", "sendPoll"], sent   # crown, menu, morning, lunch
assert G.load()["month"] == time.strftime("%Y-%m")
print("ok  |  month end: crown, tie-break on saved, reset, hall of fame, no double/backward roll")
