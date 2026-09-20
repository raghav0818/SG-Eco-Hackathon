"""Chope forecast.  COOK = confirmed_eating + r*unconfirmed + margin.
r starts at 1.0 (= exactly today's number) and only moves when a meal is scored.
r estimates the truth; the margin carries the safety; a stock-out ratchets r up.
Stdlib only.  `python forecast.py` runs the self-check."""
import json, math, os, sys

HERE    = os.path.dirname(os.path.abspath(__file__))
STATE   = os.environ.get("CHOPE_STATE", os.path.join(HERE, "chope_state.json"))
ALPHA        = 0.25   # EWMA on r.  ~12 meals to settle, no oscillation.
STOCKOUT_ERR = 2.0    # stock-out widens the margin by 2*this; decays back over ~10 meals
R_FLOOR      = 0.50   # never trust fewer than half the silent
MARGIN_K, MARGIN_MIN = 2.0, 3   # margin = 2 x EWMA(|forecast error|), >= 3 portions
ERR_A   = 0.30


def new():
    return {"r": 1.0, "err": 0.0, "n": 0, "base": 0, "stockouts": 0}


def load():
    try:
        return json.load(open(STATE))
    except OSError:
        return new()                          # first run, nothing written yet
    except ValueError:                        # corrupt file: r would reset to 1.0
        print("WARNING:", STATE, "is corrupt, r resets to 1.0", file=sys.stderr)
        return new()


def save(s):
    json.dump(s, open(STATE + ".tmp", "w"))
    os.replace(STATE + ".tmp", STATE)         # atomic: a power cut can't half-write it


def margin(s):
    return max(MARGIN_MIN, math.ceil(MARGIN_K * s["err"]))


def cook(s, confirmed_eating, unconfirmed):
    """At the cook cutoff.  Locks the number on the kitchen board."""
    s["base"] = confirmed_eating + math.ceil(s["r"] * unconfirmed)
    return s["base"] + margin(s)


def score(s, confirmed_eating, unconfirmed, cooked, left):
    """After service, from the keypad.  left = portions left."""
    taken = cooked - left
    s["err"] += ERR_A * (abs(taken - s["base"]) - s["err"])
    s["n"]   += 1
    if unconfirmed <= 0:
        return s                              # no information about r; leave it alone
    obs = min(1.0, max(0.0, (taken - confirmed_eating) / unconfirmed))
    if left == 0:                  # ran out -> taken is censored, true demand >= taken
        s["stockouts"] += 1
        s["r"]   += ALPHA * max(0.0, obs - s["r"])   # can only ever be evidence r is HIGHER
        s["err"] += STOCKOUT_ERR                     # and widen the margin; it decays back
    else:
        s["r"] += ALPHA * (obs - s["r"])
    s["r"] = min(1.0, max(R_FLOOR, s["r"]))
    return s


# ponytail: binomial by summing coin flips; scipy is not worth a dependency for this.
def _demand(rng, C, U, p):
    return C + sum(rng.random() < p for _ in range(U))


def demo():
    import random
    rng = random.Random(7)
    C, U, P = 60, 40, 0.72

    # 1. converges in ~10 meals, stays there, and cook() never sits below expected demand
    s, shortfalls, rs = new(), 0, []
    for i in range(200):
        cooked = cook(s, C, U)
        if i >= 15:
            rs.append(s["r"])
            assert abs(s["r"] - P) < 0.10, (i, s["r"])           # no drift, no oscillation
            assert cooked >= C + P * U, (i, cooked)              # margin covers the wobble
        d = _demand(rng, C, U, P)
        shortfalls += d > cooked
        score(s, C, U, cooked, max(0, cooked - d))
    assert abs(sum(rs) / len(rs) - P) < 0.03, sum(rs) / len(rs)  # unbiased
    assert shortfalls / 200 < 0.05, shortfalls                   # noise, not bias
    assert s["n"] == 200

    # 2. a stock-out can only raise r, and widens the margin
    s = new(); s["r"] = 0.70
    c = cook(s, C, U); m0 = margin(s); score(s, C, U, c, 0)
    assert s["r"] > 0.70 and margin(s) > m0, (s["r"], m0, margin(s))

    # 3. regime shift up (block leave ends).  The margin absorbs it in 3 meals,
    #    r catches up inside 12.  This is the honest recovery claim.
    s = new()
    for _ in range(60):
        c = cook(s, C, U); score(s, C, U, c, max(0, c - _demand(rng, C, U, 0.40)))
    assert s["r"] < 0.55, s["r"]
    n0, late = s["stockouts"], 0
    for i in range(12):
        c = cook(s, C, U); d = _demand(rng, C, U, 0.95)
        late += (i >= 3 and d > c)
        score(s, C, U, c, max(0, c - d))
    assert s["stockouts"] - n0 <= 3 and late == 0, (s["stockouts"] - n0, late)
    assert s["r"] > 0.85, s["r"]

    # 4. everybody replied: no division by zero, r untouched
    s = new(); s["r"] = 0.7
    assert cook(s, 100, 0) == 100 + margin(s)
    score(s, 100, 0, 103, 5)
    assert s["r"] == 0.7

    # 5. day one == today's number + a 3-portion margin
    s = new()
    assert cook(s, 60, 40) == 103

    print("ok  |  200 meals: mean r=%.3f (true %.2f), stock-outs=%d"
          % (sum(rs) / len(rs), P, shortfalls))


if __name__ == "__main__":
    demo()
