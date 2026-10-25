================================================================================
FIREBALL DETECTION & AUTO-SWIPE BOT — WINDOWS + ANDROID USB
================================================================================

PROJECT OVERVIEW
----------------
This project aims to build a computer-vision-based game assistant that detects
fireballs, avoids bomb-like hazards, and performs safe swipe gestures in
compatible Android games.

The initial development environment is Windows 10/11, using Python, OpenCV, and
Android Debug Bridge (ADB). A future version may use a native Android
application with a floating on-screen control panel.

For the formatted Markdown version, please see: README.md

OBJECTIVES
----------
- Capture and process game screenshots over ADB or simulated environments.
- Detect and classify fireballs, bombs, and uncertain objects.
- Track moving objects across consecutive frames (vertical & diagonal asteroids).
- Identify safe swipe paths while maintaining a strict safety margin around hazards.
- Provide Start, Stop, and emergency-stop controls (Q key or window close).
- Display detection results, trajectory vectors, and debugging information.
- Support games that permit automated interaction.

PLANNED TECHNOLOGY STACK
------------------------
- Python: Core automation and decision-making logic.
- OpenCV: Image processing, color filtering, contour analysis, and GUI preview.
- NumPy: Efficient array manipulations, vector calculations, and image decoding.
- ADB: Android screen capture and touch input injection during compatible testing.
- Kotlin (future): Optional native Android application.
- Android Accessibility Service (future): Gesture automation where permitted.

DEVELOPMENT PHASES
------------------
Phase 1 — Screen Capture:
Establish a connection to a compatible Android test device and capture screenshots.
Auto-detects ADB in Android SDK platform-tools.

Phase 2 — Object Detection:
Identify candidate fireballs and bomb-like objects. Display bounding boxes and
confidence scores.

Phase 3 — Object Tracking:
Track objects between frames and estimate their movement speed and angle.

Phase 4 — Safe Swipe Planning:
Select target fireballs, check proposed swipe paths against detected hazards,
and skip uncertain targets or candidates near hazards.

Phase 5 — Automation Interface:
Add Start/Stop controls, a detection preview, configurable thresholds, static
screenshot inspection (--image), and an offline interactive simulator (--demo).

Phase 6 — Testing and Optimization:
Measure detection accuracy, false positives, missed hazards, response time, and
resource usage.

COMPATIBILITY AND SECURITY LIMITATIONS
--------------------------------------
Some applications, including financial applications (such as Slice UPI), may
restrict access when USB debugging, wireless debugging, screen capture, or
accessibility automation is enabled.

The bot must not assume that ADB or accessibility gestures will work in every
application. If an application blocks automation, development and testing should
continue in a compatible test environment rather than attempting to conceal
debugging, bypass security checks, or interfere with application protections.

Attempting to bypass security checks on financial accounts risks triggering
automated risk flags, account freezes, or forfeiture of rewards.

This project does not guarantee compatibility with Slice or authorization to
automate reward-bearing games. Any use with third-party games must comply with
their terms and applicable rules.

SAFETY REQUIREMENTS
-------------------
- Detection-only mode is the default.
- Unknown or ambiguous objects must be treated as potential hazards.
- Automated swipes must remain disabled until detection has been tested.
- Include an accessible emergency-stop mechanism (Q key or window close).
- Do not root a daily-use banking device solely to enable automation.
- Never store banking credentials, payment information, or other sensitive
  account data in the project.

CURRENT STATUS
--------------
The initial Windows/Python implementation supports:
- Automatic ADB discovery from Android SDK Platform-Tools.
- Offline simulation mode (--demo) with diagonal asteroids and auto-slicing.
- Static screenshot calibration (--image <path>).
- Perpendicular swipe cuts tailored to falling angles.
- Strict devil ball / bomb safety radius check.
- Latency compensation (--lead-time) to lead moving targets.

QUICK START COMMANDS
--------------------
1. Install Dependencies:
   py -m pip install -r requirements.txt

2. Test Offline Simulator (No phone needed):
   py slice_bot.py --demo
   py slice_bot.py --demo --auto

3. Compatible Android Device Testing:
   py slice_bot.py                                 # Observe mode
   py slice_bot.py --auto                          # Auto slicing mode
   py slice_bot.py --auto --swipe-length 140 --cooldown 0.40 --lead-time 0.07 --devil-margin 80

SUCCESS CRITERIA
----------------
- Reliable screen capture in a compatible test environment.
- Correct classification of representative fireballs and hazards.
- Conservative behavior when objects overlap or detection is uncertain.
- Safe, responsive controls and an effective emergency stop.
- Documented limitations and repeatable test results.
