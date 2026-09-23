# PRD — Chope (Prototype 1)

> **A note on this document's shape.** It follows a standard SaaS platform PRD template, heading for
> heading. Chope is not a SaaS platform — it is a Telegram poll, a number on a screen, and a numeric
> keypad — so many fields are answered **"None, and here is why."** Those answers are kept rather than
> deleted: in a Green Zone, *what a system deliberately does not collect* is the load-bearing part of
> the design, not an omission.
>
> **Provenance.** `[T1]` Raghav's own service at SBAB · `[T2]` senior NSF interview, 4 Sep · `[cited]`
> public source · `[VERIFIED]` code in this folder, self-check passes · `[ASSUMED]` needs fieldwork.
> Sources: `00-master-plan.md`, `01-problem-map.md`, `02-journey-maps.md` (**most authoritative**),
> `07-architecture.md` at the repo root.

---

I need to build a simple yet robust MVP for **closing the feedback loop between a cookhouse bin and the forecast that filled it** targeting **outsourced institutional catering — SAF cookhouses as the beachhead, and any closed population where meals are declared ahead and someone cooks to a forecast**. This will primarily solve **the fact that nobody ever tells the kitchen how much food came back, so the over-provision that causes the waste is invisible to every person in a position to reduce it** and our main competitive advantage is **every incumbent points a camera at the bin and measures the loss after it is irreversible; this measures the forecast before the food is cooked — and it works in an environment where a camera is not deployable at all.**

The core functionality should handle **posting one anonymous poll into a unit's existing Telegram group, locking a cook number at the cutoff as `min(confirmed + unconfirmed, confirmed + r × unconfirmed + margin)`, displaying that number on a kitchen screen, accepting **two** figures on a numeric keypad after service — what was *actually cooked*, then what was *left* — and using `taken = actual_cooked − left` to score the forecast and update `r` — permanently, meal after meal.**

---

## Problem statement

Three compounding layers of over-provision, each individually rational, each invisible to the next
`[T2]`:

| Layer | Who | Why it is rational for them | Visible to the next layer? |
|---|---|---|---|
| **1 · The padded declaration** | The unit / food IC | Being short is complained about the same day. Being over is not | No |
| **2 · The confirmed tally** | Meal accounting | Proxy scans and out-ration reclassification make the number come out right | No |
| **3 · The kitchen buffer** | The cookhouse | *"If you input 100 they will cook more than 100"* — because running out means cooking again under pressure | **No — nobody knows the percentage** |

> **Nobody in this chain is making a mistake. Each of the three is correctly solving the problem in
> front of them. The waste is what the three correct answers add up to.** — `02-journey-maps.md`

All three exist because of one asymmetry: **being short is loud, being over is silent.** Under-supply
is detected immediately and is recoverable — the kitchen just cooks more. Over-supply is detected
never and is irreversible: past the four-hour hot-hold limit food cannot be chilled, re-served or
donated `[cited]`. **The system has a remedy for the recoverable failure and none for the irreversible
one.**

**The critique that shapes the whole product.** The interviewed senior said: *"You can make the process
of indenting easier and yet it does not solve the root cause, only the symptoms."* `[T2]` **That lands,
and it kills half of this design.**

| | What it is | Verdict |
|---|---|---|
| **Half A** | Better headcounting — the poll in the group chat | **Indent-easing. The critique kills it.** Necessary plumbing, never the pitch |
| **Half B** | **The feedback wire** — scoring every meal, `cooked / left / taken`, fed back | **The level-4 answer. Always lead with this** |

**Chope does not shrink the kitchen buffer.** It produces the evidence that would let the kitchen
shrink it themselves without being reckless. That distinction is the entry.

**Competitive advantage, stated precisely.** Winnow, Leanpath, Orbisk and Kitro are camera-plus-scale
over the kitchen bin, £5,000–15,000 per kitchen, subscription-priced, chef-facing `[cited]`. Raccoon
Eyes intervenes at the plate-return point — **after the portion is already fixed** `[cited]`. Fort
Jackson's EPA study instrumented two Army dining facilities and found **83% of food waste came from
overproduction, not plate scrapings** `[cited]` — the waste is upstream of the diner's fork, and every
product on the market is downstream of it. Chope is ~S$100, has no camera, no cloud, no app and no
personal data, and it is the only one that could be installed in a Green Zone at all.

---

## Core functionality

| # | Capability | Model involved? |
|---|---|---|
| F1 | Post one anonymous two-option poll into the unit's existing Telegram group | **no** |
| F2 | Close the poll at the cook cutoff and read back aggregate counts only | **no** |
| F3 | Lock and display `COOK = min(confirmed + unconfirmed, confirmed + r × unconfirmed + margin)` on a kitchen screen | **no** |
| F4 | Accept one integer — portions left — on a USB numeric keypad after service | **no** |
| F5 | Score the forecast: `taken = cooked − left`, append to `meals.csv` | **no** |
| F6 | Update `r` (EWMA) and the safety margin (separate EWMA on absolute error) | **no** |
| F6b | Log `buffer_pct = actual_cooked ÷ board` every meal — **this is K1**, the number nobody in the SAF has | **no** |
| F7 | Ratchet `r` upward only on a stock-out — censored observation | **no** |
| F8 | Replay a meal ledger to demonstrate the loop where no deployment is possible | **no** |

**Chope contains no model at all.** It is a counter and a control loop, and that is worth saying out
loud in a hackathon full of teams bolting an LLM onto everything.

**F5 is the product.** F1–F3 are the plumbing that makes F5 possible. *"Nobody asks how much came
back"* `[T2]` is the gap; one integer a day closes it.

---

## User Experience & Flow

The user interface should **be three surfaces, none of which is an app, and two of which already exist
in the user's hands.**

| Surface | Who | Interaction | Time cost |
|---|---|---|---|
| **A poll in the group they are already in** | ~90 NSFs | Two taps: *Eating* / *Not eating* | ~3 seconds |
| **One number on a screen on the kitchen wall** | Kitchen staff | Read it | 0 |
| **A USB numeric keypad** | Kitchen staff | Type a number, press enter, once per service | ~10 seconds |

```
        ┌──────────────────────────────┐
        │                              │
        │            91                │     ← one number, 34vw tall,
        │           COOK               │       readable across a kitchen
        │                              │
        └──────────────────────────────┘
              [7][8][9]
              [4][5][6]   ← "portions left", after service
              [1][2][3]      one integer, then Enter
              [ 0 ][Ent]
```

Key interactions should **cost ten seconds a day for the only person who has to do anything new.** The
NSF taps a poll they were already being asked to reply to — in most units the existing mechanism is a
Telegram headcount message, so this is *less* work, not more. The kitchen types one number.

The overall user journey will **run twice a day, forever, and get quieter as it converges.** Morning:
poll posts itself. Cutoff: the board locks a number. After service: one integer. That is the entire
loop, and the only new behaviour anywhere in the chain is the one integer.

We need **no formal accessibility standards** and **no internationalization** — **one number in a font
34% of the screen width is the accessibility design**, legible across a hot kitchen at distance, with
no colour coding, no icon vocabulary and nothing to read. The poll is two words in English, which is
the working language of the group it is posted into.

There will also be **an after-service message back to the group** — *"lunch: 91 cooked, 9 left"* — that
should be accessible in a **the-phone-they-already-have** manner. **This is Half B pointed at the
other end of the chain**: it is the first time the people declaring the headcount ever see the
consequence of declaring it. The entire application must be **existing-surfaces-first** first and
foremost: no new app, no new hardware in anyone's pocket, no account to create.

---

## User Tiers & Access

There will be **three** roles, and **none of them is an account**: **the NSF, the kitchen, and the unit's
food IC.**

| | The NSF | The kitchen | The food IC |
|---|---|---|---|
| Role | Taps a poll. **Anonymous, and not identifiable even in principle** | Reads one number, types one number | Sees the after-service message |
| Knows the system exists? | Sees a poll, same as today | Yes — it is on their wall | Yes |
| Has an account? | **No. There is no user table** | No | No |
| Who pays at scale? | — | **The catering contractor** | — |

**NSF** users will get **a two-option anonymous poll and nothing else**, while **kitchen** users
(**no payment — at scale the buyer is the catering contractor, not the unit and not the serviceman**)
will get **the locked cook number, and the scoring loop that makes it get better.**

We're planning **no** trial periods, and the onboarding process will **be: someone with authority adds
a bot to a group, and someone plugs a screen into a Pi.** There is nothing to configure per user
because there are no users in the software sense.

Payments will be collected with **nothing.** There is no monetisation in the MVP and no payment code
anywhere in this repo.

**Scale-up, for the slides only:** SAF's ~60 cookhouses are run by **two catering contractors — SATS
Defence Catering and Foodfare** `[cited]`. **You do not have to convince the SAF unit by unit; you have
to convince two companies** — and food waste is a direct cost against their contract margin, so the
commercial incentive is aligned without appealing to sustainability at all. Policy channel: the SAF
Sustainability Office, established 2020 `[cited]`. **Chope is not an army product** — it fits any
closed population where meals are declared ahead and someone cooks to a forecast: nursing homes,
hospitals, boarding schools, hostels, corporate canteens. The SAF is the beachhead, not the market.

---

## Technical Stack

This will be deployed on **a Raspberry Pi 5 (2 GB) already owned, booting from a USB stick, driving an
HDMI screen, with an outbound-only internet connection**, so a **~250-line plain Python 3 program, run
from cron, with no daemon and no listening socket** app is probably best. Use **no authentication
service** for user management — **the system never receives an identity, so there is nothing to
authenticate**. Database can be **one JSON file and one append-only CSV.** For static assets and
performance, we'll use **a local `file://` page in `chromium --kiosk`** and our backup strategy is
**`meals.csv` is append-only, and `chope_state.json` is written via `os.replace` so a power cut cannot
half-write it.**

| Layer | Choice | Why not the usual thing |
|---|---|---|
| Telegram | **`urllib.request`, three outbound POSTs** | `python-telegram-bot` is v22.8 and **async-only since v20** — an asyncio event loop and a `JobQueue` to wrap three HTTP calls |
| Update delivery | **None. No polling loop, no webhook** | `stopPoll` *returns* the final counts. There is nothing to listen for |
| Board | `chromium --kiosk` on a local `file://` page, refreshed by `<meta http-equiv="refresh">` | tkinter still needs a display server and costs hand-written layout; framebuffer means writing a font renderer. **And the page cannot `fetch()`** — Chromium blocks XHR on `file://`, so `chope.py` writes `board.js` as `B={...}` and a `<script src>` tag reads it. A local HTTP server would also work and would contradict the no-listening-socket claim on the slide |
| Keypad | `evdev` with **`.grab()`** | Without the grab, every digit also lands in the browser and the console |
| State | `chope_state.json` + `meals.csv` | Two files, six keys |
| GPIO | **None whatsoever** | Chope touches HDMI and USB only. **The Pi 5 `RPi.GPIO`/`lgpio` trap does not apply** — do not install `lgpio` and do not put "GPIO" on the slide |
| Boot media | **A bought microSD** `[T4, 19 Sep]` | The card exists now, so the USB-mass-storage trick is retired — it only ever existed to dodge a purchase that had not happened. Still S$0: nothing new is needed. If only one card was bought, **Tray Watch takes it** (it writes 150 MB a day) and Chope boots off the USB stick, which the Pi 5 bootloader checks after SD |

**Webhook vs long polling, settled:** a webhook requires a public HTTPS endpoint on port 443/80/88/8443
— impossible behind an arbitrary NAT, and **a listening socket on a defence network is a conversation
you do not want to have.** `getUpdates` needs no inbound port. **But the anonymous-poll design needs
neither**, which is the laziest correct answer available.

**Files, all written and passing their self-checks** `[VERIFIED]`:

| File | Lines | |
|---|---|---|
| `forecast.py` | 119 | The `r` loop and the margin. `python forecast.py` runs the self-check |
| `chope.py` | 99 | `check` / `open` / `lock` / `left N`, cron-driven |
| `keypad.py` | 26 | `evdev` + `grab()` |
| `replay.py` | 104 | The 2 Oct demo, plus its own self-check |
| `board.html` | 23 | One number |
| `install.sh` | 85 | **New.** The whole deployment: token file, root cron, keypad unit, kiosk autostart. Idempotent |
| `test_chope.py` | 64 | **New.** The plumbing `forecast.py` cannot see — board round-trip, CSV header, both stale-board guards |

**Four bugs found and fixed on 19 Sep by reading the code end to end, none of which the
self-checks could have caught:**

| | Bug | What it would have cost |
|---|---|---|
| 1 | `board.html` read `b.locked` / `b.note`; `chope.py` wrote neither | The board would have shown a number with no context, permanently unlocked, and nobody would have known why |
| 2 | The page used `fetch()` on a `file://` URL | **Chromium blocks XHR on `file://`.** The board would have read `no data` forever — on the demo table, on 2 Oct. Now the page is a `<script src="board.js">` plus a 5 s meta refresh: no fetch, no server, no listening socket |
| 3 | `forecast.py` defaulted `CHOPE_STATE` to a **relative** path | Under cron and systemd the CWD is `/`. The state file would have been written somewhere else, `load()` would have silently returned `new()`, and **`r` would have reset to 1.0 every run** — the forecast quietly reverting to today's number with no error anywhere |
| 4 | `keypad.py` spawned `"chope.py"` by relative path | Same root cause as 3. The keypad would have done nothing under systemd |
| 5 | The margin had a **flat floor of 3 portions** and `cook()` had **no upper bound at all** | A group of one who answered *"not eating"* was told to cook **3**. The same defect at full scale told a 90-man lunch to cook for 93 people who do not exist. A number a judge can break in one sentence is worth nothing, however good the estimator behind it is |
| 6 | `R_FLOOR = 0.50` floored `r` regardless of evidence | **34 wasted portions a meal** in a unit where silence mostly means "not eating" — twelve times the entire saving, invisible, and dressed as a safety feature |
| 7 | A **hard** cap at `confirmed + unconfirmed`, with no release | If decliners ever turn up, the system converges to failing **97% of meals while reporting zero forecast error** — and it is *high* poll reply rates that trigger it, i.e. Chope working |
| 8 | `slack` clamped at use but never written back | A ceiling learned on a 40-decliner lunch lay dormant and sprang back on a later meal |
| 9 | A meal where **nothing** was cooked has `left == 0` by arithmetic | It was read as a stock-out, manufacturing ceiling evidence out of an empty pan |
| 10 | The keypad took **one** number, and the meal was scored against the **board's** number | `[T5]` the kitchen cooks ~10% above whatever it is given, so `left` was measured against a pan 10% bigger than the one in the sum. `taken` read 10% low every meal, **`r` collapsed from 0.72 to 0.42 (measured; 0.21 at a 20% buffer)** — and it could never be noticed, because the kitchen's own buffer covered the shortfall the error caused. Two numbers now, and the first one *is* the K1 instrument |

**And two guards added**, because both failures are silent and both destroy a meal's data:
`lock` and `left` now refuse a board written on a different day, and `left` refuses a board that
is not in the `cook` state. A morning where the poll failed to post used to leave yesterday's
numbers in place and score today's meal against them.

### The number is bounded, and that — not the estimator — is the claim

```
base = confirmed + ceil(r × unconfirmed)            r ≤ 1, so base ≤ cap
cap  = confirmed + unconfirmed + min(slack, declined)            ≤ strength
COOK = min(cap, base + margin)
```

Three properties hold **for every input and every internal state**, and `forecast.py`'s self-check
proves them by fuzzing 4,000 random states rather than asserting them on one flattering example:

1. **`confirmed ≤ COOK ≤ strength`.** Both bounds are counts anyone in the room reads straight off
   the poll, so the number is checkable *without trusting the model at all*.
2. **One more "Eating" vote never lowers COOK. One more "Not eating" never raises it.** The board
   cannot move the wrong way. This is the property a sceptic actually reaches for.
3. **Nobody who declined is cooked for** — unless decliners have actually turned up before, and
   then only by as many portions as turned up.

The slide line:

> **We never cook for someone who told us they aren't coming, and we never leave out someone who
> told us they are.** Everything the model does happens strictly between two numbers you can count.

The degenerate cases stop being special cases — they fall out of the arithmetic:

| eat | not eating | silent | COOK | why |
|---|---|---|---|---|
| 0 | 1 | 0 | **0** | one man, he said no. Cook nothing. *(was 3)* |
| 0 | 0 | 1 | **1** | one man, silent. Silence counts as eating, as it does today |
| 2 | 8 | 0 | **2** | everybody answered; nothing left to estimate *(was 38 with a stale margin)* |
| 0 | 0 | 40 | **40** | nobody answered; exactly today's indent |
| 60 | 12 | 28 | **88** | the live case: `r` and the margin do their work inside the 28 |

**Three pieces of state, each moved only by its own evidence — and none of them a tuned constant:**

| | what it estimates | what moves it |
|---|---|---|
| `r` | what fraction of the **silent** eat | EWMA of observed turn-up, α = 0.25 |
| `margin` | how **noisy** the forecast is | EWMA of abs(error); ≈ 1.6 σ at `MARGIN_K = 2.0` |
| `slack` | how wrong the **ceiling** is | ratchets only on a stock-out that happened *while already cooking for everyone who did not decline* |

#### Why there is a ceiling ratchet at all, given decliners *don't* turn up

`[T5, 20 Sep]`: *"assume no. if not eating means they have plan already, so very high chance that
they are not eating."* Measured against that answer, **`slack` stays at exactly 0 in every
realistic regime** — 20 runs × 60 meals at the replay's reply rate, and at 30%, 70% and 95%. The
valve costs literally nothing to carry.

It stays anyway, and this is the argument: it guards the **only assumption in the design that is
about human behaviour rather than arithmetic**, Chope is explicitly not an SAF-only product
(nursing homes, hostels, boarding schools — where "not eating" may well mean something softer), and
the failure it prevents is silent. A hard cap is correct only if a "Not eating" vote is never
wrong. If
even 10% of decliners turn up, a hard cap fails — and it fails **worst exactly where Chope is
trying to go.** Measured, 300 meals, 100-man unit, 10% of decliners turning up:

| poll reply rate | hard cap: meals short | hard cap: `err` reports | with the ratchet |
|---|---|---|---|
| 30% | 3.7% | 3.0 | 3.7% |
| 70% | 3.0% | 4.7 | 3.0% |
| 95% | **81.7%** | 2.3 | **10.7%** |
| 100% | **97.3%** | **0.0** | **5.0%** |

Read the 100% row twice. With a hard cap the system **fails 97% of meals while reporting zero
forecast error.** When the cap binds, `cooked == base`, so the measured error `abs(taken − base)` is
identically zero however short you were — and with nobody silent, the stock-out branch was never
even reached. **Chope's own Half A success is what detonates it:** the better the poll adoption, the
smaller the silent pool, the harder the ceiling bites. The ratchet is the release valve, and it
costs nothing when decliners never turn up — `slack` stays at 0 at every reply rate in the control.

#### Two constants deleted, both of them floors on waste

| deleted | what it did | measured cost |
|---|---|---|
| `MARGIN_MIN = 3` — a flat margin floor | told a group of one who declined to cook **3**; told a 90-man lunch to cook for **93 people who do not exist** | 3 portions every meal, buying no safety — on meals that genuinely run short the shortfall is far bigger than 3 |
| `R_FLOOR = 0.50` — *"never trust fewer than half the silent"* | floored `r` at 0.5 regardless of evidence | in a unit where silence mostly means "not eating": **34 wasted portions a meal at p = 0.15, 29.5 at p = 0.25, 13.9 at p = 0.40** — against ~6 with no floor, and **twelve times Chope's entire saving** |

Deleting `R_FLOOR` costs exactly **one extra tight meal per regime shift** — 4 short meals in the 12
after a block leave, against 3 with the floor. That is the whole downside, and it is bought back
inside a fortnight of normal service. **Do not add a third constant of this species.**

#### What is deliberately *not* fixed, and what it costs

- **One keypad number cannot tell "ran out" from "exactly right."** Both leave `left == 0`. So a
  perfect forecast is scored as a stock-out and the ceiling creeps up. **Measured residual: exactly
  1 portion, at 10 men and at 500** — it does not scale with unit size. That is the entire price of
  the three-keystroke UX, and it is paid in the safe direction.
- **`err` tracks `abs(taken − base)`, which equals `abs(margin − left)`.** That is a real forecast
  error only while `left` moves with real demand. If the kitchen reports leftovers against a pan
  other than the one keyed in, the margin feeds on its own leftovers and runs away upward.
  **Watch `left` in week one.**
- **SBAB serves no dinner; lunch only** `[T5, 20 Sep]`, so one state file and five meals a week.
  `CHOPE_STATE` stays an environment variable, so a camp that serves two meals gets a second cron
  line and no code change — a single `r` across lunch and dinner would oscillate between two
  genuinely different turn-up rates.
- **No day-of-week term.** Monday and Friday do differ, but one meal per weekday gives one sample
  per bucket per week — seven EWMAs learning seven times slower, and it is exactly the
  training-set-shaped thing this project deliberately does not build. α = 0.25 has a ~7-meal
  window, so it *tracks* weekly drift even though it cannot *anticipate* it.

---

## Performance & Scale

We're expecting **~90 NSFs in one group and one kitchen** initially, with performance targets of
**`r` converging within ~12 meals, mean error under 0.03 across 200 replayed meals, and under 2.5%
stock-out meals.** Data volume should be around **one CSV row per meal — a year is 700 rows** and we
need to serve **one** region. Uptime requirements are **none in the SLA sense; the failure mode that
matters is a missed cutoff, and the fallback is that the kitchen cooks exactly what it cooks today.**

**The honest performance numbers** `[VERIFIED]` — from `replay.py`, 60 synthetic meals:

| | vs. the indent | ran short |
|---|---|---|
| Cumulative, including the learning period | **4.0%** | 2.4% of meals |
| **Steady state, after `r` converged** | **4.8%** | 2.1% of meals |

*(20 runs × 60 meals, not one seed — a shortfall rate measured on 40 meals of a single run is
noise, and the old self-check asserted on exactly that.)*

**Both figures go on the slide, and the small one goes first.** The cumulative number includes the
period when `r` is still near 1.0 and Chope deliberately cooks *more* than today. That cost is real.

**Two things that make the modest number honest rather than disappointing:**

1. **The buffer is multiplicative, so the percentage is exactly right — and the real prize is
   bigger than the forecast.** `[T5, 20 Sep]`: *"if you put 100, they will cook 110. smth like
   that."* A ~×1.10 buffer scales today's cooking and Chope's alike, so 4.8% is the honest
   percentage and only the absolute portion count is 10% larger than the replay prints. **But a
   10% buffer against a 4.8% forecast saving means the buffer is worth more than twice the
   forecast.** Half B is literally the bigger half. The pitch is not *"we forecast better"* — it
   is: *the kitchen keeps a 10% buffer because being short is loud and being over is silent, and
   it has never once been shown how accurate the number it is given actually is. Chope shows it,
   every lunch, in the kitchen's own handwriting.* 10% → 3% is a further ~7% on top, and **nothing
   else in this project can produce that evidence.**
2. **The safety margin eats roughly half the gain, on purpose.** That trade is the design, and it is
   tunable. The table below is the most credible artifact the prototype has, because it shows the
   design admitting its own cost instead of quoting one flattering number:

| `MARGIN_K` | portions not cooked | stock-outs per 80 meals |
|---|---|---|
| 1.0 | 6.9% | 5.8 |
| 1.5 | 5.7% | 3.0 |
| **2.0 — shipped** | **4.8%** | **1.7** |
| 2.5 | 3.8% | 1.2 |
| 3.0 | 2.9% | 0.6 |

*(20 runs × 60 meals each, so one lucky seed cannot pick the shipped row. `MARGIN_K` has a clean
reading: the margin is ≈ 0.8 × K standard deviations of cover, so 2.0 ≈ 1.6 σ. Held against
turn-up rates from 0.25 to 0.90 the worst case is 2.3% of meals short — inside the 2.5% target.)*

---

## Design & Branding

The design should have **one number, as large as the screen allows, white on black.** The primary colour
is **white**, with accents of **nothing — colour coding would imply a judgement
about the number, and the number is not a score.** Our brand guidelines are at **nowhere; there is no
brand** and we'll need **no design system** for consistency.

**The one design decision that matters:** the board shows the number the kitchen should cook, **not**
how much they wasted yesterday. `01-problem-map.md` §4.1 is a hard constraint — the intervention must
not read as a management tool imposed on staff. **It is a signal the servery generates for itself.**
A board that displayed yesterday's waste would be a performance dashboard pointed at the lowest-paid
people in the building, and it would be unplugged inside a week.

---

## Content Strategy

We'll need **no CMS** for content management. There's existing data at **`00-master-plan.md`,
`01-problem-map.md` and `02-journey-maps.md`** that needs migration — **none; they stay unchanged, and
`02` remains the most authoritative document on cookhouse reality.** For SEO, we want **none** and
we'll track everything with **`meals.csv`, which opens in Excel.** Note that **there is no dynamic
content and no javascript embed** beyond fifteen lines that write one number into one `<div>`.

---

## Security & Compliance

We need **no-personal-data-by-construction** security level with **no PDPA exposure — and the reason
matters** compliance. Industry regulations include **the Public Sector (Governance) Act 2018 and the
Government Instruction Manual on ICT&SS Management (IM8), which are the actual regimes for MINDEF and
the SAF.** Data encryption should be **not applicable — no personal data exists to encrypt** and we
need **`meals.csv`, append-only, one row per meal, containing no field capable of holding a person**
for audit trails.

### Get the legal framing right in front of this audience

> **The PDPA does not apply to public agencies.** MINDEF and the SAF are governed by the **Public
> Sector (Governance) Act 2018** and **IM8** `[cited]`. Saying *"PDPA-compliant"* to a defence audience
> signals you do not know the regime.

The correct sentence is: **"No personal data is collected at all, so neither the PSGA framework nor
IM8's personal-data provisions have anything to bite on."**

### The privacy claim is enforced by Telegram's servers, not by our code

This is the single best architectural decision in Chope, and it came from asking what the *minimum*
was rather than the most controllable:

| | Inline keyboard + callback | **Native anonymous poll** |
|---|---|---|
| Does a `user_id` reach the Pi? | **Yes, on every tap** | **No. Never. There is no code path** |
| Dedup | You write it | **Telegram enforces it server-side** |
| Lines of code | ~80 + the privacy problem | ~9 |
| The claim | a promise about our code | **a property of Telegram's servers** |

`sendPoll` defaults `is_anonymous=True`. The `poll_answer` update is documented as firing only for
*non-anonymous* polls, so for an anonymous poll it is never sent at all. `stopPoll` returns aggregate
`voter_count` per option. **The entire input to the forecast is three integers.**

**Retention rule: nothing to retain.** No identifier is received, so none is stored, expired or
deleted. That sentence is auditable in nine lines of `chope.py`.

**A salted hash would not have helped, and we should say why we rejected it.** Under the PDPC's *Guide
to Basic Anonymisation*, pseudonymised data remains personal data because of re-identification risk
`[cited]` — and in a 90-person group an attacker enumerates 90 user IDs and rebuilds the table in a
second. It buys nothing and costs the clean claim.

**The price paid, stated honestly:** *"Same as last week"* is per-person state and is therefore
impossible. **It is cut** — see §After MVP. Individual non-replier nudges are also impossible. Both
losses are in Half A, the half the senior's critique already kills.

### Token handling — this repository is public on GitHub

```
/etc/chope.env    →  CHOPE_TOKEN=...            chmod 600, root:root       [install.sh step 2]
systemd + cron    →  EnvironmentFile=/etc/chope.env  /  . /etc/chope.env
code              →  os.environ["CHOPE_TOKEN"]  # KeyError, never a default   [VERIFIED]
.gitignore        →  *.env  chope_state.json  meals.csv  board.js            [done]
before pushing    →  git log -p | grep -c ':AA'   must print 0               [VERIFIED 0]
```

**Everything Chope runs is root** — the token file is 600 root:root, so cron has to be root's, and
root reads `/dev/input` without adding anyone to the `input` group. Chromium is the only thing that
runs as the desktop user, and it only ever *reads* `board.js`.

**A leaked token lets anyone post as the bot into a unit group.** That is not a code bug, that is the
end of the project. If it ever lands in a commit, `/revoke` in @BotFather — a force-push does not
un-leak it.

---

## Integrations

We'll need to integrate with **the Telegram Bot API, and nothing else** and connect to **no other**
APIs. Webhook support for **nothing** is required — **and that is a deliberate security position, not
a gap.** Our API strategy is **to expose none** and data portability needs are **total: `meals.csv`
opens in Excel.**

**Explicitly not integrated, and each for a reason:** the electronic meal accounting system (no access,
and it is the thing whose blind spot we are describing); Camp Companion (an Army app; SBAB is RSAF and
the food IC there still works in Telegram `[T1]`); any cloud service; any notification service.

---

## Multi-Platform Needs

Mobile app requirement: **none. Telegram is the mobile app, and it is already installed.** Offline
functionality should **cover the whole kitchen side** — the board and the keypad need no network, and a
dropped connection costs one poll, not the loop. Real-time features needed: **none; the cutoff is a
cron entry.** Push notifications will **be one group message after service, and that is the feedback
wire** and we need to support **whatever Telegram supports, which is everything.**

**One Telegram constraint worth knowing:** `open_period` and `close_date` on a poll are capped at
**5–600 seconds**, so a morning-to-noon poll **must** be closed by our own `stopPoll` call on cron, not
by Telegram's timer.

---

## Public Access & Marketing

We will also need a **none — no web presence, no landing page, no logged-out state** for non-logged in
users. See **nothing; the only published artifact is the stale Claude artifact `e1c1e124`, listed as
known-wrong in `CLAUDE.md` — it still says the kitchen cooks 90% of the indent, which contradicts the
interview, still shows a thermal printer, still says Raspberry Pi 4, and leads with the headcount
instead of the feedback wire. It needs replacing or withdrawing before 2 Oct** for our current page
which we will need to port over. **Nothing** should be visible before login and to access **anything**
the user must authenticate — **there is no authentication anywhere in this system.** Marketing tools we
use: **none** and lead capture should **not exist.**

---

## Timeline & Resources

Target launch is **1 Oct 2026 (deliverables) / 2 Oct 2026 (showcase)** with a budget of **S$0 in new
purchases — the Pi 5 is owned, the boot media is a USB stick already owned, and an HDMI screen and USB
keypad are borrowed or owned.** Our team consists of **one solo SUTD undergraduate.** We'll measure
success by **the KPIs below** and we're competing against **Winnow, Leanpath, Orbisk, Kitro and Raccoon
Eyes — all of whom measure waste after it is irreversible.**

**Chope gets three build days.** Tray Watch is the one with a hard six-day field window; Chope has no
deployment, so it is schedulable around it.

| Day | | Why this order |
|---|---|---|
| **Day 1 — 20 Sep** | **Put the poll into a real group with real NSFs and start collecting** | **The long pole. It needs seven calendar days to run, so it must start first** |
| Day 2 | Pi boots off the USB stick, chromium kiosk, keypad `grab()`, end-to-end on the desk | Hardware risk retired early |
| Day 3 — ~29 Sep | Replay wired to the *measured* reply rate, the margin table, slides | Uses data that only exists by then |

**One free ask, make it now.** Ask the senior who gave the 4 Sep interview `[T2]` to run the same poll
in his **actual unit group** for a week. No camp entry, no hardware in camp, no photography, no
approval chain — it is a message in a chat he is already in. If yes, the reply-rate number becomes a
real one from a real unit. If no, the friends-group version still stands.

### KPIs

| # | KPI | Target | Why this one |
|---|---|---|---|
| C1 | Real NSFs recruited into the Telegram trial | **10–15** | Also feeds the 10+ People Log requirement |
| C2 | Real headcounts collected | **14** — 7 days × 2 meals | The only real measurement Chope will have |
| C3 | **Reply rate and reply latency** | **measured and reported with n** | **This is `U`, the input the entire forecast runs on. Nobody has this number** |
| C4 | `r` converges | **within ~12 meals, mean error < 0.03** `[VERIFIED]` | Replayed, and labelled as replayed |
| C5 | Stock-out rate in replay | **< 2.5%** `[VERIFIED]` | The failure the design promises to avoid |
| C6 | End-to-end hardware loop working on the table | **yes / no** | A demo that fails in front of a judge is worse than no demo |
| C7 | Token leaked to git | **0** | `git log -p \| grep -c ':AA'` |

**C3 is the real one**, and it is the reason the Telegram trial is not a consolation prize: *what
fraction of a real NSF group actually taps a button, and how fast* is the one number the whole
forecast depends on, and camp access is not required to measure it.

---

## After MVP is finished and operational

1. **The forecast learns structure it currently ignores:**
   - Day-of-week `r` — Fridays and pre-block-leave differ, and one `r` averages them into a number
     that is wrong twice a week
   - Per-meal `r` — breakfast, lunch and dinner are different populations
   - Confidence intervals on `r`, so the margin is derived rather than tuned
   - **Proper censored-data statistics for stock-out meals.** The shipped `max(0, obs − r)` rule is a
     deliberate approximation, marked in the code: *`ponytail:` one-sided EWMA on censored
     observations; upgrade to a Tobit update if a pilot ever produces >5% stock-out meals*

2. **A plating-side signal** that will **tell the plating line what mix to plate next from the observed
   take rate**, so that users can **stop making a discretionary portioning judgement hundreds of times
   a service with zero feedback on whether it was ever right** — `02-journey-maps.md` Map B stage 3,
   *"a control loop with an actuator and no sensor."* Technical requirements for this include shelf
   sensing, and it must be framed as a signal the servery generates for itself rather than a
   management tool `01` §4.1. **Explicitly out of scope before 2 Oct.**

3. Administration dashboard for managing **multiple units and multiple cookhouses under one catering
   contractor**, including **per-site over-provision trends** and **nothing pointed at individual
   staff.**

---

## Monitoring & Operations

For monitoring, we'll use **`meals.csv`, one row per meal** for errors and **the `err` field in
`chope_state.json`, which is the EWMA of absolute forecast error** for performance. A rising `err`
means the forecast is degrading and the margin widens automatically to compensate — **the system
responds to its own uncertainty rather than requiring someone to notice.** User behavior tracking with
**none — and it is not possible, by construction.** A/B testing via **none.** Maintenance windows are
**none; there is no daemon to restart.**

**The operational failure that matters** is a missed cutoff — the poll never closes, so the board never
locks. The fallback is that the kitchen cooks exactly what it cooks today, which is the current state
of the world. **Chope cannot make things worse than not having Chope**, and that property is worth
more than any uptime figure.

---

## Legal Stuff

We need **no terms of service** for terms of service, **no privacy policy, because there is no personal
data — and the correct framing is PSGA/IM8, not PDPA** for privacy policy, and **no cookie compliance**
for cookies. IP protection: **none sought; the repo is public** and data retention rules: **`meals.csv`
kept indefinitely; it contains no field capable of holding a person.**

**The one real permission question, and it is not technical:** *whether a bot is permitted in an SAF
unit Telegram group is a decision for the unit, not for us.* **Ask before 2 Oct rather than assuming
it.** If the answer is no, the friends-group trial still produces C3 and the honest sentence changes by
one clause.

---

**Special considerations:** **This cannot be installed, and the pitch must say so first.** No camp
access, no authority to put hardware in an SAF cookhouse, and **SAF cookhouses are Green Zone —
unauthorised photography is an offence** `[cited]`, which is why there is no camera in this prototype
at all and why that is an argument rather than a limitation. The exact wording for the slide:

> Chope was tested with N national servicemen over seven days in a live Telegram group — 14 real
> headcounts, with measured reply rate and reply latency. The kitchen board and keypad are built and
> working, and are demonstrated here on real hardware. **They have not been installed in a cookhouse:
> we have no camp access and did not seek to bypass that.** The forecast loop is shown against 60
> replayed meals; those meals are synthetic and are marked as such on every chart.

**And put the 1% figure on your own slide, before anyone else can.** MINDEF has publicly stated SAF
cookhouse food waste is ~1% of meals catered, tracked by the electronic meal accounting system
`[cited, PQ 3 Feb 2020]`. **Never say the number is wrong.** Say:

> That figure is meal accounting — meals issued against meals drawn. It is a count of meals and it is
> almost certainly accurate. It cannot see the thing this prototype is about: food the kitchen cooks
> *above* the indent is never issued as a meal, so it never enters the numerator or the denominator.
> When the interviewed serviceman says *"if you input 100 they will cook more than 100,"* **that
> surplus is structurally invisible to a system that counts meals. 1% is the right answer to a
> different question.**
>
> We do not know what the buffer percentage is. Nobody does — and that is precisely the point: there
> is no feedback channel that could tell anyone. Chope's first output is not a saving. It is a number
> that has never existed: **how many portions came back today.**

That converts the biggest unknown in the project from a hole in the work into the reason the work
exists.

**Technical constraints:** No camp access, so no deployment. No camera, ever. Outbound-only networking
— no listening socket on any network connected to a defence context. The repo is public, so the bot
token must never be committed. `RPi.GPIO` does not work on the Pi 5, but **Chope touches no GPIO at
all**, so the trap does not apply — do not install `lgpio`. A USB numeric keypad is a plain HID
keyboard, so without `evdev`'s `.grab()` every digit also lands in the kiosk browser.

**Business constraints:** S$0 available and S$0 needed. Thirteen days, solo, with a second prototype
that has a hard six-day field window. The buyer at scale is a catering contractor, not the SAF and not
the serviceman — and food waste is already a direct cost against their contract margin, so the pitch
does not have to appeal to sustainability at all.

**Long-term vision:** **Put a sensor on the one control loop in institutional catering that has never
had one.** Someone decides how much to cook, hundreds of times a week, and is never told what came
back. That is true in cookhouses, nursing homes, hospitals, boarding schools and corporate canteens.
The fix is not a smarter forecast — it is a wire. Chope is ~S$100 of wire, and the first thing it
produces is a number nobody in the building has ever seen.
