# Chope kitchen board — UI/UX, as built

Mockup (approved, matches shipped `board.html`): https://claude.ai/code/artifact/66b9c23a-9b6c-43fd-8369-d637abb61909

This went through three rounds before landing: a richer trend-dashboard version was cut for
reading as a performance dashboard (§0); the palette was redone to the reference image Raghav
supplied (a retro dusk-desert poster); the content was then cut a second time because a cook
mid-service doesn't want yesterday's trend, he wants today's number. What's below is what's
actually in `board.html`, `chope.py` and `install.sh` now — not a proposal.

---

## 0. The one rule that survived every rewrite

`08-chope-prd.md`'s Design & Branding section: *"the board shows the number the kitchen should
cook, **not** how much they wasted yesterday... a board that displayed yesterday's waste would be
a performance dashboard pointed at the lowest-paid people in the building."* Sourced to
`01-problem-map.md` §4.1 — a real interview constraint, not a style preference.

The shipped board has **no history anywhere on it.** No trend, no sparkline, no "r held," no
buffer percentage, no cumulative anything. Every screen answers one question: *what does the cook
need to do right now.* That's a stronger form of the same rule, arrived at from the opposite
direction — Raghav's objection was "he's not a data scientist," not "don't judge him," but they
land in the same place: nothing on this board is for anyone to interpret after the fact.

---

## 1. The four screens, exactly as shipped

| State (`B.state`) | What's on screen | Data used |
|---|---|---|
| `open` | A ring, ticking down to the cutoff. Nothing else. | `B.cutoff` ("HH:MM") |
| `cook` | The number. "COOK" beneath it. Three plain counts underneath: confirmed / declined / silent. | `B.cook`, `B.eat`, `B.notc`, `B.unconf`, `B.t` |
| `cooked` | "Left over?", and the pan it is asking about: *of 97 cooked*. | `B.actual` |
| `done` | A checkmark, "Logged." | nothing |

No equation, no bounds line, no percentages, no leftover breakdown. The three counts on the `cook`
screen are the only carry-over from earlier drafts, and they're counts, not arithmetic — no `×`,
no `r`, no "margin."

`meals.csv` and `chope_state.json` are untouched and keep logging everything (`r`, `buffer_pct`,
`slack`, `stockouts`, the full history) exactly as before — that data still exists, for whoever
wants to read the CSV later. It's just off the wall.

---

## 2. Look

Palette taken directly from the reference poster Raghav supplied (retro dusk-desert, halftone
grain): navy `#1a2e35`/`#244855` ground, rust `#874F41` borders, sage `#90AEAD` secondary, cream
`#FBE9D0` for the hero number, one accent — orange `#E64833` — used only for state/UI (chips, the
countdown ring, the checkmark), never as a judgement on the number.

Type: Anton (the hero digit and short prompts — poster-scale, not mono, so the number reads as a
headline, not a readout), Archivo Narrow (all caption/label text, tracked and uppercase),
JetBrains Mono (the countdown and the three plain counts — anywhere digits need to line up).

A hand-rolled SVG grain filter (`feTurbulence`, no image asset) sits behind the `open` screen only.
`cook`/`cooked`/`done` paint flat navy over it — calmer, on purpose, for the one moment a number
actually sits on the wall.

---

## 3. What changed in code

**`board.html`** — full rewrite. Fills the actual viewport (`position:fixed;inset:0`) instead of a
centered box — the first version of this file looked designed for a phone, not the HDMI screen
it's actually going on. Still exactly `<script src="board.js">` + the 5 s `<meta refresh>`. Still
no `fetch()`, no server, no listening socket.

Fonts are **self-hosted**, not loaded from Google Fonts' CDN: `fonts/anton.woff2`,
`fonts/archivo-narrow.woff2`, `fonts/jetbrains-mono.woff2` sit next to `board.html` and are loaded
via local `@font-face` rules. Reason: `chope.py`'s cron jobs need the internet (Telegram), but
`board.html` itself must render correctly even if the Pi's WiFi is down at that instant — that's
the same claim `install.sh` already makes about the kitchen half needing no network, just applied
to typography too. (Archivo Narrow and JetBrains Mono downloaded as their variable-font files,
which is why one `.woff2` each covers weights 500–700 and 400–700 respectively — `font-weight: 500
700` in the `@font-face` rule, not three separate files.)

**One count-up animation, gated correctly.** The board reloads *the whole page* every 5 seconds —
so an animation that just runs on page load would replay from zero every 5 seconds for as long as
the board sits in `cook`, which could be hours. Fixed by keying a `localStorage` flag on
`B.d + state + B.cook`: the animation fires once, the first reload after a new number appears, and
every reload after that just prints the number flat. This is the one place in the file doing
something non-obvious, and it's commented in code as to why.

**`chope.py`** — one field added. `CUTOFF = os.environ.get("CHOPE_CUTOFF", "")`, passed as
`cutoff=CUTOFF` in `cmd_open()`'s `board()` call. That's the entire backend change — the earlier
draft of this PRD planned a `recent()` history helper and `n`/`stockouts` fields; none of that
shipped, because the screens that would have used it got cut in §0/§1 above.

**`install.sh`** — derives `CHOPE_CUTOFF` from the `LOCK_AT` cron variable that already exists
(`"30 10"` → `"10:30"`) and writes it into `/etc/chope.env`, idempotently, so editing `LOCK_AT` and
re-running `install.sh` is the only place the cutoff ever needs to change — it can't drift out of
sync with the actual cron job the way a separately-typed value could.

**`keypad.py`** — untouched, as planned.

---

## 4. Verified before shipping

- `python forecast.py` and `python test_chope.py` — both still pass unmodified; the board change
  touches no forecasting logic and `test_chope.py` doesn't assert on `cutoff`, so nothing to update
  there.
- `node --check` against the extracted inline script — valid JS.
- `sh -n install.sh` — valid shell.
- All three font files downloaded and confirmed as real WOFF2 (not error pages) before wiring them
  in.

**Not yet done, and it's the one real gap:** nobody has opened this in `chromium --kiosk` on an
actual Pi 5 with an HDMI screen. The self-hosted fonts, the grain filter, and the full-viewport
layout are all standard Chromium/CSS, but "should work" is not the same claim as "watched it boot."
Do that before 2 Oct.

---

## 5. Cost

**S$0.** Fonts are free (Google Fonts, self-hosted, three files). No new hardware. No dependency
added to either the Python side or the page.
