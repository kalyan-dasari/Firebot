SLICE BOT STARTER — WINDOWS + ANDROID USB
Specialized for Slice UPI 'Play Fire' Game

IMPORTANT
---------
The default mode is OBSERVE ONLY. It captures screenshots and draws
heuristic candidate boxes. It does not swipe until --auto is passed.

Detector Legend:
- Green = FIREBALL candidate (meteors / asteroids)
- Red = DEVIL BALL / BOMB candidate (hazards — strictly avoided)
- Orange = UNKNOWN candidate

Yellow arrows show the computed flight velocity vector and angle.

1. INSTALL ADB
--------------
Download Android SDK Platform Tools:
https://developer.android.com/tools/releases/platform-tools

If you already have Android Studio installed, ADB is already located at:
C:\Users\<user>\AppData\Local\Android\Sdk\platform-tools\adb.exe
The bot detects this automatically!

2. PHONE USB SETUP
------------------
1. On your phone: Settings > About phone > tap Build number 7 times.
2. Settings > Developer options:
   - USB debugging: ON
   - USB debugging (Security settings): ON (allows simulated touch/swipes)
3. Connect phone via USB, unlock it, and accept the "Allow USB debugging" prompt.

3. INSTALL PYTHON DEPENDENCIES
------------------------------
Run:
    py -m pip install -r requirements.txt

4. TESTING WITHOUT PHONE (DEMO MODE)
------------------------------------
Test real-time computer vision, diagonal asteroid flight, and swipe cuts:
    py slice_bot.py --demo

Test automated swiping and devil-ball hazard avoidance in simulation:
    py slice_bot.py --demo --auto

5. LIVE GAMEPLAY IN SLICE UPI APP
---------------------------------
For a complete, step-by-step walkthrough on running the bot live on your
phone while playing the Slice UPI Play Fire game, see:
    SLICE_APP_GUIDE.md

1. Open Slice UPI App > Play Fire game.
2. Run Observe Mode first:
    py slice_bot.py
   (Or double-click run_bot.bat)
3. Check that boxes track falling fireballs and devil balls.
4. Enable Auto Slicing:
    py slice_bot.py --auto

Useful options for Slice Fire Game:
    py slice_bot.py --auto --min-confidence 0.58 --cooldown 0.40
    py slice_bot.py --swipe-length 140          # stroke cut length (pixels)
    py slice_bot.py --lead-time 0.07            # lead fast falling balls (touch latency comp)
    py slice_bot.py --devil-margin 80           # strict safety radius around devil balls (px)
    py slice_bot.py --zone-min 0.15 --zone-max 0.88 # safe slicing zone
    py slice_bot.py --demo                      # test simulation with diagonal asteroids
    py slice_bot.py --demo --auto               # test auto-slicing simulation
    py slice_bot.py --image test.png            # calibrate on static screenshot
    py slice_bot.py --preview-scale 0.5         # scale preview window size
    py slice_bot.py --device <serial>           # select target ADB device
    py slice_bot.py --adb-path C:\path\adb.exe  # custom adb path

TROUBLESHOOTING
---------------
- "unauthorized": unlock phone and accept the USB debugging prompt.
- "no devices": try another USB cable/port; some cables are charge-only.
- swipes not registering: enable "USB Debugging (Security settings)" in Developer Options.
- adb not found: install Platform Tools (or Android Studio) or use --adb-path.
- screenshot is rotated/different resolution: the bot uses the screenshot's
  coordinate space; test input carefully before automation.
- game blocks input or automation: stop and respect the game's rules.
