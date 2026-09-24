# Tray Watch Console — local control and observation plan

Status: grilled, revised, and implemented in this checkout, 24 September 2026. Local fixture and browser checks pass; Pi service, camera, SSH permissions, and field accuracy still require validation on the device. The decisions below close the design tree for this operator console.

## What the prototype actually does

Tray Watch has two places of work. The Pi captures a privacy-cropped JPEG and a CSV row every two minutes. It must keep capturing when Wi-Fi or the laptop is absent. The laptop receives copies, runs `analyse.py` to turn images into tray-fill readings and daily rows, then runs `report.py` to make the owner's one-page report. The AI fill readings have not been validated on real stall trays. The synthetic demo is labelled as such. The rearrangement study is exploratory; the operational product is the visual leftover and refill record. A fill percentage is a camera estimate of appearance, not food mass or proven waste saved. Source comments describing closing fill as “exact” refer to a synthetic signal simulation, not real-world vision accuracy. The console and report must say “camera-estimated fill.”

Three existing code issues affect the interface promise: `analyse.py` currently ignores the `block,from_ts` roster columns and aggregates one slot across a full day; `report.py` overwrites `page.html` and inserts unescaped operator/model text into HTML; and `capture.py --check` writes a full-resolution candidate crop before a human has confirmed that no person is in it. The new workflows must resolve these before claiming correct dish identity, safe report approval, or non-persistent crop preview.

## User and jobs

The console is for Raghav, the prototype operator, on his laptop. The stall owner still receives a simple report and does not operate the console. The console replaces repeated SSH, systemctl, CSV, and Python commands with clear operations and visible progress.

1. Connect to the Pi and see whether it is reachable, clock-synced, capturing, and retaining valid frames.
2. Set and verify a privacy crop before starting capture. A blurred low-resolution aiming image is allowed before a crop; a full-resolution candidate preview is cropped in memory before JPEG encoding and never persisted. The operator confirms all trays and the grey card are visible and no person is visible before applying it.
3. Start, stop, or restart capture; see the exact outcome and any permission or camera error. Never make capture depend on the console staying open.
4. Browse actual captured frames and the day's capture timeline. Distinguish no data, camera gaps, stale capture, white-balance warning, and good capture.
5. Receive frame copies on the laptop without losing a frame on Pi/network failure. Show mirror status and last successful transfer.
6. Maintain the dish-to-slot roster, including time blocks when trays move. Never invent dish identity from images. The current `analyse.py` only understands one mapping per day, so block-level attribution needs a separate, explicit change before the UI claims it works.
7. Run analysis and report generation with a visible job log, progress, approximate cost estimate, cooperative cancel action, and resume. Require a deliberate Run action before paid API calls; a page refresh must never start or duplicate them. Store no API key in browser storage or repo.
8. Inspect `daily.csv` and an A4 draft alongside its source photos, review the wording, then approve a versioned printable page. Keep synthetic data visually separate from field data.

## Interface design

Design source: `design-research.md` §§2.3–2.5. The console should look like an instrument at a hawker stall, not a marketing landing page: data and the newest tray photograph dominate. Use a quiet warm paper surface, dark green-black text, stainless dividers, and one amber accent for actionable warnings. Use a compact serif page title and a legible sans body. No gradients, stock charts, decorative icons, fake metrics, heavy animation, or nested cards. Real empty states say what is missing. Controls have keyboard focus, disabled/loading/error/success states; motion is minimal and respects reduced-motion.

Layout: four operator sections: **Overview**, **Camera**, **Frames & dishes**, and **Analysis & report**. Connection settings and diagnostics are a small panel. Dashboard: capture state and last valid frame timestamp at top, current cropped frame as the largest area, capture timeline and actionable alerts beside it. Desktop uses a narrow navigation rail; mobile stacks navigation above content and keeps the photo first. Every page shows its data source and freshness. Status does not use an unlabeled green dot alone. “Live” means the latest stored two-minute frame, never streaming video. “Connected” means a recent SSH status check; “recording” requires an active service *and* a valid frame newer than the cadence plus tolerance. A stale image is labelled stale even if the service reports active.

```text
Tray Watch   Overview  Camera  Frames & dishes  Analysis & report
─────────────────────────────────────────────────────────────────
Recording · last valid frame 14:32 · Pi clock synced · mirror 14:30
┌────────────────────────────────────┐ ┌───────────────────────┐
│ latest privacy-cropped tray photo  │ │ Today: 97 valid       │
│ photographed 14:32, Pi source      │ │ 1 camera failure      │
│                                    │ │ last transfer 14:34   │
└────────────────────────────────────┘ └───────────────────────┘
Timeline: 08:00 ━━━━━━ × ━━━━━━━━━ ● 14:32        [Sync now]
```

## Architecture

Run a small Python stdlib HTTP server bound to `127.0.0.1` on the laptop. Browser calls same-origin JSON endpoints; no internet-hosted UI assets or account. The server owns configuration, SSH calls, local mirror operations, analysis/report subprocesses, and job state. Plain HTML/CSS/JS keeps setup small and works without Node or a cloud frontend. The Pi keeps only its existing capture service plus a small fixed-command bridge in this repository. SSH is the control link; the Pi does not need a new HTTP port. The laptop's SSH key and a one-time restricted service-control privilege are prerequisites for remote start/stop/restart. If absent, the UI reports the exact missing step. Bind to loopback; reject non-loopback Host values, validate Origin on mutations, require an unpredictable startup action token in a header, and send `Cache-Control: no-store` for status/images.

The bridge exposes fixed verbs: `status`, `aim`, `check-crop x,y,w,h`, `apply-crop x,y,w,h`, `service start|stop|restart`, and `export` for bounded frame sequence batches. Status returns structured JSON for service state, crop, latest valid frame, last CSV rows, Pi clock sync/timezone, disk, and complete-frame inventory. Never accept an arbitrary shell command, path, or URL from the browser. The bridge reads frame JPEGs only from its configured capture directory. SSH uses native Windows `ssh.exe` with `BatchMode=yes` and normal host-key verification; all subprocesses use argument arrays, bounded timeouts, bounded output, and separate stdout/stderr. No captured image or API key goes into a URL or log. Differentiate disconnected Pi, SSH authentication failure, service permission failure, camera error, and unsynced clock. An offline Pi leaves local mirrored browsing/report review available with explicit last-contact time.

The Pi service remains autonomous. One-time Pi setup must migrate `install-pi.sh` to a validated user-writable crop environment file referenced by `EnvironmentFile=`; write it with a temporary file and atomic rename. Its current `ExecStart=/usr/bin/python3 $HERE/capture.py` and `Environment=TW_FRAMES=$HERE/frames` require correct systemd quoting because `HERE` contains `hawker prototype 2`. Verify the installed unit on a Pi with `systemd-analyze verify`. The normal-user crontab's `/sbin/shutdown -h now` may lack privilege: migrate scheduled shutdown to a root-owned systemd timer or an explicitly permitted mechanism, and verify it at deployment. Document one-time, exact passwordless sudoers entries for `systemctl start|stop|restart traywatch.service` only. The bridge calls `sudo -n` so a permission error is immediate and visible. The web UI never installs packages, edits cron, shuts down the OS, or prompts for a sudo password.

Applying a crop is atomic and restarts capture only after a successful cropped preview and explicit operator confirmation. The bridge must take a fresh frame, crop it in memory before JPEG encoding, serve it only to the loopback browser with no-store headers, and discard it on rejection. Do not call existing `capture.py --check`: it writes `check.jpg` before human privacy review. If the camera cannot be opened while the capture service is active, pause capture explicitly, show the resulting gap, and restore the prior run state after apply or cancel. Validate bounds against the actual frame before applying. On restart failure, restore the previous crop and report both outcomes. The human review is the privacy gate; do not claim an unreviewed candidate image is person-free. Preserve the pre-write crop invariant in ongoing `capture.py`; capture remains independent of the console and mirror.

The development laptop has native OpenSSH `ssh.exe` and `scp.exe`, but no `rsync` or Paramiko. Use a fixed Pi bridge `export` verb to stream one tar archive per bounded batch of missing numbered JPEGs plus a snapshot of `frames.csv`. The bridge includes only rows with `bytes>0` whose corresponding JPEG exists and matches the recorded size, so it cannot copy a partly written `cv2.imwrite` file. Include a manifest with sequence, size, and hash. The laptop compares full remote inventory with local files and retries holes; never assume that copying the largest sequence means earlier sequences arrived. Extract only `frames.csv`, manifest, and `NNNNNN.jpg` members; reject links, path traversal, duplicate names, oversize payloads, and hash/size mismatch. Stream into temporary files, validate CSV schema, and atomically rename. A dropped connection keeps the prior mirror intact. Show transferred/pending/failed counts. The existing Pi cron mirror can continue independently, but the console labels *its own* mirror rather than implying all backup routes are healthy. Sync is explicit or scheduled only while the console runs; its absence cannot harm capture.

Analyse and report paths are fixed to this project checkout. Run one operation at a time to avoid crop/service/sync races. Keep `readings.csv` resumable and emit machine-readable analysis progress after bounded batches with total, cached, succeeded, failed, and in-flight counts. A cooperative cancel stops scheduling new model calls, waits for in-flight work, and saves successful readings atomically. A rerun uses the cache. Display an approximate cost for remaining calls with the model and assumption named; never imply a guaranteed charge. Refresh only reads job state. Persist job metadata so a server restart marks an orphaned run interrupted instead of quietly restarting it. Capture/analysis/report logs are bounded and scrubbed before display. `--no-llm` report is a visible fallback and also needs review.

## Data contracts and guardrails

- Config: local, untracked JSON with Pi host/user/path, local mirror path, polling interval; never passwords or API keys. Browser input cannot select an arbitrary remote command, local path, or URL.
- Status: connected, service active, *fresh valid frame*, latest sequence/time, age, bytes, gap count, `wb_locked`, Pi clock sync/timezone, storage, mirror latest/lag, last-contact time. Unknown values remain unknown. A zero-byte CSV row is a camera failure; a missing interval can also mean the service was stopped, the Pi was off, or sync is incomplete, so label the evidence rather than inventing a cause.
- Jobs: idle/running/succeeded/failed/cancelled/interrupted, start/end timestamps, bounded log tail, progress count, operation ID. Refreshing the browser only reads state. Only deliberate POST actions start paid work.
- Roster: `day,block,from_ts,slot,dish,is_veg`. Require a complete map of known slots at each block start, unique slots and dish names in a block, increasing starts, valid Singapore local times, and nonempty names. A day with no swap uses one block. Each frame uses the active map at its timestamp. Unmapped periods stay unknown and cannot appear as a named finding.
- Analysis: aggregate by **dish/day**, preserving the actual slot and first/last image references for each segment. Do not compare fills across a slot swap as if it were a refill. Calculate sales/refills within contiguous dish segments, then combine with documented semantics; closing fill is from the last observed segment. A dish removed before close is not automatically “left at close.” Neighbour contrast must be calculated per block or marked unavailable. Missing/ambiguous mapping makes the report ineligible.
- Preview: aim image is blurred/downscaled; candidate crop image is cropped in memory and ephemeral. No raw uncropped preview is served or persisted. Human confirmation that no person is visible precedes activation.
- Reports: HTML-escape every operator/model string. Write versioned drafts in an untracked output directory; no approved page is overwritten. Show source images, times, estimated numbers, and exact proposed wording for operator review. Approval creates an immutable printable version with timestamp and dataset fingerprint. Rejection retains a draft but does not produce an approved page. Label source as field/synthetic based on directory provenance, not a manually editable title. Never present model fill as exact volume, kilograms, or measured waste reduction.

## Delivery order and checks

1. Fix the Pi service path, frame directory, crop environment file, and shutdown privilege; create the fixed-command bridge. Test parsers, crop bounds, privacy preview, service permission failure, and malformed CSV without a camera. Verify final systemd unit and shutdown path on a real Pi before field use.
2. Build the localhost server and real status/crop/controls. Test with a fake bridge and Pi-like fixture. Test loopback-only binding, Host/Origin/action-token checks, offline Pi, stale image with active service, unsynced clock, and a zero-byte camera-failure row.
3. Add tar-stream sync and gallery. Verify partial transfer, hash mismatch, malicious tar member, missing earlier sequence, reboot sequence continuation, and no duplicate/partial local image writes.
4. Add roster editor **and** block-aware attribution before report enablement. Test a dish moved at 14:35, no false refill at the boundary, unknown mapping, and a dish removed before close. Keep the exploratory contrast metric per block or unavailable.
5. Add bounded analysis jobs, cooperative cancel/resume, report draft/review/approval, HTML escaping, and versioned output. Test no model call on page refresh, cached rerun, `--no-llm`, missing photos, malformed model text, synthetic stamping, and no approved-page overwrite. Exercise `demo_week.py` as a clearly synthetic run; never infer field accuracy from it.
6. Check keyboard navigation, narrow layout, reduced motion, loading/error/empty states, disconnected Pi operation, and A4 print output. Keep a short operator setup guide with one command to start the console and exact one-time Pi install steps.

## Grilled design tree: settled decisions

| Question | Answer | Consequence |
| --- | --- | --- |
| Q1: Where should control live? | Laptop localhost with SSH to the Pi. | Analysis and report remain local; no Pi HTTP port; Pi capture survives disconnection. |
| Q2: Which actions are safe and useful? | Status, aim/crop, service start/stop/restart, sync, analysis, report review. | No install, OS shutdown, cron edits, arbitrary sudo, or command execution in UI. |
| Q3: Transfer on Windows? | Native OpenSSH plus fixed bridge tar stream, not rsync-dependent SFTP/scp loops. | CSV-confirmed complete frames, manifest hashes, atomic mirror, hole retries. |
| Q4: Dish identity during swaps? | Finish block-aware analysis before enabling named report claims. | Map each frame by timestamp; split at swaps; unknown mapping cannot silently become a dish. |
| Q5: Recommendation safety? | Evidence-backed, escaped, versioned draft with operator approval. | Camera uncertainty visible; no automatic publish or overwrite. |
| Q6: Who can control the service? | Narrow one-time sudoers entries for three `systemctl` actions. | `sudo -n` failures are visible; console needs no general root privilege. |
| Q7: What protects privacy while aiming? | Blurred aim, in-memory cropped candidate, human check before activation. | Candidate is never persisted; pause active service if camera sharing fails. |
| Q8: What does “live” mean? | Latest stored frame with its timestamp and source. | Active service alone is not shown as healthy capture; offline mirror is labelled stale. |
| Q9: How do jobs behave under refresh or failure? | Explicit start, serialized operation, persisted state, cooperative cancel. | Refresh cannot duplicate paid calls; cached readings survive interruptions. |
| Q10: What happens after deployment? | One-time Pi install migration and real hardware check. | Fixtures cannot validate camera lock, sudoers, systemd parsing, host resolution, or field accuracy. |

No unanswered interface decision should be hidden inside implementation. If a real Pi cannot be reached from this checkout, deliver the fixture-tested console and state the deployment checks explicitly; do not claim hardware controls were exercised.
