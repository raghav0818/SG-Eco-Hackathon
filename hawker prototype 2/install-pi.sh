#!/bin/sh
# Tray Watch installer. On the Pi, as the normal user:   sh install-pi.sh
# Idempotent -- re-run it after changing TW_CROP or the times below.
#
# Installs: the capture service, the rsync cron, the USB mirror, the shutdown timer.
# It does NOT choose the crop -- that needs the camera pointed at her stall. Run
# `python3 capture.py --aim` first; this script refuses without a crop, for the same
# reason capture.py does.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
USER_=$(id -un)

LAPTOP="${LAPTOP:-}"          # e.g. raghav@192.168.1.20 -- blank disables the rsync cron
EVERY=120                     # seconds between frames
CLOSE="20 19"                 # mirror to USB and power down (cron: MIN HOUR)
                              # She closes 19:00 [T7, 22 Sep]. Mirror 19:20, shutdown 19:35.

[ -n "$TW_CROP" ] || {
  echo "TW_CROP is not set."
  echo "  1.  python3 capture.py --aim      # writes a blurred 240px aim.jpg + grid"
  echo "  2.  export TW_CROP=x,y,w,h"
  echo "  3.  python3 capture.py --check    # confirm framing, and that nobody is in it"
  echo "  4.  TW_CROP=\$TW_CROP sh install-pi.sh"
  exit 1
}

echo "== 1. packages (v4l2-ctl via apt; OpenCV via pip -- see note below)"
dpkg -s v4l-utils >/dev/null 2>&1 || sudo apt-get install -y v4l-utils \
  || { sudo apt-get update && sudo apt-get install -y v4l-utils; }
# apt's python3-opencv drags in libopencv-viz -> VTK -> OpenMPI -> libevent-pthreads,
# which wants an exact libevent-core build the trixie repo has since moved past --
# apt refuses the downgrade and the whole install fails. We never call cv2.viz.
# opencv-python-headless ships a prebuilt aarch64 wheel on PyPI: a download, not
# the multi-hour source build pip used to mean on a 32-bit Pi.
python3 -c "import cv2" 2>/dev/null || {
  dpkg -s python3-pip >/dev/null 2>&1 || sudo apt-get install -y python3-pip
  pip3 install --break-system-packages opencv-python-headless
}

echo "== 2. lock white balance and exposure, then VERIFY the lock took"
# capture.py re-applies this on EVERY boot (UVC controls reset on re-enumeration).
# This run is for immediate feedback -- you see below whether the lock takes at all.
# CLAUDE.md trap 5: cap.set(CAP_PROP_AUTO_WB, 0) silently no-ops on many UVC cameras,
# and a silent no-op loses the colour arm with no error. Set via v4l2-ctl, then read
# back. Control names differ between kernels, so try both spellings and ignore misses.
for c in white_balance_automatic=0 white_balance_temperature_auto=0 auto_exposure=1; do
  v4l2-ctl -d "${TW_DEV:-/dev/video0}" --set-ctrl "$c" 2>/dev/null || true
done
v4l2-ctl -d "${TW_DEV:-/dev/video0}" --list-ctrls | grep -E "white_balance|exposure" || true
echo "   ^ white_balance_automatic should read 0 and auto_exposure 1. If they do not,"
echo "     capture still runs and marks every row wb_locked=0 -- the waste ledger is"
echo "     unaffected, the colour arm is void. That is a warning, not a blocker."

echo "== 3. make the clock gate actually gate"
# After=time-sync.target is PASSIVE: without this unit enabled nothing ever delays the
# target, so capture would start before NTP steps the clock and the first frames of the
# day would carry the previous shutdown's DATE -- landing in a phantom dish-day.
sudo systemctl enable systemd-time-wait-sync.service 2>/dev/null   || echo "   (systemd-time-wait-sync unavailable; check 'timedatectl' by hand each morning)"

echo "== 3b. capture service (gated on the clock being correct)"
sudo tee /etc/systemd/system/traywatch.service >/dev/null <<EOF
[Unit]
Description=Tray Watch capture
# The Pi 5 has no RTC battery: it boots at the last shutdown time and NTP steps the
# clock BACKWARDS seconds later. Frames are named by sequence so a step cannot make
# them collide, but every row logs wall clock too -- wait for the step before frame 1.
After=time-sync.target
Wants=time-sync.target
[Service]
User=$USER_
WorkingDirectory=$HERE
Environment=TW_CROP=$TW_CROP
Environment=TW_EVERY=$EVERY
Environment=TW_DEV=${TW_DEV:-/dev/video0}
Environment=TW_FRAMES=$HERE/frames
ExecStart=/usr/bin/python3 $HERE/capture.py
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now traywatch.service

echo "== 4. timezone (cron times are local, and Imager defaults to Europe/London)"
TZ_=$(timedatectl show -p Timezone --value 2>/dev/null)
[ "$TZ_" = "Asia/Singapore" ] || { sudo timedatectl set-timezone Asia/Singapore; sudo systemctl restart cron 2>/dev/null || true; }

echo "== 5. cron: rsync out every 10 min, USB mirror and shutdown at close"
CRON_=$(mktemp)
crontab -l 2>/dev/null | grep -v '# traywatch' > "$CRON_" || true
[ -n "$LAPTOP" ] && cat >> "$CRON_" <<EOF
*/10 * * * * rsync -az --partial --append-verify "$HERE/frames/" "$LAPTOP:~/traywatch/frames/"  # traywatch
EOF
# +15 min, carried properly: a naive $1+15 emits minute 65 for CLOSE="50 14" and
# crontab then rejects the WHOLE file, taking the rsync line down with it.
SHUT=$(echo "$CLOSE" | awk '{m=($2*60+$1+15)%1440; printf "%d %d", m%60, int(m/60)}')
cat >> "$CRON_" <<EOF
$CLOSE * * * [ -d /media/usb ] && rsync -a "$HERE/frames/" /media/usb/frames/ && sync  # traywatch
$SHUT * * * /sbin/shutdown -h now  # traywatch
EOF
crontab "$CRON_"
rm -f "$CRON_"
[ -n "$LAPTOP" ] || echo "   LAPTOP is unset, so no rsync cron. The USB mirror is your only"
[ -n "$LAPTOP" ] || echo "   second copy -- set LAPTOP=user@host and re-run to fix that."

echo
echo "installed. crop=$TW_CROP, every ${EVERY}s, frames in $HERE/frames"
echo "check it is alive:"
echo "  systemctl status traywatch --no-pager"
echo "  tail -2 $HERE/frames/frames.csv     # seq climbing, bytes > 0"
echo
echo "EVERY MORNING, from your phone, before you walk away:"
echo "  ssh $USER_@\$(hostname).local tail -1 $HERE/frames/frames.csv"
echo "That says booted, capturing, and this is the last frame it wrote. A blank or a"
echo "stale seq means go and look -- a gap on day 5 is the one thing you cannot redo."
