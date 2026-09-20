# PRD — Tray Watch (Prototype 2)

> **A note on this document's shape.** It follows a standard SaaS platform PRD template, heading for
> heading. Tray Watch is not a SaaS platform — it is a camera on a hawker stall — so a large
> number of fields are answered **"None, and here is why."** Those answers are kept rather than
> deleted, because *what a product deliberately does not have* is the most defensible part of this
> entry. A PRD claiming a payment processor and a CDN for a Raspberry Pi writing CSVs to an SD card is
> what a judge takes apart first.
>
> **Provenance.** `[T3]` stall owner, interviewed 17 Sep · `[cited]` public source · `[DERIVED]`
> implied by cited facts · `[VERIFIED]` tested, output in `07-architecture.md` · `[ASSUMED]` needs
> fieldwork. Source documents: `03-hawker-5w1h.md`, `04-hawker-journey-map.md`,
> `05-traywatch-plan.md` (build + schema), `06-traywatch-user-journey.md`, `07-architecture.md`.

---

I need to build a simple yet robust MVP for **a display-side food waste prevention instrument** targeting **independent cai png (mixed rice) hawker stalls, and the food court operators above them**. This will primarily solve **the fact that vegetables go unsold, get binned, and keep being re-bought at the same rate — because the stall owner has no way to test whether anything she changes about her display actually works** and our main competitive advantage is **every competitor points their camera at the bin; this one points at the display, during service, while there is still time to act.**

The core functionality should handle **photographing a row of eight display trays every two minutes through a six-hour lunch service, reading each tray's fill level per frame, detecting mid-service refills as distinct from sales, computing each dish's colour and therefore its colour contrast against its neighbours, and producing one printed A4 page a week carrying two photographs and exactly one recommended change.**

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
kitchen, need cloud, and need a chef who interacts with them; they sell to hotels and large commercial
kitchens `[cited]`. Lumitics is literally a smart bin — you throw food in and press a green button.
**They measure the corpse.** Nobody serves the bottom of the market. This is ~S$73 of hardware, no
cloud, no app, no training, nothing to maintain — and it does not just report, it **changes the
display and measures whether that worked.** Prevention, not accounting.

---

## Core functionality

| # | Capability | Model involved? |
|---|---|---|
| F1 | Capture one cropped JPEG of the tray row every 2 min through service, unattended, **with no network call in the capture path** | no |
| F2 | Read fill level 0–100 per tray per analysed frame, **plus an `obscured` flag** | **yes — vision** |
| F3 | Distinguish a refill from a sale (she tops trays up mid-service, so `start − end` is wrong) | no |
| F4 | Compute each dish's median CIELAB and its ΔE contrast to its left and right neighbours | no |
| F5 | Aggregate to 48 dish-days: served, cooked, leftover, over-provision, last refill, sell-out time | no |
| F6 | Within-dish sign-flip permutation test of `served_total` against arrangement, n=8 dishes | no |
| F7 | Emit one A4 page: two photographs, one sentence, one change | **yes — one call** |
| F8 | Hand-coded audit day yielding a model-vs-eye agreement rate | no — that is the point |

**F3 is the product, not an implementation detail.** Fill alone gives `start − end`. Deltas give the
decision: *"a tray topped up at 2:15pm that is still 60% full at close — that top-up went straight
into the bin, and it is identifiable to the minute."*

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
│  You cooked about 3 trays. You sold about 1.        │
│                                                     │
│  ► Put the kangkong between the curry chicken       │
│    and the tofu tomorrow.                           │
└─────────────────────────────────────────────────────┘
```

Key interactions should **cost her thirty seconds and be undoable tomorrow.** The only action the
product ever asks for is moving two trays at open. Free, fast, reversible — anything failing one of
those three does not get done by someone on a 10–15% net margin working twelve-hour days
`04-hawker-journey-map.md` §4.

The overall user journey will **be flat for six days and then ninety seconds long.** Install takes ten
minutes once. For the whole logging week her emotional line does not move, and **that is the design
achievement, not a gap in the map** — `04` §7 requires *"zero interaction during service, zero manual
data entry ever, survives being ignored."* Then: she reads the page, moves two trays, and the
following week's page tells her whether it worked. Full detail in `06-traywatch-user-journey.md`.

We need **near-zero-literacy** accessibility support and **effectively no language dependency** for
internationalization. This is not a nicety and it is not the usual WCAG checklist — it is the
difference between a product she uses and a document she is polite about:

- **Two photographs and one arrow carry the entire finding.** The sentence is a courtesy, not the
  payload.
- English is not necessarily her first language `[ASSUMED]`; Mandarin, Hokkien, Teochew and Malay are
  all live possibilities in a Singapore cai png stall.
- Units are **trays and percentages**, never grams — *"you cooked about 3 trays, you sold about 1"* —
  because that is the unit she already thinks in.
- Printed on paper, so it works with reading glasses, wet hands, no battery and no login.
- **WCAG is not applicable** — there is no web interface to conform to. The accessibility requirement
  here is real and physical, and it is stricter.

There will also be **a looping forty-second timelapse of the real week** (one `ffmpeg` line over the
JPEGs already on the card) that should be accessible in a **laptop-on-a-table, no-network** manner —
that is the showcase artifact for 2 Oct, and it cannot crash. The entire application must be
**paper-first and offline-first** first and foremost.

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
the favour, not the other way round. **Operator** users (**a per-site rental, not a per-stall licence
sale — thousands of tiny customers is the harder business, so do not sell stall-by-stall**) would get
**the fleet view plus the per-stall page delivered by phone instead of on paper.**

We're planning **no** trial periods, and the onboarding process will **be a ten-minute conversation
and a camera going up while she stands aside** — plus fifteen minutes of her talking, which becomes
`context.md` (below). There is no account to create, no form to fill, and nothing to configure.

Payments will be collected with **nothing. There is no monetisation in the MVP and no payment code
anywhere in this repo.** The commercial model is in `06` §7 and `CLAUDE.md` §Business framing; it is a
scale-up argument for the slides, not a feature of the prototype.

---

## Technical Stack

This will be deployed on **a Raspberry Pi 5 (2 GB) already owned, running Raspberry Pi OS, on the
stall's WiFi — outbound only, nothing listens**, so a **plain Python 3 script started by systemd** app is probably
best. Use **no authentication service** for user management — **there are no users in the software
sense, no accounts, no identities and no login**. Database can be **five plain files: CSV and one
JSON, about 1,400 rows for the entire week.** A database would be strictly more code, more failure
modes and more to explain, for zero benefit at this volume. For static assets and performance, we'll
use **no CDN — nothing is ever served to anybody** and our backup strategy is **`rsync` every ten
minutes over the stall's WiFi, so the laptop holds the day while the day is still happening.** The
card stays in the slot and is the second copy, not the first. A camera gap on day 1 is recoverable;
losing five days on day 5 is not — and this is the change that makes losing them nearly impossible.

| Layer | Choice | Why not the usual thing |
|---|---|---|
| Stall runtime | Python 3 + OpenCV, ~40 lines, systemd | No framework. It writes JPEGs to a folder |
| Storage | `frames.csv`, `trays.json`, `readings.csv`, `events.csv`, `daily.csv` | 1,400 rows. SQLite would be defensible; a server is not |
| Colour maths | `cv2.cvtColor` on float32 → true CIELAB `[VERIFIED]` | **Not `PIL.Image.convert("LAB")`** — see `07-architecture.md` §4.1 |
| Fill reading | one vision call per frame, all 8 trays at once, strict JSON | ~340 calls, not thousands. Tray numbers burned into the image |
| Analysis | numpy + pandas on a laptop | Nothing runs at the stall after capture |
| Recommendation | one LLM call over the 48-row table + `context.md` | Constrained to her six levers, or it suggests a loyalty programme |
| Transport | **`rsync` over the stall's WiFi, every 10 min** | Frames leave while service is still running. See §Multi-Platform |

**Dependency count at the stall: one.** OpenCV, for the webcam and the colour maths. That is the whole
stack.

---

## Performance & Scale

We're expecting **one** user initially, with performance targets of **≥5 usable service days per dish,
zero frames containing a recognisable person, and a stated model-vs-eye agreement rate.** Data volume
should be around **24 MB per day, ~150 MB for the week, ~2,000 JPEGs and ~1,400 CSV rows** and we need
to serve **one** region — one stall, in the SUTD canteen. Uptime requirements are **none in the SLA
sense; the requirement is that a crash is self-healing.** `capture.py` starts on boot, so if it dies
the next boot fixes it, and a two-minute cadence means a lost frame costs two minutes, not a day.

**The honest performance statement for the slide:**

> One stall, six days, 48 dish-days. The claim is *"this instrument detects a contrast effect and here
> is the direction it points"* — **not** *"vegetables sell 23% better."*

Stating the sample size is what separates this from the teams who will overclaim.

---

## Design & Branding

The design should have **no branding at all on the thing she receives.** The primary colour is **the
actual colour of her own food**, photographed — and the only accent is **one arrow.** Our
brand guidelines are at **nowhere; there is no brand** and we'll need **no design system** for
consistency.

The four load-bearing properties of the page, from `06` §4:

1. **It is her own stall.** `04` §7 closes: *"the measurement has to be theirs, not yours — a number
   they trust because it came off their own stall, not a claim in a slide."* Two photographs of her own
   tray four hours apart are not a claim; they are the thing itself. **A load cell could never have
   produced this** — it is the single strongest argument for the pivot.
2. **It needs almost no English.**
3. **There is exactly one recommendation.** Not five. Five get zero of them done.
4. **It is free, fast and reversible.**

Deliverable slides (Scale-Up Plan PDF, due 1 Oct) are the only place a visual system exists, and they
inherit the hackathon deck's format.

---

## Content Strategy

We'll need **no CMS** for content management. There's existing data at **`03-hawker-5w1h.md` and
`04-hawker-journey-map.md`** that needs migration — **no migration, they stay unchanged. The research
holds; the pivot changed the instrument, not the problem.** For SEO, we want **none — nothing is
published to the web.** and we'll track everything with **no analytics tooling; the analytics *are*
the product output.** Note that **there is no dynamic content and no javascript embed anywhere in this
system** — so there is nothing to ensure compatibility with.

**The one content artifact that genuinely matters is `context.md`.**

> Her own knowledge, in her own words, one page, read by the recommendation call.

This exists because of the sharpest critique the project faces, which she delivered herself: **she
already knows which dishes sell badly** `[T3]`. A system whose weekly output is *"kangkong sells
slowly"* has told an expert something she has known for ten years, and she will stop reading it in week
two. `context.md` holds which dishes she says sell fast and slow, which she will not drop, what she has
already tried, and her supplier and tray constraints — so the model's output *starts* from her
expertise instead of colliding with it.

**Not a database, not Obsidian, not a knowledge graph.** One markdown file, a page long, pasted into
the prompt. The three things the camera can say that she cannot already know:

| Her knowledge | What the camera adds |
|---|---|
| *"Kangkong sells slowly"* | **How** slowly — the depletion curve — and therefore how much less to cook |
| *"I top up when it looks low"* | **Which of those top-ups went in the bin**, to the minute |
| *"That's just how it is"* | **Whether a change worked.** Nobody can A/B test their own display while running a stall |

---

## Security & Compliance

We need **a physical-privacy-by-construction** security level with **no GDPR or CCPA exposure — no
personal data is collected, stored or transmitted, and there is no controller, processor or data
subject** compliance. Industry regulations include **SFA food hygiene rules governing anything mounted
near an open food display, and the canteen operator's own permission for a fixture in shared space —
neither is a software compliance regime, and both are real.** Data encryption should be **not
applicable — there is nothing to encrypt, because no personal data exists and nothing leaves the SD
card** and we need **`fill_raw` retained unmodified beside every smoothed `fill`** for audit trails.

**The privacy claim is a property of the code, not a policy:**

- The camera points **down at food**, oblique, at the tray row.
- **The crop is applied before the JPEG is written to disk.** A customer at the frame edge never
  reaches storage — not "is deleted later," *never exists*.
- Verified on day 1 by opening frames and checking. If a person appears, the crop is tightened before
  day 2.

Two live obligations, neither of them software:

1. **Canteen permission.** The stall owner cannot authorise a fixture in shared space. Mounting on her
   own sneeze guard — her fixture, her stall — is the materially easier argument, and it is the one to
   make. **This is the single thing that can stop the Monday mount, and it must be settled before
   hardware goes up.**
2. **Her informed consent**, given in person, with the crop shown to her on a phone screen — *"show her
   the crop, not a privacy policy"* `06` §3.

**Audit trail, in the sense that actually matters here:** the hand-coded audit day. ~190 readings coded
by eye into `fill_hand`, producing a stated agreement rate. *"The model agreed with me on 87% of
readings"* is the number a judge asks for. *"The model read the trays"* is not.

---

## Integrations

We'll need to integrate with **nothing** and connect to **one vision API and one text API, both called
from a laptop after the week, never from the stall** APIs. Webhook support for **nothing** is required
— there is no inbound network path and no event any external system needs. Our API strategy is **to
expose none** and data portability needs are **total and trivial: the entire dataset is CSV and JPEG
in a folder. She can keep it, read it in Excel, or delete it.**

**Third-party services deliberately not used:** no cloud storage, no MQTT broker, no IoT platform, no
fleet management, no telemetry, no crash reporting. The Pi is on the stall's WiFi `[T4, 19 Sep]` and
uses it for exactly two things — NTP and `rsync` to a laptop — both outbound, both able to fail without
costing a frame. **Having a network is not the same as depending on one**, and every service on this
list would convert the second into the first.

---

## Multi-Platform Needs

Mobile app requirement: **none, for anybody.** Offline functionality should **be how capture behaves
even though the network exists** — see the rule below. Real-time features needed: **none. The output is
weekly, and a live nudge is explicitly phase 2** (`05` §4.7). Push notifications will **never be sent to
anyone** and we need to support **one device: a Raspberry Pi 5 with one USB webcam.**

**How the data physically moves.** `[T4, 19 Sep: the Pi has internet at the stall.]` ~150 MB for the
week. That revises the earlier ranking — the previous #1 was a phone hotspot held up for sixty seconds
at close, which was the best available answer only because no network was assumed.

| # | Option | Verdict |
|---|---|---|
| 1 | **`rsync` on a 10-minute cron over the stall's WiFi** | **Do this.** The laptop holds today's frames *before today ends*. Nothing else on this list can say that |
| 2 | **USB stick left permanently in, cron mirror** | Do this *as well*. One line, and it is the copy that survives the WiFi being down all week |
| 3 | Phone hotspot + `rsync` at close | **Demoted to the fallback**, for the day the stall's WiFi is out |
| 4 | Ethernet straight to the laptop | Fine second fallback. `ssh pi@raspberrypi.local` works on Bookworm with no config |
| 5 | Pi as a WiFi access point | No. It would take the Pi off the network that now supplies both NTP and transport |
| 6 | ~~Pull the microSD card daily~~ | **No. Still the option that loses day 4.** Every extraction is a fresh chance the card doesn't reseat, the filesystem is dirty, or Windows touches the boot partition |

> **The rule the network must not break: capture never depends on it.** `capture.py` writes the JPEG to
> the card and returns. `rsync` is a *separate* cron job that may fail as often as it likes. WiFi
> dropping mid-service must cost **zero frames** — if a dropped connection can lose a frame, the
> design is wrong. This is the whole reason the stall device stays a dumb logger even with internet.

```bash
# on the Pi, crontab -e. --partial resumes; the trailing && keeps the mirror honest.
*/10 * * * * rsync -az --partial --append-verify /home/pi/frames/ laptop:~/traywatch/frames/
30  14 * * * rsync -a /home/pi/frames/ /media/usb/frames/ && sync
45  14 * * * /sbin/shutdown -h now
```

**The card never leaves the slot**, and the Pi is always powered down by `shutdown` rather than by
pulling the plug — the single largest cause of a Pi that will not boot. **The morning health check is
now better than it was:** there is no screen, but the Pi is on the network, so `ssh pi@raspberrypi.local
tail -1 frames.csv` from a phone says *booted, capturing, and this is the last frame it wrote*. The
hotspot version could only ever say "it booted." Run it every morning before walking away.

---

## Public Access & Marketing

We will also need a **none — there is no web presence, no landing page and no logged-out state** for
non-logged in users. See **nothing; the only published artifact is a stale Claude artifact
(`e1c1e124`) listed as known-wrong in `CLAUDE.md` and scheduled for replacement or withdrawal** for our
current page which we will need to port over. **Nothing** should be visible before login, but to access
**anything** the user must authenticate — **there is no authentication anywhere in this system.**
Marketing tools we use: **none** and lead capture should **not exist.**

The actual go-to-market argument, for the Scale-Up Plan slides only: sell to **food court operators**
(Koufu, Kopitiam, Fei Siong) who control fit-out and already carry sustainability reporting, or rent
rather than sell, or fund through NEA hawker programmes. **The operator buys the fleet; the stall
owner's ninety seconds a week stay identical.** That invariance is the test of whether the design
holds.

---

## Timeline & Resources

Target launch is **1 Oct 2026 (deliverables) / 2 Oct 2026 (public showcase, Temasek Shophouse)** with a
budget of **~S$73 of new purchases, against S$160.50 remaining of S$400, every item requiring the
mentor's written approval before purchase.** Our team consists of **one person — a solo SUTD
undergraduate, team name "autobots" — who is the researcher, the builder, the installer, the labeller
and the analyst.** We'll measure success by **the KPIs below** and we're competing against **Winnow,
Leanpath, Orbisk and Lumitics — all of whom point the camera at the bin.**

### Budget

| Item | ~S$ | Note |
|---|---|---|
| ~~microSD 32 GB A1~~ | ~~15~~ | **Bought** `[T4, 19 Sep]`. Off the list. Receipt still needs to reach `FINANCE CLAIMS/` |
| USB webcam, 1080p, 90°+ FOV | 30 | Must support locking white balance — any UVC cam does, via `v4l2-ctl` |
| USB extension, 3 m | 5 | Keeps the Pi off a hot greasy counter, where 50 cm of CSI ribbon cannot |
| Mount hardware | 15 | After measuring her stall |
| ~~RTC backup battery~~ | ~~8~~ | **Struck** `[T4, 19 Sep]`. It existed only to give a networkless Pi a plausible clock. The stall has WiFi, NTP does it free. Do not ask the mentor for what a working network already handles |
| Grey card | printed | Free, and the colour experiment is worthless without it |
| **Total** | **~50** | Down from ~73: the card is bought and the RTC battery is struck. Vision API for the entire week: **US$4**, verified against current pricing |

Already spent: **S$239.50** — 2 × Pi 5 2 GB (Cytron CI14269757, S$196.00) and 3 × PETG filament
(PolyMate INV/26/09/018, S$43.50). **There is no Pi 4 in this project. There is no kitchen scale and
there will not be one** — `05` §6.1.

**USB webcam, not the Pi camera module**, because the Pi 5's camera connector is 22-way 0.5 mm and
every current camera product ships the 15-way 1 mm FPC, so CSI means waiting on an adapter cable with
13 days on the clock. Also check the power supply: the Pi 5 caps total USB current at 600 mA unless it
detects a 5 A-capable USB-C PD supply.

### Schedule

| Date | |
|---|---|
| **Fri 18 Sep** | Phone test at the stall. Ask her N1–N4, A3, A5. Message the mentor. Buy |
| Sat–Sun 19–20 Sep | Flash the card. `capture.py`. Bench the loop on a tray at home. Print the grey card |
| **Mon 21 Sep** | Mount at open. Set crop geometry on-site. Dry run — data kept if it works |
| **Tue 22 – Mon 28 Sep** | **Six service days, alternating baseline / contrast** |
| 29–30 Sep | `analyse.py`, `report.py`, hand-code the audit day, write-up, slides, People Log |
| **1 Oct** | Deliverables due |
| **2 Oct** | Showcase |

**Zero slack.** That is the entire argument for buying a webcam off a shelf rather than waiting on a
courier.

### KPIs

| # | KPI | Target | Why this one |
|---|---|---|---|
| K1 | Service days with no capture gap | **6 / 6** | A gap on day 5 is unrecoverable |
| K2 | Dishes with ≥5 usable days | **all**, or named exceptions | Honesty beats coverage |
| K3 | Frames containing a recognisable person | **0** | The privacy claim is falsifiable, so falsify it |
| K4 | Model-vs-eye agreement on the audit day | **stated, whatever it is** | A number, not an adjective |
| K5 | Refill events detected vs. her own account (N2) | **directionally consistent** | F3 is the product |
| K6 | **Did she make the recommended change?** | **yes / no, reported honestly** | The only behavioural KPI, and the one that matters |
| K7 | Within-dish sign-flip permutation test, n=8 dishes | **exact p reported with all four caveats** | The 48-point regression can never reach p<0.05 — `07` §5.5 |

**K6 is the real one.** A recommendation she does not act on is a report, not a product.

---

## After MVP is finished and operational

1. **The weekly loop becomes automatic rather than hand-run:**
   - The card is imaged on insertion and the pipeline runs without being invoked
   - The page renders to PDF and prints without a human assembling it
   - Each week's recommendation is checked against the *next* week's data automatically, so the system
     scores its own advice — the same feedback-wire idea Chope is built around
   - A recommendation that failed twice is retired rather than repeated

2. **A live L3 nudge** that will **watch the trays during service and signal once, quietly, when a
   late top-up is about to become waste**, so that users can **stop refilling tray 4 at 1:30pm on the
   day rather than reading about it the following Monday.** Technical requirements for this include
   on-device inference or a cheap arithmetic proxy (the food/metal boundary is computable without a
   model against a grey-card-normalised frame), a signal she can see from where she stands without
   looking at a screen, and a hard rule that it never fires twice for the same tray in one service.
   **Explicitly out of scope before 2 Oct** — `05` §4.7.

3. Administration dashboard for managing **a fleet of stalls under one food court operator**,
   including **per-stall leftover trends and a site-level sustainability figure the operator can put in
   a report** and **nothing else — the stall owner's paper page is not replaced by it.**

---

## Monitoring & Operations

For monitoring, we'll use **`frames.csv` and the `n_frames` column** for errors and **a daily
eyeball of the day's folder** for performance. `bytes = 0` in `frames.csv` means the camera failed
that cycle, and a low `n_frames` in `daily.csv` means a camera gap rather than a quiet day — that
distinction is the difference between a missing observation and a false zero. User behavior tracking
with **none** and A/B testing via **the alternating baseline/contrast schedule, which is the entire
experiment** — and it alternates rather than blocking three-then-three, because a block confounds the
intervention with everything else that changes later in a week. Maintenance windows are **none; there
is nothing to maintain, which is the point** `04` §7.

**Nulls are a live operational hazard and are called out in the schema:** `sold_out_ts` and
`last_refill_ts` are null far more often than not, and `over_provision` is undefined when a dish sold
nothing. Anything treating those nulls as zero will silently report that a dish sold out at midnight.

---

## Legal Stuff

We need **no terms of service** for terms of service, **no privacy policy — but a verbal, in-person
explanation with the crop shown on a phone, which is stronger** for privacy policy, and **no cookie
compliance; there is no website** for cookies. IP protection: **none sought; the repo is public on
GitHub and the hackathon deliverables are public** and data retention rules: **frames and CSVs are
kept through 2 Oct for the showcase timelapse, then deleted or handed to her, her choice.**

Three real legal or quasi-legal items, none of them software:

| | |
|---|---|
| **Canteen / SUTD permission for a fixture in shared space** | **Unresolved. Blocks the Monday mount** |
| Her consent to a camera on her stall | Given in person, crop shown `[T3]` |
| SFA rules on fixtures near an open food display | Check before drilling anything |

---

**Special considerations:** **She already knows which dishes sell badly, and she said so.** Take it
seriously — it is the sharpest critique the project faces, and the answer is `context.md` plus the
three things in §Content Strategy that she cannot know. Also: **the first analysis must be allowed to
kill the premise.** Group `leftover_close` by `is_veg` before anything else; if vegetables waste *less*
than the meat dishes, that is a finding, not a failure. Assuming the answer and then presenting it is
what loses to a judge who reads carefully.

**Technical constraints:** The stall has WiFi `[T4, 19 Sep]`, which fixes the clock and moves the data
— and makes one failure routine. The Pi 5's RTC has no battery, so it boots at the last shutdown time
and NTP then **steps the clock backwards** seconds later. `HHMM.jpg` filenames would collide and
`imwrite` would overwrite silently. With no network that was a rare risk; **with a network it is every
morning.** Frames are therefore named by **sequence number**, never by the clock, every row carries both
wall-clock and `CLOCK_BOOTTIME`, and the capture unit is gated on `time-sync.target` — see
`07-architecture.md` §2.5. No Pi 4 exists — both boards are Pi 5, so CSI needs a 22-way cable and a
wait. **The microSD is bought** `[T4]`.
`PIL.Image.convert("LAB")` silently produces garbage `[VERIFIED]` — use OpenCV. Auto white balance must
be locked *and* backed by the grey card or the experiment measures the canteen lighting. Oblique
mounting means near trays partly occlude far trays; accept it and check on day 1.

**Business constraints:** S$160.50 remaining across both prototypes, every purchase gated on the
mentor's written approval `[T3, 17 Sep]`. Thirteen days, solo, with a second prototype to finish.
Thousands of tiny customers makes this the better prototype but the harder business — the buyer at
scale is the food court operator, not the stall.

**Long-term vision:** **Move the whole category from accounting to prevention.** Every incumbent
measures waste after it happens, because the bin is where measurement is easy. The display is where
the decision is still reversible. A ~S$65 instrument that tells a stall owner which change to make and
then tells her whether it worked is a different product class from a £10,000 smart bin that tells a
hotel what it already threw away — and it is the only one that fits the bottom of the market, which is
most of the market.
