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

- **The kitchen cooks ABOVE the indent.** *"If you input 100 they will cook more than 100."* The
  percentage is unknown and is the single biggest open question in the project.
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
- At the cook cutoff the board locks `COOK = confirmed + r × unconfirmed + margin`.
- After service, staff key in **portions left**. `taken = cooked − left` scores the forecast.
- **`r` and the margin are SEPARATE state.** `r` estimates the truth via a symmetric EWMA (α=0.25);
  the margin is its own EWMA of absolute forecast error. **Two traps, both hit in practice:** an
  asymmetric learning rate biases `r` ≈ +0.087 high and never converges; folding the margin back into
  the estimator compounds it upward and `r` never moves at all. A stock-out is a **censored**
  observation and may only ever push `r` **up**.
- **`r` starts at 1.0**, which reproduces today's number (everyone silent counts as eating), so day
  one carries no risk of running short. *(The artifact wrongly says it starts at 0.90 "the kitchen's
  current constant" — there is no such constant.)*
- **Honest measured result:** 2.7% steady-state saving against the indent over 60 replayed meals, and
  the learning period costs more than it saves. The baseline excludes the kitchen buffer on top (K1,
  unmeasured) so it understates. Ship the margin/stock-out trade table — it is the most credible
  artifact the prototype has.
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

USB webcam on the sneeze guard + Pi 5 logger. ~S$80 to buy. **Pivoted 17–18 Sep. Not built yet.**

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
  (median CIELAB), and therefore the **colour contrast to its neighbours** — that is the manipulated
  variable.
- **The experiment: the vegetable dishes never move.** Only their neighbours change, on alternate
  days. That separates colour from position, which a position experiment cannot do.
- 8 trays × 6 days = **48 dish-days** with a continuous contrast value — not a 3-vs-3 before/after.
  **But the headline test is a within-dish sign-flip permutation test over n = 8 dishes, not the
  48-point regression.** Arrangement changes by day, so a day-level test has a floor p of 0.10 and
  can never reach 0.05. The within-dish version has floor p = 0.0078 and holds dish identity,
  popularity, tray size and position constant by construction. `07-architecture.md` §5.5.
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

Files: `hawker prototype 2/05-traywatch-plan.md` (full build + schema) ·
`06-traywatch-user-journey.md` (the answer to Jamie's *"what is the user journey"*) ·
`09-traywatch-prd.md` (the PRD) · `07-architecture.md` at the repo root (**both** prototypes: data
flow, the clock, the colour maths, the statistics — diagrams).

**Known weak point:** rearranging the neighbours also moves the meat dishes, and where a popular dish
sits changes where the queue slows down. Not separable in six days. Say so rather than pretending the
contrast effect is clean.

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
| **K1** | What is the kitchen's buffer percentage? 5%? 20%? | The biggest single unknown in the project |
| **§8** | Is the caterer paid per meal *scanned*? If so they are reimbursed for food nobody ate, the waste costs MINDEF not them, and the customer is MINDEF — not SATS/Foodfare | Chope's entire business model |
| **N1** | Can I rearrange which dishes sit next to each other, on alternate days? | **The entire Tray Watch experiment.** Ask before mounting anything |
| **N2** | How often do you top up a tray during lunch, and when do you stop? | The late-refill finding, the sharpest output in the project |
| **N3** | Do all the trays hold the same amount? | `tray_size`, and the abundance/tray-size lever |
| **N4** | What time do you open and close, and which days? | The six-day calendar and the weekday/weekend confound |
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
