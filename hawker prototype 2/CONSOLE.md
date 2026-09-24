# Tray Watch Console

The console runs on your laptop at `http://127.0.0.1:8765`. It uses SSH to control the Pi and copies captured frames to this checkout for analysis. Closing the browser or laptop does **not** stop Pi capture.

## One-time setup

1. On the Pi, update this repository and install the revised capture service from `hawker prototype 2`:

   ```sh
   export TW_CROP=x,y,w,h
   sh install-pi.sh
   python3 pi_bridge.py status
   ```

   Use the already reviewed crop for this first install. The installer writes the crop to `~/.config/traywatch/capture.env`, fixes the service path containing spaces, grants the login user only three passwordless `systemctl` actions for `traywatch.service`, and installs a root-owned shutdown timer. Check `systemctl status traywatch`, `systemctl status traywatch-shutdown.timer`, and `sudo -n systemctl restart traywatch.service` on the Pi. The console's camera page can preview and change the crop afterwards.

2. Set up key-based SSH from the laptop to the Pi and verify it without a password prompt: `ssh -o BatchMode=yes USER@traywatch.local 'echo connected'`. Confirm the Pi host key when you first connect directly in a terminal. The console deliberately does not bypass host-key checks or store an SSH password.

3. On the laptop, install the Python dependencies needed by the existing pipeline: `python -m pip install opencv-python-headless numpy google-genai`. Native Windows OpenSSH `ssh.exe` must be on `PATH`; `rsync` and Node are not required.

4. In PowerShell, set the API key for the current terminal if you will run image analysis or an AI-written recommendation:

   ```powershell
   $env:GEMINI_API_KEY = 'your-key'
   python '.\hawker prototype 2\console.py'
   ```

   Open the printed localhost URL. The key stays in the Python process environment; the browser never receives it. The **Create simple draft** button works without a recommendation API call, but tray-fill analysis still needs the model.

5. Open **Pi connection settings** and enter the Pi login user, host, and remote checkout directory. The default directory is `~/SG-Eco-Hackathon/hawker prototype 2`. The laptop and Pi must be reachable over SSH on the same network or through an existing SSH route.

## Daily flow

On **Overview**, check that the service is active **and** the last valid frame is fresh. An active service with a stale frame is a problem, not healthy capture. Check Pi clock sync and camera failure rows. **Copy frames to laptop** uses only complete JPEGs confirmed by the Pi CSV and retries missing sequence numbers.

On **Frames & dishes**, review the copied photos and enter each slot's dish name. If trays swap, add a new time block with the actual swap time and a full slot map. An incomplete or unknown map prevents a named report.

On **Analysis & report**, explicitly start paid analysis, inspect the daily rows, create a draft, review the photos and text, and approve a printable copy. Drafts and approved copies are separate files under `reports/`. A report's fill percentage is a **camera estimate of visual fullness**, not a weight or a measured saving. `--no-llm` produces a simple draft if the recommendation call is unavailable.

## Limits and field check

The console is bound only to the laptop loopback address and opens no new Pi web port. It is intended for the prototype operator, not the stall owner. The Pi, camera, systemd unit, sudoers, clock, and crop must be checked on the actual hardware; fixture tests in this checkout cannot verify them. The vision model's real-stall fill error and food waste reduction remain unmeasured. A synthetic demo is available with `python 'hawker prototype 2/demo_week.py'` and is marked synthetic.
