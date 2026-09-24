#!/usr/bin/env python3
"""USB numeric keypad OR ordinary keyboard -> `chope.py key N`.  Two numbers after
service: cooked, then left.  The board says which one it wants; this stays dumb.
Digits from the numpad or the top row, then Enter; any other key clears.
No desktop session needed.
grab() is the whole trick: without it every digit also lands in the console TTY
and in the kiosk browser.  Runs as root under systemd, so no `input` group needed.
The grabbed keyboard types into nothing else -- administer the Pi over SSH."""
import os, re, subprocess, sys

CHOPE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chope.py")
DIGIT = re.compile(r"KEY_(?:KP)?(\d)$")   # KEY_7, KEY_KP7 -- NOT KEY_F7, NOT KEY_NUMERIC_7


def digit(k):
    m = DIGIT.match(k)
    return m and m.group(1)


def pick(devs, e):
    """Enter AND digit keys, numpad preferred.  Enter alone is not enough: the Pi 5's
    HDMI ports (vc4-hdmi-0/1, CEC) advertise KEY_ENTER, and grabbing one of those
    means waiting forever on a TV remote while the real keyboard is ignored."""
    ok = []
    for d in devs:
        k = set(d.capabilities().get(e.EV_KEY, []))
        if {e.KEY_ENTER, e.KEY_KPENTER} & k and {e.KEY_1, e.KEY_KP1} & k:
            ok.append((e.KEY_KP1 not in k, d))          # False sorts first: numpads win
    return min(ok, key=lambda t: t[0])[1] if ok else None


def main():
    from evdev import InputDevice, ecodes, list_devices
    dev = pick(map(InputDevice, list_devices()), ecodes)
    if dev is None:                                      # systemd retries every 5 s
        sys.exit("no numpad or keyboard plugged in -- retrying")
    print("reading", dev.path, dev.name, flush=True)
    dev.grab()                                 # EVIOCGRAB: exclusive. Nothing else sees it.
    buf = ""
    for ev in dev.read_loop():
        if ev.type != ecodes.EV_KEY or ev.value != 1:    # 1=down, 2=autorepeat, 0=up
            continue
        k = ecodes.KEY[ev.code]
        k = k[0] if isinstance(k, list) else k           # some codes alias to a list
        if k.endswith("ENTER"):
            if buf:
                subprocess.run([sys.executable, CHOPE, "key", buf])
            buf = ""
        elif digit(k):
            buf = (buf + digit(k))[:4]
        else:
            buf = ""                                     # any other key clears


if __name__ == "__main__":
    main()
