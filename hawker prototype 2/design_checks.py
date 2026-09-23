#!/usr/bin/env python3
"""Tray Watch design checks.  `python design_checks.py`  -- stdlib only, ~30 s.

Every number tagged [MEASURED, 21 Sep] in 09-traywatch-prd.md comes out of this file.
It exists because four of the design's load-bearing claims turned out to be wrong when
they were measured instead of argued, and a claim nobody can re-run is a claim nobody
should believe.

  C1  the rearrangement experiment cannot reach p<0.05 -- exhaustive, not an estimate
  C2  ...and even if it could, it is underpowered by roughly an order of magnitude
  C3  the six-line analysis in 07-architecture.md 5.5 returns p=0.0000 on a missing dish
  C4  cooked_total is biased LOW by ~23% at a 6-min analysis gap, ~9.5% at 2 min
  C5  the descriptive waste claim needs none of the above and lands every time
  C6  ...but leftover_close, the number the page prints, is exact at every gap
  C7  swapping the row mid-afternoon beats swapping it on alternate days, 2.4-3.9x

The service model is HER day: open 08:00, close 19:00 [T7, 22 Sep], three peaks and a
dead afternoon. It used to be a 6-hour lunch-only day, which is why the bias numbers
in this file moved when she said "seven pm" -- the old -12% certified a day that does
not exist. Numbers here are re-measured, 22 Sep.
"""
import math, random, statistics as st
from itertools import permutations, product

# The chain under test is the SHIPPED one. Importing it rather than copying it is the
# whole point: a copy drifts, and then these checks certify code nobody runs.
from analyse import smooth, day_totals, MIN_DROP, REFILL_JUMP


# ---------------------------------------------------------------- C1
def max_clean_dishes(n_trays):
    """A dish only tests CONTRAST if it did not move -- a dish that moved has position
    confounded with contrast and six days cannot separate them.  So: over every possible
    rearrangement of the row, how many dishes can be both never-moved AND given new
    neighbours?  That count, not the tray count, is the n of the sign-flip test."""
    base = tuple(range(n_trays))
    def nbrs(a):
        return {a[i]: frozenset(a[max(0, i-1):i] + a[i+1:i+2]) for i in range(n_trays)}
    b, best = nbrs(base), 0
    for arr in permutations(base):
        moved = {arr[i] for i in range(n_trays) if arr[i] != base[i]}
        a = nbrs(arr)
        best = max(best, sum(1 for d in base if d not in moved and a[d] != b[d]))
    return best


def floor_p(n):
    """Best-case two-sided p of a sign-flip test on n units: every unit moves the same
    way.  If this is above 0.05 the experiment is unwinnable before it starts."""
    return 2 / 2 ** n if n else 1.0


# ---------------------------------------------------------------- C2, C3
SIGNS = [s for s in product((-1, 1), repeat=8)]


def sign_flip_p(diff):
    """07-architecture.md 5.5, faithfully -- including its behaviour on a NaN."""
    n = len(diff)
    obs = sum(diff) / n
    signs = SIGNS if n == 8 else list(product((-1, 1), repeat=n))
    null = [sum(s[i] * abs(diff[i]) for i in range(n)) / n for s in signs]
    return obs, sum(1 for x in null if abs(x) >= abs(obs)) / len(null)


def power(effect_pct, cv, days_per_arm, nsim=1000, seed=1):
    """Share of experiments reaching p<0.05 when the effect is REAL and that big."""
    rng, hits = random.Random(seed), 0
    for _ in range(nsim):
        diff = []
        for _d in range(8):
            base = rng.uniform(80, 250)             # this dish's daily sales
            sd = base * cv                          # its day-to-day wobble
            a = st.mean(rng.gauss(base, sd) for _ in range(days_per_arm))
            b = st.mean(rng.gauss(base * (1 + effect_pct / 100), sd)
                        for _ in range(days_per_arm))
            diff.append(b - a)
        if sign_flip_p(diff)[1] < 0.05:
            hits += 1
    return 100.0 * hits / nsim


# ---------------------------------------------------------------- C4
DAY = 660          # 08:00 -> 19:00 in one-minute ticks. t=0 is 08:00.


def rate(t):
    """Portions per minute through her real day, not a generic lunch service."""
    if t < 90:   return 0.5        # 08:00-09:30  breakfast trickle
    if t < 210:  return 0.3        # 09:30-11:30  dead
    if t < 330:  return 2.2        # 11:30-13:30  LUNCH
    if t < 540:  return 0.4        # 13:30-17:00  the lull -- this is when she can swap
    return 1.6                     # 17:00-19:00  dinner


def service(rng, refills=((200, 45), (265, 40), (330, 20), (540, 50), (600, 30))):
    """One tray, one 11-hour day.  Truth is known.  Five refills, because a day this
    long has a pre-lunch, an in-lunch and a pre-dinner top-up, not four lunch ones."""
    fill, out, cooked, ref = 100.0, [], 100.0, dict(refills)
    for t in range(DAY):
        if t in ref:
            add = min(ref[t], 100 - fill)
            fill += add
            cooked += add
        fill = max(0.0, fill - rng.gauss(rate(t), 0.5))
        out.append(fill)
    return out, cooked


def sampled(truth, rng, gap_min, model_sd=4.0):
    """What the vision model would have returned: the true level plus reading error,
    quantised to the 0-100 step-5 grid the schema asks for."""
    return [round(max(0, min(100, truth[t] + rng.gauss(0, model_sd))) / 5) * 5
            for t in range(0, DAY, gap_min)]


def recovered_cooked(truth, rng, gap_min, model_sd=4.0):
    return day_totals(sampled(truth, rng, gap_min, model_sd))["cooked_total"]


def cooked_bias(gap_min, ndays=300):
    err = []
    for i in range(ndays):
        truth, ct = service(random.Random(i))
        err.append(100.0 * (recovered_cooked(truth, random.Random(i + 9999), gap_min) - ct) / ct)
    return sum(err) / len(err), min(err)


def leftover_bias(gap_min, ndays=300, model_sd=4.0):
    """C6, and it is the one that decides what the paper page may say.  cooked_total
    is a SUM OF DETECTED JUMPS and inherits every refill the chain mis-sized.
    leftover_close is a LEVEL READ at close -- no refill, no lag, no threshold between
    it and the truth.  They are not the same kind of number and must not be presented
    as though they were."""
    err = []
    for i in range(ndays):
        truth, _ = service(random.Random(i))
        raw = sampled(truth, random.Random(i + 9999), gap_min, model_sd)
        err.append(day_totals(raw)["leftover_close"] - truth[-1])   # fill-points, not a ratio
    return sum(err) / len(err)


# ---------------------------------------------------------------- C7
BLOCK = (1.0, 0.75)      # 08:00-14:00 sells more than 14:00-19:00. Never cancels.


def week(effect_pct, day_cv, design, rng, n_dish=5, days=6,
         block_cv=0.15, read_cv=0.08):
    """One simulated six-day week -> (estimated effect %, 95% CI half-width).

    n_dish defaults to 5, not 8: C1 already showed only five dishes are ever
    countable, so measuring this at n=8 would flatter it by sqrt(8/5).

    Three noise sources, all applied to BOTH designs. The first version of this check
    gave the crossover no within-block noise and it returned +/-0.0 -- perfect by
    construction, which was a bug in the simulation, not a result.
        day     footfall / weather / exam week   <- cancels ONLY within a day
        block   how many people came this block  <- never cancels
        read    the vision chain's own error     <- never cancels"""
    per_dish = []
    for _d in range(n_dish):
        base = rng.uniform(80, 250)
        logr, A, B = [], [], []
        for i in range(days):
            day = max(0.05, rng.gauss(1.0, day_cv))

            def sold(j, arr):
                e = 1 + effect_pct / 100 if arr == "B" else 1.0
                n = base * day * BLOCK[j] * e * max(0.05, rng.gauss(1.0, block_cv))
                return max(1.0, n * max(0.05, rng.gauss(1.0, read_cv)))

            if design == "between":                    # whole day, one arrangement
                arr = "A" if i % 2 == 0 else "B"
                (A if arr == "A" else B).append(sold(0, arr) + sold(1, arr))
            else:                                      # swap in the lull; order alternates
                order = ("A", "B") if i % 2 == 0 else ("B", "A")
                a, b = sold(order.index("A"), "A"), sold(order.index("B"), "B")
                # log ratio: `day` and `base` cancel EXACTLY within the day, and BLOCK
                # cancels across days because the order is counterbalanced.
                logr.append(math.log(b / a))
        if design == "between":
            per_dish.append(100.0 * (st.mean(B) - st.mean(A)) / st.mean(A))
        else:
            per_dish.append(100.0 * (math.exp(st.mean(logr)) - 1))
    return st.mean(per_dish), 1.96 * st.stdev(per_dish) / n_dish ** 0.5


def design_ci(effect_pct, day_cv, design, nsim=2000, seed=11):
    rng = random.Random(seed)
    est = [week(effect_pct, day_cv, design, rng) for _ in range(nsim)]
    return (st.mean([m for m, _ in est]), st.mean([h for _, h in est]),
            100.0 * sum(1 for m, h in est if m - h > 0) / nsim)


# ---------------------------------------------------------------- C5
def descriptive_ci(true_over, cv, ndays=6, nsim=2000, seed=5):
    """'This dish is over-cooked by X%' from ndays of observation.  No experiment,
    no arrangement, no coin to flip -- so the only question is precision."""
    rng, halves, clears = random.Random(seed), [], 0
    for _ in range(nsim):
        d = [rng.gauss(true_over, true_over * cv) for _ in range(ndays)]
        h = 1.96 * st.stdev(d) / (ndays ** 0.5)
        halves.append(h)
        clears += (st.mean(d) - h) > 0
    return sum(halves) / len(halves), 100.0 * clears / nsim


# ---------------------------------------------------------------- report
if __name__ == "__main__":
    print("C1  Can the rearrangement experiment reach p<0.05 at all?")
    for r in (8, 9):
        n = max_clean_dishes(r)
        print("      %2d trays -> at most %d dishes are never-moved AND re-neighboured"
              "  ->  best possible p = %.4f  %s"
              % (r, n, floor_p(n), "OK" if floor_p(n) < 0.05 else "<-- UNWINNABLE"))
    assert max_clean_dishes(8) == 5, "8 trays must cap at 5 clean dishes"
    assert floor_p(5) > 0.05, "n=5 must be unwinnable"
    assert floor_p(8) < 0.05, "n=8 would be winnable, which is why the n matters"

    print("\nC2  ...and at n=8, ignoring C1, how often does a REAL effect get detected?")
    print("      effect   3 days/arm, wobble 25%    3 days/arm, wobble 40%")
    for eff in (10, 20, 30):
        print("       %+3d%%           %5.1f%%                  %5.1f%%"
              % (eff, power(eff, .25, 3), power(eff, .40, 3)))
    assert power(10, .40, 3) < 25, "a +10% effect must be shown to be mostly invisible"

    print("\nC3  The 07-architecture.md 5.5 analysis, fed a dish that missed an arm")
    good = [4.0, 6.0, 2.0, 5.0, 3.0, 7.0, 1.0, 4.0]
    holey = good[:3] + [float("nan")] + good[4:]
    print("      all 8 dishes present : obs=%+.2f  p=%.4f" % sign_flip_p(good))
    print("      one dish missing     : obs=%+.2f  p=%.4f   <-- FAKE CERTAINTY"
          % sign_flip_p(holey))
    assert sign_flip_p(holey)[1] == 0.0, "the NaN must produce p=0.0, or this is fixed"

    print("\nC4  cooked_total recovery vs how often frames are analysed")
    for gap in (2, 4, 6):
        m, w = cooked_bias(gap)
        print("      every %d min  mean %+6.1f%%   worst %+6.1f%%" % (gap, m, w))
    assert cooked_bias(2)[0] > cooked_bias(6)[0], "2-min must beat 6-min"
    assert cooked_bias(2)[0] < 0, "the bias is always DOWNWARD -- never a coin flip"

    print("\nC6  ...but WHICH number? cooked is a sum of jumps; leftover is a level read")
    for gap in (2, 6):
        print("      every %d min  cooked_total %+6.1f%%   leftover_close %+.1f fill-points"
              % (gap, cooked_bias(gap)[0], leftover_bias(gap)))
    assert abs(leftover_bias(6)) < 1.0, "leftover_close must be clean even at a 6-min gap"
    assert cooked_bias(6)[0] < -20, "cooked_total must be badly biased at a 6-min gap"

    print("\nC7  She CAN move the trays [N1 answered YES, 22 Sep] -- so WHEN?")
    print("      An 11-hour day with a dead 13:30-17:00 lets her swap IN the lull, so")
    print("      every dish sees both arrangements on the SAME day. n=5, six days.")
    print("      effect  wobble   design      est.     95% CI half   CI clears 0")
    for eff in (10, 25):
        for cv in (.25, .40):
            for design in ("between", "crossover"):
                m, h, clears = design_ci(eff, cv, design)
                print("       %+3d%%     %2d%%    %-9s   %+5.1f%%     +/-%4.1f        %3.0f%%"
                      % (eff, cv * 100, design, m, h, clears))
    bt, cr = design_ci(10, .40, "between"), design_ci(10, .40, "crossover")
    assert cr[1] < bt[1] / 2, "the crossover must at least halve the CI, or do not ask her"
    assert abs(cr[0] - 10) < abs(bt[0] - 10), "between-day is biased UP: noisy denominator"
    assert design_ci(10, .25, "crossover")[1] == cr[1],         "the crossover must be INDIFFERENT to day wobble -- that is the whole point"
    print("      ^ the crossover rows are IDENTICAL at 25% and 40% wobble: the day")
    print("        effect cancels inside the day. That is what buys the CI.")
    print("      IT DOES NOT FIX C1. Five countable dishes, floor p 0.0625, so still")
    print("      no p-value. This buys PRECISION on the effect size, not significance.")

    print("C5  The descriptive claim on the same six days, with no experiment")
    for over in (40, 100):
        for cv in (.25, .40):
            h, clears = descriptive_ci(over, cv)
            print("      true over-provision %+4d%%, wobble %2d%%  ->  +/-%4.1f points,"
                  "  CI clears zero %3.0f%% of weeks" % (over, cv * 100, h, clears))
    assert descriptive_ci(40, .40)[1] > 99, "the descriptive claim must land every time"

    print("\n=== all design checks pass ===")
