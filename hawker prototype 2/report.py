#!/usr/bin/env python3
"""The A4 page -- the ninety seconds the whole build serves.

    python report.py              # daily.csv -> reports/draft-*.html, one LLM call
    python report.py --no-llm     # same page, arithmetic sentence, no API
    python report.py --selftest   # picking + rendering, no API, no frames

Review the versioned draft before approval. Photos are embedded base64.

Four properties this page must keep (06 section 4):
  1. It is HER stall. Two photographs four hours apart are not a claim, they are the
     thing itself -- a load cell could never have produced this.
  2. It needs almost no English. The photos and the arrow carry the finding.
  3. There is EXACTLY ONE recommendation. Five get zero of them done.
  4. It is free, fast and reversible. Nothing else gets done on a 10-15% margin.

`--no-llm` is not a debug flag. It is the deadline plan: if the API is down on
30 Sep the page still prints, with a sentence built from arithmetic.
"""
import base64, csv, hashlib, html, json, os, sys
from datetime import datetime, timezone
from collections import defaultdict

HERE   = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.environ.get("TW_FRAMES") or os.path.join(HERE, "frames")
DAILY  = os.path.join(HERE, "daily.csv")
LAYOUT = os.path.join(HERE, "layout.json")
CTX    = os.path.join(HERE, "context.md")
REPORTS = os.path.join(HERE, "reports")
MODEL  = os.environ.get("TW_MODEL", "claude-opus-5")

LEVERS = """L1 which dishes sit next to which (free, 30 seconds, at open)
L2 how much of each dish to cook (morning prep)
L3 whether to top up a tray late in service
L4 what size tray a dish goes in
L5 which dishes stay on the menu
L6 how much raw ingredient to buy"""


def pick(rows):
    """The mapped dish with the highest camera-estimated closing fill.
    Not by over_provision, which divides by served_total and inherits its -9.5%."""
    by = defaultdict(list)
    for r in rows:
        if (r.get("mapping_status") == "mapped" and
            r.get("left_at_close") == "1" and
            r.get("leftover_close") not in ("", None)):
            by[r["dish"]].append(r)
    if not by:
        return None, None
    dish = max(by, key=lambda d: sum(float(r["leftover_close"]) for r in by[d]) / len(by[d]))
    worst = max(by[dish], key=lambda r: float(r["leftover_close"]))
    return dish, worst


def photo(seq, box):
    """Crop one tray out of one EXACT frame -- the frame the level was read from,
    named by analyse.py in `open_seq` / `close_seq`.

    Never re-derive "first and last frame of the day" here: capture runs from boot to
    the shutdown cron, so the day's first frame can predate prep and the last can
    postdate clearing. Captioning an empty rack "Opening" would put a contradiction on
    the one sheet the whole build serves."""
    import cv2
    if seq in ("", None):
        return None
    im = cv2.imread(os.path.join(FRAMES, "%06d.jpg" % int(seq)))
    if im is None:
        return None
    if box:
        x, y, w, h = box
        im = im[y:y + h, x:x + w]
    ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return ("data:image/jpeg;base64," + base64.b64encode(buf).decode()) if ok else None


def tray_pct(worst):
    """Camera-estimated fill points, never food mass or waste measured in kg."""
    return round(float(worst["leftover_close"]))


def sentence(dish, worst, rows, use_llm):
    """One finding, one change. Constrained to her six levers, because an
    unconstrained model suggests a loyalty programme."""
    pct = tray_pct(worst)
    late = worst.get("last_refill_ts", "")
    if not use_llm:
        f = "The %s tray looked about %d%% full at close (camera estimate)." % (dish, pct)
        if late:
            f += " You topped it up again at %s." % late[11:16]
        return f, "Try preparing less %s tomorrow." % dish

    from google import genai
    ctx = open(CTX, encoding="utf-8").read() if os.path.exists(CTX) else \
        "(no context.md yet -- she has not been asked what she already knows)"
    table = "\n".join(
        "%s | %s | cooked %s | left at close %s | refills %s | last top-up %s"
        % (r["day"], r["dish"], r["cooked_total"], r["leftover_close"],
           r["refills"], r.get("last_refill_ts", "") or "-")
        for r in rows)
    # This one call IS reasoning -- it weighs six levers against her own words -- so
    # thinking stays dynamic here, unlike the 1,980 perception calls in analyse.py.
    r = genai.Client().models.generate_content(
        model=MODEL,
        config={"response_mime_type": "application/json",
                "thinking_config": {"thinking_budget": -1}, "max_output_tokens": 2000,
                "response_schema": {
                    "type": "object",
                    "properties": {"finding": {"type": "string"},
                                   "recommendation": {"type": "string"}},
                    "required": ["finding", "recommendation"]}},
        contents=["""You write one sheet of A4 for a cai png \
hawker on a 10-15%% net margin who works twelve-hour days. English may not be her first \
language.

WHAT SHE ALREADY KNOWS -- start from this, never restate it back to her:
%s

HER WEEK, in fill-points (100 = a heaped tray at opening):
%s

THE DISH THIS PAGE IS ABOUT: %s, on %s.

Write exactly two things.
`finding`: ONE sentence, plain words, about what appears in the closing photo. \
Call all percentages camera estimates; never claim measured mass or proven waste saved.
`recommendation`: ONE change, phrased as an instruction, that is free, takes under a \
minute, and she can undo tomorrow. It MUST be one of her six levers:
%s

Do not suggest anything outside that list -- no loyalty schemes, no pricing, no new \
dishes, no signage. Do not tell her which dishes sell slowly; she has known for years. \
Note: both `cooked` and `left at close` are camera-based estimates. There is no \
field validation of their accuracy. Do not call them exact.""" % (ctx, table, dish, worst["day"], LEVERS)])
    if not r.text:
        raise RuntimeError("empty response; --no-llm writes the page without this call")
    d = json.loads(r.text)
    return d["finding"], d["recommendation"]


HTML = """<!doctype html><meta charset="utf-8"><title>%(dish)s &mdash; %(day)s</title>
<style>
  @page { size: A4 portrait; margin: 14mm; }
  html { background: #fff; }
  /* background stated explicitly: this is a sheet of paper, and a viewer in dark
     mode would otherwise paint its own ground behind #111 text and lose the page. */
  body { font: 16px/1.5 system-ui, "Segoe UI", Arial, sans-serif; color: #111;
         background: #fff; max-width: 182mm; margin: 0 auto; padding: 8mm 0; }
  h1 { font-size: 34px; margin: 0 0 2mm; text-transform: uppercase; letter-spacing: .02em; }
  .day { color: #666; font-size: 18px; margin-bottom: 8mm; }
  .pair { display: flex; gap: 6mm; }
  .pair figure { flex: 1; margin: 0; }
  .pair img { width: 100%%; border: 1px solid #ddd; display: block; }
  .pair figcaption { margin-top: 2mm; font-size: 15px; }
  .pair b { font-size: 21px; display: block; }
  .finding { font-size: 21px; margin: 9mm 0 7mm; }
  .rec { font-size: 25px; font-weight: 700; border-top: 3px solid #111; padding-top: 5mm; }
  .rec span { color: #c0392b; }
  footer { margin-top: 10mm; font-size: 12px; color: #888; }
  .none { border: 1px dashed #bbb; padding: 10mm; text-align: center; color: #888; }
  .demo { background: #c0392b; color: #fff; padding: 4mm 5mm; margin: 0 0 7mm;
          font-size: 15px; line-height: 1.4; }
  .demo b { display: block; font-size: 19px; letter-spacing: .04em; }
</style>
%(banner)s
<h1>%(dish)s</h1><div class="day">%(day)s</div>
<div class="pair">
  <figure>%(img_open)s<figcaption><b>%(t_open)s</b>first observed fill</figcaption></figure>
  <figure>%(img_close)s<figcaption><b>%(t_close)s</b>about %(pct)s%% full, camera estimate</figcaption></figure>
</div>
<p class="finding">%(finding)s</p>
<p class="rec"><span>&#9658;</span> %(rec)s</p>
<footer>Tray Watch &middot; %(source)s &middot; %(ndays)s service days &middot;
Visual estimates from photographs; no food weight or waste saving measured.</footer>
"""


# The dedicated demo checkout gets this banner from its directory provenance.
BANNER = ('<div class="demo"><b>SYNTHETIC DEMONSTRATION &mdash; NOT REAL DATA</b>'
          'These numbers were invented by <code>demo_week.py</code> to rehearse the '
          'page layout before the stall week exists. No tray in this page was '
          'photographed at any stall, and nothing here is a finding.</div>')


def source_kind():
    """Demo provenance comes from the dedicated demo checkout, not page wording."""
    return "synthetic" if os.path.basename(os.path.normpath(HERE)) == "demo" else "field"


def render(dish, worst, rows, finding, rec, img_open, img_close):
    def tag(u):
        if not u:
            return '<div class="none">no photo</div>'
        if not u.startswith("data:image/jpeg;base64,"):
            raise ValueError("report image must be an embedded JPEG")
        return '<img src="%s" alt="Photograph of the tray">' % html.escape(u, quote=True)
    return HTML % {
        "banner": BANNER if source_kind() == "synthetic" else "",
        "dish": html.escape(dish.upper()), "day": html.escape(worst["day"]),
        "img_open": tag(img_open), "img_close": tag(img_close),
        # Real clock times off the frames, so the captions cannot contradict the photos.
        "t_open": html.escape(worst.get("open_ts", "")),
        "t_close": html.escape(worst.get("close_ts", "")),
        "pct": tray_pct(worst),
        "finding": html.escape(finding), "rec": html.escape(rec),
        "ndays": len({r["day"] for r in rows}),
        "source": "SYNTHETIC DEMONSTRATION" if source_kind() == "synthetic" else "field photographs",
    }


def main():
    if not os.path.exists(DAILY):
        sys.exit("no daily.csv -- run analyse.py first")
    with open(DAILY, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or any(r.get("mapping_status") != "mapped" for r in rows):
        sys.exit("report ineligible: each analyzed period needs a complete, time-block dish roster")
    dish, worst = pick(rows)
    if not dish:
        sys.exit("report ineligible: no named dish has an observed closing fill")
    boxes = {}
    if os.path.exists(LAYOUT):
        with open(LAYOUT, encoding="utf-8") as fh:
            boxes = {t["tray"]: t["box"] for t in json.load(fh)["trays"]}
    if int(worst["open_slot"]) not in boxes or int(worst["close_slot"]) not in boxes:
        sys.exit("report ineligible: source tray boxes are missing from layout.json")
    finding, rec = sentence(dish, worst, rows, "--no-llm" not in sys.argv)
    open_img = photo(worst.get("open_seq"), boxes.get(int(worst["open_slot"])))
    close_img = photo(worst.get("close_seq"), boxes.get(int(worst["close_slot"])))
    if not open_img or not close_img:
        sys.exit("report ineligible: source photographs are missing or unreadable")
    page = render(dish, worst, rows, finding, rec, open_img, close_img)
    with open(DAILY, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    os.makedirs(REPORTS, exist_ok=True)
    path = os.path.abspath(os.path.join(REPORTS, "draft-%s-%s.html" % (stamp, digest)))
    with open(path, "x", encoding="utf-8") as fh:
        fh.write(page)
    print("REPORT_PATH=" + path, flush=True)
    print("draft for review: %s, %s; %s" % (dish, worst["day"], finding))


def selftest():
    rows = [
        {"day": "2026-09-22", "slot": "4", "dish": "kangkong", "leftover_close": "60",
         "cooked_total": "100", "served_total": "40", "refills": "2", "last_refill_ts": "2026-09-22 14:15:00",
         "open_seq": "0", "close_seq": "9", "open_ts": "09:05", "close_ts": "15:02",
         "mapping_status": "mapped", "left_at_close": "1"},
        {"day": "2026-09-23", "slot": "4", "dish": "kangkong", "leftover_close": "50",
         "cooked_total": "100", "served_total": "50", "refills": "1", "last_refill_ts": "",
         "mapping_status": "mapped", "left_at_close": "1"},
        {"day": "2026-09-22", "slot": "2", "dish": "curry chicken", "leftover_close": "5",
         "cooked_total": "100", "served_total": "95", "refills": "3", "last_refill_ts": "",
         "mapping_status": "mapped", "left_at_close": "1"},
    ]
    dish, worst = pick(rows)
    assert dish == "kangkong", dish              # mean leftover 55 vs 5
    assert worst["day"] == "2026-09-22", worst   # its own worst day, not the first

    f, r = sentence(dish, worst, rows, use_llm=False)
    assert "60%" in f and "14:15" in f, f        # estimated fill and source top-up time
    # The headline must be leftover-as-%-of-a-tray, NOT leftover/cooked. With a 9.5%-low
    # cooked_total those differ, and only one of them is checkable against the photo.
    assert tray_pct(worst) == 60, tray_pct(worst)
    assert tray_pct({"leftover_close": "50", "cooked_total": "88"}) == 50
    html = render(dish, worst, rows, f, r, None, None)
    assert "KANGKONG" in html and "no photo" in html and "60%" in html
    assert "09:05" in html and "15:02" in html, "captions must carry the real frame times"
    assert html.count("class=\"rec\"") == 1, "more than one recommendation on the page"
    hostile = render("<script>x</script>", dict(worst, day='"<bad>', open_ts='<a>'),
                     rows, '<img src=x onerror=alert(1)>', '<b>wrong</b>', None, None)
    assert "<script>" not in hostile and "<img src=x" not in hostile and "<b>wrong" not in hostile
    assert "&lt;script&gt;" in hostile.lower() and "&lt;b&gt;wrong&lt;/b&gt;" in hostile

    # A day where nothing sold must not divide by zero, and blanks must not crash.
    assert pick([{"dish": "x", "leftover_close": ""}]) == (None, None)
    z = [{"day": "d", "slot": "1", "dish": "x", "leftover_close": "0",
          "mapping_status": "mapped", "left_at_close": "1",
          "cooked_total": "0", "served_total": "0", "refills": "0", "last_refill_ts": ""}]
    d2, w2 = pick(z)
    render(d2, w2, z, *sentence(d2, w2, z, use_llm=False), None, None)
    print("ok  |  picks the worst mapped closing estimate, then its own worst day; "
          "one recommendation; zero-cooked and blank rows do not crash")


if __name__ == "__main__":
    bad = [arg for arg in sys.argv[1:] if arg not in ("--selftest", "--no-llm")]
    if bad:
        sys.exit("unknown argument %s" % bad[0])
    selftest() if "--selftest" in sys.argv else main()
