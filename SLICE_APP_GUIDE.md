# Slice UPI 'Play Fire' Game — Live Android Bot Guide

This guide explains how to connect your Android phone, how the bot captures your screen in real time, and how to auto-swipe fireballs while completely avoiding devil balls in the **Slice UPI app's Fire Game**.

---

## 1. How It Works Under the Hood

```
┌─────────────────────────┐          USB Cable          ┌───────────────────────────┐
│      Android Phone      │ ◄─────────────────────────► │        Windows PC         │
│  (Slice UPI Fire Game)  │                             │                           │
│                         │   `adb exec-out screencap`  │  1. Capture live frame    │
│  • Falling fireballs    │ ──────────────────────────► │  2. Color ratio detector  │
│  • Diagonal asteroids   │                             │  3. Velocity & angle track│
│  • Devil balls (bombs)  │    `adb shell input swipe`  │  4. Devil safety check    │
│                         │ ◄────────────────────────── │  5. Perpendicular swipe   │
└─────────────────────────┘                             └───────────────────────────┘
```

1. **Live Screen Capture**: The bot requests raw screenshot frames directly from Android's surface flinger via ADB (`exec-out screencap -p`). This streams the uncompressed frame into OpenCV memory without storing files on disk.
2. **Real-Time Computer Vision**: OpenCV analyzes the frame using HSV color filtering:
   - **Fireballs (Green box)**: Bright core + warm trailing flame.
   - **Devil Balls / Bombs (Red box)**: Dark face + red eyes + warm outer ring.
3. **Multi-Direction Trajectory Tracking**: The bot tracks each fireball across frames, calculating its exact speed and trajectory angle (straight down or diagonal asteroid angle).
4. **Touch Latency Compensation**: Because USB touch commands take ~50–70ms, the bot leads the fireball forward along its flight path, ensuring clean hits on moderate and fast-falling balls.
5. **Devil Ball Safety Buffer**: Before every swipe, the bot calculates the Euclidean distance between the swipe line segment and all detected devil balls (both current and projected positions). If a swipe comes within the safety radius (**default 75px**), the swipe is **blocked** to protect your game score.

---

## 2. Phone Preparation (One-Time Setup)

### Step 1: Enable Developer Options & USB Debugging
1. On your phone, go to **Settings** → **About Phone**.
2. Locate **Build Number** and tap it **7 times** until you see *"You are now a developer!"*.
3. Go back to **Settings** → **System** (or Additional Settings) → **Developer Options**.
4. Turn **ON** the following toggles:
   - **USB Debugging**: ON
   - **USB Debugging (Security settings)** *(Crucial on Xiaomi/MIUI/Realme/Oppo/Vivo)*: ON (allows simulated touch/swipes).
   - **Stay Awake** (Optional but recommended): Screen won't sleep while charging.

### Step 2: Connect Phone via USB
1. Connect your phone to your PC using a reliable data-capable USB cable (use a USB 3.0 port if possible for faster frame rates).
2. Set the USB mode on the phone to **File Transfer (MTP)** or **MIDI** if prompted.
3. Your phone will show a prompt: **"Allow USB debugging?"**.
   - Check the box: **"Always allow from this computer"**.
   - Tap **Allow**.

---

## 3. Verify Connection in Terminal

Open Command Prompt or PowerShell in the project folder and run:
```powershell
py slice_bot.py
```
- If connected properly, the bot will display:
  ```
  Checking ADB environment...
  ADB located at: C:\Users\kalya\AppData\Local\Android\Sdk\platform-tools\adb.exe
  List of devices attached
  XXXXXXXX    device
  Targeting device: XXXXXXXX
  ```
- If it says `unauthorized`, unlock your phone screen and tap **Allow** on the prompt.

---

## 4. Live Gameplay Walkthrough

### Phase 1: Launch the Game on Phone
1. Open the **Slice UPI App** on your phone.
2. Navigate to the **Play Fire** game screen.
3. Keep the game screen open and visible.

### Phase 2: Run in OBSERVE Mode (Safety Check)
Before turning on automated swipes, make sure the detector sees the fireballs and devil balls accurately:
```powershell
py slice_bot.py
```
*(Or double-click `run_bot.bat`)*

A preview window will open on your PC showing your phone's live screen:
- **Green Box (`FIRE`)**: Fireballs / meteors.
- **Red Box (`DEVIL`)**: Devil balls / hazards.
- **Yellow Arrow**: Detected flight angle and velocity vector.
- **Gray Lines (`ZONE TOP` & `ZONE BOTTOM`)**: Active slicing zone.

> **What to check during Observe Mode:**
> - Are fireballs consistently tagged green?
> - Are devil balls tagged red?
> - Press **Q** in the preview window to stop.

---

### Phase 3: Calibrate with a Screenshot (If needed)
If the game lighting or colors on your phone look different from default thresholds:
1. Capture a live screenshot during the game:
   ```powershell
   & "C:\Users\kalya\AppData\Local\Android\Sdk\platform-tools\adb.exe" exec-out screencap -p > slice_shot.png
   ```
2. Inspect the detection boxes and confidence scores offline:
   ```powershell
   py slice_bot.py --image slice_shot.png
   ```
3. If fireballs have a confidence of e.g. `0.52`, lower `--min-confidence` to `0.50`.

---

### Phase 4: Run AUTO Mode (Live Automated Swiping)

Once you're satisfied with detection, start a round in the Slice UPI app and run:
```powershell
py slice_bot.py --auto
```

#### Recommended Settings for Slice UPI Fire Game:
```powershell
py slice_bot.py --auto --swipe-length 140 --cooldown 0.38 --lead-time 0.07 --devil-margin 80
```

### Parameter Breakdown:
| Parameter | Default | Recommended for Slice | Description |
|---|---|---|---|
| `--swipe-length` | `130` | `140` | Length of the cut stroke (px). Cuts cleanly across diagonal asteroids. |
| `--cooldown` | `0.42` | `0.35`–`0.40` | Minimum delay between swipes in seconds. Lower values swipe faster. |
| `--lead-time` | `0.065` | `0.070` | Touch latency compensation. Leads faster falling balls. |
| `--devil-margin` | `75.0` | `80.0` | Safety radius (px) around devil balls. Zero tolerance for touching hazards. |
| `--zone-min` | `0.15` | `0.15` | Ignores top 15% of screen (avoids top headers, scores, coins). |
| `--zone-max` | `0.88` | `0.88` | Ignores bottom 12% of screen (avoids bottom gesture docks). |
| `--preview-scale`| `Auto` | `0.5` | Scales preview window so tall phone screens fit desktop displays. |

---

## 5. Troubleshooting Checklist

| Issue | Cause | Solution |
|---|---|---|
| **"No authorized Android device found"** | Phone locked or debugging prompt not accepted | Unlock phone, re-plug USB, tap "Always allow" on phone prompt. |
| **Swipes are not registering in app** | Android permission blocks automated touch | In Developer Options, enable **"USB Debugging (Security Settings)"** or **"Disable permission monitoring"**. |
| **Fast fireballs missed** | USB latency or ball moved past swipe point | Increase `--lead-time 0.08` and increase `--swipe-length 150`. |
| **Swiping too close to devil balls** | Devil safety buffer needs widening | Increase `--devil-margin 90` or `--devil-margin 100`. |
| **FPS is low (< 5 FPS)** | Phone running in battery saver or slow USB port | Plug into a blue USB 3.0 port, keep phone plugged into power, turn off battery saver. |
| **Preview window too large** | Phone screen is 2400px+ tall | Pass `--preview-scale 0.45` or drag the window corner to resize. |

---

## 6. Testing Anytime Without Phone (Demo Mode)

You can test the entire diagonal asteroid slicing engine anytime offline:
```powershell
# Observe diagonal asteroids and tracks:
py slice_bot.py --demo

# Test auto-slicing diagonal asteroids with devil ball avoidance:
py slice_bot.py --demo --auto
```
