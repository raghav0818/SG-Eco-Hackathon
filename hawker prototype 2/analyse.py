#!/usr/bin/env python3
"""Tray Watch analysis -- runs on the laptop, never at the stall.

    python analyse.py            # frames/ -> readings.csv -> daily.csv
    python analyse.py --selftest # the noise chain, no API, no frames

Reads `frames/` + a time-block roster in `dishes.csv`, writes `readings.csv`
and `daily.csv` (one row per dish-day, with source frame references).

All fill numbers are camera estimates, not food mass or measured waste. The
synthetic simulation in design_checks.py measures filter behaviour, not field
vision accuracy.
    cooked_total     LOW BY ~9.5%, ALWAYS DOWNWARD, and no filter fixes it. A refill
    served_total     is instantaneous; the 3-frame median only reveals it two frames
    over_provision   later; sales continue through the lag. Four fixes were measured
                     and three made it worse -- the bias is in the signal. At a 6-min
                     analysis gap it is -23%, which is why EVERY frame is analysed.

So: the paper page leads with leftover, and cooked appears only in rounded trays.
Do not "improve" the filter here without re-running design_checks.py.
"""
import argparse, csv, datetime as dt, json, os, statistics as st, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        "leftover_close": levels[-1],                      # final smoothed camera estimate
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


def load_dishes(slots=None):
    """Return ordered, complete time-block maps. Missing days remain unmapped.

    A legacy four-column roster is treated as one block at midnight so the
    synthetic rehearsal continues to use the same analysis chain.
    """
    if not os.path.exists(DISHES):
        return None
    blocks = defaultdict(dict)
    with open(DISHES, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not {"day", "slot", "dish", "is_veg"} <= set(reader.fieldnames or []):
            raise ValueError("dishes.csv needs day,block,from_ts,slot,dish,is_veg")
        has_blocks = {"block", "from_ts"} <= set(reader.fieldnames or [])
        if ("block" in (reader.fieldnames or [])) != ("from_ts" in (reader.fieldnames or [])):
            raise ValueError("dishes.csv needs both block and from_ts")
        for line, r in enumerate(reader, 2):
            day = r["day"].strip()
            try:
                dt.date.fromisoformat(day)
                start = (r["from_ts"].strip() if has_blocks else "00:00")
                if dt.datetime.strptime(start, "%H:%M").strftime("%H:%M") != start:
                    raise ValueError("from_ts must be HH:MM")
                slot = int(r["slot"])
            except (ValueError, TypeError) as exc:
                raise ValueError("invalid date, from_ts or slot on dishes.csv line %d" % line) from exc
            block = r["block"].strip() if has_blocks else "all"
            dish = r["dish"].strip()
            veg = r["is_veg"].strip().lower()
            if not block or not dish or slot < 1 or veg not in ("0", "1", "true", "false", "yes", "no", "y", "n"):
                raise ValueError("invalid block, dish, slot or is_veg on dishes.csv line %d" % line)
            key = (block, start)
            mapping = blocks[day].setdefault(key, {})
            if slot in mapping or any(v[0] == dish for v in mapping.values()):
                raise ValueError("duplicate slot or dish in %s block %s" % (day, block))
            mapping[slot] = (dish, veg in ("1", "true", "yes", "y"))
    result = {}
    for day, items in blocks.items():
        names = [name for name, _ in items]
        starts = [start for _, start in items]
        if len(set(names)) != len(names) or len(set(starts)) != len(starts):
            raise ValueError("duplicate block name or start on %s" % day)
        ordered = sorted(((start, name, mapping) for (name, start), mapping in items.items()))
        if slots is not None:
            for start, name, mapping in ordered:
                if set(mapping) != set(slots):
                    raise ValueError("%s block %s at %s must map every layout slot" % (day, name, start))
        result[day] = ordered
    return result


def active_block(roster, frame):
    """A frame before the first recorded block has unknown dish identity."""
    return next((b for b in reversed(roster or []) if frame["wall"][11:16] >= b[0]), None)


def cached_readings():
    if not os.path.exists(READINGS):
        return {}
    out = defaultdict(dict)
    for r in csv.DictReader(open(READINGS)):
        if r["fill_raw"] == "":      # a blank is an absent reading, not a zero, and
            continue                 # smooth() cannot compare None to a float
        out[int(r["seq"])][int(r["tray"])] = (float(r["fill_raw"]), r["obscured"] == "1")
    return out


def aggregate_daily(frames, have, layout, dishes):
    """Aggregate each dish/day through its observed, contiguous roster blocks.

    A move starts a new filter segment. Its first fill is not counted as a refill
    or extra cooking when the dish was present in the immediately prior block.
    Removed dishes keep their last observed fill but have no closing leftover.
    """
    boxes = {t["tray"]: t["box"] for t in layout["trays"]}
    by_day = defaultdict(list)
    for f in frames:
        by_day[f["day"]].append(f)
    first_day = min(by_day)
    base = dishes.get(first_day, []) if dishes else []
    base_map = base[0][2] if base else None
    rows = []
    for day, fs in sorted(by_day.items()):
        fs.sort(key=lambda f: (f["wall"], f["seq"]))
        roster = (dishes or {}).get(day, [])
        last_block = active_block(roster, fs[-1])
        group_frames = defaultdict(list)
        for f in fs:
            block = active_block(roster, f)
            start = block[0] if block else "unknown"
            group_frames[start].append(f)
        segments_by_dish = defaultdict(list)
        contrast_by_dish = defaultdict(list)
        for start, block_fs in sorted(group_frames.items()):
            block = active_block(roster, block_fs[0])
            mapping = block[2] if block else {}
            labs = {}
            card = layout.get("grey_card")
            if card:
                for slot in boxes:
                    labs[slot] = dish_lab(block_fs[0]["path"], boxes[slot], card)
            for slot in sorted(boxes):
                dish, veg = mapping.get(slot, ("slot%d" % slot, ""))
                samples, obscured_count = [], 0
                for f in block_fs:
                    reading = have.get(f["seq"], {}).get(slot)
                    if reading is None or reading[0] is None:
                        continue
                    fill, obscured = reading
                    if obscured:
                        obscured_count += 1
                        if samples:
                            samples.append((f, samples[-1][1]))
                    else:
                        samples.append((f, fill))
                totals = day_totals([fill for _, fill in samples])
                if totals is None:
                    continue
                neighbour_values = [de(labs.get(slot), labs.get(other))
                    for other in (slot - 1, slot + 1)]
                neighbour_values = [v for v in neighbour_values if v is not None]
                if neighbour_values:
                    contrast_by_dish[dish].append(sum(neighbour_values) / len(neighbour_values))
                segments_by_dish[dish].append({
                    "block": block[1] if block else "unknown", "start": start,
                    "slot": slot, "veg": veg, "samples": samples, "totals": totals,
                    "obscured": obscured_count, "mapped": bool(block),
                })
        for dish, segments in segments_by_dish.items():
            segments.sort(key=lambda s: (s["samples"][0][0]["wall"], s["slot"]))
            first, last = segments[0], segments[-1]
            mapped = all(s["mapped"] for s in segments)
            close_mapped = last_block and any(value[0] == dish for value in last_block[2].values())
            left_at_close = bool(mapped and close_mapped and last["start"] == last_block[0])
            # A roster gap or intervening block in which a dish was absent makes
            # its return a new opening; adjacent moves do not create new cooking.
            cooked = 0.0
            served = 0.0
            refills = 0
            refill_ts = ""
            sold_out_ts = ""
            previous_index = None
            for s in segments:
                t, samples = s["totals"], s["samples"]
                current_index = next((i for i, b in enumerate(roster) if b[0] == s["start"]), None)
                contiguous = (previous_index is not None and current_index == previous_index + 1)
                if not contiguous:
                    cooked += t["fill_open"]
                cooked += t["cooked_total"] - t["fill_open"]
                served += t["served_total"]
                refills += t["refills"]
                if t["last_refill_i"] is not None:
                    refill_ts = samples[t["last_refill_i"]][0]["wall"]
                if not sold_out_ts and t["sold_out_i"] is not None:
                    sold_out_ts = samples[t["sold_out_i"]][0]["wall"]
                previous_index = current_index
            last_fill = last["totals"]["leftover_close"]
            close_fill = last_fill if left_at_close else ""
            contrasts = contrast_by_dish[dish]
            rows.append({
                "day": day, "slot": last["slot"], "dish": dish,
                "is_veg": int(first["veg"]) if first["veg"] != "" else "",
                "mapping_status": "mapped" if mapped else "unknown",
                "left_at_close": int(left_at_close),
                "open_slot": first["slot"], "close_slot": last["slot"] if left_at_close else "",
                "segments": len(segments), "last_observed_fill": last_fill,
                "totals_scope": "single_segment" if len(segments) == 1 else "observed_segments_only",
                "arrangement": ("unknown" if not mapped or base_map is None else
                    "baseline" if all(s["slot"] == next((slot for slot, v in base_map.items()
                    if v[0] == dish), None) for s in segments) else "rearranged"),
                "n_frames": sum(len(s["samples"]) for s in segments),
                "obscured": sum(s["obscured"] for s in segments),
                "fill_open": first["totals"]["fill_open"],
                "leftover_close": close_fill,
                "cooked_total": round(cooked, 1), "served_total": round(served, 1),
                "over_provision": (round(100 * last_fill / served, 1)
                    if left_at_close and served > 0 and len(segments) == 1 else ""),
                "refills": refills, "last_refill_ts": refill_ts,
                "sold_out_ts": sold_out_ts,
                "open_seq": first["samples"][0][0]["seq"],
                "close_seq": last["samples"][-1][0]["seq"],
                "open_ts": first["samples"][0][0]["wall"][11:16],
                "close_ts": last["samples"][-1][0]["wall"][11:16],
                # A single dish/day contrast would hide a changed neighbour at
                # the swap. Leave it unavailable until block rows are exposed.
                "neighbour_contrast": round(contrasts[0], 1)
                    if len(segments) == 1 and contrasts else "",
                "wb_locked": first["samples"][0][0]["wb"],
            })
    return rows


def main(cancel_file=None):
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
                completed = 0
                succeeded = 0
                # Submit one bounded batch. A cancelled job cannot leave hundreds
                # of queued paid calls behind, and each batch reaches disk first.
                for offset in range(0, len(todo), max(1, WORKERS)):
                    if cancel_file and os.path.exists(cancel_file):
                        print("CANCELLED after %d of %d frame calls" % (completed, len(todo)),
                              flush=True)
                        return 130
                    batch = todo[offset:offset + max(1, WORKERS)]
                    futures = {ex.submit(one, f): f for f in batch}
                    for future in as_completed(futures):
                        f, res = future.result()
                        completed += 1
                        if res is None:
                            continue
                        got = {t["tray"]: t for t in res["trays"]}
                        if len(got) != n or set(got) != set(boxes):
                            print("  seq %06d returned incorrect trays -- dropped" % f["seq"],
                                  file=sys.stderr)
                            continue
                        have[f["seq"]] = {k: (max(0.0, min(100.0, float(v["fill"]))),
                                              bool(v["obscured"])) for k, v in got.items()}
                        succeeded += 1
                    save()
                    print("PROGRESS " + json.dumps({"total": len(frames),
                        "cached": len(frames) - len(todo), "completed": completed,
                        "succeeded": succeeded, "failed": completed - succeeded,
                        "remaining": len(todo) - completed}), flush=True)
        finally:
            save()
        missing = len(todo) - sum(1 for f in todo if f["seq"] in have)
        if missing:
            print("%d frame(s) still unread -- re-run to retry just those" % missing,
                  file=sys.stderr)

    dishes = load_dishes(boxes)
    rows = aggregate_daily(frames, have, layout, dishes)

    cols = ["day", "slot", "dish", "is_veg", "mapping_status", "left_at_close",
            "open_slot", "close_slot", "segments", "last_observed_fill", "totals_scope",
            "arrangement", "n_frames", "obscured",
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
        print("NOTE: no dishes.csv. Slot-only rows are unmapped and ineligible for reports.")
    days = sorted({f["day"] for f in frames})
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

    # At a 14:35 swap the rise in slot 1 belongs to a different dish. A new
    # roster block resets the filter; neither dish gets a false refill.
    frames = [{"seq": i, "day": "2026-09-22", "wall": "2026-09-22 %s:00" % clock,
               "path": "unused", "wb": "1"}
              for i, clock in enumerate(("14:30", "14:32", "14:36", "14:38", "14:42"))]
    have = {
        0: {1: (10, False), 2: (60, False)},
        1: {1: (10, False), 2: (60, False)},
        2: {1: (90, False), 2: (60, False)},
        3: {1: (85, False), 2: (50, False)},
        4: {1: (80, False), 2: (45, False)},
    }
    roster = {"2026-09-22": [
        ("08:00", "am", {1: ("greens", True), 2: ("chicken", False)}),
        ("14:35", "pm", {1: ("chicken", False), 2: ("greens", True)}),
    ]}
    aggregate = aggregate_daily(frames, have, {"trays": [
        {"tray": 1, "box": [0, 0, 1, 1]}, {"tray": 2, "box": [1, 0, 1, 1]}]}, roster)
    by_dish = {r["dish"]: r for r in aggregate}
    assert by_dish["greens"]["refills"] == 0 and by_dish["chicken"]["refills"] == 0
    assert by_dish["greens"]["open_slot"] == 1 and by_dish["greens"]["close_slot"] == 2
    assert by_dish["greens"]["open_seq"] == 0 and by_dish["greens"]["close_seq"] == 4
    assert by_dish["greens"]["left_at_close"] == 1
    roster["2026-09-22"].append(("14:40", "last", {
        1: ("chicken", False), 2: ("tofu", True)}))
    removed = {r["dish"]: r for r in aggregate_daily(frames, have, {
        "trays": [{"tray": 1, "box": [0, 0, 1, 1]},
                  {"tray": 2, "box": [1, 0, 1, 1]}]}, roster)}
    assert removed["greens"]["left_at_close"] == 0
    assert removed["greens"]["leftover_close"] == ""
    assert removed["greens"]["last_observed_fill"] != ""

    print("ok  |  clamp discards sub-threshold rises, refills counted once, sold-out "
          "is the FIRST zero, swaps and removals keep dish identity")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse captured Tray Watch frames")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--cancel-file", help="stop after current saved batch if this file appears")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        sys.exit(main(args.cancel_file))
