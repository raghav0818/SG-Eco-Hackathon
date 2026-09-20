# Stock Clock — build guide

A four-slot ingredient rack for a cai png stall. Each slot weighs itself, so the Pi knows what came
in, what got used, and how old the oldest stock is — with nobody typing anything.

Build it in this order. Every step ends with a **✅ check** — if that check fails, fix it before
moving on. A wiring mistake found at step 5 takes a minute; the same mistake found at step 11 takes
an evening.

**Total time:** one afternoon on the bench, one afternoon on the rack.
**Wiring diagram:** [`wiring.svg`](wiring.svg) — open it and keep it next to you.

---

## ⚠️ Read this first

1. **Power the Pi off while wiring.** Only plug the USB-C in once every wire is checked.
2. **The HX711 VCC goes to 3.3 V, never 5 V.** At 5 V its data pin pushes 5 V into a 3.3 V input and
   can permanently kill that GPIO pin.
3. **Count pins from pin 1** — the corner nearest the microSD slot. Being one pin out is the single
   most common failure in this whole build.
4. **The Pi 5 uses micro-HDMI**, not full-size HDMI.
5. **Never put more than 5 kg on a slot.** The load cells bend to measure; overload one and it stays
   bent, reading wrong forever. Don't lean on the rack.

---

## 1 · Parts

| # | Part | Qty | Note |
|---|---|---|---|
| A | Raspberry Pi 5, 2 GB | 1 | ✔ bought |
| B | Official 27 W USB-C supply | 1 | A phone charger will brown-out the Pi 5 |
| C | Active cooler | 1 | The Pi 5 throttles without one |
| D | microSD card, 32 GB | 1 | |
| E | 5 kg load cell **bundled with its HX711** | 5 | **5 kg, not 20 kg** — 20 kg can't resolve a handful of greens. Buy 5: one spare, they die if overloaded |
| F | *(included with E)* | — | Cytron sells the cell and amplifier as one kit |
| G | 5 mm RGB LED, **common cathode** | 4 | Longest leg is the cathode. Buy a pack of 10 |
| H | 220 Ω resistor | 8 | Two per LED. An assorted resistor kit is cheaper than buying 8 |
| I | **ML-2020 RTC battery** for Pi 5 | 1 | The Pi 5 has a clock built in — this is just its battery. **No DS3231 needed** |
| J | Momentary push button | 1 | 6 mm tactile, buy a pack |
| K | HDMI screen, 5–7" | 1 | Any monitor works for bench testing |
| L | **micro-HDMI to HDMI cable** | 1 | Easy to forget |
| M | Half-size breadboard + jumper wires (M–F and M–M) | 1 set | |
| N | Plywood base, acrylic top plates, spacer blocks, M4/M5 bolts | — | SUTD fab lab |

**Tools:** small screwdriver (for the HX711 screw terminals), wire strippers, drill, hex keys.
A multimeter is not required but makes step 5 much easier to debug.

---

## 2 · Bench before rack

**Do not build any woodwork yet.** Get one load cell reading real grams on a table first. If
something is wrong with the electronics, you want to find out before you've drilled anything.

---

## 3 · Set up the Pi

1. Flash **Raspberry Pi OS (64-bit, with desktop)** to the microSD using Raspberry Pi Imager.
2. Boot the Pi with the screen, keyboard and mouse attached.
3. Open a terminal and run:

```bash
sudo apt update
sudo apt install -y python3-lgpio gpiod
sudo raspi-config     # Interface Options → I2C → Enable → reboot
```

4. Find out which GPIO chip your kernel uses — this differs between Pi 5 OS versions:

```bash
gpiodetect
```

> ✅ **Check:** you see a line mentioning `pinctrl-rp1`. Note whether it says `gpiochip0` or
> `gpiochip4`. The code tries both automatically, so you don't need to change anything — but if
> something fails later, this is the first thing to look at.

**Why not the libraries in most tutorials?** `RPi.GPIO` and `rpi_ws281x` do **not** work on the Pi 5
— the RP1 chip replaced the hardware they talk to. Almost every HX711 and NeoPixel tutorial online
uses them. This build avoids both: it talks to `lgpio` directly and uses plain LEDs.

---

## 4 · Copy the software onto the Pi

Put `stockclock.py` in a folder on the Pi, then:

```bash
python3 stockclock.py demo
```

> ✅ **Check:** prints `demo: all checks passed`. This tests the batch and buy-list logic with fake
> weights, so it works before any hardware is connected. If this fails, the problem is the file, not
> your wiring.

---

## 5 · Wire ONE load cell (slot 1)

### 5a · Load cell → HX711

Strip the four wires and screw them into the HX711's terminal block:

| Load cell wire | HX711 terminal |
|---|---|
| Red | E+ |
| Black | E− |
| White | A− |
| Green | A+ |

Leave `B+` and `B−` empty.

> Wire colours vary between manufacturers. If your numbers go **down** when you press on the cell,
> swap green and white. Nothing is damaged by getting it backwards.

### 5b · HX711 → Pi

Power off the Pi first.

| HX711 pin | Pi pin | |
|---|---|---|
| VCC | **pin 1** | 3.3 V — **not 5 V** |
| GND | pin 6 | |
| DT | pin 29 | GPIO 5 |
| SCK | pin 31 | GPIO 6 |

Power the Pi back on and run:

```bash
python3 stockclock.py test
```

> ✅ **Check:** slot 1 shows a raw number, and the number **changes when you press down on the load
> cell**. It will be a large number like `-84213` or `271044` — that's normal, it's raw ADC counts.
> Slots 2–4 will time out with an error; that's expected, nothing is connected to them yet.

**If it hangs or errors:** 99% of the time it's (a) VCC on the wrong pin, (b) DT and SCK swapped, or
(c) a loose screw terminal. Check those three before anything else.

---

## 6 · Calibrate slot 1

This is the step everything downstream depends on.

```bash
# 1. Nothing on the load cell at all
python3 stockclock.py tare 1

# 2. Put a KNOWN weight on it — a sealed 1 kg bag of rice is perfect
python3 stockclock.py cal 1 1000

# 3. Read it back
python3 stockclock.py test
```

> ✅ **Check:** with the 1 kg bag on, slot 1 reads between **980 and 1020 g**. Take it off and it
> should return to roughly 0. Put it back on — still ~1000 g.

If it reads a wildly wrong number, your `scale` is off — re-run `tare` with a genuinely empty cell
and try again.

---

## 7 · Repeat for slots 2, 3, 4

Same as steps 5 and 6, with these pins:

| Slot | HX711 DT | HX711 SCK | VCC | GND |
|---|---|---|---|---|
| 1 | pin 29 (GPIO 5) | pin 31 (GPIO 6) | 3.3 V | any GND |
| 2 | pin 32 (GPIO 12) | pin 33 (GPIO 13) | 3.3 V | any GND |
| 3 | pin 35 (GPIO 19) | pin 36 (GPIO 16) | 3.3 V | any GND |
| 4 | pin 38 (GPIO 20) | pin 40 (GPIO 21) | 3.3 V | any GND |

Run `tare` and `cal` for each (`tare 2`, `cal 2 1000`, and so on).

Use the breadboard's power rails: one jumper from pin 1 (3.3 V) to the red rail, one from pin 6 (GND)
to the blue rail, then every HX711 takes its VCC and GND from the rails. Far tidier than four
separate jumpers to the header.

> ✅ **Check:** `python3 stockclock.py test` shows four sensible gram readings, and pressing each
> cell moves only its own number. If pressing cell 2 moves cell 3's number, you've crossed a wire.

---

## 8 · Wire the four LEDs

Each RGB LED has four legs. The **longest** one is the common cathode. Blue is not used.

For each LED:
- **Red leg** → 220 Ω resistor → its GPIO pin
- **Green leg** → 220 Ω resistor → its GPIO pin
- **Longest leg** → ground rail
- **Blue leg** → nothing

| Slot | Red leg → | Green leg → |
|---|---|---|
| 1 | pin 11 (GPIO 17) | pin 13 (GPIO 27) |
| 2 | pin 15 (GPIO 22) | pin 16 (GPIO 23) |
| 3 | pin 18 (GPIO 24) | pin 22 (GPIO 25) |
| 4 | pin 24 (GPIO 8) | pin 26 (GPIO 7) |

Red and green lit together make amber — that's why there's no third channel.

```bash
python3 stockclock.py leds
```

> ✅ **Check:** each LED in turn goes green → amber → red → off. If one shows red where green should
> be, its two legs are swapped. If one never lights, check the resistor and that the long leg really
> is in the ground rail.

---

## 9 · Wire the button and the clock

**Button:** one leg → pin 37 (GPIO 26), other leg → pin 39 (GND). No resistor needed — the software
switches on the Pi's internal pull-up.

**Clock — Pi 5 only, no wiring.** The Pi 5 has a real-time clock built into its power-management
chip. It only needs a battery. Find the small two-pin **J5 / BAT** socket just right of the USB-C
port, and plug the ML-2020 in. Stick the cell to the case with its adhesive pad. That's it — no
module, no I²C, no wires, and `stockclock.py` needs no change, because it just asks the operating
system for the date.

Charging is off by default, so turn it on once:

```bash
sudo rpi-eeprom-config --edit     # add the line:  POWER_OFF_ON_HALT=1
sudo bash -c 'echo 3000000 > /sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/max_user_freq' 2>/dev/null
sudo hwclock -w                   # write the current time into the RTC
```

> ✅ **Check:** `sudo hwclock -r` prints the correct date and time. Now unplug the Pi from the
> network entirely, power it off for a minute, boot it back up, and run `date`. **The time must
> still be right.** This is the whole point — the stall has no Wi-Fi, and if the Pi boots thinking
> it's 1970, every age light is wrong.

> If you are bench-testing on an older Pi that has no built-in RTC, skip this step. It is the one
> step you cannot do before the Pi 5 arrives, and it takes five minutes.

---

## 10 · Build the rack

Now the woodwork. Four identical slots, 190 mm apart. Dimensions come from
[`../models/prototypes.scad`](../models/prototypes.scad) — open it in OpenSCAD and press F5 to see
what you're building.

```
                    basin (ingredient)
                 ┌────────────────────┐
                 │  acrylic top plate │   180 × 260 × 5 mm
                 └────────┬───────────┘
                          │ load-end spacer   ← bolts to the FREE end
     ═══════════════════════════════════      ← load cell, arrow pointing DOWN
        fixed-end spacer │                    ← bolts to the base
 ┌────────────────────────────────────────┐
 │            plywood base                │
 └────────────────────────────────────────┘
```

**The mistake everyone makes:** bolting the load cell flat to the base. It is a *beam* — it works by
bending. If both ends are held rigid, it reads nothing.

Rules per slot:
- One end bolts to a spacer on the base. The other end bolts to a spacer under the top plate.
- The arrow stamped on the cell **points down**.
- There must be an **air gap** under the free end so it can flex.
- **Nothing may touch the top plate except the basin.** Not the frame, not the next plate along.
  A plate resting on its neighbour ruins both readings.
- Bolts are usually M5 at the fixed end, M4 at the load end — check the cells that arrive.

Mount the Pi and breadboard in the 3D-printed enclosure, **away from the wet basins**, and run the
load cell cables along the back.

> ✅ **Check:** `python3 stockclock.py test` again, now on the rack. Press gently on each plate —
> only that slot's number should move. Put the 1 kg bag on each plate in turn; each should read
> ~1000 g. **Re-run `tare` for every slot now that the plates and basins are on**, then check the
> empty rack reads ~0 g everywhere.

---

## 11 · Run it

```bash
python3 stockclock.py run
```

Fullscreen display, four slots, live. Press the button to switch to the buy list. Press `Esc` to
quit.

To make it start on boot, add it to autostart:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/stockclock.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Stock Clock
Exec=python3 /home/pi/stockclock/stockclock.py run
EOF
```

---

## 12 · Full test

Walk the lettuce scenario on the real rack — this is exactly what `demo` asserts, done physically:

| Do this | Should happen |
|---|---|
| Put 500 g in slot 1 | Slot 1 reads 500 g, light **green** |
| Rest your hand on the basin for 5 s | **Nothing recorded** — under the 20 g / 2 s threshold rules |
| Take out 200 g | Slot 1 reads 300 g, still green, usage logged |
| Change the Pi's date to tomorrow, restart | Light turns **amber** — the stock is now day 2 |
| Change the date forward again | Light turns **red** |
| Add 400 g of fresh stock | Light stays **red** — the *oldest* batch is what counts |
| Take out 300 g | Old batch drains first, light returns to **green** |
| Press the button | Screen shows the buy list |

> ✅ **Final check:** unplug the Pi mid-service, plug it back in. The batch ages and the stock
> figures must survive — they're saved to `state.json` on every event.

---

## 13 · Troubleshooting

| Symptom | Most likely cause |
|---|---|
| `HX711 never became ready` | VCC not connected, or on 5 V instead of 3.3 V; or DT/SCK swapped |
| Readings jump around wildly | Loose screw terminal, or the load cell cable is running alongside mains wiring |
| Weight goes down when you add load | Swap the green and white load cell wires |
| Reads roughly 0 no matter what | The cell is bolted flat at both ends and can't bend — add the spacers |
| One slot mirrors another | Two DT pins crossed on the header |
| LED shows red instead of green | The two LED legs are swapped |
| LED never lights | Resistor missing, or the long leg isn't in the ground rail |
| Time is wrong after a power cut | ML-2020 not plugged into J5, or never charged — run `sudo hwclock -w` with the battery in and leave the Pi powered for an hour |
| `No GPIO chip found` | Not running on a Pi, or `python3-lgpio` isn't installed |
| Numbers drift over an hour | Normal thermal drift — re-run `tare` at the start of each test day |

---

## What to tune once it's at the stall

These are set at the top of `stockclock.py` and **should** be changed against the real stall, not
guessed on a bench:

| Knob | Default | Change it if |
|---|---|---|
| `MIN_CHANGE_G` | 20 g | Knocks are registering as stock (raise it), or small additions are missed (lower it) |
| `SETTLE_SECONDS` | 2.0 s | Readings land before the basin stops rocking |
| `SAMPLES` | 15 | Readings look noisy (raise it) or the display feels sluggish (lower it) |

---

## The assumption to keep an eye on

The software drains the **oldest batch first**. If she digs past the old stock to get the fresh
stuff, the recorded ages drift away from reality and the lights start lying.

The amber light is what nudges toward taking the old one — but it's an assumption, not a
measurement. Watch for it during testing, and say so honestly in the pitch. It's marked with a
`ponytail:` comment in `apply_delta()`.
