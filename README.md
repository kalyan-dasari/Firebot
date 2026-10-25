# Fireball Detection & Auto-Swipe Bot

## Project Overview

This project aims to build a computer-vision-based game assistant that detects fireballs, avoids bomb-like hazards, and performs safe swipe gestures in compatible Android games.

The initial development environment is Windows 10/11, using Python, OpenCV, and Android Debug Bridge (ADB). A future version may use a native Android application with a floating on-screen control panel.

---

## Objectives

- **Screen Capture & Ingestion:** Capture and process real-time game screenshots over ADB or simulated environments.
- **Object Classification:** Detect and classify fireballs (meteors/asteroids), bombs (devil hazards), and uncertain objects using color ratios and contours.
- **Multi-Direction Trajectory Tracking:** Track moving objects across consecutive frames to estimate velocity vectors, falling angles, and lead times.
- **Safe Swipe Path Planning:** Identify target fireballs, compute perpendicular slice cuts, check proposed paths against detected hazards, and strictly avoid hazards with safety buffers.
- **Operational Controls:** Provide Start, Stop, and emergency-stop controls (`Q` key or window close).
- **Visual Feedback:** Display real-time detection bounding boxes, confidence scores, trajectory arrows, and slice zone boundaries.
- **Permissible Game Support:** Support games and test environments that permit automated interaction.

---

## Planned Technology Stack

- **Python:** Core automation and decision-making logic.
- **OpenCV:** High-performance image processing, color space transformations, contour analysis, and GUI preview.
- **NumPy:** Efficient array manipulations, vector calculations, and image buffer decoding.
- **ADB (Android Debug Bridge):** High-speed screen capture (`screencap`) and touch input injection (`input swipe`) during compatible testing.
- **Kotlin (future):** Optional native Android application.
- **Android Accessibility Service (future):** On-device gesture automation where permitted.

---

## Development Phases

### Phase 1 — Screen Capture
Establish a connection to a compatible Android test device and capture screenshots directly into memory with zero disk overhead. Auto-detects ADB in Android SDK platform-tools.

### Phase 2 — Object Detection
Identify candidate fireballs (bright core + warm flame trail) and bomb-like objects (dark face + red features + warm outline). Display bounding boxes and confidence scores.

### Phase 3 — Object Tracking
Track moving objects between frames (`SimpleTracker`), measure velocity ($v_x, v_y$), calculate trajectory angles (vertical & diagonal asteroids), and predict future positions to compensate for touch latency.

### Phase 4 — Safe Swipe Planning
Select target fireballs prioritized by vertical urgency, compute perpendicular slicing strokes across the motion vector, check proposed swipe paths against all detected hazards, and skip any candidate near a hazard.

### Phase 5 — Automation Interface & Offline Simulator
Add Start/Stop controls, a resizable detection preview window (`WINDOW_NORMAL`), configurable thresholds, static screenshot inspection (`--image`), and an offline interactive game simulator (`--demo`).

### Phase 6 — Testing and Optimization
Measure detection accuracy, false positives, missed hazards, response time, and resource usage.

---

## Compatibility and Security Limitations

> [!WARNING]
> **Anti-Debugging & Financial App Protections**
> Some applications, including financial applications (such as Slice UPI), strictly restrict access when **USB debugging**, **wireless debugging**, screen capture, or accessibility automation is enabled on the device.

- **ADB & Permission Blocks:** The bot must not assume that ADB or accessibility gestures will work in every application. Regulated banking/UPI apps query system flags (`Settings.Global.ADB_ENABLED` and `Settings.Global.ADB_WIFI_ENABLED`) and will intentionally block access to mini-games (e.g. *"Disable USB debugging and restart app"*).
- **Zero-Bypass Policy:** If an application blocks automation, development and testing should continue in a **compatible test environment** rather than attempting to conceal debugging, bypass security checks, or interfere with application protections. Attempting to bypass security checks on financial accounts risks triggering automated risk flags, account freezes, or forfeiture of rewards.
- **Third-Party Compliance:** This project does not guarantee compatibility with Slice or authorization to automate reward-bearing games. Any use with third-party games must comply with their terms of service and applicable rules.

---

## Safety Requirements

- **Observe-Only by Default:** Detection-only mode is active by default. No swipes are dispatched until `--auto` is explicitly supplied.
- **Conservative Hazard Treatment:** Unknown, ambiguous, or low-confidence objects must be treated as potential hazards (`BOMB`/`UNKNOWN`).
- **Pre-Flight Validation:** Automated swipes must remain disabled until detection quality has been verified in observe mode.
- **Emergency Stop:** Immediate shutdown upon pressing `Q`, `ESC`, or closing the OpenCV window.
- **No Daily-Driver Rooting:** Do not root a daily-use banking device solely to enable automation.
- **Credential Protection:** Never store banking credentials, payment information, or other sensitive account data in the project.

---

## Current Status

The Windows/Python implementation supports:
- **Automatic ADB Discovery:** Automatically detects ADB from local Android SDK Platform-Tools.
- **Offline Simulation Mode (`--demo`):** Interactive game simulator with diagonal asteroids, varied falling speeds, and auto-slicing.
- **Offline Screenshot Calibration (`--image <file>`):** Analyze static game screenshots to verify confidence scores.
- **Perpendicular Swipe Cuts:** Generates slice strokes angled perpendicular to the falling trajectory.
- **Strict Devil Ball Safety Guard:** Point-to-segment Euclidean distance check against current and projected hazard locations.
- **Latency Compensation (`--lead-time`):** Leads moving targets forward along their velocity vector.

---

## Quick Start & Usage

### 1. Installation
Ensure Python 3.11+ is installed. Open Command Prompt in the repository folder:
```powershell
py -m pip install -r requirements.txt
```

### 2. Test in Offline Demo Mode (No Phone Needed)
Test computer vision, diagonal asteroid tracking, and preview UI:
```powershell
py slice_bot.py --demo
```
Test auto-slicing with devil ball hazard avoidance in simulation:
```powershell
py slice_bot.py --demo --auto
```

### 3. Compatible Android Device Testing
1. Enable **Developer Options** & **USB Debugging** on a compatible test device.
2. Connect via USB and accept the *Allow USB debugging* prompt.
3. Run in **Observe-Only Mode**:
   ```powershell
   py slice_bot.py
   ```
   *(Or double-click `run_bot.bat`)*
4. Run in **Auto Mode** (only in games permitting automation):
   ```powershell
   py slice_bot.py --auto --swipe-length 140 --cooldown 0.40 --lead-time 0.07 --devil-margin 80
   ```

### 4. CLI Arguments Reference

| Flag | Default | Description |
|---|---|---|
| `--demo` | `False` | Run offline simulation mode without an Android device. |
| `--auto` | `False` | Enable automated swipes (observe-only by default). |
| `--image <path>` | `None` | Inspect detections on a static screenshot file. |
| `--min-confidence` | `0.58` | Minimum heuristic score required to trigger a swipe. |
| `--cooldown` | `0.42` | Minimum seconds between consecutive swipes. |
| `--swipe-length` | `130` | Length of the slice cut stroke in pixels. |
| `--swipe-duration` | `65` | Touch swipe duration in milliseconds. |
| `--lead-time` | `0.065` | Latency lead time in seconds to hit fast-falling targets. |
| `--devil-margin` | `75.0` | Strict safety radius around devil balls/bombs in pixels. |
| `--zone-min` | `0.15` | Fraction from top of screen to ignore (avoids top headers). |
| `--zone-max` | `0.88` | Fraction from top of screen to ignore (avoids bottom docks). |
| `--device` | `None` | Target specific ADB device serial if multiple devices are attached. |
| `--preview-scale` | `Auto` | Display scale factor for preview window on high-res monitors. |

---

## Success Criteria

- Reliable screen capture in a compatible test environment.
- Correct classification of representative fireballs and hazards.
- Conservative behavior when objects overlap or detection is uncertain.
- Safe, responsive controls and an effective emergency stop.
- Documented limitations and repeatable test results.
