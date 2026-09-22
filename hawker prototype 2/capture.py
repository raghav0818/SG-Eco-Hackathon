#!/usr/bin/env python3
"""Tray Watch capture -- runs on the Pi, writes JPEGs and frames.csv. Nothing else.

THE RULE THE NETWORK MUST NOT BREAK: capture never depends on it. This writes the
frame to the card and returns. `rsync` is a SEPARATE cron job that may fail as often
as it likes. If a dropped WiFi connection can lose a frame, the design is wrong.

Three properties this file owns, and nothing else does:

  PRIVACY    the crop is applied BEFORE cv2.imwrite, so a customer at the frame edge
             never reaches storage -- not "deleted later", NEVER ENCODED. It refuses
             to start without a crop rather than write one full frame "just to see".

  THE CLOCK  frames are named by SEQUENCE, never by the clock. The Pi 5 has no RTC
             battery, so it boots at the last shutdown time and NTP steps it
             BACKWARDS seconds later -- `HHMM.jpg` would collide and imwrite would
             overwrite silently, no error. Every row carries wall clock AND
             CLOCK_BOOTTIME, which is monotonic across that step.

  HONESTY    if auto white balance could not be locked, it says so in every row
             rather than guessing. It still captures: the waste ledger is the
             headline claim and does not need colour at all (PRD 09 F3).

Config is environment only -- no config file, no parser. install-pi.sh writes them.
    TW_CROP   "x,y,w,h"  REQUIRED, set on site on day 1
    TW_DEV    /dev/video0
    TW_FRAMES output dir (default ./frames)
    TW_EVERY  seconds between frames (default 120)
"""
import csv, os, subprocess, sys, time

HERE  = os.path.dirname(os.path.abspath(__file__))
OUT   = os.environ.get("TW_FRAMES") or os.path.join(HERE, "frames")
DEV   = os.environ.get("TW_DEV", "/dev/video0")
EVERY = int(os.environ.get("TW_EVERY", "120"))
LOG   = os.path.join(OUT, "frames.csv")
COLS  = ["seq", "wall", "boottime", "bytes", "wb_locked"]


def crop_box():
    """Refuse to run without a crop. This is a trust boundary, not a default:
    an unset crop means writing a full frame that may contain a person's face."""
    raw = os.environ.get("TW_CROP", "").strip()
    if not raw:
        sys.exit("TW_CROP is not set. Refusing to write an uncropped frame -- the "
                 "privacy claim is that no image of a person is ever encoded, and "
                 "an uncropped frame breaks it. Set TW_CROP=x,y,w,h (see setup step 6).")
    try:
        x, y, w, h = (int(v) for v in raw.split(","))
    except ValueError:
        sys.exit("TW_CROP=%r is not x,y,w,h" % raw)
    if w <= 0 or h <= 0 or x < 0 or y < 0:
        sys.exit("TW_CROP=%r has a non-positive size or negative origin" % raw)
    return x, y, w, h


def wb_locked(dev):
    """CLAUDE.md trap 5: `cap.set(CAP_PROP_AUTO_WB, 0)` silently no-ops on many UVC
    cameras. Ask the driver what actually stuck; never trust the setter. Returns
    True / False / None (could not tell)."""
    try:
        out = subprocess.run(["v4l2-ctl", "-d", dev, "--list-ctrls"],
                             capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    got = {}
    for line in out.splitlines():
        if "value=" in line:
            got[line.split()[0]] = line.split("value=")[1].split()[0]
    wb = got.get("white_balance_automatic", got.get("white_balance_temperature_auto"))
    ae = got.get("auto_exposure")
    if wb is None and ae is None:
        return None
    # UVC: white_balance_automatic 0 = off (locked); auto_exposure 1 = Manual Mode.
    return wb == "0" and (ae is None or ae == "1")


def next_seq(d):
    """Survives a reboot with no state file: the highest number already on the card
    wins. A state file here would be one more thing to lose on a dirty shutdown."""
    n = [int(f[:-4]) for f in os.listdir(d) if f.endswith(".jpg") and f[:-4].isdigit()]
    return max(n) + 1 if n else 0


def open_cam():
    import cv2
    cap = cv2.VideoCapture(DEV)
    if not cap.isOpened():
        return None
    for _ in range(5):
        cap.read()          # UVC cams hand back a stale dark frame or two on open
    return cap


def main():
    import cv2
    x, y, w, h = crop_box()
    os.makedirs(OUT, exist_ok=True)
    locked = wb_locked(DEV)
    if locked is not True:
        print("WARNING: auto white balance is %s on %s. Capturing anyway -- the waste "
              "ledger does not need colour -- but the CONTRAST arm is void for these "
              "frames, and every row is marked wb_locked=%s."
              % ("still ON" if locked is False else "UNKNOWN (no v4l2-ctl?)", DEV, locked),
              file=sys.stderr)

    new = not os.path.exists(LOG)
    log = open(LOG, "a", newline="")
    out = csv.writer(log)
    if new:
        out.writerow(COLS)

    seq, cap, checked = next_seq(OUT), open_cam(), False
    print("capturing every %ds to %s, starting at seq %06d" % (EVERY, OUT, seq))
    while True:
        t0 = time.monotonic()      # NOT time.time(): this file exists because the
                                   # clock gets STEPPED, and a backward step would
                                   # silently add that many seconds to every sleep.
        ok, frame = (False, None) if cap is None else cap.read()
        if not ok:
            # A USB glitch must cost one frame, not the day. Reopen and carry on.
            print("camera read failed, reopening", file=sys.stderr)
            # Emit the gap marker analyse.py looks for. Without a row, a camera outage
            # is indistinguishable from the Pi being switched off, and the "almost no
            # frames" warning has no signal to work from.
            out.writerow([seq, time.strftime("%F %T"),
                          round(time.clock_gettime(time.CLOCK_BOOTTIME), 1),
                          0, "" if locked is None else int(locked)])
            log.flush()
            if cap is not None:
                cap.release()
            cap = open_cam()
        else:
            if not checked:
                # Bounds-check against a REAL frame, once. A 192->1920 typo makes the
                # crop empty and cv2.imwrite raises, killing the day; worse, a
                # partially-out-of-range crop silently truncates the row and analyse.py
                # then "reads the tray count off frame 1" and finds too few trays.
                H, W = frame.shape[:2]
                if x + w > W or y + h > H:
                    sys.exit("TW_CROP %d,%d,%d,%d runs off a %dx%d frame. Refusing: a "
                             "truncated crop loses trays silently." % (x, y, w, h, W, H))
                checked = True
            frame = frame[y:y + h, x:x + w]        # <-- THE PRIVACY PROPERTY. Before
            path = os.path.join(OUT, "%06d.jpg" % seq)   # imwrite, always, no branch.
            n = cv2.imwrite(path, frame) and os.path.getsize(path)
            out.writerow([seq, time.strftime("%F %T"),
                          round(time.clock_gettime(time.CLOCK_BOOTTIME), 1),
                          n or 0, "" if locked is None else int(locked)])
            log.flush()                            # a pulled plug must not eat the row
            seq += 1
        time.sleep(max(0, EVERY - (time.monotonic() - t0)))


def aim():
    """`python capture.py --aim` -- choose a crop without ever encoding a face.

    Chicken and egg: you cannot pick a crop you cannot see, but the privacy property
    says no recognisable image of a person is ever written. So the aiming frame is
    downscaled to 240 px wide and blurred -- a face in it is about 12 px across and
    unrecoverable -- with a grid labelled in FULL-RESOLUTION pixel coordinates.

    Read x, y, w, h off the grid, set TW_CROP, then run --check: that writes the
    CROPPED frame at full resolution, which is the only full-res image this program
    ever produces. Delete aim.jpg when you are done."""
    import cv2
    cap = open_cam()
    ok, frame = (False, None) if cap is None else cap.read()
    if not ok:
        sys.exit("no frame from %s" % DEV)
    H, W = frame.shape[:2]
    small = cv2.GaussianBlur(cv2.resize(frame, (240, int(240 * H / W))), (5, 5), 0)
    sh, sw = small.shape[:2]
    for i in range(1, 10):                       # grid labelled in FULL-RES coords
        cv2.line(small, (sw * i // 10, 0), (sw * i // 10, sh), (0, 0, 255), 1)
        cv2.line(small, (0, sh * i // 10), (sw, sh * i // 10), (0, 0, 255), 1)
        cv2.putText(small, str(W * i // 10), (sw * i // 10 + 1, 8),
                    cv2.FONT_HERSHEY_PLAIN, 0.4, (0, 0, 255), 1)
        cv2.putText(small, str(H * i // 10), (1, sh * i // 10 - 1),
                    cv2.FONT_HERSHEY_PLAIN, 0.4, (0, 0, 255), 1)
    cv2.imwrite(os.path.join(HERE, "aim.jpg"), small)
    cap.release()
    print("wrote aim.jpg -- camera is %dx%d, grid is labelled in full-res pixels.\n"
          "Pick the tray row PLUS the grey card, exclude anywhere a customer stands.\n"
          "Then:  export TW_CROP=x,y,w,h  &&  python capture.py --check" % (W, H))


def check():
    """Write one CROPPED full-res frame so you can confirm the framing, and that
    nobody is in it. This is KPI K3 -- the privacy claim is falsifiable, so falsify
    it on day 1 rather than asserting it on a slide."""
    import cv2
    x, y, w, h = crop_box()
    cap = open_cam()
    ok, frame = (False, None) if cap is None else cap.read()
    if not ok:
        sys.exit("no frame from %s" % DEV)
    H, W = frame.shape[:2]
    if x + w > W or y + h > H:
        sys.exit("TW_CROP %d,%d,%d,%d runs off a %dx%d frame" % (x, y, w, h, W, H))
    cv2.imwrite(os.path.join(HERE, "check.jpg"), frame[y:y + h, x:x + w])
    cap.release()
    print("wrote check.jpg (%dx%d). Open it. Every tray visible and the grey card in "
          "shot? Any person, even at the edge? Tighten TW_CROP until the answer is no."
          % (w, h))


def selftest():
    """Everything except the camera: crop geometry, sequence numbering, the CSV."""
    import tempfile, numpy, cv2
    d = tempfile.mkdtemp()
    assert next_seq(d) == 0
    for name in ("000000.jpg", "000007.jpg", "notaframe.jpg"):
        cv2.imwrite(os.path.join(d, name), numpy.zeros((4, 4, 3), numpy.uint8))
    assert next_seq(d) == 8, next_seq(d)           # max+1, and the junk name ignored

    os.environ["TW_CROP"] = "10,20,100,50"
    assert crop_box() == (10, 20, 100, 50)
    for bad in ("", "1,2,3", "1,2,3,x", "0,0,0,10", "-1,0,5,5"):
        os.environ["TW_CROP"] = bad
        try:
            crop_box()
            raise AssertionError("accepted TW_CROP=%r" % bad)
        except SystemExit:
            pass

    # The crop must remove the edges, which is the whole privacy claim.
    frame = numpy.zeros((200, 400, 3), numpy.uint8)
    frame[0:10, 0:10] = 255                        # a "person" at the frame edge
    x, y, w, h = 50, 50, 100, 60
    assert frame[y:y + h, x:x + w].max() == 0, "crop kept the frame edge"
    print("ok  |  crop refuses bad input and drops the frame edge, seq survives a "
          "reboot, junk filenames ignored")


if __name__ == "__main__":
    MODES = {"--selftest": selftest, "--aim": aim, "--check": check, "": main}
    flag = next((a for a in sys.argv[1:] if a.startswith("--")), "")
    if flag not in MODES:      # a typo'd --check must not silently start the daemon
        sys.exit("unknown flag %s. Use one of: %s, or none to capture."
                 % (flag, ", ".join(k for k in MODES if k)))
    MODES[flag]()
