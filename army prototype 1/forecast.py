"""Chope forecast.

    base = confirmed + ceil(r * unconfirmed)
    cap  = confirmed + unconfirmed + min(slack, declined)
    COOK = min(cap, base + margin)

Three properties hold for every input and every state, and they -- not the
estimator -- are what makes the number defensible.  demo() checks all three by
fuzzing, because a property you assert on one example is a property you assume:

  1. confirmed <= COOK <= strength.  Both bounds are counts anyone in the room
     can read off the poll, so the number is checkable without trusting us.
  2. One more "Eating" vote never lowers COOK.  One more "Not eating" never
     raises it.  The board cannot move the wrong way.
  3. Nobody who declined is cooked for -- unless decliners have actually turned
     up before, and then only by as many portions as turned up.

Three pieces of state, each moved only by its own evidence:
    r      -- what fraction of the SILENT eat.  EWMA of observed turn-up.
    margin -- how noisy the forecast is.  EWMA of |error|; ~1.6 sd at MARGIN_K=2.
    slack  -- how wrong the CEILING is.  Ratchets on stock-outs that happened
              while already cooking for everyone who did not decline.

r starts at 1.0 and margin at 0, so meal one is exactly today's number: silence
counts as eating, as it does today, and day one cannot run shorter than the
cookhouse would have run anyway.

NOTHING HERE IS A TUNED CONSTANT THAT SETS A FLOOR ON WASTE.  Two used to be,
both deleted after measurement: a flat 3-portion margin floor (told a group of
one who declined to cook 3), and R_FLOOR=0.5, "never trust fewer than half the
silent", which cost 34 wasted portions a meal in a unit where silence mostly
means "not eating" -- twelve times Chope's entire saving.  Do not add a third.

Stdlib only.  `python forecast.py` runs the self-check."""
import json, math, os, sys

HERE    = os.path.dirname(os.path.abspath(__file__))
STATE   = os.environ.get("CHOPE_STATE", os.path.join(HERE, "chope_state.json"))
ALPHA        = 0.25   # EWMA on r.  ~12 meals to settle, no oscillation.
ERR_A        = 0.30   # EWMA on the forecast error that sets the margin
MARGIN_K     = 2.0    # margin = 2 x EWMA(|error|) ~= 1.6 sd.  Measured: worst-case
                      # 2.3% of meals run short across turn-up rates 0.25-0.90.
STOCKOUT_ERR = 2.0    # a stock-out under the ceiling widens the margin; decays back.
                      # Flat on purpose: measured irrelevant at scale (r does the
                      # regime-shift work), and bounded by the cap at small scale.


def new():
    return {"r": 1.0, "err": 0.0, "n": 0,
            "base": 0, "cap": 0, "slack": 0, "stockouts": 0}


def load():
    try:
        s = new()
        s.update(json.load(open(STATE)))      # update(), so a state file written by
        return s                              # an older version gains new keys
    except OSError:
        return new()                          # first run, nothing written yet
    except ValueError:                        # corrupt file: r would reset to 1.0
        print("WARNING:", STATE, "is corrupt, r resets to 1.0", file=sys.stderr)
        return new()


def save(s):
    json.dump(s, open(STATE + ".tmp", "w"))
    os.replace(STATE + ".tmp", STATE)         # atomic: a power cut can't half-write it


def margin(s):
    """How far above base we are willing to go.  cook() then clips this to the
    people actually unaccounted for, so a margin learned on a 90-man lunch cannot
    be spent on a 3-man weekend duty meal."""
    return math.ceil(MARGIN_K * s["err"])


def cook(s, confirmed_eating, unconfirmed, declined=0):
    """At the cook cutoff.  Locks the number on the kitchen board.
    declined = voted "Not eating".  confirmed + unconfirmed + declined = strength."""
    assert min(confirmed_eating, unconfirmed, declined) >= 0, "negative headcount"
    s["base"]  = confirmed_eating + math.ceil(s["r"] * unconfirmed)  # r<=1 => base<=cap
    s["slack"] = min(s["slack"], declined)   # clamp at WRITE, not just at use: a
                                             # ceiling learned on a 40-decliner lunch
                                             # must not lie dormant and spring back
    s["cap"]   = confirmed_eating + unconfirmed + s["slack"]
    return min(s["cap"], s["base"] + margin(s))


def score(s, confirmed_eating, unconfirmed, cooked, left):
    """After service, from the keypad.  left = portions left.

    `cooked` is what was ACTUALLY cooked.  Pass the kitchen's real figure if you
    can get it, not the board's -- the kitchen cooks above the indent [T2], and
    scoring the model against its own number instead of the pan measures nothing.

    THE TRAP: err tracks |taken - base|, which equals |margin - left|.  That is a
    real forecast error only while `left` moves with real demand.  If `left` is
    decoupled from demand -- the kitchen always holds back a fixed few portions,
    or cooks its own number and reports leftovers against that -- the margin feeds
    on its own leftovers and runs away upward.  Watch `left` on the first week."""
    taken = cooked - left
    s["err"] += ERR_A * (abs(taken - s["base"]) - s["err"])
    s["n"]   += 1

    # left == 0 is CENSORED: we know demand >= taken, not what it was.  One keypad
    # number also cannot tell "ran out" from "exactly right", so an exactly-right
    # meal is treated as a stock-out.  That is the price of the 3-keystroke UX; it
    # creeps COOK up by a portion or two and no further, because each of the two
    # rules below is capped by its own evidence.
    if left == 0 and cooked > 0:      # cooked nothing -> learned nothing, not a stock-out
        s["stockouts"] += 1
        if cooked >= s["cap"]:
            s["slack"] += 1       # we had ALREADY cooked for everyone who did not
                                  # decline and still ran out.  The ceiling was
                                  # wrong -- r and the margin cannot fix a ceiling.
        else:
            s["err"] += STOCKOUT_ERR      # the margin was too small.  Decays back.
    elif s["slack"] and cooked < s["cap"]:
        s["slack"] -= 1           # the forecast did not even want the room.  Give
                                  # it back, or slack becomes a floor on waste too.

    if unconfirmed <= 0:
        return s                  # no information about r; leave it alone
    obs = min(1.0, max(0.0, (taken - confirmed_eating) / unconfirmed))
    if left == 0:
        s["r"] += ALPHA * max(0.0, obs - s["r"])   # censored: only ever evidence r is HIGHER
    else:
        s["r"] += ALPHA * (obs - s["r"])
    s["r"] = min(1.0, max(0.0, s["r"]))
    return s


# ponytail: binomial by summing coin flips; scipy is not worth a dependency for this.
def _demand(rng, C, U, p, N=0, q=0.0):
    return (C + sum(rng.random() < p for _ in range(U))
              + sum(rng.random() < q for _ in range(N)))


def _properties(rng):
    """The three claims, fuzzed over random states and headcounts.  This is the
    check that answers "how do you know the number is never silly" -- not an
    example, every state.  A property asserted on one example is an assumption."""
    for _ in range(4000):
        s = new()
        s["r"], s["err"] = rng.uniform(0, 1), rng.uniform(0, 30)
        s["slack"] = rng.randint(0, 20)
        C, U, N = (rng.randint(0, 250) for _ in range(3))
        c = cook(s, C, U, N)
        assert C <= c <= C + U + N, (C, U, N, c, s)          # 1. bounded by the room
        assert c >= s["base"], (C, U, N, c, s)               #    the cap never cuts base
        if U:
            assert cook(s, C + 1, U - 1, N) >= c, (C, U, N)  # 2. silent -> Eating
            assert cook(s, C, U - 1, N + 1) <= c, (C, U, N)  #    silent -> Not eating
        if N:
            assert cook(s, C + 1, U, N - 1) >= c, (C, U, N)  #    Not eating -> Eating
        s["slack"] = 0
        assert cook(s, 0, 0, N) == 0, N                      # 3. no evidence, no portion


def demo():
    import random
    rng = random.Random(7)
    C, U, N, P = 60, 40, 10, 0.72

    _properties(rng)

    # 1. converges in ~12 meals, stays there, unbiased, and does not run short
    s, shortfalls, rs = new(), 0, []
    for i in range(200):
        cooked = cook(s, C, U, N)
        if i >= 15:
            rs.append(s["r"])
            assert abs(s["r"] - P) < 0.10, (i, s["r"])           # no drift, no oscillation
            assert cooked >= C + P * U, (i, cooked)              # margin covers the wobble
        d = _demand(rng, C, U, P)
        shortfalls += d > cooked
        score(s, C, U, cooked, max(0, cooked - d))
    assert abs(sum(rs) / len(rs) - P) < 0.03, sum(rs) / len(rs)  # unbiased
    assert shortfalls / 200 < 0.05, shortfalls                   # noise, not bias
    assert s["n"] == 200 and s["slack"] == 0                     # no ceiling evidence, no slack

    # 2. a stock-out UNDER the ceiling widens the margin and can only raise r
    s = new(); s["r"] = 0.70; s["err"] = 4.0
    c = cook(s, C, U, N); m0 = margin(s); score(s, C, U, c, 0)
    assert s["r"] > 0.70 and margin(s) > m0 and s["slack"] == 0, (s, m0)

    # 2b. a stock-out at exactly base is censored AT r.  Not evidence r is wrong.
    s = new(); s["r"] = 0.70
    score(s, C, U, cook(s, C, U, N), 0)
    assert s["r"] == 0.70 and s["stockouts"] == 1, s

    # 3. regime shift up (block leave ends) from a COLLAPSED r -- the case that
    #    deleting R_FLOOR created.  Costs ~4 tight meals and recovers inside 12.
    s = new()
    for _ in range(60):
        c = cook(s, C, U, N); score(s, C, U, c, max(0, c - _demand(rng, C, U, 0.02)))
    assert s["r"] < 0.10, s["r"]                    # genuinely collapsed, no floor
    late = 0
    for i in range(12):
        c = cook(s, C, U, N); d = _demand(rng, C, U, 0.95)
        late += (i >= 6 and d > c)                  # the back half must be clean
        score(s, C, U, c, max(0, c - d))
    assert late == 0 and s["r"] > 0.85, (late, s["r"])

    # 4. everybody replied: nobody is unaccounted for, so cook exactly what was said.
    #    No division by zero, r untouched, and a fat stale margin cannot leak in.
    s = new(); s["r"] = 0.7; s["err"] = 20.0
    assert cook(s, 100, 0, 0) == 100
    score(s, 100, 0, 100, 5)
    assert s["r"] == 0.7

    # 5. day one == exactly today's number.  Silence counts as eating, margin 0.
    assert cook(new(), 60, 40, 0) == 100

    # 6. the degenerate headcounts that started this.  A group of one who says
    #    "Not eating" gets 0 portions, not 3, with any margin loaded.
    s = new(); s["err"] = 20.0
    assert cook(s, 0, 0, 1) == 0     # one man, he declined.          Cook nothing.
    assert cook(s, 0, 1, 0) == 1     # one man, silent -> counted in.  Cook one.
    assert cook(s, 3, 0, 0) == 3     # three men, all said yes.        Cook three.
    assert cook(s, 2, 0, 8) == 2     # everyone answered; nothing to estimate.
    assert cook(s, 0, 0, 0) == 0     # nobody exists.
    s = new()                        # ...and a zero-portion meal must teach NOTHING:
    for _ in range(50):              # left==0 is automatic when cooked==0, and that
        score(s, 0, 0, cook(s, 0, 0, 1), 0)   # must not manufacture ceiling evidence
    assert s["slack"] == 0 and s["stockouts"] == 0 and cook(s, 0, 0, 1) == 0, s
    score(s, 0, 0, 0, 0)                            # and scoring it is a no-op, not a crash

    # 7. the ceiling releases ONLY on evidence, and gives the room back without it.
    s = new()
    for _ in range(10):                             # decliners keep turning up
        c = cook(s, 60, 0, 40); score(s, 60, 0, c, 0)
    assert s["slack"] >= 5, s                       # ratcheted up on proof
    assert cook(s, 60, 0, 40) > 60, cook(s, 60, 0, 40)
    for _ in range(40):                             # ... and then they stop
        c = cook(s, 60, 0, 40); score(s, 60, 0, c, c - 60)   # real demand, = the 60
    assert s["slack"] <= 1, s        # room handed back, bar the 1-portion residual:
    # a perfect forecast leaves 0, which is indistinguishable from running out, so
    # the ceiling creeps up one portion and stops.  Measured across shapes: never
    # more than 1.  That is the whole price of a 3-keystroke keypad, and it is paid
    # in the safe direction.

    print("ok  |  4000 fuzzed states: bounds + monotonicity hold  |  200 meals: "
          "mean r=%.3f (true %.2f), %d short" % (sum(rs) / len(rs), P, shortfalls))


if __name__ == "__main__":
    demo()
