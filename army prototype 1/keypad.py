#!/usr/bin/env python3
"""USB numeric keypad -> `chope.py key N`.  Two numbers after service:
cooked, then left.  The board says which one it wants; this stays dumb.
No desktop session needed.
grab() is the whole trick: without it every digit also lands in the console TTY
and in the kiosk browser.  Runs as root under systemd, so no `input` group needed."""
import os, subprocess, sys
from evdev import InputDevice, ecodes, list_devices

CHOPE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chope.py")

dev = next(d for d in map(InputDevice, list_devices())
           if ecodes.KEY_KPENTER in d.capabilities().get(ecodes.EV_KEY, []))
dev.grab()                                   # EVIOCGRAB: exclusive. Nothing else sees it.
buf = ""
for ev in dev.read_loop():
    if ev.type != ecodes.EV_KEY or ev.value != 1:      # 1=down, 2=autorepeat, 0=up
        continue
    k = ecodes.KEY[ev.code]
    k = k[0] if isinstance(k, list) else k             # some codes alias to a list
    if k.endswith("ENTER"):
        if buf:
            subprocess.run([sys.executable, CHOPE, "key", buf])
        buf = ""
    elif k[-1].isdigit():
        buf = (buf + k[-1])[:4]
    else:
        buf = ""                                       # any other key clears
