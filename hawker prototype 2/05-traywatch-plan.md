# Tray Watch — Prototype 2 plan

> Supersedes `BUILD-GUIDE.md` (Stock Clock), archived 18 Sep 2026.
> User journey: `06-traywatch-user-journey.md`. Research unchanged: `03-hawker-5w1h.md`, `04-hawker-journey-map.md`.
>
> **Provenance.** `[testimony]` the stall owner, via Raghav, 17 Sep `[T3]` · `[cited]` public source · `[DERIVED]` · `[ASSUMED]`

---

## Context

Prototype 2 was **Stock Clock** — four load cells under four ingredient trays, weighing raw stock in
and out. Cancelled 17 Sep. Two things killed it, and neither was technical.

**1. The stall owner said the problem is demand, not storage** `[testimony]`:

> *"vegetables often spoil because meat products sell fast… whereas vegetables sell slow… so she had
> to throw a lot of veggies, uncooked ones especially."*

Stock Clock would have measured the rotting perfectly and changed nothing, because the rot is a
*symptom*. The chain runs:

```
students don't pick vegetables
  → cooked veg is left at close
  → she keeps buying at the same rate
  → raw veg sits, gets stacked over, rots
```

Stock Clock attacked the last link. **Tray Watch attacks the first one.**

**2. She preferred the camera when it was put to her.** Stock Clock told her what she was *wasting*.
Tray Watch tells her how to *sell more*. She is on a 10–15% net margin (`04-hawker-journey-map.md`
§4); of course she picked the one that makes money. That is also the pitch: **not a waste tool that
helps sales — a sales tool that cuts waste**, which is why it will still be running in week three.

**End goals, in order:**

1. **Get students to choose the vegetables.**
2. **Reduce what is binned — cooked at close, and raw upstream of it.**

Every data point below traces to one of those through a decision she can actually make. Everything
else is cut.

---

## 1. What it is, in one paragraph

A USB webcam on the sneeze guard above the cai png display, photographing the tray row every two
minutes through service for six days. No screen, no interaction — the stall device is a dumb logger
that happens to be on the stall's WiFi `[T4, 19 Sep]`, which carries frames off it every ten minutes
and keeps its clock honest. **Capture does not depend on that network and must never be allowed to.** Afterwards the frames are analysed off-site: a vision model reads how full each tray is,
and the images themselves yield the **colour of each dish** and therefore the **colour contrast
between neighbouring trays**. That contrast is the thing we manipulate. One LLM call at the end turns
the week's table into recommendations constrained to her actual levers.

It passes every constraint in `04-hawker-journey-map.md` §7, and beats the load cells on two:

| §7 constraint | Stock Clock | Tray Watch |
|---|---|---|
| Zero interaction during service | ✅ | ✅ |
| Zero manual data entry, ever | ✅ | ✅ |
| Survives being ignored | ⚠️ re-taring, knocked trays | ✅ **nothing to maintain** |
| Payback in weeks | ✅ | ✅ |
| **The number must feel like hers** | a reading she has to trust | ✅ **she can look at the photo** |

That last row decides it. §7 closes: *"the measurement has to be theirs, not yours — a number they
trust because it came off their own stall."* You can put the 9am photo of her tray next to the 3pm
photo of the same tray. No load cell can do that, and **it needs no language** — which matters, see
the user journey §4.

---

## 2. Her decision levers

Data that does not move one of these is decoration.

| # | Lever | When she decides |
|---|---|---|
| **L1** | **Which dishes sit next to which** | At open. Free, 30 seconds, fully reversible. **This is the one we test** |
| L2 | How much of each dish to cook | Morning prep |
| L3 | Whether to top up a tray late in service | Continuously, by eye |
| L4 | What size tray a dish goes in | At open |
| L5 | Which dishes stay on the menu | Weekly-ish |
| L6 | How much raw ingredient to buy | Pre-dawn. Highest financial exposure of the day |

---

## 3. The experiment

### 3.1 The intervention: colour contrast, not position

The tested variable is **how different a dish looks from the dishes beside it.** A row of three
similar greens reads as one undifferentiated mass at the speed a student walks past it. The same
greens between an orange curry and a pale tofu register as a distinct thing.

**The design trick that makes this measurable in six days:**

> **The vegetable dishes never move.** Kangkong stays in slot 4 for all six days. What changes is
> **its neighbours.**

That separates colour from position. A position experiment cannot do this — move the dish and you
have changed two things at once, and six days will never tell you which one mattered.

### 3.2 The independent variable is computed from the photographs

Not a judgement call. Per tray, per day:

1. Take the **opening frames** (first 5, median) — tray full, so the crop is food, not bare metal.
2. Convert the crop to **CIELAB** and take the median `L*a*b*`. That is `dish_lab`.
   **Use `cv2.cvtColor(crop_float32, cv2.COLOR_BGR2LAB)`, not Pillow.** `PIL.Image.convert("LAB")`
   does not raise, but it stores a\* and b\* as *signed* bytes rather than offset by +128 — decode it
   the obvious way and the error is ΔE ≈ 180, larger than the entire range of the measurement, and
   the numbers still look plausible. Even decoded correctly it is worst on **green** (ΔE 7.5 vs
   0.01 for OpenCV), which is the one colour this experiment cannot afford to be sloppy about.
   OpenCV is already a dependency for the webcam. Tested — see `07-architecture.md` §4.1.
3. Contrast to a neighbour is **ΔE = Euclidean distance in LAB** — perceptually uniform, which plain
   RGB distance is not.
4. `neighbour_contrast` for a tray = mean of ΔE to its left and right neighbours.

Colour is measured at open, not continuously, because as a tray empties the metal shows through and
drags the mean — a real confound, avoided for free by fixing the measurement at the one moment the
tray is full.

### 3.3 The grey card — do not skip this

**Tape a printed grey/white reference card at the end of the tray row, permanently in frame.**

Without it the colour measurement is worthless: a webcam's auto white balance re-corrects the colour
every frame, and canteen lighting changes between 11am and 3pm and between days. Every frame is
normalised by dividing each channel by the card's channel mean before anything else happens. Three
lines of code and a piece of paper.

Also lock white balance and exposure in `capture.py` (`cv2.CAP_PROP_AUTO_WB = 0`, manual exposure).
Belt and braces — the card corrects what the lock misses.

### 3.4 Six days is 48 data points, not 6

The obvious critique of a one-week study is that three days against three days proves nothing. That
critique applies to a **binary** before/after. It does not apply here, because `neighbour_contrast`
is **continuous, and every dish has one every day**:

- 8 trays × 6 days = **48 dish-days**, each with a measured contrast value and a measured
  `served_total`.
- We *manipulate* it on alternate days to push the range wider.

**Corrected 19 Sep — the headline test is not the 48-point regression.** Those 48 rows carry nowhere
near 48 units of information: arrangement changes by *day*, so day effects (rain, exam week, payday)
are confounded with treatment at the day level, and there are only six days. With a binary arrangement
over six days there are only `C(6,3) = 20` possible day-level assignments, giving a **floor p-value of
2/20 = 0.10 — it can never reach 0.05, however strong the effect is.**

**The headline test is a within-dish sign-flip permutation test, n = 8 dishes.** Difference each
dish's contrast days against its own baseline days — which removes dish identity, popularity, tray
size and position entirely, because the never-move design holds all four constant within a dish — then
enumerate all 2⁸ = 256 sign flips for an exact p-value. Floor p = 0.0078, so it *can* reach
significance. Six lines of numpy, no scipy. Code, the plot, and the four caveats that must be stated
alongside it: `07-architecture.md` §5.5.

The 48-point slope stays in the write-up as a **descriptive effect size** — fill-points per unit ΔE —
and never as the significance claim.

**Still state the sample size on the slide.** One stall, six days. The claim is *"this instrument
detects a contrast effect and here is the direction it points"* — not *"vegetables sell 23% better."*
That discipline is what separates this from the teams who will overclaim.

**The honest limitation:** rearranging the neighbours also moves the *meat* dishes, and where a
popular dish sits changes where the queue slows down. That cannot be eliminated in six days. Say so.

### 3.5 The schedule: alternate, do not block

Days alternate **baseline / contrast / baseline / contrast…**, not three-then-three. A three-then-three
block confounds the intervention with everything else that changes later in the week — traffic, her
prep, the weather, day of week. Alternating spreads that flat. Costs her 30 seconds each morning.

**Confirm which days the canteen is actually open (N4) before fixing the calendar.**

### 3.6 What is recommended but not claimed

Two other levers appear in the LLM's output and are **explicitly not measured**:

- **Abundance / tray size** (L4) — `04-hawker-journey-map.md` stage 3 asserts *"a depleted tray deters
  customers"*, flagged `[ASSUMED]`. Plot `depletion_rate` against `fill`; if the rate collapses below
  ~25% full, the fix is a smaller tray so the same food looks full for longer. A load cell physically
  cannot measure this. Report it as a finding if it appears, not as a tested claim.
- **Late top-ups** (L3) — see §4.6.

---

## 4. The data model

### 4.1 Captured — per photo, per tray

| Field | Source |
|---|---|
| `ts` | Pi clock |
| `frame` | JPEG path |
| `tray_id` | Fixed crop geometry, 1..N — set **once** when the camera is mounted |
| `fill` | Vision model, 0–100 in steps of 5 |
| `lab` | Arithmetic on the crop. **Not the model** — it is a median, it is exact, it is free |

`tray_id` is free information. The dish in slot 3 changes daily; **slot 3 does not.**

### 4.2 Labelled once a day — by Raghav, not by her

Sixty seconds off the first frame of the morning: `dish` per `tray_id`, `is_veg`, `tray_size`, and
`arrangement` (`baseline` or `contrast`).

**The vision model is never asked to name a dish.** Across ~340 calls it would drift between
"kangkong", "stir-fried greens" and "sayur" and destroy every grouping. One job — estimate fill —
removes that failure mode entirely.

§7's "zero manual data entry, ever" is about **her** workload. Raghav is the researcher and is opening
the images anyway.

### 4.3 Derived — per tray, per day

**Not one of these is a straight subtraction, because she tops the trays up during service.**

| Metric | How | Lever |
|---|---|---|
| `served_total` | Σ of all negative deltas | L2, L6 |
| `refills` | list of `(ts, amount)` where delta > +15 | L3 |
| `cooked_total` | opening fill + Σ refill amounts | L2 |
| **`leftover_close`** | fill at last frame of the day | **L2, L5, L6** |
| `over_provision` | `cooked_total ÷ served_total` | L2 — the ratio she has never seen |
| `sold_out_ts` | first `fill = 0` with no refill after | L2 — flags **under**-cooking |
| `depletion_rate(t)` | −Δfill per 30-minute bin | L1, L3 |
| `last_refill_ts` | last positive delta | **L3** |
| **`neighbour_contrast`** | **mean ΔE to left and right trays (§3.2)** | **L1 — the experiment** |

### 4.4 Derived — across the week

| Metric | Question it answers | Lever |
|---|---|---|
| **`served_total` regressed on `neighbour_contrast`, all 48 dish-days** | **Does looking different from your neighbours sell food?** | **L1** |
| Same, veg dishes only, baseline vs contrast days | The simple version of the same question | **L1** |
| `leftover_close` grouped by `is_veg` | **Do vegetables actually waste more than meat?** | — |
| `depletion_rate` plotted against `fill` | Is there a fullness floor below which a dish stops selling? | L4 |
| `served_total` by hour, veg vs meat | Do vegetables sell early or late? | L2, L1 |

### 4.5 The first analysis must be allowed to kill the premise

The goal is "sell the vegetables." **The first thing the data does is test whether vegetables are
actually the problem.** Group `leftover_close` by `is_veg` before anything else.

If vegetables waste *less* than the meat dishes, that is a finding, not a failure, and the
recommendations follow the data instead of the assumption. Assuming the answer and then presenting it
is what loses to a judge who reads carefully.

### 4.6 The sharpest single thing this system can say

A tray topped up at 2:15pm that is still 60% full at close. **That top-up went straight into the bin,
and it is identifiable to the minute.** It produces:

> **"Stop topping up tray 4 after 1:30pm."**

Compare *"cook 10% less kangkong"* — vague, scary, risks running out, which is the one thing she will
not accept. The refill finding is specific, free, reversible, and she can act on it tomorrow morning
without touching her buy, her menu or her prep.

**This is why refill detection is not an implementation detail.** Fill alone gives `start − end`.
Deltas give the decision.

### 4.7 Cut, and why

| Cut | Reason |
|---|---|
| **`waste_dollars` per dish** | Three stacked estimates — vision fill → grams → cost per kg — and the last only exists if she discloses ingredient costs, which breaks §7. A judge pulls one thread and the number unravels. **The dollar argument stays in the pitch**, computed once from the ~8×-of-sales maths in `04-hawker-journey-map.md` §4 against a leftover *volume*. It does not belong in the per-dish pipeline |
| Dish identification by the model | §4.2 — name drift across 340 calls |
| Day-of-week effects | Six service days. An LLM handed six points produces confident noise |
| Position effects | Deliberately held constant — that is what makes §3.1 work |
| Portion-size waste (what diners leave on the plate) | Different bin, different person — `04-hawker-journey-map.md` §5 |
| Any live display at the stall | Output is a weekly page. A live nudge for L3 is phase 2 |

### 4.8 Concrete schema

Five files, plain CSV and JSON, ~1,400 rows total. No database.

**`frames.csv`** — written at the stall, one row per photo. Exists so a gap in the day is detectable
without opening 700 images.

| Column | Type | Note |
|---|---|---|
| `ts` | `str` ISO 8601, local | `2026-09-22T11:04:00` |
| `path` | `str` | `frames/2026-09-22/1104.jpg` |
| `bytes` | `int` | 0 means the camera failed that cycle |

**`trays.json`** — the only hand-written file.

```json
{
  "geometry":  { "1": [120,340,210,180], "2": [330,340,210,180] },
  "ref_card":  [40, 300, 60, 60],
  "days": {
    "2026-09-22": {
      "arrangement": "baseline",
      "trays": {
        "1": { "dish": "kangkong",        "is_veg": true,  "tray_size": "full" },
        "2": { "dish": "sweet_sour_pork", "is_veg": false, "tray_size": "full" }
      }
    }
  }
}
```

| Field | Type | Note |
|---|---|---|
| `geometry[tray_id]` | `[int,int,int,int]` | Crop box `x,y,w,h` in pixels. **Set once** |
| `ref_card` | `[int,int,int,int]` | The grey card crop (§3.3) |
| `days[date].arrangement` | `enum` `baseline` \| `contrast` | |
| `days[date].trays[id].dish` | `str` snake_case | By hand, so it cannot drift |
| `days[date].trays[id].is_veg` | `bool` | |
| `days[date].trays[id].tray_size` | `enum` `full` \| `half` | |

**`readings.csv`** — one row per (analysed frame × tray). **~1,150 rows.**

| Column | Type | Note |
|---|---|---|
| `ts` | `str` ISO 8601 | |
| `date` | `str` `YYYY-MM-DD` | Grouping key |
| `tray_id` | `int` 1–8 | |
| `dish`, `is_veg` | `str`, `bool` | Joined from `trays.json` |
| `fill_raw` | `int` 0–100, step 5 | **Straight from the vision model. Never overwritten** |
| `fill` | `float` 0–100 | 3-frame rolling median + monotonic clamp (§5.3) |
| `fill_hand` | `float` \| `null` | **Hand-coded by eye. Null except on the audit day (§10)** |
| `lab_L`, `lab_a`, `lab_b` | `float` | Median LAB of the crop, after grey-card normalisation |
| `flag` | `str` \| `null` | `dish_swap?`, `parse_fail`, `occluded` |

`fill_raw` is kept beside `fill` so the smoothing is auditable. If a judge asks how much the filter
changed the data, the answer is a column diff, not a shrug.

**`events.csv`** — derived, one row per detected change. **~200 rows.**

| Column | Type | Note |
|---|---|---|
| `ts`, `date`, `tray_id`, `dish` | | |
| `kind` | `enum` `refill` \| `drop` \| `sellout` | |
| `delta` | `float` fill-points, signed | `+` refill, `−` consumption |

**`daily.csv`** — the analysis table. One row per (date × tray). **48 rows.**

| Column | Type | Note |
|---|---|---|
| `date`, `tray_id`, `dish`, `is_veg` | | |
| `arrangement` | `enum` `baseline` \| `contrast` | |
| `open_fill` | `float` 0–100 | First frame of the day |
| **`leftover_close`** | `float` 0–100 | Last frame. **The waste number** |
| `served_total` | `float` ≥ 0 | Σ\|negative deltas\|. **Can exceed 100** if refilled |
| `cooked_total` | `float` ≥ 0 | `open_fill` + Σ refills. Same unit |
| `over_provision` | `float` ≥ 1.0 \| `null` | `cooked ÷ served`. `null` when `served = 0` |
| `n_refills` | `int` ≥ 0 | |
| `last_refill_ts` | `str` \| `null` | **`null` if never refilled.** Feeds §4.6 |
| `sold_out_ts` | `str` \| `null` | **`null` if it never sold out** — the common case |
| **`dish_lab_L/a/b`** | `float` | The dish's measured colour that day, from the opening frames |
| **`contrast_left`**, **`contrast_right`** | `float` \| `null` | ΔE to each neighbour. `null` at the ends of the row |
| **`neighbour_contrast`** | `float` | Mean of the two. **The independent variable** |
| `n_frames` | `int` | Coverage check — a low count is a camera gap, not a quiet day |

**On units.** `fill` is **percent of that tray's capacity** — not grams, not portions. Summed deltas
are **fill-points**, which is why `served_total` can exceed 100 on a twice-refilled tray. **Grams never
appear at all** — see §6.1. Nothing in this prototype is weighed, and no column converts to mass.

**On nulls.** `sold_out_ts` and `last_refill_ts` are null more often than not, and `over_provision` is
undefined when a dish sold nothing. Anything treating those nulls as zero will silently report that a
dish sold out at midnight.

---

## 5. Architecture

### 5.0 The clock — added 19 Sep, and it invalidates §4.6 if ignored

**Revised 19 Sep — the stall has WiFi** `[T4]`. Read this carefully, because the network solves the
obvious half and makes the dangerous half routine.

The Pi 5's RTC ships without a battery, so it always boots at **the time of last shutdown**. Then NTP
associates and **steps the clock backwards** to the truth. With `frames/YYYY-MM-DD/HHMM.jpg`, every
filename after that step collides with one already on disk and `cv2.imwrite` overwrites it with no
error. **Networkless, that step happened basically never. Networked, it happens at every boot.**

Every timestamped output in §4.6 — *"stop topping up tray 4 after 1:30pm"* — depends on this:

1. **Name frames by sequence number, never by the clock**, and log wall-clock *and* `CLOCK_BOOTTIME`
   in every row. Ordering can then never collide or reverse. **Mandatory.**
2. **Gate the capture unit on `time-sync.target`** so frame 1 waits for the backward step rather than
   being cut in half by it. One `[Unit]` stanza. **Mandatory now that there is a network.**
3. ~~RTC backup battery, ~S$8~~ — **struck.** It only ever bought a plausible clock with no network.
   NTP does that free. Do not spend S$8, and do not ask Jamie for it.

Full detail and code in `07-architecture.md` §2.5.

### 5.1 At the stall — `capture.py`

- One photo every **2 minutes** through service. Capture is free; resolution you did not record is
  gone forever.
- **Lock white balance, exposure and gain** before the first frame (§3.3). Auto-WB destroys the colour
  measurement.
- **Crop to the tray row before writing the JPEG**, so a customer at the frame edge never reaches
  disk. Privacy as a property of the code, not a policy.
- Downscale to ~1280×720, ~200 KB. About 24 MB/day.
- Write `frames/NNNNN.jpg` — **sequence, not clock** (§5.0) — plus a row in `frames.csv`. That is the
  entire state; no database, and **no network call in this path.** A separate `rsync` cron ships the
  folder every ten minutes and is free to fail; `capture.py` never knows it exists.
- `systemd` unit or `cron @reboot`. If it crashes, the next boot fixes it.

~40 lines.

### 5.2 Back at SUTD — `analyse.py`

- Analyse **every 5th frame** (10-minute spacing) on the first pass. The 2-minute frames stay on disk
  for re-analysis around anything odd.
- Normalise by the grey card first. Then compute `lab_*` per crop — arithmetic, not a model call.
- One vision call per frame covering **all trays at once**: the model sees relative fullness across the
  row, and it is ~340 calls for the week rather than thousands.
- **Burn the tray numbers into the image before sending** — draw the numbered crop boxes with PIL, ~6
  lines — so the model reads "tray 3" off the picture instead of inferring it.
- Rows to `readings.csv`. Then `report.py` builds §4.3–4.4 and makes one LLM call over the aggregate.

### 5.3 Noise handling — reuse what already works

`stockclock.py` solved the same problem for load cells and the pattern ports directly:

| `stockclock.py` | Tray Watch |
|---|---|
| `statistics.median` over `SAMPLES = 15` | 3-frame rolling median over `fill` |
| `MIN_CHANGE_G = 20` — *"smaller than this is a knock or a hand, not stock"* | `MIN_DROP = 3` fill points |
| `SETTLE_SECONDS = 2.0` | Change must persist into the next frame |
| Weight up = new batch | `REFILL_JUMP = 15` fill points |

Plus **a three-frame median at capture time** — hands, ladles, plate stacks and steam are transient
across four seconds and food is not. Untreated, every occlusion becomes a phantom refill, and refill
detection is the sharpest output in the project. `07-architecture.md` §2.6.

Plus one prior the load cells did not have: **between refills, fill can only go down.** Clamp upward
drift below the refill threshold. That kills most of the vision model's error for free.

One constants block at the top, carrying the same comment `stockclock.py` carries:

```python
# Calibration knobs. Tune these against the real stall, not against a bench.
```

### 5.4 The vision call

One job, one number per tray. Give it the morning's full-tray frame **and** an empty-tray reference in
the same prompt — relative judgement is far more reliable than absolute, and the references cost two
images per call.

Strict JSON out, via constrained decoding against a schema — so there is no parse-failure branch to
write at all: `[{"tray": 1, "fill": 45, "obscured": false}, ...]`.

**`obscured` matters more than `fill`.** A frame where a customer's arm crosses tray 4 must be
*dropped*, not read as "tray 4 emptied then refilled two minutes later." Without that flag every
occlusion becomes a phantom refill.

Cost for the whole week, verified against current pricing: **about US$4.** This is not a budget line.

### 5.5 The recommendation call

One call, at the end, over the week's aggregated table. This is the LLM the mentor asked for.

**Feed it `context.md` (§6.3)** — what she already knows, in her words — so it builds on her
expertise instead of restating it.

**Constrain it to the §2 levers in the prompt.** An unconstrained model will suggest a loyalty
programme. Given the lever list it can only say things like *put X between Y and Z*, *cook less of X*,
*stop refilling W after 1:30*, *use a smaller tray for V*.

**The LLM is never in the measurement path.** Everything in §4.3 and §4.4 is arithmetic over CSV and
can be audited by hand. That is deliberate: the model reads fill and writes advice, and neither of
those is allowed to be the only thing standing between you and a result (§10).

---

## 6. Nothing is weighed — and her knowledge is the starting point, not the output

### 6.1 No scale, no grams, no kilograms

**This prototype measures nothing in grams and that is deliberate.** The Waste Diary weigh-in is a
hackathon housekeeping deliverable — it exists to make contestants recycle their own waste — and it is
**not** a requirement on the prototype. Tray Watch's job is to *reduce* waste, not to *report* it.

So the unit is **trays and percentages**, all the way through:

> *"You cooked about 3 trays of kangkong. You sold about 1."*

That is more legible to her than *"1,840 g"*, it comes straight off the photographs, and it removes an
entire class of stacked-estimate error (fill → grams → kg → dollars) that a judge could pull apart.
Anything in this repo that mentions a kitchen scale, `g_per_point`, `served_g` or `leftover_g` is
superseded by this section.

Ground truth is therefore **the hand-coded audit day** (§10), not a scale — you check the model
against your own eyes on the same photographs, and report the agreement rate.

### 6.2 She already knows which dishes sell badly — and that is a threat

Her own words, when the idea was pitched to her `[testimony]`: **she already knows what sells and what
does not.**

Take that seriously, because it is the sharpest critique the project will face: *a system whose
weekly output is "kangkong sells slowly" has told an expert something she has known for ten years, and
she will stop reading it in week two.*

**Three things it can say that she does not already know**, and all of them survive her objection:

| Her knowledge | What the camera adds |
|---|---|
| *"Kangkong sells slowly"* | **How** slowly — the depletion curve — and therefore how much less to cook, and by when it is clear the day is lost |
| *"I top up when it looks low"* | **Which of those top-ups went in the bin**, to the minute (§4.6). She is doing it by eye while serving; nobody is watching the clock |
| *"That's just how it is"* | **Whether a change worked.** She cannot A/B test her own display while running a stall. This can |

### 6.3 `context.md` — her knowledge, written down and fed to the model

One plain markdown file, written from what she says, read by the recommendation call (§5.5):

- which dishes she says sell fast and slow, in her words
- which she will not take off the menu, and why
- what she has already tried, and what happened
- her constraints — supplier minimums, tray sizes, prep order

**Not a database, not Obsidian, not a graph.** One file, a page long, pasted into the prompt. The
entire value is that the model's suggestions then *start* from her expertise instead of colliding with
it — so the output is *"you already know kangkong is slow; here is the part you can't see"* rather
than a stranger explaining her own stall to her.

**Ask A5 in §12 to fill it.** Fifteen minutes of her talking is the whole build.

---

## 7. Camera placement

**Oblique, roughly 40° above horizontal — not a bird's-eye view.**

From directly overhead you see *area covered*, not *depth*, and depth is most of the volume: a tray
with 2 cm of food and one with 6 cm look nearly identical. An angled view shows the food's profile
against the tray's back wall, which is the thing that makes fill readable. Ceiling mounting also puts
rising steam directly in the optical path.

**Mount on top of the sneeze guard, customer side, looking down and across the row.** That avoids
shooting *through* glass (reflections), keeps steam mostly out of the path, and gives every tray
similar lighting — which matters more than usual now that colour is the measurement.

Cost: near trays partially occlude far ones. Accept it, and check it on day 1.

**Settle this for free today:** stand where the camera would go and take phone photos at open, noon
and close. **If you cannot tell 40% from 60% in those photos, no webcam will either** — and you find
that out before spending anything.

---

## 8. Hardware and budget

### What you already have — corrected 18 Sep against the invoices

| Item | Invoice | S$ |
|---|---|---|
| **2 × Raspberry Pi 5, 2 GB** | Cytron CI14269757, 14 Sep | 196.00 |
| 3 × PETG filament | PolyMate INV/26/09/018, 10 Sep | 43.50 |
| | **Spent** | **239.50** |

**Three corrections to earlier documents:**

1. **There is no Raspberry Pi 4 in this project.** `CLAUDE.md` says "a Pi 5 was bought" — singular. The
   invoice says **quantity 2**. One runs the camera, one runs Chope.
2. ~~There is no microSD card.~~ **Bought `[T4, 19 Sep]`** — in hand, nothing is blocked on it. The
   receipt still has to reach `FINANCE CLAIMS/`, and until it does the S$239.50 spent / S$160.50
   remaining figures below are stale by the card's price.
3. **Check you have a USB-C PD supply.** The Pi 5 caps total USB current at 600 mA unless it detects a
   5 A-capable supply. A 1080p webcam draws 150–250 mA so it fits, but an under-spec supply will
   throttle and you will lose a day to it.

Budget is S$200 per prototype, S$400 total. **Remaining: S$160.50**, and every further purchase needs
Jamie's approval in writing first (her instruction, 17 Sep).

### To buy

**USB webcam, not the Pi camera module.** Both boards are Pi 5, whose camera connector is 22-way
0.5 mm; every current camera product is 15-way 1 mm, so CSI means waiting on an adapter cable. USB has
none of that, and a 3 m USB extension keeps the Pi off a hot greasy counter where 50 cm of FPC ribbon
cannot. Autofocus is the only loss and the mount distance is fixed.

**Check before paying: 90°+ field of view, ideally 120°**, and that white balance can be locked (any
UVC webcam can, via `v4l2-ctl`). Horizontal coverage = 2 × d × tan(HFOV/2) — a 78° webcam at 60 cm
covers only ~0.95 m of tray row; 100° covers ~1.4 m.

| Item | ~S$ |
|---|---|
| ~~microSD 32 GB A1~~ — **bought `[T4, 19 Sep]`** | ~~15~~ |
| USB webcam, 1080p, 90°+ FOV | 30 |
| USB extension, 3 m | 5 |
| Mount hardware — after measuring her stall | 15 |
| Grey card | printed |
| ~~RTC battery~~ — **struck, the stall has WiFi and NTP is free** | ~~8~~ |
| **Total** | **~50** |

Vision API for the week: a few dollars. Leaves ~S$95 headroom for a PD supply if needed.

**No kitchen scale.** See §6.1 — nothing in this prototype is weighed.

**Fallback if nothing local is wide enough:** Cytron SG, *Camera Module 3 (120°) with 50 cm Pi 5 CSI
cable*, S$61.71 — that bundle's cable is the correct 22-way for the Pi 5.

**Cancelled, do not buy:** 4× load cells, 4× HX711, RGB LEDs, resistors, breadboard, push button,
ML-2020 battery, HDMI screen, micro-HDMI cable, plywood, acrylic.

---

## 9. The week

| Date | |
|---|---|
| **Fri 18 Sep** | **Phone test at the stall during lunch (§7).** Ask her §12. Message Jamie. Buy |
| Sat–Sun 19–20 Sep | Flash the card (**in hand**). `capture.py`. Join the Pi to the stall WiFi and confirm `timedatectl` says *synchronized: yes*. Bench the whole loop on a tray at home. Print the grey card |
| **Mon 21 Sep** | Mount at open. Set crop geometry on-site. Dry run — data kept if it works |
| **Tue 22 – Mon 28 Sep** | **Six service days. Alternating baseline / contrast** |
| 29–30 Sep | `analyse.py`, `report.py`, hand-code the audit day, the write-up, slides, Waste Diary, People Log |
| **1 Oct** | Deliverables due |
| **2 Oct** | Showcase, Temasek Shophouse |

**Zero slack.** That is the whole argument for buying a webcam off a shelf today rather than waiting
on a courier. Confirm her opening days (N4) before fixing the six.

### What goes on the 1.2 m table on 2 Oct

A PDF of charts is a weak showcase. The frames solve it for free:

**Loop a timelapse of the real week.** One `ffmpeg` line over the JPEGs already on the card — 340
frames of her actual trays emptying, refilling and sitting half-full at close, compressed into forty
seconds on a laptop. It is the entire argument made visually, and anyone walking past understands it
before you open your mouth.

Then the camera itself on the table beside it, pointed at a mock tray, so people see the thing that
produced the video. **No live analysis** — a live demo that fails in front of a judge is worse than no
live demo. The video is real data and it cannot crash.

---

## 10. Verification

The model is not allowed to be a single point of failure.

**Before the stall:**
- `python3 capture.py demo` — the `demo()` self-check pattern from `stockclock.py`. Asserts the delta
  logic end to end against a synthetic fill series containing a refill, a noise spike and a sell-out.
  No hardware, no camera, no API.
- Run `capture.py` for one hour on a tray at home, removing food by hand on a known schedule. Confirm
  `analyse.py` recovers that schedule.
- **Feed it a deliberate refill.** If `refills` misses it, §4.6 is unreachable and the thresholds need
  tuning before day 1.
- **Grey-card check:** photograph the same tray under two different lights. After normalisation the
  `lab_*` values must agree within a few ΔE. If they do not, the colour experiment is measuring the
  lighting.

**At the stall, day 1:**
- Confirm no customer appears in any written frame. If one does, tighten the crop before day 2.
- Confirm the day's frames survived a full service with no gap. A gap on day 1 is recoverable; a gap
  on day 5 is not.

**End of week — the audit day:**
- **Hand-code one full day by eye** (~190 readings, ~20 minutes) into `fill_hand`. Report the agreement
  rate with `fill_raw` on the slide: *"the model agreed with me on 87% of readings"* is the number a
  judge asks for, and *"the model read the trays"* is not.
- If agreement is bad, you still have five days of frames and a weekend to hand-code them. **The
  project cannot fail on model accuracy** — that is the entire point of keeping the LLM out of the
  measurement path.
- Every dish has ≥5 days of data, or say which does not and why.

---

## 11. What this deliberately does not do

- **Does not see raw or prep waste, and does not weigh anything.** It works in trays and percentages,
  which is the unit she already thinks in. See §6.
- **Does not measure what diners leave on their plates.** Different bin, different person,
  structurally invisible from the stall — `04-hawker-journey-map.md` §5.
- **Does not price waste per dish.** §4.7.
- **Does not test position.** Held constant on purpose — §3.1.
- **Does not run live at the stall.** Logger only; the page comes after.
- **Does not train a model.** A vision API call handles lighting, steam and glare with zero labelling.
  With 13 days, training anything is how this fails.

---

## 12. Before mounting anything — ask her

| # | Question | Blocks |
|---|---|---|
| **N1** | Can I rearrange which dishes sit next to each other, on alternate days? | **The entire experiment** |
| **N2** | How often do you top up a tray during lunch, and when do you stop? | §4.6 |
| **N3** | Do all the trays hold the same amount? | §4.2 `tray_size`, §3.6 |
| **N4** | What time do you open and close, and which days? | The six-day calendar |
| **A3** | Where can a camera mount — sneeze guard, hood, pole? Is there a socket? | §7 |
| **A5** | Which vegetable dishes do you already know sell badly? | §6 — her knowledge is the model's starting context, not its output |

A1 (raw versus cooked) is answered `[testimony]` and is no longer asked. **A5 is new and it is the
most important question on this list** — see §6.

---

## 13. Positioning against the competition

`CLAUDE.md` currently says *"'No camera' is market access, not a limitation."* **That line is now false
and is being replaced, not patched.** Lumitics, Winnow and Orbisk are all camera + AI.

The replacement distinction is cleaner and stronger:

> **Every one of them points the camera at the bin.** Lumitics is literally a smart bin — you throw
> food in and press a green button. They measure the corpse.
>
> **This points at the display, during service, while there is still time to act** — and it does not
> just report, it **changes the display and measures whether that worked.**

Prevention, not accounting. `03-hawker-5w1h.md` §9 already argues that Singapore's hawker-centre
response has been overwhelmingly *treatment*, with prevention sitting above it in the waste hierarchy.

The privacy argument survives in a stronger, concrete form: **the camera points down at food, and the
crop is applied before anything is written to disk.** No faces, no queue, no customers — not as a
policy, as a property of the code.

---

## 14. Files

| Path | |
|---|---|
| `05-traywatch-plan.md` | This document |
| `06-traywatch-user-journey.md` | The user journey — Jamie's question, answered |
| `capture.py` | **To write.** Stall-side logger, ~40 lines |
| `analyse.py` | **To write.** Frames → grey-card normalise → LAB + vision → `readings.csv` |
| `report.py` | **To write.** CSV → §4.3/§4.4 tables → one LLM call |
| `trays.json` | **To write.** Crop boxes, grey card, daily labels |
| `context.md` | **To write.** Her knowledge in her words, read by the recommendation call — §6.3 |
| `archive/` | Stock Clock, kept not deleted — see below |
| `03-hawker-5w1h.md`, `04-hawker-journey-map.md` | **Unchanged.** The research holds; the pivot changes the instrument, not the problem |

**Archived, not deleted.** `BUILD-GUIDE.md`, `stockclock.py`, `wiring.svg` and `models/spacer.scad`
are **untracked** — `git status` shows `??`, so they exist in exactly one place and deleting them is
unrecoverable. They also have value: a judge asking *"how did you arrive at this?"* gets a real answer
when you can show the weighing rack you designed, costed and abandoned after the stall owner told you
the problem was demand, not storage. That is evidence of iteration, and it costs one folder.
