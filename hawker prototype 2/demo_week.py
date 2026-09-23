#!/usr/bin/env python3
"""Build a SYNTHETIC week so the page can be rehearsed before a real one exists.

    python demo_week.py          # writes demo/page.html
    python demo_week.py --clean  # deletes demo/ entirely

WHAT THIS IS, AND WHAT IT IS NOT
    It is a dress rehearsal. The numbers are invented here; the ANALYSIS is the real
    shipped code. It pre-writes `layout.json` and a complete `readings.csv`, so
    analyse.py finds every frame already cached, makes ZERO API calls, and still runs
    the genuine chain -- smooth() -> day_totals() -> refill detection -> dish_lab()
    -> daily.csv -> report.py. What you see on the page is the real pipeline's output
    shape, driven by fabricated input.

    It is NOT a data source and NOT a finding. `report.py` renders a red SYNTHETIC
    banner whenever TW_DEMO is set, and this script always sets it. Same rule
    `replay.py` carries for Chope: a rehearsal on invented numbers is normal and
    useful; the same page shown as six real days at her stall is fabricated evidence.

    Deliberate differences from the real rig, so nobody quotes these as measurements:
      * frames every 10 min, not 2 -- 66 a day instead of 330, to keep this fast.
        cooked_total is therefore ~23% low here rather than ~9.5% (design_checks C4).
      * dish names, sell rates and the day-to-day wobble are all made up.
      * everything lands in demo/, which is gitignored, never beside the real CSVs.
"""
import csv, json, os, random, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.join(HERE, "demo")
FRAMES = os.path.join(DEMO, "frames")

GAP_MIN, OPEN_H, CLOSE_H = 10, 8, 19          # real rig: 2 min, 08:00-19:00 [T7]
W, H = 1600, 400
DAYS = ["2026-09-%02d" % d for d in range(23, 29)]        # six service days
WOBBLE = [1.00, 0.92, 1.09, 0.96, 1.13, 0.88]             # footfall, day to day

# name, is_veg, fill-points sold per frame at peak, BGR, hour she stops topping up.
# Meat moves ~2x veg -- that is the stall owner's own testimony, not a measurement,
# and it is invented here only so the page has something shaped like her problem.
# Sambal fish gets topped up LATE (17:30), which is the failure this prototype exists
# to catch: the last top-up of the day goes straight in the bin.
DISHES = [
    ("sweet and sour pork",   0, 5.0, (60, 80, 200),  16.0),
    ("curry chicken",         0, 4.8, (40, 130, 215), 16.0),
    ("sambal fish",           0, 4.0, (50, 70, 170),  17.6),
    ("fried egg",             0, 3.6, (90, 200, 235), 16.0),
    ("stir-fried kangkong",   1, 2.4, (60, 120, 60),  15.0),
    ("long beans",            1, 2.2, (70, 140, 80),  15.0),
    ("cabbage",               1, 1.6, (150, 190, 190), 15.0),
    ("braised beancurd",      1, 2.6, (90, 120, 150), 15.0),
]
N = len(DISHES)
BOX = [[20 + i * 182, 60, 165, 270] for i in range(N)]    # matches what we draw
CARD = [1500, 120, 70, 140]


def rush(hour):
    """Her real shape: breakfast, a lunch peak, a dead 13:30-17:00, dinner."""
    if hour < 9.5:   return 0.65
    if hour < 11.5:  return 0.35
    if hour < 13.5:  return 1.00
    if hour < 17.0:  return 0.08
    return 0.70


def slots_for(day_i):
    """Trays 2 and 5 swap on alternate days -- the counterbalanced crossover.
    analyse.py takes day 1 as the baseline and derives the rest."""
    order = list(range(N))
    if day_i % 2 == 1:
        order[1], order[4] = order[4], order[1]
    return order


def draw(fills, order):
    import cv2, numpy as np
    im = np.full((H, W, 3), 58, np.uint8)
    cv2.rectangle(im, (0, 340), (W, H), (78, 74, 72), -1)             # counter front
    for slot in range(N):
        colour = DISHES[order[slot]][3]
        x, y, w, h = BOX[slot]
        cv2.rectangle(im, (x - 6, y - 6), (x + w + 6, y + h + 6), (188, 188, 192), -1)
        cv2.rectangle(im, (x, y), (x + w, y + h), (112, 112, 118), -1)
        f = fills[slot]
        if f > 0:
            top = int(y + h - h * f / 100.0)
            cv2.rectangle(im, (x + 4, top), (x + w - 4, y + h - 4), colour, -1)
            for k in range(0, w - 20, 17):        # texture, so it is not a flat block
                cv2.circle(im, (x + 14 + k, top + 14 + (k % 26)), 5,
                           tuple(int(c * 0.8) for c in colour), -1)
    cv2.rectangle(im, (CARD[0], CARD[1]), (CARD[0] + CARD[2], CARD[1] + CARD[3]),
                  (128, 128, 128), -1)
    cv2.rectangle(im, (CARD[0], CARD[1]), (CARD[0] + CARD[2], CARD[1] + CARD[3]),
                  (205, 205, 205), 2)
    return im


def build():
    import cv2
    rng = random.Random(7)
    os.makedirs(FRAMES, exist_ok=True)
    per_day = (CLOSE_H - OPEN_H) * 60 // GAP_MIN
    frame_rows = [["seq", "wall", "boottime", "bytes", "wb_locked"]]
    read_rows = [["seq", "tray", "fill_raw", "obscured"]]
    dish_rows = [["day", "slot", "dish", "is_veg"]]
    seq = 0

    for di, day in enumerate(DAYS):
        order = slots_for(di)
        for slot in range(N):
            name, veg = DISHES[order[slot]][0], DISHES[order[slot]][1]
            dish_rows.append([day, slot + 1, name, veg])

        fills = [100.0] * N
        for f in range(per_day):
            mins = OPEN_H * 60 + f * GAP_MIN
            hour = mins / 60.0
            for slot in range(N):
                rate, stop_at = DISHES[order[slot]][2], DISHES[order[slot]][4]
                sold = rate * rush(hour) * WOBBLE[di] * rng.uniform(0.7, 1.3)
                fills[slot] = max(0.0, fills[slot] - sold)
                # A top-up is PARTIAL -- she adds what is prepped, not a fresh tray.
                if fills[slot] < 20 and hour < stop_at:
                    fills[slot] = min(100.0, fills[slot] + 45 + rng.uniform(-6, 6))

            im = draw(fills, order)
            path = os.path.join(FRAMES, "%06d.jpg" % seq)
            cv2.imwrite(path, im)
            frame_rows.append([seq, "%s %02d:%02d:00" % (day, mins // 60, mins % 60),
                               round(1000 + seq * GAP_MIN * 60, 1),
                               os.path.getsize(path), 1])
            for slot in range(N):
                # What the MODEL would report, not the truth: measured MAE ~5 points
                # on 22 Sep, and it answers in steps of 5.
                obs = round(min(100, max(0, fills[slot] + rng.gauss(0, 4))) / 5) * 5
                read_rows.append([seq, slot + 1, float(obs),
                                  1 if rng.random() < 0.03 else 0])
            seq += 1

    with open(os.path.join(FRAMES, "frames.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(frame_rows)
    with open(os.path.join(DEMO, "readings.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(read_rows)
    with open(os.path.join(DEMO, "dishes.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(dish_rows)
    json.dump({"trays": [{"tray": i + 1, "box": BOX[i]} for i in range(N)],
               "grey_card": CARD}, open(os.path.join(DEMO, "layout.json"), "w"), indent=1)
    return seq


def main():
    if "--clean" in sys.argv:
        shutil.rmtree(DEMO, ignore_errors=True)
        return print("removed %s" % DEMO)

    shutil.rmtree(DEMO, ignore_errors=True)
    os.makedirs(DEMO, exist_ok=True)
    n = build()
    # The real analysis scripts, run in demo/ so HERE resolves there and not one
    # directory up beside the real CSVs. Copied fresh every run so they cannot drift.
    for f in ("analyse.py", "report.py"):
        shutil.copy2(os.path.join(HERE, f), os.path.join(DEMO, f))

    env = dict(os.environ, TW_DEMO="1")
    env.pop("TW_FRAMES", None)              # demo/frames, not whatever is exported
    for cmd in (["analyse.py"], ["report.py", "--no-llm"]):
        r = subprocess.run([sys.executable] + cmd, cwd=DEMO, env=env,
                           capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode:
            sys.exit("%s failed" % cmd[0])

    print("\n%d frames over %d days, %d trays -- zero API calls (all pre-cached)."
          % (n, len(DAYS), N))
    print("open: %s" % os.path.join(DEMO, "page.html"))
    print("The page carries a red SYNTHETIC banner. Do not remove it.")


if __name__ == "__main__":
    main()
