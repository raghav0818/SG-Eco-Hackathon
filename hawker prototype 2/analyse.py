#!/usr/bin/env python3
"""Tray Watch analysis -- runs on the laptop, never at the stall.

    python analyse.py            # frames/ -> readings.csv -> daily.csv
    python analyse.py --selftest # the noise chain, no API, no frames

Reads `frames/` + `dishes.csv`, writes `readings.csv` (one row per frame per tray,
`fill_raw` kept beside the smoothed `fill`) and `daily.csv` (one row per dish-day).

WHICH NUMBERS ARE EXACT, AND WHICH ARE NOT  [MEASURED -- design_checks.py C4/C6]
    leftover_close   EXACT. A level read at close: no refill, no lag, no threshold
                     between it and the truth. +/-0.0 fill-points at any frame rate.
    cooked_total     LOW BY ~9.5%, ALWAYS DOWNWARD, and no filter fixes it. A refill
    served_total     is instantaneous; the 3-frame median only reveals it two frames
    over_provision   later; sales continue through the lag. Four fixes were measured
                     and three made it worse -- the bias is in the signal. At a 6-min
                     analysis gap it is -23%, which is why EVERY frame is analysed.

So: the paper page leads with leftover, and cooked appears only in rounded trays.
Do not "improve" the filter here without re-running design_checks.py.
"""
import csv, json, os, statistics as st, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE     = os.path.dirname(os.path.abspath(__file__))
FRAMES   = os.environ.get("TW_FRAMES") or os.path.join(HERE, "frames")
DISHES   = os.path.join(HERE, "dishes.csv")
READINGS = os.path.join(HERE, "readings.csv")
DAILY    = os.path.join(HERE, "daily.csv")
LAYOUT   = os.path.join(HERE, "layout.json")
MODEL    = os.environ.get("TW_MODEL", "gemini-2.5-flash")
WORKERS  = int(os.environ.get("TW_WORKERS", "8"))

MIN_DROP, REFILL_JUMP = 3, 10     # fill-points. Calibration knobs -- tune against the
                                  # real stall, then re-run design_checks.py.

# ---------------------------------------------------------------- the noise chain

def smooth(raw):
    """3-frame rolling median -> monotonic clamp -> refill threshold.

    The clamp is free accuracy: food does not appear in a tray except when someone
    refills it, so an upward move below REFILL_JUMP is model error BY DEFINITION and
    can be discarded without a judgement call.

    THE MEDIAN LAGS BY ONE FRAME (~2 min), and that is the price of resisting a
    single bad reading. It lands on two outputs and on neither does it matter at the
    resolution of the claim: `leftover_close` becomes the median of the closing
    frames (more robust, and flat at close anyway -- design_checks.py C6 measures it
    unbiased), and `sold_out_ts` reads ~2 min LATE. Do not "fix" the lag by shrinking
    the window: design_checks.py C4 shows the same lag under-sizes every refill by
    ~9.5%, four fixes were measured, and three made it worse.

    Returns (levels, refills) with refills as [(index, size), ...]."""
    if not raw:
        return [], []
    med = [raw[0]] + [st.median(raw[max(0, i - 2):i + 1]) for i in range(1, len(raw))]
    levels, refills, prev = [med[0]], [], med[0]
    for i in range(1, len(med)):
        s = med[i]
        d = s - prev
        if d > REFILL_JUMP:
            refills.append((i, d))
        elif d >= -MIN_DROP:
            s = min(s, prev)
        prev = s
        levels.append(s)
    return levels, refills


def day_totals(raw):
    """One tray, one day. `cooked` and `served` carry the -9.5% documented above."""
    levels, refills = smooth(raw)
    if not levels:
        return None
    cooked = levels[0] + sum(size for _, size in refills)
    return {
        "fill_open":      levels[0],
        "leftover_close": levels[-1],                      # exact
        "cooked_total":   cooked,                          # lower bound
        "served_total":   cooked - levels[-1],             # lower bound
        "refills":        len(refills),
        "last_refill_i":  refills[-1][0] if refills else None,
        "sold_out_i":     next((i for i, v in enumerate(levels) if v <= 0), None),
        "levels":         levels,
    }


# ---------------------------------------------------------------- the vision calls

# Gemini, not Claude: the key Raghav has is a Gemini one. Reading how full a tray is
# is perception, so 2.5 Flash with thinking OFF is both the right tool and ~13x cheaper
# (US$2 a week against US$26). THINKING_BUDGET is the knob: 0 = off, -1 = dynamic.
THINK = {"low": 0, "medium": -1}


def _client():
    from google import genai
    return genai.Client()          # reads GEMINI_API_KEY from the environment


def _img(path):
    from google.genai import types
    return types.Part.from_bytes(data=open(path, "rb").read(), mime_type="image/jpeg")


def _ask(client, content, schema, effort="low"):
    r = client.models.generate_content(
        model=MODEL, contents=content,
        config={"response_mime_type": "application/json", "response_schema": schema,
                "thinking_config": {"thinking_budget": THINK[effort]},
                "max_output_tokens": 4000})
    # A safety block or a hit output cap returns text=None, not an exception. Raise so
    # the per-frame handler logs this frame and the other 1,439 still get written.
    if not r.text:
        raise RuntimeError("empty response (%s)" % getattr(r, "prompt_feedback", ""))
    return json.loads(r.text)


LAYOUT_SCHEMA = {
    "type": "object",
    "properties": {
        "trays": {"type": "array", "items": {
            "type": "object",
            "properties": {"tray": {"type": "integer"},
                           "box": {"type": "array", "items": {"type": "integer"},
                                   "minItems": 4, "maxItems": 4}},
            "required": ["tray", "box"]}},
        "grey_card": {"type": "array", "items": {"type": "integer"},
                      "minItems": 4, "maxItems": 4},
    },
    # grey_card is NOT required: if no card is in frame the model must OMIT it,
    # not point it at the greyest thing it can find. A stainless tray rim passes
    # for a card, changes colour with the food in the tray, and would fill
    # neighbour_contrast with plausible garbage and no error.
    "required": ["trays"],
}

FILL_SCHEMA = {
    "type": "object",
    "properties": {"trays": {"type": "array", "items": {
        "type": "object",
        "properties": {"tray": {"type": "integer"},
                       "fill": {"type": "integer"},
                       "obscured": {"type": "boolean"}},
        "required": ["tray", "fill", "obscured"]}}},
    "required": ["trays"],
}


def read_layout(client, path):
    """The tray count is READ, never configured. Every document in this repo said
    '8 trays' and nobody had counted them."""
    return _ask(client, [_img(path),
        "This is a cai png stall's display tray row. Number the food trays 1..N from "
        "LEFT to RIGHT and give each one's bounding box as [x,y,width,height] in "
        "pixels. Also give `grey_card`: the bounding box of the printed grey or white "
        "reference card taped in the row. If there is NO such card, OMIT grey_card "
        "entirely -- do not substitute a grey-looking object such as a tray rim or "
        "the counter. Count only food trays; the card is not a tray."],
        LAYOUT_SCHEMA, effort="medium")


def read_fills(client, path, n):
    return _ask(client, [_img(path),
        "This is a cai png display tray row with exactly %d food trays, numbered 1..%d "
        "from LEFT to RIGHT. For each tray give `fill`: how full it is, 0 = empty metal, "
        "100 = heaped as at opening, in steps of 5. Set `obscured` true if a hand, arm, "
        "serving spoon or customer hides that tray -- an obscured tray is dropped, and "
        "guessing its fill invents a phantom refill two frames later." % (n, n)],
        FILL_SCHEMA)


# ---------------------------------------------------------------- colour

def dish_lab(path, box, card):
    """Median CIELAB of a tray, grey-card normalised.
    cv2.cvtColor on float32 -- NEVER PIL.Image.convert("LAB"), which does not raise
    and is wrong by dE ~180 (CLAUDE.md trap 6, [VERIFIED])."""
    import cv2, numpy as np
    im = cv2.imread(path).astype(np.float32) / 255.0
    cx, cy, cw, ch = card
    ref = im[cy:cy + ch, cx:cx + cw].reshape(-1, 3).mean(axis=0)
    if (ref <= 0).any() or (ref >= 0.99).any():
        return None      # card in shadow, or blown out under the lamp: a saturated
                         # channel has lost the ratio this normalisation needs.
    im = np.clip(im / ref * ref.mean(), 0, 1)         # per-channel white balance
    x, y, w, h = box
    crop = im[y:y + h, x:x + w]
    if crop.size == 0:
        return None
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).reshape(-1, 3)
    return [float(v) for v in np.median(lab, axis=0)]


def de(a, b):
    return None if a is None or b is None else sum((p - q) ** 2 for p, q in zip(a, b)) ** 0.5


# ---------------------------------------------------------------- plumbing

def load_frames():
    rows = list(csv.DictReader(open(os.path.join(FRAMES, "frames.csv"))))
    out = []
    for r in rows:
        if int(r["bytes"] or 0) <= 0:                 # bytes=0 means the camera failed
            continue                                  # that cycle: a gap, not a zero
        p = os.path.join(FRAMES, "%06d.jpg" % int(r["seq"]))
        if os.path.exists(p):
            out.append({"seq": int(r["seq"]), "day": r["wall"][:10], "wall": r["wall"],
                        "path": p, "wb": r.get("wb_locked", "")})
    return out


def load_dishes():
    """day,slot,dish,is_veg -- filled in once a day by Raghav, never by her (05 4.2).
    Dish identity cannot come from the frames: matching dishes by colour would use
    the very variable the side arm measures."""
    if not os.path.exists(DISHES):
        return None
    d = defaultdict(dict)
    for r in csv.DictReader(open(DISHES)):
        d[r["day"]][int(r["slot"])] = (r["dish"].strip(),
                                       str(r.get("is_veg", "")).strip().lower()
                                       in ("1", "true", "yes", "y"))
    return d


def cached_readings():
    if not os.path.exists(READINGS):
        return {}
    out = defaultdict(dict)
    for r in csv.DictReader(open(READINGS)):
        if r["fill_raw"] == "":      # a blank is an absent reading, not a zero, and
            continue                 # smooth() cannot compare None to a float
        out[int(r["seq"])][int(r["tray"])] = (float(r["fill_raw"]), r["obscured"] == "1")
    return out


def main():
    frames = load_frames()
    if not frames:
        sys.exit("no usable frames in %s -- run capture.py first" % FRAMES)
    # Built on FIRST USE, not up front. A fully-cached run -- layout.json on disk and
    # every frame already in readings.csv -- then needs no key, no network and no
    # google-genai installed at all. That makes a resumed run after a crash free, and
    # it is what lets demo_week.py drive the real analysis chain with no API access.
    _c = {}
    def client():
        if "c" not in _c:
            _c["c"] = _client()
        return _c["c"]

    # Cached: the layout costs a call, never changes mid-week, and report.py needs
    # the boxes to crop a single tray out of the two photographs.
    if os.path.exists(LAYOUT):
        layout = json.load(open(LAYOUT))
    else:
        layout = read_layout(client(), frames[0]["path"])
        json.dump(layout, open(LAYOUT, "w"), indent=1)
    boxes  = {t["tray"]: t["box"] for t in layout["trays"]}
    n      = len(boxes)
    if n == 0:
        # A zero-tray layout makes the `!= n` test below vacuously false for EVERY
        # frame, so nothing is queued, no fill call is ever made, readings.csv is
        # never written -- and this used to exit 0 announcing "wrote daily.csv".
        # Confident fake success in the flattering direction, the same defect §5.5
        # already carries one of. Delete the cache on the way out: otherwise the
        # empty layout is reused forever and fixing the crop changes nothing.
        os.remove(LAYOUT)
        sys.exit("frame %s shows NO TRAYS, so nothing was read and no fill call was "
                 "made. The crop probably does not contain the tray row: run "
                 "`python3 capture.py --check` and look at check.jpg. layout.json "
                 "has been deleted, so the next run asks again instead of silently "
                 "re-reading the empty answer." % os.path.basename(frames[0]["path"]))
    print("frame 1 shows %d trays (READ off the frame, not configured)" % n)

    have, todo = cached_readings(), []
    for f in frames:
        if len(have.get(f["seq"], {})) != n:
            todo.append(f)
    # gemini-2.5-flash: ~1.1k input tok @ $0.30/MTok + ~250 out @ $2.50/MTok, thinking
    # OFF for fills. ESTIMATED, not measured -- check the real spend after day 1.
    print("%d frames, %d already read, %d to call (~US$%.2f, input+output)"
          % (len(frames), len(frames) - len(todo), len(todo), len(todo) * 0.001))

    def save():
        """Rewrite readings.csv from `have`. Called in a finally, so a crash, a
        Ctrl-C or an API outage at frame 1000 keeps the 999 already paid for."""
        with open(READINGS + ".tmp", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["seq", "tray", "fill_raw", "obscured"])
            for s in sorted(have):
                for tray in sorted(have[s]):
                    v, ob = have[s][tray]
                    w.writerow([s, tray, "" if v is None else v, int(ob)])
        os.replace(READINGS + ".tmp", READINGS)   # atomic: never a half-written file

    if todo:
        client()          # warm it single-threaded before the pool races for it
        def one(f):
            # One bad frame must not discard the whole batch: ex.map re-raises on
            # iteration, so an unguarded call means 1000 paid-for readings are lost
            # because the 1001st timed out. Failures are simply left un-cached and
            # retried on the next run.
            try:
                return f, read_fills(client(), f["path"], n)
            except Exception as e:                # noqa: BLE001 - any failure is a skip
                print("  seq %06d failed: %s" % (f["seq"], e), file=sys.stderr)
                return f, None
        try:
            with ThreadPoolExecutor(WORKERS) as ex:
                for f, res in ex.map(one, todo):
                    if res is None:
                        continue
                    got = {t["tray"]: t for t in res["trays"]}
                    if len(got) != n:
                        print("  seq %06d returned %d trays, expected %d -- dropped"
                              % (f["seq"], len(got), n), file=sys.stderr)
                        continue
                    have[f["seq"]] = {k: (max(0.0, min(100.0, float(v["fill"]))),
                                          bool(v["obscured"])) for k, v in got.items()}
        finally:
            save()
        missing = len(todo) - sum(1 for f in todo if f["seq"] in have)
        if missing:
            print("%d frame(s) still unread -- re-run to retry just those" % missing,
                  file=sys.stderr)

    dishes = load_dishes()
    days   = sorted({f["day"] for f in frames})
    base   = dishes.get(days[0]) if dishes else None

    rows = []
    for day in days:
        fs = [f for f in frames if f["day"] == day]
        today = dishes.get(day) if dishes else None
        # Arrangement is DERIVED, not typed in -- so K8 ("did she keep to the
        # schedule?") is audited by the camera and nobody self-reports it.
        arrangement = ("unknown" if not (today and base)
                       else "baseline" if today == base else "rearranged")
        labs = {}
        for tray in sorted(boxes):
            # [(frame, fill)] -- the frame travels WITH its reading. `raw` is SHORTER
            # than `fs` (missing readings are skipped, and obscured frames before the
            # first good one append nothing), so indexing `fs` with a `raw`-space index
            # reports every timestamp EARLY -- by 20 min in a 12-frame test, and far
            # worse at the 2-min cadence. last_refill_ts is the project's sharpest
            # output; it has to be the right clock.
            samples, ob = [], 0
            for f in fs:
                v = have.get(f["seq"], {}).get(tray)
                if v is None or v[0] is None:    # a blank fill_raw is not a zero
                    continue
                fill, obscured = v
                if obscured:                     # drop it; carry the last good level
                    ob += 1
                    if samples:
                        samples.append((f, samples[-1][1]))
                else:
                    samples.append((f, fill))
            t = day_totals([fill for _, fill in samples])
            if t is None:
                continue
            at = lambda i: samples[i][0] if i is not None else None
            card = layout.get("grey_card")
            labs[tray] = (dish_lab(fs[0]["path"], boxes[tray], card) if card
                          else None)   # no card -> blank contrast, never a guess
            dish, veg = (today or {}).get(tray, ("slot%d" % tray, ""))
            rows.append({
                "day": day, "slot": tray, "dish": dish, "is_veg": int(veg) if veg != "" else "",
                "arrangement": arrangement, "n_frames": len(samples), "obscured": ob,
                "fill_open": t["fill_open"], "leftover_close": t["leftover_close"],
                "cooked_total": t["cooked_total"], "served_total": t["served_total"],
                "over_provision": (None if t["served_total"] <= 0 else
                                   round(100.0 * t["leftover_close"] / t["served_total"], 1)),
                "refills": t["refills"],
                "last_refill_ts": (at(t["last_refill_i"]) or {}).get("wall", ""),
                # FIRST empty frame, not necessarily a sell-out: with a 19:00 close
                # an empty tray at 14:30 is usually the afternoon lull before dinner.
                # Diagnostic only -- it never reaches the page.
                "sold_out_ts":    (at(t["sold_out_i"])    or {}).get("wall", ""),
                # The exact frames the two photographs must come from. report.py must
                # not re-derive "first and last of the day": capture runs from boot to
                # the shutdown cron, so the day's first frame can predate prep and be
                # captioned "Opening" over an empty rack.
                "open_seq": samples[0][0]["seq"], "close_seq": samples[-1][0]["seq"],
                "open_ts":  samples[0][0]["wall"][11:16],
                "close_ts": samples[-1][0]["wall"][11:16],
                "wb_locked": fs[0]["wb"],
            })
        for r in rows:
            if r["day"] != day:
                continue
            l, rt = labs.get(r["slot"] - 1), labs.get(r["slot"] + 1)
            ds = [d for d in (de(labs.get(r["slot"]), l), de(labs.get(r["slot"]), rt)) if d is not None]
            r["neighbour_contrast"] = round(sum(ds) / len(ds), 1) if ds else ""

    cols = ["day", "slot", "dish", "is_veg", "arrangement", "n_frames", "obscured",
            "fill_open", "leftover_close", "cooked_total", "served_total",
            "over_provision", "refills", "last_refill_ts", "sold_out_ts",
            "open_seq", "close_seq", "open_ts", "close_ts",
            "neighbour_contrast", "wb_locked"]
    with open(DAILY, "w", newline="") as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    print("wrote %s (%d dish-days) and %s" % (DAILY, len(rows), READINGS))
    if not dishes:
        print("\nNOTE: no dishes.csv, so dishes are 'slot1..slotN' and arrangement is "
              "'unknown'.\nWrite one -- day,slot,dish,is_veg -- to name dishes and let "
              "the camera audit the\narrangement schedule. The waste ledger works "
              "without it; the side arm does not.")
    bad = [d for d in days if not any(r["day"] == d and r["n_frames"] > 3 for r in rows)]
    if bad:
        print("DAYS WITH ALMOST NO FRAMES (a camera gap, NOT a quiet day): %s" % bad,
              file=sys.stderr)


def selftest():
    a, refills = smooth([100, 98, 95, 92, 60, 58, 55])
    assert refills == [] and a == sorted(a, reverse=True), (a, refills)

    lv, rf = smooth([100, 80, 60, 40, 90, 88, 85, 83])     # a clear refill
    assert len(rf) == 1, rf
    t = day_totals([100, 80, 60, 40, 90, 88, 85, 83])
    # leftover_close is the MEDIAN of the closing frames (85), not the last raw
    # reading (83) -- the chain ends in a 3-frame median. That is deliberate and it
    # is what design_checks.py C6 measures as unbiased: at close the tray is flat, so
    # the median is the more robust level read. It lags ~one frame only if she is
    # still selling hard at the bell, which is the case that does not happen.
    assert t["leftover_close"] == 85 and t["refills"] == 1, t
    assert t["cooked_total"] > 100, t                       # refill counted as cooked

    up = smooth([50, 50, 54, 52, 50])[0]                    # drift below REFILL_JUMP
    assert max(up) <= 50, up                                # clamped away as model error

    assert day_totals([]) is None
    t = day_totals([40])
    assert t["leftover_close"] == 40 and t["cooked_total"] == 40 and t["served_total"] == 0

    t = day_totals([100, 70, 40, 10, 0, 0])
    assert t["sold_out_i"] == 5, t         # raw hits 0 at 4; the median says 5, ~2 min
    assert t["sold_out_i"] == next(i for i, v in enumerate(t["levels"]) if v <= 0)
    assert de([0, 0, 0], [0, 3, 4]) == 5.0
    assert de(None, [0, 0, 0]) is None                      # a missing colour is not 0
    # A card the model was FORCED to return is worse than no colour arm at all.
    assert "grey_card" not in LAYOUT_SCHEMA["required"]

    # Gemini's response_schema is an OpenAPI 3.0 subset and REJECTS
    # additionalProperties with a 400. This is the one failure the stubs cannot catch,
    # so catch it here rather than on day 1 with the camera already mounted.
    assert "additionalProperties" not in json.dumps([LAYOUT_SCHEMA, FILL_SCHEMA])
    assert set(THINK) == {"low", "medium"}, "every _ask effort must map to a budget"

    print("ok  |  clamp discards sub-threshold rises, refills counted once, sold-out "
          "is the FIRST zero, schemas are Gemini-legal, empty days do not crash")


if __name__ == "__main__":
    # A typo'd --selftest must not start spending money on 1,980 API calls.
    bad = [a for a in sys.argv[1:] if a != "--selftest"]
    if bad:
        sys.exit("unknown argument %s. Use --selftest, or nothing to analyse." % bad[0])
    selftest() if "--selftest" in sys.argv else main()
