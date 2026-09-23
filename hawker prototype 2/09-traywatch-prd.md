# PRD — Tray Watch (Prototype 2)

> **A note on this document's shape.** It follows a standard SaaS platform PRD template, heading for
> heading. Tray Watch is not a SaaS platform — it is a camera on a hawker stall — so a large
> number of fields are answered **"None, and here is why."** Those answers are kept rather than
> deleted, because *what a product deliberately does not have* is the most defensible part of this
> entry. A PRD claiming a payment processor and a CDN for a Raspberry Pi writing CSVs to an SD card is
> what a judge takes apart first.
>
> **Provenance.** `[T3]` stall owner, interviewed 17 Sep · `[T4]` 19 Sep · `[T6]` 21 Sep ·
> `[cited]` public source · `[DERIVED]` implied by cited facts · `[VERIFIED]` tested, output in
> `07-architecture.md` · `[MEASURED, 21 Sep]` **simulated and reproducible — run
> `python design_checks.py`** · `[ASSUMED]` needs fieldwork. Source documents:
> `03-hawker-5w1h.md`, `04-hawker-journey-map.md`, `05-traywatch-plan.md` (build + schema),
> `06-traywatch-user-journey.md`, `07-architecture.md`, `design_checks.py`.
>
> **Rebuilt 21 Sep.** The previous revision led with a colour-contrast experiment. That experiment
> was measured and found **unable to reach significance under any outcome** — see §"What six days
> can and cannot prove". The instrument, the privacy model, the page and the competitive position
> are unchanged; what changed is which claim the prototype stands on.

---

I need to build a simple yet robust MVP for **a display-side food waste prevention instrument**
targeting **independent cai png (mixed rice) hawker stalls, and the food court operators above
them**. This will primarily solve **the fact that vegetables are cooked in quantities nobody has
ever measured, go unsold, get binned, and keep being re-bought at the same rate — because no stall
owner has ever been shown, in numbers off her own stall, how much of what she cooked came back**
and our main competitive advantage is **every competitor points their camera at the bin; this one
points at the display, during service, while there is still time to act.**

The core functionality should handle **photographing a row of display trays every two minutes
through a six-hour lunch service, reading each tray's fill level per frame, detecting mid-service
refills as distinct from sales, and producing one printed A4 page a week carrying two photographs
and exactly one recommended change.**

> **The mentor's framing, 21 Sep, and it is the one this document is built to:**
> *"the framing is to 'reduce' leftovers with more insights. Insights captured by your process."*
>
> That sentence is why the waste ledger leads and the experiment does not. The ledger is the
> insight, captured by the process, and it lands on six days of data every time. The experiment
> is an ambition that six days cannot pay for.

---

## Problem statement, in her words

> *"Vegetables often spoil because meat products sell fast… whereas vegetables sell slow… so she had
> to throw a lot of veggies, uncooked ones especially."* `[T3]`

She is not confused about her problem. She has named it exactly. **What she does not have is any way
to act on it**, because *"vegetables sell slow"* is a fact, not a decision.

The causal chain, and it matters that the camera attacks the **first** link:

```
students don't pick vegetables  →  cooked veg left at close  →  she keeps buying at the same rate  →  raw veg sits, gets stacked over, rots
        ▲
        └── Tray Watch attacks here. The cancelled load-cell rack attacked the last link.
```

**Competitive advantage, stated precisely.** Winnow, Leanpath and Orbisk cost £5,000–15,000 per
kitchen, need cloud, and need a chef who interacts with them; they sell to hotels and large
commercial kitchens `[cited]`. Lumitics is literally a smart bin — you throw food in and press a
green button. **They measure the corpse.** Nobody serves the bottom of the market. This is a camera
already owned plus ≤S$20 of mounting, no cloud, no app, no training, nothing to maintain — and it
does not just report, it **changes the display and measures whether that worked.** Prevention, not
accounting.

---

## What six days can and cannot prove

**This section exists because the previous revision got it wrong, and the error was the kind that
only shows up when you measure instead of argue.** Everything below is reproducible:
`python design_checks.py`.

### The experiment cannot reach significance. Not "probably won't" — cannot.

The design was: hold the vegetables still, change their neighbours, and test whether a dish sells
better beside a higher-contrast neighbour. The test was a within-dish sign-flip permutation test,
claimed at **n = 8 dishes**, floor p = 0.0078.

**But a dish that moved cannot be counted.** If curry chicken shifts from slot 2 to slot 6 and sells
more, that is the new neighbours *or* the new position, and six days cannot separate them. Only
dishes that **stayed put and got new neighbours** carry contrast information. So `n` is not the tray
count — it is the count of never-moved, re-neighboured dishes.

Exhaustive over all 40,320 rearrangements of an 8-tray row `[MEASURED, 21 Sep]`:

| trays | max never-moved AND re-neighboured | best possible p | |
|---|---|---|---|
| 8 | **5** | **0.0625** | **above 0.05 — unwinnable** |
| 9 | 6 | 0.0312 | winnable in principle |

Shuffling a row of 8 always costs three dishes as movers. **Even a perfect result — every countable
dish moving the right way — lands at 0.0625 and cannot be claimed.** This is the same defect
`07-architecture.md` §5.5 already caught once, in the day-level test it retired for a floor of 0.10.
Its replacement inherited the disease in a less obvious place.

### She *can* move the trays — and an 11-hour day says when `[N1 ANSWERED YES, 22 Sep]`

**N1 is answered: yes, she can swap the trays.** Note what that does and does not buy. She moves
*trays*, so the dish travels with the tray — which is exactly the confound above. **The five-dish
ceiling and the 0.0625 floor are unchanged.** A yes on N1 does not make the experiment significant
and nothing below claims it does.

What it does buy is *when*. She opens **08:00** and closes **19:00** `[T7]`, with a dead stretch
from roughly 13:30 to 17:00. So the row can be swapped **in the lull**, and every dish then sees
both arrangements **on the same day**. `design_checks.py` C7, at the honest n = 5, six days
`[MEASURED, 22 Sep]`:

| real effect | day-to-day wobble | design | estimate | 95% CI half-width | CI clears zero |
|---|---|---|---|---|---|
| +10% | 25% | alternate days | +13.1% | ±21.8 | 22% |
| +10% | 25% | **swap in the lull** | **+10.5%** | **±9.1** | **61%** |
| +10% | 40% | alternate days | +17.7% | ±35.6 | 14% |
| +10% | 40% | **swap in the lull** | **+10.5%** | **±9.1** | **61%** |
| +25% | 40% | alternate days | +33.8% | ±40.4 | 34% |
| +25% | 40% | **swap in the lull** | **+25.6%** | **±10.3** | **99%** |

Three things in that table, in order of importance:

1. **The CI is 2.4–3.9× tighter.** ±9.1 against ±21.8 to ±35.6.
2. **The crossover rows are identical at 25% and 40% wobble.** Day-to-day variation — weather,
   footfall, exam week — is the single largest noise source in the between-day design and it
   **cancels exactly** inside a day. That is what buys the interval.
3. **Alternating days is biased upward**: +17.7% estimated for a real +10%. It is a ratio of means
   with a noisy denominator, so it over-reports, in the flattering direction. The crossover reads
   +10.5% for a real +10%.

The first version of this check gave the crossover no within-block noise and returned ±0.0 —
perfect by construction, which was a bug in the simulation, not a result. C7 now carries block
footfall (CV 15%) and the vision chain's own read error (CV 8%) on **both** designs.

**The cost to her is one row-swap a day, in the dead afternoon she is standing around in anyway**,
instead of one every other morning at open. **The cost to the code is zero before mounting:** frames
are frames, so capture is byte-identical either way. Only `dishes.csv` changes — it gains `block`
and `from_ts` columns so the am/pm slot→dish maps are both recorded — and only the side-arm analysis
reads them. That is a change to make while the week runs, not before day 1.

### And at n = 8, ignoring the above, it is underpowered by roughly an order of magnitude

A dish's sales wobble day to day regardless of anything on the display. Share of experiments that
reach p<0.05 **when the effect is real and that large** `[MEASURED, 21 Sep]`:

| true effect | day-to-day wobble 25% | wobble 40% |
|---|---|---|
| +10% | 20% | **10%** |
| +20% | 61% | **30%** |
| +30% | 92% | 54% |

It needs a **+30%** shift in what students pick, from moving two trays, before it is more likely
than not to see anything. At plausible effect sizes the honest expectation is *"no significant
effect"* on showcase day, **with a real effect present.**

### The shipped analysis returns fake certainty on missing data

`07-architecture.md` §5.5's six lines, given a dish that missed one arrangement arm — which a
rotating cai png roster produces routinely `[MEASURED, 21 Sep]`:

```
all 8 dishes present : obs=+4.00  p=0.0078
one dish missing     : obs=+nan   p=0.0000     <-- perfect significance, out of a hole
```

`abs(null) >= abs(nan)` is all-False, so p is exactly 0. Not an error — a confident wrong answer, in
the direction that flatters. **The analysis must drop incomplete dishes loudly, by name, and refuse
to run below n=6.**

### The number the product actually prints is exact

The chain in `07-architecture.md` §5 recovers `cooked_total` as a **sum of detected refill jumps**. A
refill is instantaneous; the 3-frame median reveals it two frames later; sales continue through the
lag. Every refill is under-sized by rate × lag, **always downward**
`[RE-MEASURED, 22 Sep, on her real 08:00–19:00 day]`:

| frames analysed | frames/day | `cooked_total` | `leftover_close` |
|---|---|---|---|
| every 1 min | 660 | −5.6% | ±0.00 fill-points |
| **every 2 min** | **330** | **−9.5%** | **±0.00 fill-points** |
| every 3 min | 220 | −12.7% | ±0.00 |
| every 4 min | 165 | −15.4% | ±0.00 |
| every 6 min | 110 | −23.3% | +0.02 |

> **These numbers moved on 22 Sep and the old ones should not be quoted.** They were
> first measured against a 6-hour lunch-only service. She opens **08:00** and closes
> **19:00** `[T7, 22 Sep]` — 11 hours, three peaks, five refills — and on that day the
> 2-min bias is **−9.5%**, not −12%. `design_checks.py` now models her day, so the
> receipt certifies the stall that exists. `leftover_close` is unmoved at ±0.00, which
> is the point: it is the number the page leads with.

**Why 2 min and not 1 min.** 1-min halves the bias (−5.6%) for US$4 instead of US$2 —
but it halves it on a number that is *already labelled a lower bound and printed in
rounded trays*, while the headline number is exact at both. `TW_EVERY` is the knob. The
one reason to actually use it: if day 1 shows a lot of `obscured` frames, 1-min doubles
the survivors. That is a robustness argument, not an accuracy one.

**`leftover_close` is a level read at close** — no refill, no lag, no threshold between it and the
truth. It is clean at every sampling rate. `cooked_total` and `served_total` are not.

Four candidate fixes were measured and **three made it worse**: sizing refills off the raw series
(−15.7%), the conservation identity `served + leftover` (−11.9%), segment differences instead of
per-frame drops (−11.3%), and lowering `REFILL_JUMP` (total looks right, refill count doubles — two
errors cancelling). **The bias is in the signal, not the filter. Do not add a filter.** Two
consequences, both load-bearing:

1. **Analyse every frame, not every third.** −9.5% instead of −23%, for about US$1 more.
2. **The waste number and the cooked number are different kinds of number and must never be
   presented as though they were.** The page leads with leftover. `cooked_total` appears only in
   rounded tray units, where a 9.5% bias is invisible, and is labelled a lower bound.

### What the same six days *can* prove, with no experiment at all

*"You cooked about three trays of kangkong. You sold about one."* There is no luck to rule out — no
groups, no coin flips, nothing assigned. Precision of the per-dish over-provision estimate
`[MEASURED, 21 Sep]`:

| true over-provision | wobble 25% | wobble 40% | CI excludes zero |
|---|---|---|---|
| +40% | ±7.6 pts | ±12.1 pts | **100% of weeks** |
| +100% | ±19.0 pts | ±30.3 pts | **100% of weeks** |

**Same camera, same six days, same noise. The ledger lands every time; the experiment lands 10–30%
of the time.** That is the whole argument for the reordering, and it is measured, not preferred.

---

## Core functionality

| # | Capability | Model involved? | Claim strength |
|---|---|---|---|
| **F1** | Capture one cropped JPEG of the tray row every 2 min through service, unattended, **with no network call in the capture path** | no | — |
| **F2** | Read fill level 0–100 per tray per frame, **plus an `obscured` flag** | **yes — vision** | audited |
| **F3** | **`leftover_close` per dish per day — what was still in the tray at close** | from F2 | **exact `[MEASURED]`** |
| **F4** | Depletion curve per dish: how fast it empties, and whether it ever sells out | from F2 | exact |
| **F5** | Distinguish a refill from a sale, and flag top-ups that were still unsold at close | no | **directional** |
| **F6** | `cooked_total`, `served_total`, `over_provision` per dish-day | no | **lower bound, −9.5%** |
| **F7** | Each dish's median CIELAB and ΔE contrast to its neighbours | no | exact |
| **F8** | Rearrangement arm: within-dish difference by arrangement, **effect size and CI, no p-value** | no | **exploratory** |
| **F9** | Emit one A4 page: two photographs, one sentence, one change | **yes — one call** | — |
| **F10** | Hand-coded audit day yielding a model-vs-eye agreement rate | no — that is the point | — |

**F3 and F5 are the product.** F3 is the number nobody has ever put in front of her, and it is exact.
F5 is the sharpest sentence the system can produce — *"a tray topped up at 2:15pm that was still 60%
full at close — that top-up went straight into the bin"* — and a bin-mounted competitor physically
cannot say it, because by the time food reaches a bin the decision that created it is hours gone.

**F8 is deliberately demoted.** It runs, it is reported, and it is never called proof. The
crossover schedule above tightens its interval by 2.4–3.9× and removes its upward bias; it does
**not** promote it, because the five-dish ceiling is combinatorial and no schedule can lift it.

---

## User Experience & Flow

The user interface should **not exist at the stall at all.** There is no screen, no app, no button,
no light and nothing to tap. The stall device is a dumb logger. The entire user interface is **one
sheet of A4 paper, handed over on a Monday morning.**

```
┌─────────────────────────────────────────────────────┐
│  KANGKONG — Tuesday                                 │
│                                                     │
│   [ photo: her tray at 9:05am ]   [ 3:02pm ]        │
│        full                          still 60%      │
│                                                     │
│  More than half of it came back.                    │
│  You topped it up again at 2:15pm.                  │
│                                                     │
│  ► Cook two trays tomorrow, not three.              │
└─────────────────────────────────────────────────────┘
```

**The page changed in this revision and the change is the measurement talking.** It used to lead
with *"you cooked about 3 trays, you sold about 1"* — the biased pair. It now leads with **what came
back**, which is exact, and with **the timed top-up**, which is the thing she cannot know. The
cooked figure survives only as the rounded instruction in the arrow.

Key interactions should **cost her thirty seconds and be undoable tomorrow.** Cooking one less tray
is free, fast and reversible — anything failing one of those three does not get done by someone on a
10–15% net margin working twelve-hour days `04-hawker-journey-map.md` §4.

The overall user journey will **be flat for six days and then ninety seconds long.** Install takes
ten minutes once. For the whole logging week her emotional line does not move, and **that is the
design achievement, not a gap in the map** — `04` §7 requires *"zero interaction during service,
zero manual data entry ever, survives being ignored."*

We need **near-zero-literacy** accessibility support and **effectively no language dependency** for
internationalization:

- **Two photographs and one arrow carry the entire finding.** The sentence is a courtesy, not the
  payload.
- English is not necessarily her first language `[ASSUMED]`; Mandarin, Hokkien, Teochew and Malay are
  all live possibilities in a Singapore cai png stall.
- Units are **trays and percentages**, never grams — because that is the unit she already thinks in.
- Printed on paper, so it works with reading glasses, wet hands, no battery and no login.
- **WCAG is not applicable** — there is no web interface to conform to. The accessibility requirement
  here is real and physical, and it is stricter.

There will also be **a looping forty-second timelapse of the real week** (one `ffmpeg` line over the
JPEGs already on the card), accessible in a **laptop-on-a-table, no-network** manner — that is the
showcase artifact for 2 Oct, and it cannot crash. The entire application must be **paper-first and
offline-first**.

---

## User Tiers & Access

There will be **two** tiers of user: **the stall owner, and the food court operator** — and inside the
hackathon window **only the first exists.**

| | The stall owner | The student | The operator |
|---|---|---|---|
| Role | **The user.** Installs it, reads it, acts on it | **The mechanism.** Her sales move when their choices move | **The buyer, at scale** |
| Touches the product? | 90 seconds a week | **Never. Does not know it exists** | A dashboard across 40 stalls |
| Pays? | no | no | **yes** |

**This is the answer to the mentor's "what is the user journey" question in one line:** a product whose
"user" is students has no buyer, no install path and no business model. The student's behaviour is the
*variable being moved*, not the customer being served.

**Stall-owner** users will get **the whole thing, free, forever, during the pilot** — she is doing us
the favour. **Operator** users (**a per-site rental, not a per-stall licence sale — thousands of tiny
customers is the harder business, so do not sell stall-by-stall**) would get **the fleet view plus the
per-stall page delivered by phone instead of on paper.**

We're planning **no** trial periods, and onboarding is **a ten-minute conversation and a camera going
up while she stands aside** — plus fifteen minutes of her talking, which becomes `context.md`. There
is no account to create, no form to fill, and nothing to configure.

Payments will be collected with **nothing. There is no monetisation in the MVP and no payment code
anywhere in this repo.**

---

## Technical Stack

Deployed on **a Raspberry Pi 5 (2 GB) already owned, running Raspberry Pi OS, on the stall's WiFi —
outbound only, nothing listens**, so **a plain Python 3 script started by systemd**. **No
authentication service** — there are no users in the software sense, no accounts, no identities and
no login. Database is **five plain files: CSV and one JSON, about 1,400 rows for the entire week.**
**No CDN — nothing is ever served to anybody.** Backup is **`rsync` every ten minutes over the
stall's WiFi, so the laptop holds the day while the day is still happening.**

| Layer | Choice | Why not the usual thing |
|---|---|---|
| Stall runtime | Python 3 + OpenCV, ~40 lines, systemd | No framework. It writes JPEGs to a folder |
| Storage | `frames.csv`, `trays.json`, `readings.csv`, `events.csv`, `daily.csv` | 1,400 rows. SQLite defensible; a server is not |
| Colour maths | `cv2.cvtColor` on float32 → true CIELAB `[VERIFIED]` | **Not `PIL.Image.convert("LAB")`** — `07-architecture.md` §4.1 |
| Fill reading | one vision call per frame, all trays at once, strict JSON | **every frame, ~1,980 calls** — see below |
| Tray count | **read off the first frame, never configured** | An assumed 8 is a number that can be wrong |
| Analysis | numpy + pandas on a laptop | Nothing runs at the stall after capture |
| Recommendation | one LLM call over the dish-day table + `context.md` | Constrained to her six levers, or it suggests a loyalty programme |
| Transport | **`rsync` over the stall's WiFi, every 10 min** | Frames leave while service is still running |

**Dependency count at the stall: one.** OpenCV, for the webcam and the colour maths.

**Analyse every frame.** The original plan analysed roughly one frame in three on the grounds that
thousands of calls were wasteful. Measured, that subsampling costs **−23% on `cooked_total` instead
of −9.5%** `[RE-MEASURED, 22 Sep]`. Full-rate analysis over an 11-hour day is **~1,980 calls, about
US$2** for the week on `gemini-2.5-flash` with thinking off — so the cost argument for subsampling
is now dead twice over: it was already wrong on accuracy, and it is no longer even cheap.

**The tray count is read, not configured.** Every document in this repo said "8 trays." Nobody has
counted them. The analysis segments the row from the first frame and reports what it found; if that
disagrees with what you expected, it says so on day 1, when the crop can still be fixed.

---

## Performance & Scale

One user initially, with targets of **≥5 usable service days per dish, zero frames containing a
recognisable person, and a stated model-vs-eye agreement rate.** Data volume **~24 MB per day,
~150 MB for the week, ~2,000 JPEGs and ~1,400 CSV rows**; one region — one stall, SUTD canteen.
Uptime requirements are **none in the SLA sense; the requirement is that a crash is self-healing.**
`capture.py` starts on boot, so if it dies the next boot fixes it, and a two-minute cadence means a
lost frame costs two minutes, not a day.

**The honest performance statement for the slide:**

> One stall, six days. The claim is *"this dish came back more than half full on five of six days,
> and here is the photograph"* — **not** *"vegetables sell 23% better when you move them."*

Stating the sample size, and stating which of the two numbers is exact, is what separates this from
the teams who will overclaim.

---

## Design & Branding

**No branding at all on the thing she receives.** The primary colour is **the actual colour of her
own food**, photographed — the only accent is **one arrow.** Brand guidelines: **nowhere; there is
no brand.** Design system: **none.**

The four load-bearing properties of the page, from `06` §4:

1. **It is her own stall.** `04` §7 closes: *"the measurement has to be theirs, not yours — a number
   they trust because it came off their own stall, not a claim in a slide."* Two photographs of her
   own tray four hours apart are not a claim; they are the thing itself. **A load cell could never
   have produced this** — the single strongest argument for the pivot.
2. **It needs almost no English.**
3. **There is exactly one recommendation.** Not five. Five get zero of them done.
4. **It is free, fast and reversible.**

Deliverable slides (Scale-Up Plan PDF, due 1 Oct) are the only place a visual system exists.

---

## Content Strategy

**No CMS.** Existing data at `03-hawker-5w1h.md` and `04-hawker-journey-map.md` needs **no
migration — the research holds; the pivot changed the instrument, not the problem.** SEO: **none.**
Analytics: **none; the analytics *are* the product output.** **No dynamic content and no javascript
embed anywhere in this system.**

**The one content artifact that genuinely matters is `context.md`.**

> Her own knowledge, in her own words, one page, read by the recommendation call.

This exists because of the sharpest critique the project faces, which she delivered herself: **she
already knows which dishes sell badly** `[T3]`. A system whose weekly output is *"kangkong sells
slowly"* has told an expert something she has known for ten years, and she will stop reading it in
week two. `context.md` holds which dishes she says sell fast and slow, which she will not drop, what
she has already tried, and her supplier and tray constraints.

**Not a database, not Obsidian, not a knowledge graph.** One markdown file, a page long, pasted into
the prompt. The three things the camera can say that she cannot already know:

| Her knowledge | What the camera adds |
|---|---|
| *"Kangkong sells slowly"* | **How much came back** — exactly, off her own tray, six days running |
| *"I top up when it looks low"* | **Which of those top-ups was still sitting there at close**, to the minute |
| *"That's just how it is"* | **Whether a change worked.** Nobody can A/B test their own display while running a stall |

---

## Security & Compliance

**Physical-privacy-by-construction**, with **no GDPR or CCPA exposure — no personal data is
collected, stored or transmitted, and there is no controller, processor or data subject.** Industry
regulations: **SFA food hygiene rules governing anything mounted near an open food display, and the
canteen operator's own permission for a fixture in shared space — neither is a software compliance
regime, and both are real.** Encryption: **not applicable — there is nothing to encrypt.**
**`fill_raw` retained unmodified beside every smoothed `fill`** for audit.

**The privacy claim is a property of the code, not a policy:**

- The camera points **down at food**, oblique, at the tray row.
- **The crop is applied before the JPEG is written to disk.** A customer at the frame edge never
  reaches storage — not "is deleted later," *never exists*.
- Verified on day 1 by opening frames and checking. If a person appears, the crop is tightened
  before day 2.

Two live obligations, neither of them software:

1. **Canteen permission.** The stall owner cannot authorise a fixture in shared space. Mounting on
   her own sneeze guard — her fixture, her stall — is the materially easier argument, and it is the
   one to make. **This is the single thing that can stop the mount.**
2. **Her informed consent**, given in person, with the crop shown to her on a phone screen — *"show
   her the crop, not a privacy policy"* `06` §3.

**Audit trail, in the sense that matters here:** the hand-coded audit day. ~190 readings coded by
eye into `fill_hand`, producing a stated agreement rate. *"The model agreed with me on 87% of
readings"* is the number a judge asks for. *"The model read the trays"* is not.

---

## Integrations

Integrate with **nothing**; connect to **one vision API and one text API, both called from a laptop
after the week, never from the stall**. Webhooks: **none** — there is no inbound network path. API
strategy: **expose none.** Data portability: **total and trivial — the entire dataset is CSV and
JPEG in a folder. She can keep it, read it in Excel, or delete it.**

**Third-party services deliberately not used:** no cloud storage, no MQTT broker, no IoT platform, no
fleet management, no telemetry, no crash reporting. The Pi is on the stall's WiFi `[T4]` and uses it
for exactly two things — NTP and `rsync` — both outbound, both able to fail without costing a frame.
**Having a network is not the same as depending on one**, and every service on this list would
convert the second into the first.

---

## Multi-Platform Needs

Mobile app: **none, for anybody.** Offline functionality should **be how capture behaves even though
the network exists.** Real-time features: **none. The output is weekly, and a live nudge is
explicitly phase 2** (`05` §4.7). Push notifications: **never.** One device: **a Raspberry Pi 5 with
one USB webcam.**

| # | Option | Verdict |
|---|---|---|
| 1 | **`rsync` on a 10-minute cron over the stall's WiFi** | **Do this.** The laptop holds today's frames *before today ends* |
| 2 | **USB stick left permanently in, cron mirror** | Do this *as well*. One line, and it survives the WiFi being down all week |
| 3 | Phone hotspot + `rsync` at close | **Fallback**, for the day the stall's WiFi is out |
| 4 | Ethernet straight to the laptop | Fine second fallback. `ssh pi@raspberrypi.local` works on Bookworm with no config |
| 5 | Pi as a WiFi access point | No. It would take the Pi off the network that supplies both NTP and transport |
| 6 | ~~Pull the microSD card daily~~ | **No. Still the option that loses day 4** |

> **The rule the network must not break: capture never depends on it.** `capture.py` writes the JPEG
> to the card and returns. `rsync` is a *separate* cron job that may fail as often as it likes. WiFi
> dropping mid-service must cost **zero frames** — if a dropped connection can lose a frame, the
> design is wrong.

```bash
# on the Pi, crontab -e. --partial resumes; the trailing && keeps the mirror honest.
*/10 * * * * rsync -az --partial --append-verify /home/pi/frames/ laptop:~/traywatch/frames/
30  14 * * * rsync -a /home/pi/frames/ /media/usb/frames/ && sync
45  14 * * * /sbin/shutdown -h now
```

**The card never leaves the slot**, and the Pi is always powered down by `shutdown` rather than by
pulling the plug — the single largest cause of a Pi that will not boot. **Morning health check:**
`ssh pi@raspberrypi.local tail -1 frames.csv` from a phone says *booted, capturing, and this is the
last frame it wrote*. Run it every morning before walking away.

---

## Public Access & Marketing

**None — there is no web presence, no landing page and no logged-out state.** The only published
artifact is a stale Claude artifact (`e1c1e124`) listed as known-wrong in `CLAUDE.md` and scheduled
for replacement or withdrawal. **Nothing** is visible before login; **there is no authentication
anywhere in this system.** Marketing tools: **none.** Lead capture: **does not exist.**

Go-to-market, for the Scale-Up Plan slides only: sell to **food court operators** (Koufu, Kopitiam,
Fei Siong) who control fit-out and already carry sustainability reporting, or rent rather than sell,
or fund through NEA hawker programmes. **The operator buys the fleet; the stall owner's ninety
seconds a week stay identical.** That invariance is the test of whether the design holds.

---

## Timeline & Resources

Target launch **1 Oct 2026 (deliverables) / 2 Oct 2026 (public showcase, Temasek Shophouse)** with a
budget of **≤S$20, possibly S$0**, against S$160.50 remaining, every item requiring the mentor's
written approval before purchase. Team: **one person — a solo SUTD undergraduate, team name
"autobots" — researcher, builder, installer, labeller and analyst.**

### Budget — collapsed since the last revision

| Item | ~S$ | Note |
|---|---|---|
| ~~microSD 32 GB A1~~ | ~~15~~ | **Bought** `[T4]`. Receipt still needs to reach `FINANCE CLAIMS/` |
| ~~USB webcam, 1080p~~ | ~~30~~ | **Already owned** `[T6, 21 Sep]`. No purchase, no courier, no approval, no wait |
| ~~RTC backup battery~~ | ~~8~~ | **Struck** `[T4]`. The stall has WiFi; NTP does it free |
| USB extension, 3 m | 0–5 | Only if not already owned. Keeps the Pi off a hot greasy counter |
| Mount hardware | 0–15 | **Decide after seeing her stall, not before.** Tape and a clamp may do |
| Grey card | printed | Free, and the colour measurement is worthless without it |
| **Total** | **≤20** | Vision API for the week at full frame rate: **US$13** |

Already spent: **S$239.50** — 2 × Pi 5 2 GB (Cytron CI14269757, S$196.00) and 3 × PETG filament
(PolyMate INV/26/09/018, S$43.50). **There is no Pi 4 in this project. There is no kitchen scale and
there will not be one** — `05` §6.1.

**Do not send the mentor a purchase request before the mount.** The camera is owned; the remaining
items are decided by looking at her sneeze guard. If something is genuinely needed it is under S$20,
and it comes with the one-paragraph justification sourced to what she said — that was her exact
complaint `[T3, 17 Sep]`.

### Schedule — rebuilt 21 Sep, because the camera is already here

| Date | |
|---|---|
| **Mon 21 Sep** | Check `v4l2-ctl --list-ctrls` for WB/exposure locks. Print the grey card. Bench the capture loop at home |
| **Tue 22 Sep** | **Mount at open.** Set crop geometry on-site, verify no person in frame, confirm the tray count off frame 1. Day 1 data kept if it works |
| **Wed 23 – Tue 29 Sep** | **Service days. Row swapped once daily in the 13:30–17:00 lull, order counterbalanced** |
| **Wed 30 Sep** | `analyse.py`, `report.py`, hand-code the audit day, write-up, slides, People Log |
| **1 Oct** | Deliverables due |
| **2 Oct** | Showcase |

Six weekday service days — Tue 22, Wed 23, Thu 24, Fri 25, Mon 28, Tue 29 — **if the canteen is
weekdays-only, which is unconfirmed.** Nothing in the design depends on the answer: capture runs
every day, and a closed day is simply a day with no frames.

**The row is swapped once a day, in the lull, and the ORDER alternates** — arrangement A in the
morning on Wed/Fri/Tue, B in the morning on Thu/Mon — so each dish sees both arrangements every day
and neither arrangement is systematically the morning one. Counterbalancing is what makes the
block effect (mornings sell more than evenings) cancel across days; without it the design just
trades a day confound for a time-of-day confound, which is worse because it is constant.

Three-then-three is still wrong for the same reason it always was: a block confounds the
intervention with everything else that changes later in a week.

**Compliance is measured, not assumed.** The swap is visible in the frames, so KPI K8 reads the
actual swap time off the imagery rather than trusting a schedule — and `from_ts` in `dishes.csv`
records what really happened, including the days she forgot.

### KPIs

| # | KPI | Target | Why this one |
|---|---|---|---|
| **K1** | Service days with no capture gap | **6 / 6** | A gap on day 5 is unrecoverable |
| **K2** | Dishes with ≥5 usable days | **all**, or **named exceptions** | Honesty beats coverage, and naming them is what stops the p=0.0000 bug |
| **K3** | Frames containing a recognisable person | **0** | The privacy claim is falsifiable, so falsify it |
| **K4** | Model-vs-eye agreement on the audit day | **stated, whatever it is** | A number, not an adjective |
| **K5** | **Dishes with a `leftover_close` finding she did not already know** | **≥1** | The answer to her own sharpest critique |
| **K6** | **Late top-ups identified that were still unsold at close** | **≥1, with timestamp and photo** | F5 is the product, and no bin can produce it |
| **K7** | Arrangement arm: effect size **and CI**, p-value **not reported** | **reported as exploratory** | It cannot reach 0.05 — `design_checks.py` C1/C2 |
| **K8** | Days she kept to the arrangement schedule | **6 / 6, read off the frames** | The only behavioural KPI that fits inside the window |

**K5 and K6 are the real ones.** K8 replaces the old *"did she make the recommended change?"*, which
was unmeasurable by construction: capture ends 29 Sep, the page is produced 30 Sep, and the showcase
is 2 Oct — **there is no second week inside the window in which she could act.** What *is* measurable
is whether she kept to the daily arrangement, and the camera audits that itself, from the frames,
with nothing for anyone to self-report.

---

## After MVP is finished and operational

1. **The weekly loop becomes automatic rather than hand-run:**
   - The card is imaged on insertion and the pipeline runs without being invoked
   - The page renders to PDF and prints without a human assembling it
   - Each week's recommendation is checked against the *next* week's data automatically, so the
     system scores its own advice — the same feedback-wire idea Chope is built around
   - A recommendation that failed twice is retired rather than repeated

2. **The rearrangement experiment, run properly.** `design_checks.py` C1/C2 says what that takes:
   **nine or more trays** (n=6 clean dishes, floor p=0.031) and **four to six weeks**, not six days.
   This is a genuine scale-up argument rather than an apology — the instrument is already built, and
   the only missing ingredient is time the hackathon does not have.

3. **A live L3 nudge** that will **watch the trays during service and signal once, quietly, when a
   late top-up is about to become waste**, so she can **stop refilling tray 4 at 1:30pm on the day
   rather than reading about it the following Monday.** Requires on-device inference or a cheap
   arithmetic proxy, a signal she can see from where she stands, and a hard rule that it never fires
   twice for the same tray in one service. **Explicitly out of scope before 2 Oct** — `05` §4.7.

4. Administration dashboard for **a fleet of stalls under one food court operator**, with **per-stall
   leftover trends and a site-level sustainability figure the operator can put in a report** and
   **nothing else — the stall owner's paper page is not replaced by it.**

---

## Monitoring & Operations

Monitoring is **`frames.csv` and the `n_frames` column** for errors and **a daily eyeball of the
day's folder** for performance. `bytes = 0` in `frames.csv` means the camera failed that cycle, and a
low `n_frames` in `daily.csv` means a camera gap rather than a quiet day — **that distinction is the
difference between a missing observation and a false zero.** User behavior tracking: **none.** A/B
testing: **the alternating baseline/rearranged schedule**, which is the exploratory arm.
Maintenance windows: **none; there is nothing to maintain, which is the point** `04` §7.

**Nulls are a live operational hazard and are called out in the schema:** `sold_out_ts` and
`last_refill_ts` are null far more often than not, and `over_provision` is undefined when a dish sold
nothing. Anything treating those nulls as zero will silently report that a dish sold out at midnight.

**And the analysis must fail loudly, not flatteringly.** `design_checks.py` C3 is in the repo
precisely so this cannot be quietly forgotten: a dish missing an arrangement arm produced **p =
0.0000**, perfect significance out of a hole. Incomplete dishes are dropped **by name, in the output**,
and the arm refuses to run below n=6.

---

## Legal Stuff

**No terms of service.** **No privacy policy — but a verbal, in-person explanation with the crop
shown on a phone, which is stronger.** **No cookie compliance; there is no website.** IP protection:
**none sought; the repo is public on GitHub and the hackathon deliverables are public.** Data
retention: **frames and CSVs are kept through 2 Oct for the showcase timelapse, then deleted or
handed to her, her choice.**

| | |
|---|---|
| **Canteen / SUTD permission for a fixture in shared space** | **Unresolved. Blocks the mount** |
| Her consent to a camera on her stall | Given in person, crop shown `[T3]` |
| SFA rules on fixtures near an open food display | Check before drilling anything |

---

**Special considerations:** **She already knows which dishes sell badly, and she said so.** Take it
seriously — it is the sharpest critique the project faces, and the answer is `context.md` plus the
three things in §Content Strategy that she cannot know, of which **the exact quantity that came back**
and **which timed top-up was still sitting there at close** are now both measured rather than hoped
for. Also: **the first analysis must be allowed to kill the premise.** Group `leftover_close` by
`is_veg` before anything else; if vegetables waste *less* than the meat dishes, that is a finding, not
a failure. Assuming the answer and then presenting it is what loses to a judge who reads carefully.

**Technical constraints:** The stall has WiFi `[T4]`, which fixes the clock and moves the data — and
makes one failure routine. The Pi 5's RTC has no battery, so it boots at the last shutdown time and
NTP then **steps the clock backwards** seconds later. `HHMM.jpg` filenames would collide and
`imwrite` would overwrite silently. With no network that was a rare risk; **with a network it is every
morning.** Frames are therefore named by **sequence number**, never by the clock, every row carries
both wall-clock and `CLOCK_BOOTTIME`, and the capture unit is gated on `time-sync.target` —
`07-architecture.md` §2.5. Both boards are Pi 5, so CSI would need a 22-way adapter; **the webcam is
owned and this is moot** `[T6]`. `PIL.Image.convert("LAB")` silently produces garbage `[VERIFIED]` —
use OpenCV. Auto white balance must be locked *and* backed by the grey card, **and the lock must be
verified** — a `set()` that silently no-ops loses the colour half with no error. Oblique mounting means
near trays partly occlude far trays; accept it and check on day 1.

**Business constraints:** S$160.50 remaining across both prototypes, every purchase gated on the
mentor's written approval `[T3, 17 Sep]`. Ten days, solo. Thousands of tiny customers makes this the
better prototype but the harder business — the buyer at scale is the food court operator, not the
stall.

**Long-term vision:** **Move the whole category from accounting to prevention.** Every incumbent
measures waste after it happens, because the bin is where measurement is easy. The display is where
the decision is still reversible. An instrument costing under S$20 on hardware already owned, that
tells a stall owner exactly how much of each dish came back and which top-up she should not have made,
is a different product class from a £10,000 smart bin that tells a hotel what it already threw away —
and it is the only one that fits the bottom of the market, which is most of the market.
