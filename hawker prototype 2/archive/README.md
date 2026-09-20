# Archive — Stock Clock (cancelled 17 Sep 2026)

Prototype 2 was a four-slot weighing rack: 5 kg load cells under the raw ingredient trays, tracking
batch age so the oldest stock got used first. Designed, costed and specced. **Nothing was bought.**

**Why it was cancelled.** The stall owner was asked, and said the vegetables spoil because *students
do not pick them* — meat sells fast, vegetables sell slow, so she over-buys and the raw stock rots.
Stock Clock would have measured that rot perfectly and changed nothing, because the rot is the
symptom. Prototype 2 moved to the demand end of the same chain: `../05-traywatch-plan.md`.

**Kept, not deleted.** These files are the record of how the design got here, and the noise-handling
patterns in `stockclock.py` (`MIN_CHANGE_G`, `SETTLE_SECONDS`, the rolling median, the `demo()`
self-check) port directly to Tray Watch — see `../05-traywatch-plan.md` §5.3.

| File | |
|---|---|
| `BUILD-GUIDE.md` | Full build guide, wiring, parts list |
| `stockclock.py` | Working code. `python3 stockclock.py demo` is a self-check and passes |
| `wiring.svg` | HX711 → Pi 5 wiring |
| `spacer.scad` | The one printed part — a load cell spacer block. Was `models/spacer.scad` |
