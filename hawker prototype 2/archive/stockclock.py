#!/usr/bin/env python3
"""Stock Clock - four-slot ingredient rack. See BUILD-GUIDE.md for wiring.

    python3 stockclock.py demo              self-check, no hardware needed
    python3 stockclock.py test              print raw + grams for all 4 slots
    python3 stockclock.py leds              cycle every light, to check wiring
    python3 stockclock.py tare 1            zero slot 1 with an empty plate
    python3 stockclock.py cal 1 1000        tell slot 1 what 1000 g looks like
    python3 stockclock.py run               the real thing, fullscreen
"""

import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import lgpio
except ImportError:
    lgpio = None

HERE = Path(__file__).parent
CAL_FILE = HERE / "calibration.json"
STATE_FILE = HERE / "state.json"

# name, HX711 data pin, HX711 clock pin, LED red pin, LED green pin (BCM numbers),
# life = how many days SHE says that ingredient keeps. One number per slot, set by
# her, not a database. Red on the day it hits `life`, amber the day before.
SLOTS = [
    {"name": "KANGKONG", "dt": 5,  "sck": 6,  "red": 17, "grn": 27, "life": 2},
    {"name": "TAUGE",    "dt": 12, "sck": 13, "red": 22, "grn": 23, "life": 1},
    {"name": "TOFU",     "dt": 19, "sck": 16, "red": 24, "grn": 25, "life": 3},
    {"name": "CABBAGE",  "dt": 20, "sck": 21, "red": 8,  "grn": 7,  "life": 7},
]
BUTTON_PIN = 26

# Calibration knobs. Tune these against the real stall, not against a bench.
MIN_CHANGE_G = 20      # smaller than this is a knock or a hand, not stock
SETTLE_SECONDS = 2.0   # the new weight must hold this long before it counts
SAMPLES = 15           # readings per measurement, median taken


# ─────────────────────────── hardware ───────────────────────────

def open_chip():
    """Pi 5 puts its GPIO on gpiochip4 on some kernels and gpiochip0 on newer
    ones. Try both rather than making the user find out the hard way."""
    for number in (4, 0):
        try:
            return lgpio.gpiochip_open(number)
        except Exception:
            continue
    raise SystemExit("No GPIO chip found. Run 'gpiodetect' and check you are on a Pi.")


def claim_pins(handle):
    for slot in SLOTS:
        lgpio.gpio_claim_input(handle, slot["dt"])
        lgpio.gpio_claim_output(handle, slot["sck"], 0)
        lgpio.gpio_claim_output(handle, slot["red"], 0)
        lgpio.gpio_claim_output(handle, slot["grn"], 0)
    lgpio.gpio_claim_input(handle, BUTTON_PIN, lgpio.SET_PULL_UP)


def read_raw(handle, slot):
    """One 24-bit reading off an HX711, bit-banged.

    ponytail: bit-banged in Python rather than via a driver. If the OS pauses us
    mid-read the chip can power down and return junk - which is why every caller
    goes through read_grams() and its median. Move to PIO if that ever bites.
    """
    dt, sck = slot["dt"], slot["sck"]

    deadline = time.time() + 1.0
    while lgpio.gpio_read(handle, dt) == 1:      # chip pulls DT low when ready
        if time.time() > deadline:
            raise TimeoutError(f"{slot['name']}: HX711 never became ready - check DT, SCK and 3.3 V")
        time.sleep(0.001)

    value = 0
    for _ in range(24):
        lgpio.gpio_write(handle, sck, 1)
        value = (value << 1) | lgpio.gpio_read(handle, dt)
        lgpio.gpio_write(handle, sck, 0)

    lgpio.gpio_write(handle, sck, 1)             # 25th pulse: channel A, gain 128
    lgpio.gpio_write(handle, sck, 0)

    if value & 0x800000:                         # 24-bit two's complement
        value -= 0x1000000
    return value


def read_grams(handle, index, calibration):
    slot = SLOTS[index]
    readings = []
    for _ in range(SAMPLES):
        try:
            readings.append(read_raw(handle, slot))
        except TimeoutError:
            pass
    if not readings:
        return None
    raw = statistics.median(readings)
    cal = calibration.get(slot["name"], {})
    scale = cal.get("scale")
    if not scale:
        return None
    return (raw - cal.get("tare", 0)) / scale


def set_led(handle, index, colour):
    slot = SLOTS[index]
    red = colour in ("red", "amber")
    green = colour in ("green", "amber")
    lgpio.gpio_write(handle, slot["red"], 1 if red else 0)
    lgpio.gpio_write(handle, slot["grn"], 1 if green else 0)


# ─────────────────────────── the logic ───────────────────────────

def colour_for(batches, now, life=2):
    """Light shows the age of the OLDEST batch, against THAT slot's shelf life.

    life is days-until-red for this ingredient. Tauge is 1, cabbage is 7. The
    stallholder sets it once per slot; the device never guesses freshness, it
    only counts days since the stock landed.
    """
    if not batches:
        return "off"
    oldest = datetime.fromisoformat(batches[0]["at"])
    days = (now.date() - oldest.date()).days
    if days >= life:
        return "red"
    if days >= life - 1:
        return "amber"
    return "green"


def apply_delta(slot_state, delta_g, now):
    """Weight went up: a new batch arrived. Went down: stock was used.

    ponytail: usage drains the oldest batch first. That assumes she takes from
    the front. If she digs past it for fresh stock the ages drift - the amber
    light is what nudges toward taking the old one, but it is an assumption and
    not a measurement.
    """
    batches = slot_state["batches"]

    if delta_g > 0:
        batches.append({"g": round(delta_g), "at": now.isoformat()})
        return

    remaining = -delta_g
    while remaining > 0 and batches:
        if batches[0]["g"] > remaining:
            batches[0]["g"] -= remaining
            remaining = 0
        else:
            remaining -= batches[0]["g"]
            batches.pop(0)

    day = now.date().isoformat()
    slot_state["used"][day] = slot_state["used"].get(day, 0) + round(-delta_g)


def typical_use(slot_state, weekday):
    """How much this slot normally gets through on this day of the week."""
    amounts = [
        grams for day, grams in slot_state["used"].items()
        if datetime.fromisoformat(day).weekday() == weekday
    ]
    return statistics.median(amounts) if amounts else 0


def buy_list(state, now):
    tomorrow_weekday = (now.weekday() + 1) % 7
    rows = []
    for slot in SLOTS:
        slot_state = state[slot["name"]]
        on_hand = sum(b["g"] for b in slot_state["batches"])
        expected = typical_use(slot_state, tomorrow_weekday)
        rows.append({
            "name": slot["name"],
            "have": on_hand,
            "uses": expected,
            "buy": max(0, expected - on_hand),
            "colour": colour_for(slot_state["batches"], now, slot["life"]),
        })
    return rows


# ─────────────────────────── files ───────────────────────────

def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def blank_state():
    return {slot["name"]: {"batches": [], "used": {}} for slot in SLOTS}


# ─────────────────────────── screen ───────────────────────────

def run_screen():
    import tkinter as tk

    calibration = load_json(CAL_FILE, {})
    state = load_json(STATE_FILE, blank_state())
    handle = open_chip()
    claim_pins(handle)

    last_stable = {}
    pending = {}

    root = tk.Tk()
    root.title("Stock Clock")
    root.attributes("-fullscreen", True)
    root.configure(bg="#101513")
    root.bind("<Escape>", lambda e: root.destroy())

    header = tk.Label(root, font=("Helvetica", 26, "bold"), fg="#E3EAE6", bg="#101513")
    header.pack(pady=(20, 10))
    body = tk.Label(root, font=("Courier", 30), fg="#E3EAE6", bg="#101513", justify="left")
    body.pack()

    showing_buy = {"on": False}

    def tick():
        now = datetime.now()

        for index, slot in enumerate(SLOTS):
            grams = read_grams(handle, index, calibration)
            if grams is None:
                continue
            slot_state = state[slot["name"]]
            settled = last_stable.get(slot["name"], grams)
            delta = grams - settled

            if abs(delta) >= MIN_CHANGE_G:
                if slot["name"] not in pending:
                    pending[slot["name"]] = (grams, time.time())
                else:
                    held_value, since = pending[slot["name"]]
                    if abs(grams - held_value) < MIN_CHANGE_G and time.time() - since >= SETTLE_SECONDS:
                        apply_delta(slot_state, grams - settled, now)
                        last_stable[slot["name"]] = grams
                        pending.pop(slot["name"])
                        save_json(STATE_FILE, state)
                    elif abs(grams - held_value) >= MIN_CHANGE_G:
                        pending[slot["name"]] = (grams, time.time())
            else:
                pending.pop(slot["name"], None)
                last_stable.setdefault(slot["name"], grams)

            set_led(handle, index, colour_for(slot_state["batches"], now, slot["life"]))

        if lgpio.gpio_read(handle, BUTTON_PIN) == 0:
            showing_buy["on"] = not showing_buy["on"]
            time.sleep(0.3)

        rows = buy_list(state, now)
        if showing_buy["on"]:
            header.config(text=f"BUY FOR TOMORROW  ·  {now:%a %d %b}")
            body.config(text="\n".join(
                f"{r['name']:<10} have {r['have']/1000:5.1f} kg   BUY {r['buy']/1000:5.1f} kg"
                for r in rows))
        else:
            header.config(text=f"STOCK CLOCK  ·  {now:%a %d %b  %H:%M}")
            body.config(text="\n".join(
                f"{r['name']:<10} {r['have']/1000:5.1f} kg   {r['colour'].upper()}"
                for r in rows))

        root.after(1000, tick)

    tick()
    root.mainloop()


# ─────────────────────────── self-check ───────────────────────────

def demo():
    """The lettuce walkthrough, asserted end to end. No hardware needed."""
    from datetime import timedelta

    mon = datetime(2026, 9, 14, 6, 0)
    tue = mon + timedelta(days=1)
    slot = {"batches": [], "used": {}}

    apply_delta(slot, 50, mon)                       # 50 g of lettuce arrives
    assert sum(b["g"] for b in slot["batches"]) == 50
    assert colour_for(slot["batches"], mon) == "green"

    apply_delta(slot, -25, mon)                      # cook 25 g
    assert sum(b["g"] for b in slot["batches"]) == 25
    assert slot["used"]["2026-09-14"] == 25
    assert colour_for(slot["batches"], mon) == "green"

    apply_delta(slot, 40, tue)                       # buy 40 g more on Tuesday
    assert len(slot["batches"]) == 2
    assert colour_for(slot["batches"], tue) == "amber", "Monday stock is now day 2"

    apply_delta(slot, -30, tue)                      # cook 30 g, oldest first
    assert len(slot["batches"]) == 1, "Monday batch should be fully drained"
    assert sum(b["g"] for b in slot["batches"]) == 35
    assert colour_for(slot["batches"], tue) == "green", "only Tuesday stock left"

    wed = tue + timedelta(days=1)
    assert colour_for(slot["batches"], wed) == "amber"
    assert colour_for(slot["batches"], wed + timedelta(days=1)) == "red"

    state = blank_state()
    state["KANGKONG"] = {
        "batches": [{"g": 800, "at": mon.isoformat()}],
        "used": {"2026-09-09": 2600},               # a Wednesday
    }
    row = next(r for r in buy_list(state, tue) if r["name"] == "KANGKONG")
    assert row["uses"] == 2600 and row["buy"] == 1800, row

    # same stock, same day, different ingredient: the shelf life is what differs
    week_old = [{"g": 100, "at": mon.isoformat()}]
    day_after = mon + timedelta(days=1)
    assert colour_for(week_old, day_after, life=1) == "red", "tauge is gone by day 2"
    assert colour_for(week_old, day_after, life=7) == "green", "cabbage is fine"
    assert colour_for(week_old, mon + timedelta(days=6), life=7) == "amber"

    print("demo: all checks passed")


# ─────────────────────────── commands ───────────────────────────

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "demo"

    if command == "demo":
        demo()
        return

    if lgpio is None:
        raise SystemExit("lgpio not installed. Run: sudo apt install python3-lgpio")

    if command == "run":
        run_screen()
        return

    handle = open_chip()
    claim_pins(handle)
    calibration = load_json(CAL_FILE, {})

    if command == "test":
        for index, slot in enumerate(SLOTS):
            raw = statistics.median([read_raw(handle, slot) for _ in range(SAMPLES)])
            grams = read_grams(handle, index, calibration)
            shown = f"{grams:8.0f} g" if grams is not None else "  not calibrated"
            print(f"slot {index + 1}  {slot['name']:<10} raw {raw:>12.0f}   {shown}")

    elif command == "leds":
        for index, slot in enumerate(SLOTS):
            for colour in ("green", "amber", "red", "off"):
                print(f"slot {index + 1} {slot['name']}: {colour}")
                set_led(handle, index, colour)
                time.sleep(0.8)

    elif command == "tare":
        index = int(sys.argv[2]) - 1
        name = SLOTS[index]["name"]
        raw = statistics.median([read_raw(handle, SLOTS[index]) for _ in range(SAMPLES * 4)])
        calibration.setdefault(name, {})["tare"] = raw
        save_json(CAL_FILE, calibration)
        print(f"{name}: empty plate reads {raw:.0f}. Now put a known weight on and run 'cal'.")

    elif command == "cal":
        index = int(sys.argv[2]) - 1
        known_grams = float(sys.argv[3])
        name = SLOTS[index]["name"]
        if "tare" not in calibration.get(name, {}):
            raise SystemExit(f"Run 'tare {index + 1}' with an empty plate first.")
        raw = statistics.median([read_raw(handle, SLOTS[index]) for _ in range(SAMPLES * 4)])
        scale = (raw - calibration[name]["tare"]) / known_grams
        calibration[name]["scale"] = scale
        save_json(CAL_FILE, calibration)
        print(f"{name}: calibrated. 1 g = {scale:.1f} raw counts.")
        if abs(scale) < 10:
            print("  Warning: that is a very small number. Check the load cell wiring.")

    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
