# Tray Watch — Pi setup, step by step

Everything you need, in the order you need it. Tonight is ~40 minutes at your desk.
Tomorrow at the stall is ~15 minutes, and 10 of those are her talking.

**The webcam is already owned** `[T6, 21 Sep]`, so nothing is waiting on a purchase or a
courier. Do not ask Jamie for anything until you have seen her stall and know whether a
clamp is actually needed.

---

## Tonight, at your desk

### 1. Flash the card — Lite, not Desktop

Raspberry Pi Imager → **Raspberry Pi OS Lite (64-bit)**.

**Lite, not the full Desktop image.** Tray Watch has no screen, no kiosk and no browser —
every megabyte of desktop is SD wear and another thing that can hang. (Chope needed
Desktop for its HDMI board. This one does not.)

In Imager's ⚙ advanced settings, before writing:

| Setting | Value |
|---|---|
| Hostname | `traywatch` |
| Enable SSH | ✅ password or key |
| Username | your usual one |
| WiFi | the stall's network **and** your phone hotspot as a fallback |
| Locale / timezone | **Asia/Singapore** |

Timezone matters: Imager defaults to Europe/London, cron runs on local time, and the
shutdown job would fire in the middle of service. `install-pi.sh` fixes it too, but
setting it here avoids a restart dance.

### 2. Boot it and copy the code over

```bash
ssh <you>@traywatch.local
git clone <your repo> ~/SG-Eco-Hackathon        # or rsync the folder across
cd ~/SG-Eco-Hackathon/"hawker prototype 2"
```

### 3. Confirm the clock actually synced

```bash
timedatectl | grep -i "System clock synchronized"
```

Must read **`yes`**. If it says `no`, the canteen WiFi is probably a captive portal — a
headless Pi cannot answer one, **and it fails looking exactly like success**. Fall back to
your phone hotspot and re-check. Do not skip this: with no NTP, the Pi boots at the last
shutdown time and every row's wall clock is fiction. (Frames are named by *sequence*, so
nothing is ever overwritten — but `sold_out_ts` and `last_refill_ts` would be wrong.)

### 4. Packages and a camera smoke test

```bash
sudo apt-get update && sudo apt-get install -y v4l-utils python3-pip
pip3 install --break-system-packages opencv-python-headless
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-ctrls
```

**Do not `apt-get install python3-opencv`** — on Raspberry Pi OS trixie it drags in
`libopencv-viz` → VTK → OpenMPI → a `libevent-pthreads` pinned to an exact `libevent-core`
build the repo has since moved past, and apt refuses the downgrade. The install fails every
time, not just once. `opencv-python-headless` from pip ships a **prebuilt aarch64 wheel** — on
a 64-bit Pi 5 this is a download, not the source build pip used to mean on 32-bit Pi OS.

Read the **full**, ungrepped `--list-ctrls` output — do not just grep for
`white_balance|exposure`. `capture.py`'s `wb_locked()` only recognises two control-name
spellings (`white_balance_automatic` and `white_balance_temperature_auto`); a camera that uses
a third name will silently mark every frame `wb_locked=0` for the whole week with no error.
**If neither name appears at all, tell me before tomorrow** — the colour arm changes. The
waste ledger, which is the headline claim, does not need white balance at all.

### 5. Print the grey card

A plain mid-grey rectangle on white A4, about 10 cm square. Free, and the colour
measurement is worthless without one in frame. Bring two if you can — a long tray row is
lit by more than one lamp.

---

## Tomorrow at the stall

### 6. Mount, then choose the crop

Mount on **her own sneeze guard** — her fixture, her stall. That is the materially easier
permission argument than anything fixed to shared canteen structure, and it is the one to
make. Tape the grey card at the end of the tray row, permanently in frame.

```bash
cd ~/SG-Eco-Hackathon/"hawker prototype 2"
python3 capture.py --aim
```

This writes **`aim.jpg`**: a 240-pixel-wide, blurred frame with a red grid labelled in
full-resolution pixels. It is deliberately too small to recognise a face — you cannot pick
a crop you cannot see, and looking at a full frame is exactly what the privacy claim
forbids. Copy it to your laptop (`scp`) and read the numbers off the grid.

```bash
export TW_CROP=x,y,w,h        # the tray row PLUS the grey card, and nothing else
python3 capture.py --check
```

`check.jpg` is the **only full-resolution image this program ever writes**, and it is
already cropped. Open it and answer two questions:

1. Is every tray visible, with the grey card in shot?
2. **Is any person in it, even a sleeve at the edge?**

Tighten `TW_CROP` and re-run until the answer to (2) is no. This is KPI **K3** — the
privacy claim is falsifiable, so falsify it now rather than asserting it on a slide.

### 7. Install

```bash
TW_CROP=$TW_CROP LAPTOP=you@your-laptop-ip sh install-pi.sh
```

Sets the white-balance lock and **reads it back to verify**, installs the capture service
gated on `time-sync.target`, and writes three cron lines: rsync out every 10 minutes, USB
mirror at close, shutdown 15 minutes later.

`CLOSE="20 19"` is already set for her **19:00 close** `[T7, 22 Sep]` — USB mirror 19:20,
shutdown 19:35. Capture starts at boot, so there is nothing to configure for opening time;
whenever you power the Pi on is when frame 0 is written.

Leave `LAPTOP=` off if your laptop is not on the same network — but then the USB stick is
your only second copy, and the script will say so.

For the USB mirror, leave a stick in permanently and mount it at `/media/usb`:

```bash
sudo mkdir -p /media/usb
lsblk -o NAME,SIZE,FSTYPE          # find it, usually sda1
echo "/dev/sda1 /media/usb vfat defaults,nofail,uid=1000 0 0" | sudo tee -a /etc/fstab
sudo mount -a
```

`nofail` matters — without it a missing stick stops the Pi from booting.

### 8. Prove it is running before you walk away

```bash
systemctl status traywatch --no-pager
sleep 150 && tail -3 frames/frames.csv
```

At 2-min intervals over an 08:00–19:00 day that is **~330 frames a day, ~40 MB**. A week fits on
any card with room to spare, and `rsync` moves it out every 10 minutes regardless.

You want `seq` climbing and `bytes` well above zero. **`bytes=0` means the camera failed
that cycle** — that is a gap, not a quiet moment, and `analyse.py` drops those rows so they
never read as "the tray was empty".

If the `wb_locked` column reads `0`, capture still runs and the waste ledger is unaffected;
only the colour arm is void. That is a warning, not a reason to stop.

### 9. The ten minutes that matter more than any of this

**Already answered, do not re-ask** `[T7, 22 Sep]`: she opens **08:00**, closes **19:00**, the
dish roster is the **same for lunch and dinner**, and **yes, she can swap the trays**.

Still needed, and write the answers into `context.md` in her own words:

- **Which days do you open?** (the only half of N4 still missing)
- **How often do you top a tray up, and when do you stop?** (N2 — the sharpest output in the project)
- **Do all the trays hold the same amount?** (N3)
- **Which dishes do you already know sell badly?**

That last one is the sharpest critique this project faces — she already knows. `context.md` is what
stops the weekly page telling an expert something she has known for ten years.

### 9b. The one thing to actually ask her to *do*

> *"Once in the afternoon when it's quiet — around 2 or 3 — swap two of the trays around.
> Different pairs on different days. Takes thirty seconds and you can put them back any time."*

**Once a day, in the dead stretch, not every other morning at open.** Measured: that gives a
confidence interval **2.4–3.9× tighter** (±9.1 against ±21.8–±35.6) and removes an upward bias that
made alternate-days report +17.7% for a real +10% — because the day's weather and footfall cancel
exactly when both arrangements happen inside the same day. `design_checks.py` C7 is the receipt.

**Counterbalance the order**: whichever arrangement she starts the day in, start the *other* one
tomorrow. Write down the real time she swapped — `from_ts` below — including the days she forgets.
A forgotten day is data, not a failure; a fabricated schedule is neither.

It does **not** make the experiment significant — the five-dish ceiling is combinatorial and no
schedule lifts it. It buys precision, which is what the arm reports.

That last one is the sharpest critique this project faces — she already knows. `context.md`
is what stops the weekly page telling an expert something she has known for ten years.

Then show her `check.jpg` on your phone. **Show her the crop, not a privacy policy.**

---

## Every morning after, from your phone

```bash
ssh <you>@traywatch.local 'tail -1 ~/SG-Eco-Hackathon/"hawker prototype 2"/frames/frames.csv'
```

Booted, capturing, and this is the last frame it wrote. A blank line or a stale `seq` means
go and look. **A gap on day 5 is the one thing you cannot redo** — that is KPI K1, 6/6.

Fill in `dishes.csv` each day — one row per tray **per block**, because the trays move at the
afternoon swap and `slot` therefore means two different dishes before and after it:

```csv
day,block,from_ts,slot,dish,is_veg
2026-09-22,am,08:00,1,white rice,0
2026-09-22,am,08:00,2,curry chicken,0
2026-09-22,am,08:00,3,kangkong,1
2026-09-22,pm,14:35,1,white rice,0
2026-09-22,pm,14:35,2,kangkong,1
2026-09-22,pm,14:35,3,curry chicken,0
```

`from_ts` on the `pm` rows is **when she actually swapped**, not when she was asked to. If she did
not swap that day, write one `am` block covering the whole day and nothing else — the waste ledger
does not care, and the side arm should lose that day honestly rather than assume it happened.

Two minutes a day, by you, never by her. Dish identity cannot come from the frames:
matching dishes by colour would use the very variable the side arm measures.

---

## At the end of the week, on your laptop

```bash
pip install google-genai               # once
export GEMINI_API_KEY=...             # the key, not committed, not in the repo
python analyse.py                     # frames -> readings.csv -> daily.csv    (~US$2)
python report.py                      # daily.csv -> page.html
```

Model is `gemini-2.5-flash` with **thinking off** for the 1,980 fill reads — reading how
full a tray is is perception, not reasoning — and thinking **on** for the single
recommendation call, which has to weigh six levers against her own words. Override with
`TW_MODEL` if you want to compare.

`analyse.py` is **resumable** — it skips frames already in `readings.csv`, so a crash or a
Ctrl-C costs nothing. It prints the estimated cost before spending anything.

**Run it on day 1's frames the same evening.** The Gemini calls have never hit the real
endpoint — no key existed when they were written. If a schema or the thinking config is
wrong, day 1 costs 35 cents to find out and five days to fix; day 6 costs the prototype.

`report.py --no-llm` writes the same page with an arithmetic sentence and no API call. That
is not a debug flag, it is the deadline plan: if the API is down on 30 Sep, the page still
prints.

Open `page.html` and print it. One sheet, two photographs of her own tray, one sentence,
one change.

---

## Troubleshooting

| Symptom | What it is |
|---|---|
| `TW_CROP is not set. Refusing…` | Working as designed. Do step 6 — it will not write an uncropped frame. |
| `bytes=0` rows | Camera failed that cycle. Check the USB extension; the Pi 5 caps total USB current at 600 mA unless it sees a 5 A PD supply. |
| `seq` not climbing | `systemctl status traywatch`. If it is crash-looping, `journalctl -u traywatch -n 50`. |
| `System clock synchronized: no` | Captive portal. Use the phone hotspot. |
| `wb_locked=0` | Auto white balance would not lock. Colour arm void, waste ledger fine. Tell me. |
| Pi will not boot after a power cut | The shutdown cron exists so this does not happen. Never pull the plug — `sudo shutdown -h now`. |
| `analyse.py` says "no dishes.csv" | It still runs. Dishes are named `slot1..slotN` and arrangement is `unknown`. |

---

## Check everything still works before you trust it

```bash
python capture.py --selftest       # crop refuses bad input, drops the frame edge
python analyse.py --selftest       # the noise chain
python report.py  --selftest       # dish picking and the page
python design_checks.py            # the six measured claims behind the PRD
```

`design_checks.py` imports the shipped chain from `analyse.py` rather than copying it, so
if you tune `MIN_DROP` or `REFILL_JUMP` against the real stall, re-run it — the −9.5%
`cooked_total` bias is measured against those exact constants.
