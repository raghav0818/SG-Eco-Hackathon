#!/bin/sh
# Chope installer. On the Pi, as the normal desktop user:   sh install.sh
# Idempotent -- re-run it after editing anything. Nothing here touches GPIO.
#
# Everything Chope runs is root: the token file is 600 root:root (so cron must be
# root's), and root reads /dev/input without the `input` group dance. Chromium is the
# one thing that runs as you, and it only ever READS board.js.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
USER_=$(id -un)

OPEN_AT="0 7"      # poll goes out 0700
LOCK_AT="30 10"    # cook cutoff -- TUNE THIS to the real kitchen's cutoff
DAYS="1-5"

echo "== 1. evdev (the keypad grab). Nothing else is installed."
dpkg -s python3-evdev >/dev/null 2>&1 || sudo apt-get install -y python3-evdev || { sudo apt-get update && sudo apt-get install -y python3-evdev; }

echo "== 2. /etc/chope.env"
if [ ! -f /etc/chope.env ]; then
  printf '  bot token from @BotFather: ' ; read -r T
  printf '  group chat id (negative)  : ' ; read -r C
  printf '  unit strength (0 = ask TG): ' ; read -r S
  sudo install -m 600 -o root -g root /dev/null /etc/chope.env
  printf 'CHOPE_TOKEN=%s\nCHOPE_CHAT=%s\nCHOPE_STRENGTH=%s\n' "$T" "$C" "$S" \
    | sudo tee /etc/chope.env >/dev/null
fi
sudo chmod 600 /etc/chope.env
sudo chown root:root /etc/chope.env

# CHOPE_CUTOFF drives the open-screen countdown ring -- keep it derived from LOCK_AT,
# not typed separately, so editing LOCK_AT and re-running is the only place to change it.
CUTOFF_HHMM=$(set -- $LOCK_AT; printf '%02d:%02d' "$2" "$1")
sudo sed -i '/^CHOPE_CUTOFF=/d' /etc/chope.env
printf 'CHOPE_CUTOFF=%s\n' "$CUTOFF_HHMM" | sudo tee -a /etc/chope.env >/dev/null

echo "== 3. cron (root's, because only root can read the token)"
# The clock is right (NTP) but the TIMEZONE may not be. Pi OS Imager defaults to
# Europe/London unless you changed it -- cron would then fire "0 7" at 3pm SGT and
# the poll would go out after lunch, with no error anywhere.
TZ_=$(timedatectl show -p Timezone --value 2>/dev/null)
if [ "$TZ_" != "Asia/Singapore" ]; then
  echo "   timezone is $TZ_, not Asia/Singapore -- fixing (cron times are local)"
  sudo timedatectl set-timezone Asia/Singapore
fi
sudo systemctl restart cron 2>/dev/null || true   # cron caches the old zone

# Two things this line MUST do, both of which look optional and are not:
#   set -a   -- sourcing an env file sets SHELL variables, not exported ones, so
#               python3 would see no CHOPE_TOKEN and KeyError every morning.
#   "$HERE"  -- the directory is "army prototype 1". Unquoted, cd gets 3 args,
#               fails, && short-circuits, and nothing runs. Silently, at 0700.
ENV_='set -a; . /etc/chope.env; set +a'
CRON_=$(mktemp)                                   # not a predictable /tmp name
sudo crontab -l 2>/dev/null | grep -v '# chope' > "$CRON_" || true
cat >> "$CRON_" <<EOF
$OPEN_AT * * $DAYS $ENV_; cd "$HERE" && python3 chope.py open   # chope
$LOCK_AT * * $DAYS $ENV_; cd "$HERE" && python3 chope.py lock   # chope
EOF
sudo crontab "$CRON_"
rm -f "$CRON_"

echo "== 4. keypad service"
sudo tee /etc/systemd/system/chope-keypad.service >/dev/null <<EOF
[Unit]
Description=Chope keypad (cooked, then portions left)
[Service]
EnvironmentFile=/etc/chope.env
WorkingDirectory=$HERE
ExecStart=/usr/bin/python3 "$HERE/keypad.py"
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now chope-keypad.service

echo "== 4b. listener service (/commands, /demo) -- outbound long-poll, no open port"
sudo tee /etc/systemd/system/chope-listen.service >/dev/null <<EOF
[Unit]
Description=Chope listener (/leaderboard, /demo ...)
Wants=network-online.target
After=network-online.target
[Service]
EnvironmentFile=/etc/chope.env
WorkingDirectory=$HERE
ExecStart=/usr/bin/python3 "$HERE/chope.py" listen
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now chope-listen.service

echo "== 5. kiosk board on HDMI"
URL=$(printf 'file://%s/board.html' "$HERE" | sed 's/ /%20/g')   # "army prototype 1"
BIN=chromium-browser
command -v $BIN >/dev/null 2>&1 || BIN=chromium
# --password-store=basic: without it Chromium asks the GNOME keyring at startup, and an
# "Unlock Keyring" password dialog sits ON TOP of the COOK number after every boot --
# with the keyboard grabbed by chope-keypad, so nobody at the wall can dismiss it.
KIOSK="$BIN --kiosk --noerrdialogs --disable-infobars --incognito --password-store=basic $URL"
# A Pi 5 cannot boot Bullseye, so it is Bookworm, so it is wayfire or labwc. No X11 case.
# Delete-then-add, not grep-then-skip: re-running must UPDATE an old kiosk line's flags.
if [ -f "$HOME/.config/wayfire.ini" ]; then
  grep -q '^\[autostart\]' "$HOME/.config/wayfire.ini" || echo '[autostart]' >> "$HOME/.config/wayfire.ini"
  sed -i '/board.html/d' "$HOME/.config/wayfire.ini"
  # insert UNDER the header -- appending at EOF puts it in the last section instead
  sed -i "/^\[autostart\]/a chope = $KIOSK" "$HOME/.config/wayfire.ini"
else                                                          # labwc, the Pi 5 default
  mkdir -p "$HOME/.config/labwc"
  touch "$HOME/.config/labwc/autostart"
  sed -i '/board.html/d' "$HOME/.config/labwc/autostart"
  echo "$KIOSK &" >> "$HOME/.config/labwc/autostart"
  chmod +x "$HOME/.config/labwc/autostart"
fi

# Blank screen off -- a kitchen board that sleeps is not a board. Wayland, so xset
# is not an option; raspi-config is the one that works on both compositors.
sudo raspi-config nonint do_blanking 1 2>/dev/null || true

echo
echo "installed for user $USER_, code in $HERE"
echo "next, in order:"
echo "  1.  sudo sh -c 'set -a; . /etc/chope.env; set +a; python3 chope.py check'  # proves the token -- /etc/chope.env is root-only"
echo "  2.  sudo reboot                                     # board should come up on HDMI"
echo "  3.  keypad: how many were ACTUALLY cooked + Enter  # only valid after a 'lock'"
echo "  4.  keypad: how many portions are left + Enter"
echo ""
echo "  Two numbers, not one, and the first one is the pan -- not the board. The"
echo "  kitchen cooks above whatever number it is given [T5], so scoring the meal"
echo "  against the board makes r collapse from 0.72 to 0.42 with no visible error."
echo "  The screen tells the operator which number it wants."
echo "  5.  in the group: /demo  (vote, key cooked+left on the numpad)  or  /demo auto"
echo "      /demo reset between visitors.  Logs: journalctl -u chope-listen -f"
echo "  6.  python3 replay.py                               # 60 meals, no Telegram needed"
echo
echo "cook cutoff is currently $LOCK_AT -- edit LOCK_AT at the top and re-run."
