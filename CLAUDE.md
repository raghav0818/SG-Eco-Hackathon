# SG Eco Loop 2.0 — project context

Solo entry by Raghav (SUTD), team name **autobots**. Build a prototype that diverts food waste from
landfill. Two prototypes, two sites.

| When | What |
|---|---|
| **1 Oct 2026** | All deliverables due |
| **2 Oct 2026** | Public showcase, Temasek Shophouse |

**Deliverables:** prototype (tested with users) · Scale-Up Plan slides as PDF · Waste Diary (weekly
weigh-in + photo) · Reimbursement & People Log (needs **10+ people engaged**).

> **The Waste Diary is not a requirement on the prototype** `[T3, 18 Sep]`. It exists to make
> contestants recycle their own waste — it is housekeeping, submitted separately. **The prototype's
> job is to divert or reduce food waste, not to measure it.** So: **no scale, no grams, no kilograms,
> no weighing anywhere in either prototype.** Do not re-introduce a measurement deliverable that the
> competition never asked for — it adds a whole class of stacked-estimate error for nothing. Units are
> whatever the user already thinks in: trays and portions for the hawker, plates for the cookhouse.
**Budget:** S$200 per prototype. The second S$200 needs written approval *before* spending.
**Track:** Best Innovation only. Judging is 5 equally-weighted criteria — do not optimise one axis.
**Contact:** Jamie Heng, SDTA — sgecoloop@sdta.org.sg

---

## Rule 1 — his first-hand facts beat anything written in this repo

Raghav served at SBAB. When he states something about how cookhouses work, **it overrides every
document here, including ones I wrote.** Rebuild the affected reasoning; do not patch one sentence
and move on. This has already happened three times and each time it changed the design.

**Document authority, newest and most-corrected first:**

| File | Date | Trust |
|---|---|---|
| `army prototype 1/02-journey-maps.md` | 5 Sep | ✅ **Most authoritative** on cookhouse reality. Written against a real interview. |
| `army prototype 1/01-problem-map.md` | 4 Sep | ✅ Good. Rev 2. §8 (caterer payment) is still unresolved and load-bearing. |
| `army prototype 1/00-master-plan.md` | 1 Sep | ⚠️ Predates both interviews. Its §7 solution candidates are superseded. A2 is dead (no refill stations exist). §9's commercial argument may be inverted. |
| Published artifact `e1c1e124` | 13 Sep | ❌ **Three revisions stale** — see Known-wrong below. |

---

## Ground truth about the SBAB cookhouse

Established from Raghav's service `[T1]` and a senior's interview on 4 Sep `[T2]`:

- **The kitchen cooks ABOVE the indent, by roughly 10%.** *"If you input 100 they will cook more
  than 100"* `[T2]`; *"if you put 100, they will cook 110. smth like that"* `[T5, 20 Sep]`. **K1 is
  now answered to one significant figure** — approximate, from memory, and Chope is built to
  measure it exactly (see the two-number keypad below). It is no longer the biggest open question;
  **§8, the caterer payment, is.**
- **Silence in the Telegram headcount counts as eating.** Non-repliers are counted in.
- **People are told to scan their 11B whether or not they eat.** Proxy scanning happens; when numbers
  fall short the classification is changed to out-ration so it tallies.
- **Under-supply is recoverable** (the kitchen just cooks more). **Over-supply is not** — past the
  4-hour hot-hold limit it cannot be chilled, re-served or donated.
- **Three compounding layers of over-provision**, each individually rational, each invisible to the
  next: padded declaration → tally that always matches → kitchen buffer. All driven by the same
  asymmetry: *being short is loud, being over is silent.*
- **No refill stations at all.** Take the plate and the portion is final.
- Plate **count** is fixed per service; plate **contents** (rice, veg) are the plater's judgement.
- SBAB is RSAF. Camp Companion is an Army app — the food IC there still works in Telegram.

> The pitch sentence, from `02-journey-maps.md`: *"Nobody in this chain is making a mistake. Each of
> the three is correctly solving the problem in front of them. The waste is what the three correct
> answers add up to."*

### The critique that must not be quietly dropped

The senior said: *"You can make the process of indenting easier and yet it does not solve the root
cause, only the symptoms."* **This lands, and `02-journey-maps.md` §7 concedes it.**

Consequence for Chope: it has two halves. **Half A** (better headcount) is indent-easing — the part
the critique kills. **Half B** (the feedback wire that scores every meal) is the level-4 answer.
**Always lead with Half B.** Chope does not shrink the kitchen buffer — it produces the evidence that
would let the kitchen shrink it themselves without being reckless.

---

## Prototype 1 — Chope (SBAB cookhouse)

Telegram anonymous poll + Raspberry Pi 5 + HDMI kitchen board + USB numeric keypad. **S$0 to build —
everything needed is already owned.** Core code **written and passing its self-checks, 19 Sep**:
`forecast.py`, `chope.py`, `keypad.py`, `replay.py`, `board.html`.

- NSFs tap **Eating / Not eating** in a **native Telegram anonymous poll** in the unit's existing
  group. **Not an inline keyboard** — every `callback_query` carries `from.id`, so that version made
  "never names" a promise about our code. `is_anonymous=true` makes it **a property of Telegram's
  servers**: no user id has any path to the Pi, and Telegram dedups server-side. ~9 lines instead of
  ~80. **Price: "Same as last week" is per-person state and is cut.**
- **No update loop at all.** Webhook needs an inbound port (impossible, and a listening socket on a
  defence network is a conversation to avoid); `getUpdates` needs none — but neither is required,
  because `stopPoll` *returns* the final counts. Three outbound POSTs on cron, no daemon.
- At the cook cutoff the board locks **`COOK = min(cap, base + margin)`**, where
  `base = confirmed + ceil(r × unconfirmed)` and `cap = confirmed + unconfirmed + min(slack,
  declined)`. **The bound is the claim, not the estimator.** Three properties hold for every input
  and every state, fuzzed over 4,000 random states in `forecast.py`'s self-check: (1) `confirmed ≤
  COOK ≤ strength`; (2) one more "Eating" vote never lowers COOK and one more "Not eating" never
  raises it; (3) nobody who declined is cooked for unless decliners have actually turned up before.
  Both bounds are counts anyone reads off the poll, so the number is checkable without trusting the
  model. **Never cook for someone who said they aren't coming; never leave out someone who said
  they are.**
- **Three pieces of state, each moved only by its own evidence.** `r` = what fraction of the SILENT
  eat (EWMA, α=0.25). `margin` = how noisy the forecast is (EWMA of |error|, ≈1.6 σ at
  `MARGIN_K=2`). `slack` = how wrong the CEILING is — ratchets **only** on a stock-out that happened
  while already cooking for everyone who did not decline. Do not merge them; each has its own
  observable and folding them compounds error.
- **DO NOT ADD A CONSTANT THAT FLOORS THE OUTPUT.** Two were deleted after measurement, 20 Sep, and
  both were dressed as safety: `MARGIN_MIN = 3` (told a group of one who declined to cook 3, and a
  90-man lunch to cook for 93 people who do not exist) and **`R_FLOOR = 0.50`, "never trust fewer
  than half the silent" — which cost 34 wasted portions a meal at p=0.15 and 29.5 at p=0.25,
  twelve times Chope's entire saving.** Deleting `R_FLOOR` costs one extra tight meal per regime
  shift. That is the whole downside.
- **The cap must stay soft.** A *hard* cap at `confirmed + unconfirmed` converges to failing 97% of
  meals while reporting **zero** forecast error — when it binds, `cooked == base`, so `|taken −
  base|` is identically 0 however short you were. And it is triggered by *high* poll reply rates,
  i.e. by Chope's own Half A working. The `slack` ratchet is the release valve and costs nothing
  when decliners never turn up.
- After service, staff key in **two numbers: what was ACTUALLY cooked, then portions left.**
  `taken = actual_cooked − left` scores the forecast. **The first number is not bureaucracy and
  must not be optimised away.** The kitchen cooks above whatever number it is given (~10%, `[T5]`),
  so scoring against the board's own number measures `left` against a pan 10% bigger: `taken` reads
  10% low *every meal*, **`r` collapses from 0.72 to 0.42 (measured), and nobody ever sees it fail
  because the kitchen's buffer silently covers the shortfall it caused.** At a 20% buffer `r` dies
  at 0.21. One command, `chope.py key N`, dispatches on the board state, so the state lives in
  `board.js` and restarting the keypad mid-entry cannot desync it.
- **That first number is also the instrument.** `actual ÷ board` **is K1**, measured every lunch for
  free and logged as `buffer_pct`. Chope cannot deliver Half B — the evidence that lets the kitchen
  shrink its buffer — without measuring the buffer, and it could not measure it with one number.
- **`r` and the margin are SEPARATE state.** `r` estimates the truth via a symmetric EWMA (α=0.25);
  the margin is its own EWMA of absolute forecast error. **Two traps, both hit in practice:** an
  asymmetric learning rate biases `r` ≈ +0.087 high and never converges; folding the margin back into
  the estimator compounds it upward and `r` never moves at all. A stock-out is a **censored**
  observation and may only ever push `r` **up**.
- **`r` starts at 1.0**, which reproduces today's number (everyone silent counts as eating), so day
  one carries no risk of running short. *(The artifact wrongly says it starts at 0.90 "the kitchen's
  current constant" — there is no such constant.)*
- **Honest measured result** (20 runs × 60 meals, never one seed): **4.8% steady-state** saving
  against the indent, **4.0% cumulative** including the learning period, **2.1% of steady meals run
  short**. Ship the margin/stock-out trade table — it is the most credible artifact the prototype
  has. Shipped `MARGIN_K = 2.0` costs 4.8% not-cooked for 1.7 stock-outs per 80 meals; the margin
  is ≈0.8 × K standard deviations, so K=2 ≈ 1.6 σ.
- **The old line "the kitchen buffer means 4.8% UNDERSTATES the saving" is wrong — replace it, do
  not patch it.** `[T5, 20 Sep]` The buffer is *multiplicative* (~×1.10 on whatever number it is
  given), so it scales today's cooking and Chope's cooking alike: **the percentage is exactly
  right, and only the absolute portion count is 10% larger than the replay shows.**
- **The real prize is bigger than the forecast, and now it has a number.** A ~10% buffer against a
  4.8% forecast saving means **the buffer is worth more than twice the forecast**. Half B is
  literally the bigger half. Chope's pitch is not "we forecast better" — it is: *the kitchen keeps
  a 10% buffer because being short is loud and being over is silent, and it has never once been
  shown how accurate the number it is given actually is. Chope shows it, every lunch, in its own
  handwriting.* A buffer of 10% → 3% is a further ~7% on top. **Lead with this.**
- **SBAB serves no dinner — lunch only** `[T5, 20 Sep]`. So one state file, one cron pair, and
  **five meals a week**: `r` converges in ~12 meals ≈ **two and a half weeks of weekday lunches**.
  Say that in the scale-up plan rather than "12 meals", which sounds like a fortnight of nothing.
  (`CHOPE_STATE` stays an env var so a two-meal camp needs a second cron line and no code.)
- **Decliners do not turn up** `[T5, 20 Sep]`: *"if not eating means they have plan already."* So
  the ceiling ratchet `slack` **measures 0 in every realistic regime** — it costs literally nothing
  to carry. It stays anyway: it is the only assumption in the design that is about human behaviour
  rather than arithmetic, and without the valve a unit where that is *not* true converges to
  failing 97% of meals **while reporting zero forecast error**. Free insurance; do not delete it.
- **Two things deliberately not fixed, each with a measured cost** — both in `08-chope-prd.md`:
  the keypad cannot tell "ran out" from "exactly right" (both give `left == 0`), so the ceiling
  creeps by **exactly 1 portion**, at 10 men and at 500; and `err` tracks `|margin − left|`, so if
  the kitchen reports leftovers against a pan other than the one keyed in, the margin **runs away
  upward** — watch `left` in week one.
- **It cannot be installed.** No camp access, no authority for hardware in an SAF cookhouse. The
  Telegram half is genuinely user-tested; the kitchen half is real hardware on the table driven by
  `replay.py`. **Say so on the slide** — `08-chope-prd.md` has the exact wording.
- **PDPA does not apply to public agencies.** MINDEF/SAF are under the Public Sector (Governance) Act
  2018 and IM8. Saying "PDPA-compliant" to a defence audience signals you do not know the regime.
- **Chope touches no GPIO at all** — HDMI and USB only. Do not install `lgpio`, do not put "GPIO" on
  the slide. The keypad needs `evdev` `.grab()` or every digit also lands in the kiosk browser.
- **Boot media is a bought microSD** `[T4, 19 Sep]`. The USB-mass-storage trick is no longer needed —
  it only ever existed because no card had been bought. If only one card was bought, Chope takes the
  USB stick and Tray Watch takes the card; Tray Watch is the one that writes 150 MB a day.

- **The kitchen board is a `file://` page and therefore cannot `fetch()`** — Chromium blocks XHR on
  `file://`, silently. `chope.py` writes **`board.js`** as `B={...}`; `board.html` loads it with a
  `<script src>` and re-reads it with a 5 s `<meta http-equiv="refresh">`. No timer, no server, no
  listening socket. Do not "fix" this back into a `fetch`.
- **Never default a state path to a relative one.** Cron and systemd run with CWD `/`, so
  `chope_state.json` would be written elsewhere, `load()` would return `new()`, and **`r` would reset
  to 1.0 on every run** with no error. Both `forecast.py` and `keypad.py` now resolve against
  `__file__`.
- `sh install.sh` on the Pi does the whole deployment and is idempotent: `/etc/chope.env`, root cron
  for `open`/`lock`, the keypad systemd unit, and the kiosk autostart (wayfire / labwc / LXDE all
  handled). **`python3 chope.py check` proves the token and chat id without posting anything** — run
  it before trusting cron.

Files: `army prototype 1/08-chope-prd.md` (the PRD) · `forecast.py` `chope.py` `keypad.py` `replay.py`
`board.html` `install.sh` `test_chope.py` · `07-architecture.md` §6–8 at the repo root.
**Self-checks, all passing 19 Sep:** `python forecast.py`, `python replay.py demo`,
`python test_chope.py`.

## Prototype 2 — Tray Watch (cai png stall, SUTD canteen)

USB webcam on the sneeze guard + Pi 5 logger. **The webcam is already owned** `[T6, 21 Sep]`, so
the build cost is **≤S$20 and possibly S$0** — mount hardware only, decided after seeing her stall.
**Pivoted 17–18 Sep. Rebuilt 21 Sep after the statistics were measured. Mount 22 Sep.**

**Stock Clock (four-slot load cell rack) is cancelled** — archived in `hawker prototype 2/archive/`,
nothing was bought. It was killed by her own answer, not by a technical problem:

> *"vegetables often spoil because meat products sell fast… whereas vegetables sell slow… so she had
> to throw a lot of veggies, uncooked ones especially."* `[testimony, 17 Sep]`

The rot is the **symptom**. The chain is: students don't pick vegetables → cooked veg is left at
close → she keeps buying at the same rate → raw veg rots. Stock Clock attacked the last link; **Tray
Watch attacks the first.** She preferred it when it was put to her — Stock Clock told her what she was
*wasting*, Tray Watch tells her how to *sell more*, and she is on a 10–15% net margin.

- Photographs the tray row every 2 min through service for six days. No screen, no interaction.
  **It has internet** `[T4, 19 Sep]` — so frames `rsync` off the Pi *during* service, and an SD card
  that dies on day 4 no longer costs day 4. **Capture itself must never depend on the network:** write
  the JPEG to disk, let a separate cron push it. WiFi dropping must cost zero frames.
- **"No network" is dead as a privacy line — replace it, do not patch it.** The real claim was always
  the stronger one: the crop is applied **before** the JPEG is written, so no image of a person is ever
  encoded, stored or transmitted. A property of the code, not a policy — and it holds on a networked
  box exactly as well as on an airgapped one.
- A vision model reads **fill level** per tray. The images separately yield each dish's **colour**
  (median CIELAB), and therefore the **colour contrast to its neighbours**.
- **THE CONTRAST EXPERIMENT CANNOT REACH SIGNIFICANCE. This is measured, not an opinion, and it
  replaced the old "headline test, n = 8 dishes, floor p = 0.0078" claim outright** `[MEASURED,
  21 Sep — run `hawker prototype 2/design_checks.py`]`. A dish that MOVED has position confounded
  with contrast, so only never-moved, re-neighboured dishes count. Exhaustive over all 40,320
  rearrangements of 8 trays: **at most 5 such dishes exist, floor p = 0.0625 — above 0.05, so even
  a perfect result cannot be claimed.** You would need **9 trays** to reach n=6 (floor 0.031).
  This is the same defect §5.5 already retired the day-level test for; the replacement inherited it.
- **And at n=8 it is underpowered by ~an order of magnitude**: a real +10% effect is detected 10%
  of the time, +20% -> 30%, +30% -> 54% (day-to-day wobble 40%). The honest expectation on
  showcase day is "no effect detected" **with a real effect present**.
- **N1 IS ANSWERED: YES, she can swap the trays** `[T7, 22 Sep]` — and it does **not** rescue the
  p-value. She moves *trays*, so the dish travels with the tray, which is exactly the confound that
  caps the count at 5. **Floor p stays 0.0625.** What the yes buys is *when*: an 11-hour day with a
  dead 13:30–17:00 means the row can be swapped **in the lull**, so every dish sees both
  arrangements **on the same day**. `design_checks.py` C7, at the honest n=5 `[MEASURED, 22 Sep]`:
  **CI half-width ±9.1 against ±21.8–±35.6 for alternate days — 2.4–3.9× tighter** — and the
  crossover result is *identical* at 25% and 40% day-to-day wobble, because the day effect cancels
  inside the day. Alternate-days also reads **+17.7% for a real +10%**: a ratio of means with a
  noisy denominator over-reports, in the flattering direction. **So: swap once daily in the lull,
  counterbalancing which arrangement gets the morning.** Costs her one swap in dead time; costs the
  code nothing before mounting (frames are frames), only `dishes.csv` gaining `block` + `from_ts`
  and the side-arm analysis reading them. **My first version of C7 gave the crossover no
  within-block noise and returned ±0.0 — perfect by construction, a bug in the sim, not a result.**
- **So the rearrangement is a SIDE ARM: effect size and CI, never a p-value.** The prototype leads
  with the **waste ledger** — what came back, per dish, per day — whose claim lands on six days
  **100% of the time** (±7.6 to ±30.3 points). Same camera, same week: ledger 100%, experiment
  10–30%. That reordering is the mentor's own framing, 21 Sep: *"the framing is to 'reduce'
  leftovers with more insights. Insights captured by your process."*
- **`leftover_close` is EXACT; `cooked_total` is NOT, and they must never be printed as the same
  kind of number** `[MEASURED]`. Leftover is a level read at close — ±0.0 fill-points at any
  sampling rate. `cooked_total` is a sum of detected refill jumps and the 3-frame median delays
  every refill while sales continue, so it reads **−9.5% at a 2-min gap and −23% at 6 min**, always
  downward. Four fixes were measured; **three made it worse**. The bias is in the signal, not the
  filter — **do not add a filter.** Two consequences: **analyse EVERY frame** (~1,980 calls over an
  08:00–19:00 day, and on Gemini Flash that is **US$2**, so the cost argument for sampling every
  third frame is dead), and the paper page **leads with what came back**, not with "you cooked
  3 trays and sold 1".
- **The shipped §5.5 analysis returns p = 0.0000 on a dish that missed an arrangement arm** —
  `abs(null) >= abs(nan)` is all-False. Not an error; confident fake certainty, in the flattering
  direction. Incomplete dishes must be dropped **loudly, by name**, and the arm refuses below n=6.
- **Never configure the tray count.** Every doc said "8 trays"; nobody has counted them. The
  analysis reads the row off frame 1 and reports what it found, on day 1, while the crop is still
  fixable.
- Refill detection matters more than fill: she tops up during service, so `start − end` is wrong.
  Deltas give `cooked_total` vs `served_total`, and the sharpest output in the project — *"stop
  topping up tray 4 after 1:30pm."*
- **The LLM is never in the measurement path.** One hand-coded audit day gives an agreement rate; if
  the model is bad, five days of frames and a weekend still rescue it.
- **She already knows which dishes sell badly — she said so** `[testimony]`. That is the sharpest
  critique the project faces, and the answer is `context.md`: her knowledge, in her words, one page,
  pasted into the recommendation prompt so the output *starts* from her expertise. The three things
  she cannot know are in `05` §6.2 — **how fast** a dish declines, **which top-up went in the bin**,
  and **whether a change worked**. Nobody can A/B test their own display while running a stall.

**Code written 21 Sep, all self-checks passing:** `capture.py` (Pi: crop-before-write, sequence
names, WB verify) · `analyse.py` (frames → `readings.csv` → `daily.csv`, the noise chain, the
vision calls) · `report.py` (the A4 page, `--no-llm` fallback) · `design_checks.py` (the six
measured claims) · `install-pi.sh` · `SETUP.md` (step-by-step Pi setup).
**Self-checks, all passing 22 Sep:** `python capture.py --selftest`,
`python analyse.py --selftest`, `python report.py --selftest`, `python design_checks.py`.

- **`design_checks.py` imports the chain from `analyse.py`** rather than copying it — so it tests
  shipped code. If `MIN_DROP` or `REFILL_JUMP` are tuned against the real stall, **re-run it**: the
  −9.5% `cooked_total` bias is measured against those exact constants.
- **`capture.py` refuses to start without `TW_CROP`.** An unset crop means writing a full frame
  that may contain a face, and the privacy claim is that one is never encoded. `--aim` writes a
  240px blurred frame with a grid labelled in full-res pixels so a crop can be chosen without ever
  seeing a face; `--check` writes the only full-res image the program ever produces, already
  cropped. That is KPI K3, falsified on day 1 rather than asserted on a slide.
- **The tray count is read off frame 1, never configured**, and the layout is cached in
  `layout.json` so it costs one call.
- **The vision model is `gemini-2.5-flash`, not Claude** — that is the key Raghav has
  `[T7, 22 Sep]`. `THINK = {"low": 0, "medium": -1}` maps the old effort argument onto
  `thinking_budget`: **off** for the 1,980 fill reads (perception, not reasoning), **dynamic** for
  the one recommendation call that weighs six levers against her own words. **Gemini's
  `response_schema` is an OpenAPI 3.0 subset and rejects `additionalProperties` with a 400** — all
  four schemas had it, `analyse.py --selftest` now asserts it is absent, and that is the one
  API-boundary failure the stubs cannot catch.
- **`analyse.py` is resumable** — it skips frames already in `readings.csv`, writes them under a
  `finally` so an API failure at frame 1,000 keeps the 999 already paid for, and prints the
  estimated cost (**~US$2** at 1,980 frames — ESTIMATED from Flash's token prices, not
  measured; check the real spend after day 1) before spending anything. It also rejects any
  argument but `--selftest`, because a typo used to start a 1,980-call run.
- **The median lags one frame (~2 min).** `sold_out_ts` therefore reads ~2 min late, and
  `leftover_close` is the median of the closing frames — more robust, and measured unbiased.
  **Do not shrink the window to "fix" it:** the same lag is what under-sizes refills by 9.5%, and
  three of four candidate fixes measured WORSE.
- **Not yet exercised: the live API calls.** No key was available when the code was written, so
  `read_layout` / `read_fills` / the recommendation call are unit- and integration-tested against
  stubs but have never hit the real endpoint. First real run is the first test — run `analyse.py`
  on day 1's frames, not on day 6's. Needs `pip install google-genai` and `GEMINI_API_KEY` in the
  environment, **never in the repo**.
- **She opens 08:00 and closes 19:00** `[T7, 22 Sep]` — an **11-hour** day, not the 6-hour
  lunch-only service every number in this repo was measured against until 22 Sep. Consequences:
  `install-pi.sh` has `CLOSE="20 19"` (USB mirror 19:20, shutdown 19:35); **~330 frames a day,
  ~1,980 for the week**; and opening time needs no config at all, because capture starts at boot.
- **THE BIAS NUMBERS MOVED ON 22 SEP BECAUSE OF THAT. Do not quote the old ones.** `design_checks.py`
  now models her real day — three peaks, a dead 13:30–17:00, five refills — and on it `cooked_total`
  reads **−9.5% at 2 min and −23% at 6 min**, not −12% / −36%. `leftover_close` is unmoved at
  **±0.00 fill-points at every gap**, which is the whole reason the page leads with it. Re-run the
  receipt, do not re-argue it.
- **2-min stays, and 1-min was rejected on measurement.** 1-min halves the bias (−5.6%) for US$4
  instead of US$2 — but halves it on a number already labelled a lower bound and printed in rounded
  trays, while the headline number is exact at both. `TW_EVERY` is the knob. **The one real reason
  to use it: if day 1 shows many `obscured` frames, 1-min doubles the survivors.** Robustness, not
  accuracy.
- **The dish roster is CONSTANT — same dishes lunch and dinner** `[T7, 22 Sep]`. So the feared
  "slot 3 is kangkong at lunch and something else at dinner" merge does not happen, and
  `dishes.csv` needs no time column for *that* reason. It needs one for the crossover below.
- **`sold_out_ts` is the FIRST empty frame, which over an 11-hour day is usually the afternoon
  lull, not a sell-out.** Diagnostic only; it never reaches the page. Do not rename it into a
  claim.

Files: `hawker prototype 2/05-traywatch-plan.md` (full build + schema) ·
`06-traywatch-user-journey.md` (the answer to Jamie's *"what is the user journey"*) ·
`09-traywatch-prd.md` (the PRD) · `07-architecture.md` at the repo root (**both** prototypes: data
flow, the clock, the colour maths, the statistics — diagrams).

**Known weak point — now quantified rather than merely admitted:** rearranging the neighbours also
moves the meat dishes, and that is not a caveat on the experiment, it is what caps it at 5 countable
dishes and makes it unwinnable. See the measured bullets above. Say the number, not the adjective.

**`design_checks.py` is the receipt.** Six checks, stdlib only, ~30 s, all asserting. Every
`[MEASURED, 21 Sep]` claim in `09-traywatch-prd.md` comes out of it. If someone challenges the
reordering, run it in front of them.

---

## Hardware ground truth — Raspberry Pi 5, and its traps

**TWO Raspberry Pi 5 (2 GB) were bought** from Cytron on 14-09-2026 — invoice CI14269757, qty 2,
S$196.00. One runs Tray Watch, one runs Chope. **There is no Pi 4 in this project;** anything in this
repo saying "Pi 4" is out of date.

**Verified against `FINANCE CLAIMS/` on 18 Sep — total spent S$239.50** (2× Pi 5 S$196.00 + 3× PETG
filament S$43.50, PolyMate INV/26/09/018). Budget is S$200 per prototype, so **S$160.50 remains** —
**minus the microSD bought on 19 Sep, whose receipt is not yet in `FINANCE CLAIMS/`.** Both figures
are stale by that amount until it is.

Live traps — do not re-litigate:

1. ~~No microSD card has been bought.~~ **Bought. `[T4, 19 Sep]`** — Raghav has it in hand. Flash it
   and move on; nothing is blocked on boot media any more, and the USB-boot workaround that existed
   only to dodge this is deleted. **The claim still needs the receipt** — the S$239.50 / S$160.50
   figures above predate it and are stale by the card's price until that invoice reaches
   `FINANCE CLAIMS/`.
1b. **The clock — and the network makes the dangerous half MORE likely, not less.** `[T4, 19 Sep:
   the Pi has internet at the stall.]` That kills the easy half: NTP sets the clock at every boot, so
   no `fake-hwclock` drift and **no ~S$8 RTC battery needed** — struck from the buy list. But the half
   that *destroys data* survives and gets worse. The Pi 5's RTC has no battery, so it still boots at
   the last shutdown time and `systemd-timesyncd` still corrects it seconds later — which **steps the
   clock backwards**. `HHMM.jpg` filenames then collide and `imwrite` overwrites silently, no error.
   With no network that happened never; **with a network it happens every single morning.** So:
   **name frames by sequence number, never by the clock**, and log `CLOCK_BOOTTIME` beside wall-clock.
   Gate capture on `time-sync.target` so frame 1 waits for the step instead of being eaten by it.
   **Verify the network on day 1, do not assume it:** a canteen captive portal (or an eduroam-style
   802.1X login) cannot be answered by a headless Pi, and it fails looking exactly like success —
   `timedatectl` must print `System clock synchronized: yes`. If it is a portal, the phone hotspot
   comes back as the fallback and the old sixty-seconds-at-open plan applies unchanged.
   `07-architecture.md` §2.5.
2. **The Pi 5's camera connector is 22-way, 0.5 mm pitch.** Every current camera product ships the
   15-way, 1 mm "standard" FPC. A CSI camera therefore needs a 22→15 adapter cable and a wait. **Use a
   USB webcam** — identical on both boards, and a 3 m USB extension keeps the Pi off a hot greasy
   counter where 50 cm of ribbon cannot.
3. **Pi 5 caps total USB current at 600 mA** unless it detects a 5 A-capable USB-C PD supply. A 1080p
   webcam draws 150–250 mA so it fits, but an under-spec supply throttles and costs a day.
4. **`RPi.GPIO` does not work on the Pi 5.** The RP1 chip replaced the hardware it talks to. Use
   `lgpio`. Relevant to Chope's keypad/board, not to Tray Watch.
5. **Lock the webcam's white balance and exposure**, and keep printed grey cards in frame — **two, one
   at each end of the row**, because eight trays are lit by more than one lamp and a single card bakes
   a light gradient into the measurement. Auto-WB re-corrects colour every frame and would destroy the
   contrast measurement, which is the whole experiment. `cap.set(cv2.CAP_PROP_AUTO_WB, 0)` is not
   reliable — lock via `v4l2-ctl` and **verify the lock took**, because a `set()` that silently no-ops
   loses the experiment with no error.
   - **THE ACTUAL WEBCAM CANNOT DO ANY OF THIS** `[T8, 22 Sep]`. `v4l2-ctl -d /dev/video0
     --list-ctrls` on the real device (USB Camera, 046d:08d9) lists only `brightness`,
     `contrast`, `gamma`, `exposure` (read-only/auto), `gain_automatic`, `power_line_frequency`,
     `sharpness` — **no `white_balance_*` control and no `auto_exposure`/`exposure_auto` toggle
     exist at all.** This is not the "control names differ, ignore misses" case the code was
     built to tolerate — there is nothing to lock, on this hardware, full stop. `wb_locked()`
     correctly degrades to `None` (unverifiable) rather than crashing, so capture is not
     blocked. Decision: **do not swap cameras for this** — the colour-contrast side arm was
     already unwinnable at floor p=0.0625 even with a perfect lock, so what's lost is a bonus,
     not the headline. The waste ledger and the swap-in-the-lull crossover (C7) both read
     fill-level / refill jumps, never pixel colour, so neither is touched. **The colour-contrast
     claim is retired, not degraded** — relabel any surviving arrangement result as a *position*
     effect (moving a dish's neighbour changed sell-through), never a *contrast* effect (there is
     no trustworthy ΔE to attribute it to). Grey cards are now optional, not required.
   - **SUPERSEDED WITHIN THE HOUR** `[T8, 22 Sep]`: a second webcam already owned (no purchase)
     lists `white_balance_automatic` (bool) and `auto_exposure` (standard V4L2 enum, 0=Auto/
     1=Manual/2=Shutter/3=Aperture) — exact matches for what `capture.py`/`install-pi.sh`
     already try. **Use this camera, not the 046d:08d9 one.** The contrast arm is back in play
     (still capped at floor p=0.0625, still a side arm, never the headline) — the bullet above
     stays as the record of why it was nearly dropped and the graceful-degradation path the
     code still needs for any THIRD camera that behaves like the first one.
6. **`PIL.Image.convert("LAB")` silently returns a wrong answer** `[VERIFIED 19 Sep on this machine,
   Pillow 11.3.0]`. It does **not** raise. Pillow stores a\*/b\* as *signed* bytes, not offset by +128,
   so the obvious decode gives ΔE ≈ 180 — larger than the entire range of the measurement — and the
   numbers still look plausible. Even decoded correctly it is worst on **green** (ΔE 7.5 vs 0.01 for
   OpenCV). **Use `cv2.cvtColor` on float32.** And never take a Euclidean distance on the packed uint8
   triple: L is stretched 2.55× there, so ΔE would be dominated by which lamp a tray sits under.

Archived with Stock Clock (`hawker prototype 2/archive/`), true but no longer in play: `rpi_ws281x`
does not work on the Pi 5 so no WS2812 LEDs · HX711 VCC is 3.3 V never 5 V · load cells must be 5 kg
not 20 kg · the GPIO chip is `gpiochip0` on some kernels and `gpiochip4` on others.

---

## Known-wrong, not yet fixed

1. **Published artifact** `https://claude.ai/code/artifact/e1c1e124-7687-4387-91ef-2c5b22b52d2f` —
   says the kitchen cooks 90% of the indent (contradicts the interview), still shows the thermal
   printer, says Raspberry Pi 4, leads Chope with the headcount instead of the feedback wire, and its
   status line "Nothing is built or tested yet" is stale.
2. **Claim form tab 1** in `[SG Eco Loop] Reimbursement & People Log Template.xlsx` — the Prototype
   Description repeats the same 90% error. The field's requirement is *"clear enough to relate to the
   expenses below."*
3. **`models/prototypes.scad`** — line 2 says "Both run a Raspberry Pi 4 Model B" and the `pi4()`
   module draws Pi 4 geometry. Board outline and mounting holes are the same on Pi 5, but Ethernet
   and USB swap sides, the 3.5 mm AV jack is gone, and there is a new power button and PCIe
   connector. Renders in `models/renders/` would need re-exporting. **It also still models the
   cancelled Stock Clock rack** — strip that.
4. **`04-hawker-journey-map.md` header** says *"No `[testimony]` yet — no hawker has been
   interviewed."* No longer true as of 17 Sep. The body of that file still holds; only the provenance
   line is stale. `06-traywatch-user-journey.md` §1 says so explicitly.

---

## Spending is gated — Jamie's instruction, 17 Sep

**S$239.50 spent, S$160.50 left.** Verified against `FINANCE CLAIMS/` on 18 Sep.

> *"if you have any other expenses required, please let me know BEFORE purchasing… lmk what you need
> to buy, how much, and i can let you know if approved."*

She also said the two prototype descriptions were *"still quite vague to us"*, that the last claim
*"wont pass"* on his description, and that she rewrote it herself to get the reimbursement through.
**Never propose a purchase without also proposing the one-paragraph justification that goes with it**,
sourced to what the user actually said — that is the exact complaint she made.

Her other unanswered questions, now addressed: *"what is the user journey"* →
`hawker prototype 2/06-traywatch-user-journey.md` §8. *"you cannot assume your design is the best way
to solve her problem without asking her"* → asked, and the answer caused the pivot.

---

## Still unverified — do not invent answers

| # | Question | Blocks |
|---|---|---|
| ~~K1~~ | ~~What is the kitchen's buffer percentage?~~ **ANSWERED ≈10%** `[T5, 20 Sep]` — approximate. Chope's first keypad number now measures it exactly, every lunch, and logs it as `buffer_pct` | Was the biggest unknown; now instrumented |
| **§8** | Is the caterer paid per meal *scanned*? If so they are reimbursed for food nobody ate, the waste costs MINDEF not them, and the customer is MINDEF — not SATS/Foodfare | Chope's entire business model |
| ~~N1~~ | ~~Can I rearrange which dishes sit next to each other?~~ **ANSWERED YES** `[T7, 22 Sep]` — she can swap the trays. Schedule is now one swap per day in the 13:30–17:00 lull, order counterbalanced | Was the whole side arm; now scheduled |
| **N2** | How often do you top up a tray during lunch, and when do you stop? | The late-refill finding, the sharpest output in the project |
| **N3** | Do all the trays hold the same amount? | `tray_size`, and the abundance/tray-size lever |
| **N4** | ~~What time do you open and close~~ **08:00–19:00** `[T7, 22 Sep]` — but **which days is still open** | The six-day calendar and the weekday/weekend confound |
| **A3** | Where can a camera mount — sneeze guard, hood, pole? Is there a socket? | Camera placement |

**A1 is answered** (`[testimony]`, 17 Sep): the waste is raw, uncooked vegetables, caused by
vegetables selling slowly. That answer is what killed Stock Clock. The weighed version — cooked
leftovers and raw/prep waste on a kitchen scale, separately, daily — is still worth two minutes a day
because it is the Waste Diary deliverable. **A2 is dead** with Stock Clock.

---

## Business framing (worked out 15 Sep, revised 18 Sep for the camera pivot)

> Winnow, Leanpath and Orbisk cost £5,000–15,000 per kitchen, need cloud and a chef who interacts
> with it. They sell to hotels and large commercial kitchens. **Nobody serves the bottom of the
> market** — hawker stalls, cookhouses, nursing homes, school canteens. This is ~S$80, no cloud, no
> app, no training, nothing to maintain.

- **The old line "'no camera' is market access" is dead** — Tray Watch has a camera. **Do not patch
  it, replace it.** The replacement is stronger: **every competitor points the camera at the BIN.**
  Lumitics is literally a smart bin — you throw food in and press a green button. They measure the
  corpse. **This points at the display, during service, while there is still time to act** — and it
  does not just report, it changes the display and measures whether that worked. Prevention, not
  accounting, which is the argument `03-hawker-5w1h.md` §9 already makes.
- **Privacy survives in a better form:** the camera points down at food, and the crop is applied
  before anything is written to disk. Not a policy — a property of the code. Chope remains
  camera-free, so the Green Zone / eldercare access argument still holds for that half.
- **Chope is not an army product.** It fits any closed population where meals are declared ahead and
  someone cooks to a forecast: nursing homes, hospitals, boarding schools, hostels, corporate
  canteens. The SAF is the beachhead, not the market.
- **Tray Watch is the better prototype but the harder business** — thousands of tiny customers.
  Don't sell stall-by-stall: sell to food court operators (Koufu, Kopitiam, Fei Siong) who control
  fit-out and carry sustainability reporting, or rent rather than sell, or fund it through NEA's
  hawker programmes. The operator buys the fleet; the stall owner's ninety seconds a week stay
  identical — see `06-traywatch-user-journey.md` §7.

---

## Working with Raghav

- **Give a decision, not a menu.** Recommend, state the tradeoff in one line, move on.
- **Deliverables must carry the full hardware and technical architecture**, not prose summaries. He
  will ask for it back if it's missing.
- **He asks comprehension questions and means them** ("I don't really understand"). Trace the actual
  mechanism with a concrete worked example — not a summary of what it does.
- Be honest about what is assumed vs measured. He tags provenance in his own files
  (`[T1]` `[T2]` `[cited]` `[weak]` `[ASSUMED]`) and expects the same discipline back.
