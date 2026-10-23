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

ADB is auto-detected from standard Android SDK locations automatically.
You can also specify --adb-path if installed in a custom location.

4. FIRST RUN: SCREEN CAPTURE + VISUAL DETECTION
-----------------------------------------------
Run:
    py slice_bot.py
(Or double-click run_bot.bat)

TESTING WITHOUT A PHONE (DEMO MODE):
------------------------------------
You can test the bot and its OpenCV detection loop without a phone:
    py slice_bot.py --demo
Or test with auto slicing enabled in simulation:
    py slice_bot.py --demo --auto

A window will show the screen with candidate boxes:
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

Useful options for falling fireballs:
    py slice_bot.py --auto --min-confidence 0.60 --cooldown 0.5
    py slice_bot.py --swipe-length 140          # width of horizontal cut (pixels)
    py slice_bot.py --zone-min 0.15 --zone-max 0.85 # slice zone (ignores top/bottom UI)
    py slice_bot.py --demo                      # test simulation without phone
    py slice_bot.py --demo --auto               # test auto-slicing simulation
    py slice_bot.py --image test.png            # calibrate on static screenshot
    py slice_bot.py --preview-scale 0.5         # scale preview window size
    py slice_bot.py --device <serial>           # select target ADB device
    py slice_bot.py --adb-path C:\path\adb.exe  # custom adb path

A higher confidence threshold reduces some false positives but may miss
targets. The bounding-box safety check is deliberately conservative but is
not a guarantee: the detector may fail to identify a bomb in the first place.

TROUBLESHOOTING
---------------
- "unauthorized": unlock phone and accept the USB debugging prompt.
- "no devices": try another USB cable/port; some cables are charge-only.
- adb not found: install Platform Tools (or Android Studio) or use --adb-path.
- screenshot is rotated/different resolution: the bot uses the screenshot's
  coordinate space; test input carefully before automation.
- game blocks input or automation: stop and respect the game's rules.
