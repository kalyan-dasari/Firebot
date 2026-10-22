SLICE BOT STARTER — WINDOWS + ANDROID USB

IMPORTANT
---------
The default mode is OBSERVE ONLY. It captures screenshots and draws
heuristic candidate boxes. It does not swipe.

The included detector is an initial color-based heuristic, not a trained
model. It may miss objects or confuse effects, UI elements, fireballs and
bombs. Do not use --auto until you have inspected it over multiple rounds.
The auto mode is experimental and may still make mistakes.

1. INSTALL ADB
--------------
Download Android SDK Platform Tools:
https://developer.android.com/tools/releases/platform-tools

Extract the ZIP to a simple folder, for example:
C:\platform-tools

Open Windows Settings on the phone:
- Settings > About phone
- Tap Build number seven times (if Developer options are not already enabled)
- Developer options > USB debugging: ON

Connect the phone by USB, unlock it, and accept the "Allow USB debugging?"
prompt. Set the USB mode to File Transfer if needed.

Open Command Prompt in the platform-tools folder and run:
    adb devices

The device should appear with status "device", not "unauthorized".
If the command is not found, add C:\platform-tools to PATH or run commands
from that folder.

2. INSTALL PYTHON
-----------------
Install Python 3.11 or 3.12 from:
https://www.python.org/downloads/

During installation, select "Add Python to PATH".

3. INSTALL BOT DEPENDENCIES
---------------------------
Extract this project folder. Open Command Prompt in the project folder and run:
    py -m pip install -r requirements.txt

If ADB is not on PATH, either add platform-tools to PATH or edit slice_bot.py
so its ADB commands use the full path to adb.exe.

4. FIRST RUN: SCREEN CAPTURE + VISUAL DETECTION
-----------------------------------------------
Run:
    py slice_bot.py

A window should show the live phone screen with boxes:
- Green = FIREBALL candidate
- Red = BOMB candidate
- Orange = UNKNOWN candidate

Press Q while the preview window is focused to quit.
If the window is blank or capture fails, run:
    adb devices
    adb exec-out screencap -p > test.png
and check test.png.

5. CALIBRATE BEFORE ANY AUTOMATION
----------------------------------
Play several rounds and observe whether the boxes track the real objects.
False detections and missed bombs are expected in this first heuristic version.
Detection quality depends on resolution, effects, UI and game animation.

Do not treat confidence values as calibrated probabilities. For dependable
play, collect example crops from your actual game and train/test a detector
or use a more robust template/object detector. Track detections over multiple
frames and add a conservative no-swipe zone around uncertain objects.

6. EXPERIMENTAL AUTO MODE
-------------------------
Only after testing observe-only mode, run:
    py slice_bot.py --auto

This enables heuristic swipes. It is not guaranteed safe. Keep the phone
visible and stop with Q or Ctrl+C if it behaves incorrectly.

Useful options:
    py slice_bot.py --auto --min-confidence 0.78 --cooldown 0.8

A higher confidence threshold reduces some false positives but may miss
targets. The bounding-box safety check is deliberately conservative but is
not a guarantee: the detector may fail to identify a bomb in the first place.

TROUBLESHOOTING
---------------
- "unauthorized": unlock phone and accept the USB debugging prompt.
- "no devices": try another USB cable/port; some cables are charge-only.
- adb not found: add Platform Tools to PATH or use the full path to adb.exe.
- screenshot is rotated/different resolution: the bot uses the screenshot's
  coordinate space; test input carefully before automation.
- game blocks input or automation: stop and respect the game's rules.
