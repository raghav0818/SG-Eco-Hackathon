# Chope — showcase bot: decisions from the grilling session (23 Sep)

**Why this exists.** Mentor: *"for Chope, do consider to look into gamification … as you are
targeting the behavioural changes."* Raghav, 23 Sep: Chope is "just a counter" and cannot be
filmed on base. This file records what was decided so the last round of Chope changes can be built
in one go, before attention moves to the Scale-Up Plan (which is what gets judged).

Inputs: `11-chope-gamification-research.md` (anonymity constraint, Telegram API facts),
`12-chope-retention-and-prize.md` (monthly special lunch, Goal Days, prize rules; **supersedes 11's
"no prizes"**).

---

## 1. Decisions

| # | Question | Decision | Source |
|---|---|---|---|
| Q1 | What is the showcase? | **Live and interactive.** Raghav brings the product; visitors play with it on **one phone** in a demo Telegram group | Raghav |
| Q2 | How many live units? | **One** — the demo group | Raghav |
| Q3 | Where does the game appear? | **Telegram only.** The kitchen board stays as shipped (`10-chope-board-ui-prd.md`) — it is for the chefs. Numpad test on the real board: **24 Sep** | Raghav |
| Q4 | Real Telegram trial? | **No.** All data is seeded and fake, and labelled as such on the slide | Raghav |
| Q5 | Time budget | **Live demo only, finish ASAP.** These are the last Chope changes; the Scale-Up Plan comes next | Raghav |
| Q6 | Commands need the bot to read the chat | **Yes — add a listening loop on the Pi.** Outbound long-poll (`getUpdates`), no open port | Raghav |
| Q7 | Who is on the leaderboard? | **All units** — the demo unit plus seeded rivals. Names are **made-up and army-flavoured** (e.g. Alpha Coy, Hangar 3), not real SBAB squadrons, so fake numbers never look like real data about a real unit `[default — say if you want otherwise]` | Raghav + default |
| Q8 | Commands | **All eight** (§3) | Raghav |
| Q9 | Stickers / GIFs | **Public Telegram sticker packs only.** Animated/video stickers stand in for GIFs — no GIF files, no hot-linked URLs to die mid-demo | Raghav |
| Q10 | Demo flow | **Wizard of Oz**: `/demo` runs a full lunch in ~90 s; Raghav keys the kitchen numbers on the real numpad; `/demo auto` fakes them if the numpad fails | Raghav |
| Q11 | Tone | **Singlish NS banter.** Jokes never target the kitchen or a person | Raghav |

---

## 2. What changes, and what does not

**Unchanged:** the poll stays a native **anonymous** poll — votes never carry a user id.
`forecast.py`, the COOK bound, the two-number keypad and `meals.csv` are untouched; `board.html` got two lines for the 45 s demo ring (§5b).

**Privacy line for the slide** (replaces "no daemon"): *"Votes are anonymous, enforced by
Telegram. Commands are answered and forgotten — Chope stores no user id anywhere."* A command
message does arrive with `from.id`; the listener reads the text and discards the rest.

**Added:**

| Piece | What | Why |
|---|---|---|
| `chope.py listen` | Long-poll loop: `getUpdates(timeout=25, allowed_updates=["message","poll"])`, dispatches `/commands`; only the configured group chat can drive it. Systemd unit `chope-listen` | Commands need a listener; outbound-only keeps "no listening socket" true |
| `units.json` (via `game.py`) | Seeded month: each unit's Goal Days, portions saved. The demo unit's row is updated by every real scorecard | Q4: fake data, but the demo unit visibly climbs as visitors vote |
| Sticker lookup | `getStickerSet(name)` once at startup, cache `file_id`s by mood (win / sad / thinking / hype). **A missing pack skips the sticker, never the message** | Q9; a sticker must never be the thing that breaks the demo |
| Banter in `chope.py` messages | `open`, `lock`, `left` messages rewritten in the voice of §4, plus a sticker | Q11 |
| `install.sh` | Adds the `chope-listen` service | Idempotent, like the rest |

**Removed from the group message:** the kitchen buffer (`kitchen cooked 99 (+10%)`,
`chope.py:136`). It points a performance number at kitchen staff in a chat full of NSFs —
the same rule the board follows (`01-problem-map.md`/`00-master-plan.md` §4.1). Still logged as
`buffer_pct` in `meals.csv`. `[flagged by 11; say if you want it kept]`

**Game rules — Q12, decided 23 Sep: option B, most points wins.**
- **Goal Day** = replies ≥ 80% of strength = **1 point**. "Not eating" counts exactly as much
  as "Eating", so a false reply earns nothing.
- **The unit with the most points at month end wins the cookhouse's monthly special**
  (Western by default). Single winner; ties broken by portions saved.
- `/menu` is an anonymous poll on next month's special.
- Known cost, accepted: in single-winner contests the leader coasts and units far behind stop
  trying (`12`). If it ever runs for real, watch the bottom two units' reply rates in week 3.
- **Month end** (built 23 Sep, `game.rollover`): `units.json` carries `"month"`. The first
  `chope.py open` of a new month posts the final table and crowns the leader (ties → portions
  saved) **before** the lunch poll, zeroes every unit, opens the champion's menu vote, and
  appends to `champions` — `/leaderboard` then shows *"Last month: 🏆 …"*. A month with no Goal
  Days crowns nobody. It only rolls **forward**, so a demo fast-forward is never undone by cron.
- **At the booth:** `/demo monthend` runs the same rollover now. Sequence for the audience:
  `/demo` (visitor votes → Alpha takes the lead) → `/demo monthend` (Alpha crowned, everyone
  to 0, menu vote) → `/leaderboard` (October, "Last month: 🏆 Alpha Coy") → `/demo reset`.
  If the visitor did **not** vote, Bravo wins the tie on portions saved and the bot says
  *"Alpha Coy finished #2. Next month our turn lah."* — the stakes of one tap, on screen.

---

## 3. Commands

| Command | Reply |
|---|---|
| `/leaderboard` | All units ranked by Goal Days this month, 🥇🥈🥉, demo unit marked 👈 |
| `/progress` | `▓▓▓▓▓▓▓░░░ 14 pts · #2 of 5 · 3 lunches left` + the prize line |
| `/saved` | Portions not wasted this month — *"the food you didn't waste becomes your Western lunch"* |
| `/menu` | Anonymous poll: next month's special — Western / Mala / Korean BBQ / Pizza |
| `/today` | Replies so far vs the 80% goal, minutes to cutoff |
| `/excuse` | Random NS excuse for skipping lunch + sticker |
| `/8ball` | *"Will lunch be good today?"* — random answer + sticker |
| `/demo` · `/demo auto` | Full lunch in ~90 s (§5) |
| `/help` | This list |

---

## 4. Voice — sample messages

```
🍛 Lunch today, who's eating?
Yesterday only 6 plates came back. Steady lah Alpha.
Goal: 72 replies. Silent = cooked for you anyway.
▓▓▓▓▓▓▓░░░ 14 pts · #2 of 5 · 3 lunches left
```
```
🔒 Poll closed. 74/90 replied — GOAL DAY ✅
Kitchen cooking 81. Don't say bojio.
```
```
Lunch done. 5 plates came back (yesterday 9) 👏
▓▓▓▓▓▓▓▓░░ 15 pts · #1 of 5 · 2 lunches left
[sticker: hype]
```
```
🔒 Poll closed. 72/90 replied — GOAL DAY ✅ +1 pt
🥇 ALPHA COY TAKES THE LEAD! 🍔 Western lunch is within reach.
[sticker: win]
```
`/excuse` pool (sample): *"Sergeant say run 2.4 during lunch."* · *"Guard duty, cannot."* ·
*"Book out early, eat McDonald's already."* · *"Canteen got chicken rice, sorry cookhouse."*

---

## 5. The booth demo, step by step

1. Visitor taps `/demo` on the phone. Bot posts the poll with a **45 s** countdown; fake
   voters are pre-seeded so the numbers look like a unit, the visitor's vote is added on top.
2. Poll locks → the **real kitchen board** on the table shows **COOK N**.
3. Raghav keys *cooked* then *left* on the **real numpad** (or `/demo auto` fills them).
4. Scorecard + sticker land in the chat; `/leaderboard` has moved. Seeded so **Alpha Coy is
   tied for first on 14 pts**, and the 71 seeded votes are **one short** of the 72-reply goal —
   **the visitor's own tap earns the Goal Day** and puts the unit in the lead
   (*"🥇 ALPHA COY TAKES THE LEAD!"*). If they don't vote, the unit misses — which is the point.

Reset between visitors: `/demo reset`.

## 5b. As built (23 Sep)

| File | Change |
|---|---|
| `game.py` (new) | League state in `units.json`, seed, Goal Day, ranking, all message text, stickers |
| `chope.py` | `open`/`lock`/`left` call the game; new `listen` (long-poll + 9 commands + `/demo` timer); buffer line gone from the group; `check` reports the sticker packs |
| `board.html` | Two lines: cutoff accepts seconds, ring starts at `B.opened` for a 45 s demo |
| `install.sh` | `chope-listen` systemd service |
| `test_chope.py` | Stubs every Telegram method; asserts Goal Day at 80%, the demo's one-vote tip, the lead change |

Knobs (env, `/etc/chope.env`): `CHOPE_UNIT` (default Alpha Coy), `CHOPE_PRIZE`, `CHOPE_STICKERS`
(default `UtyaDuck,HotCherry` — **unverified until `chope.py check` runs on the Pi**).

---

## 6. Open items

| Item | Owner | When |
|---|---|---|
| Numpad on the real board, end to end | Raghav | 24 Sep |
| Pick sticker packs (send `t.me/addstickers/...` links, or Claude picks) — verified on the Pi with `getStickerSet`, since no token exists off the Pi | Raghav / Claude | at build |
| Demo group created, bot added as admin (needs admin to read `/commands` reliably with privacy mode on — commands work without admin, plain text does not) | Raghav | before build test |
| Venue Wi-Fi at Temasek Shophouse unknown → phone hotspot for the Pi as the default | Raghav | 2 Oct |
| Slide label: *"Seeded demo data. Telegram half is real; the kitchen half is real hardware driven by a demo script — not installed on base."* | Raghav | slides |
