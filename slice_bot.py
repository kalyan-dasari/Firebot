"""
Slice game bot starter for Windows + Android USB/ADB.

Default mode is OBSERVE ONLY. It captures the phone screen and draws
heuristic candidate boxes. Automated swipes are disabled unless --auto
is explicitly supplied.

Detection is a starter heuristic, not a trained classifier. Calibrate it
against real gameplay before enabling actions.
"""
import argparse
import math
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class Detection:
    box: tuple  # x, y, w, h
    kind: str   # FIREBALL, BOMB, UNKNOWN
    confidence: float


# Cached ADB path once resolved
RESOLVED_ADB_PATH: Optional[str] = None


def find_adb(custom_path: Optional[str] = None) -> Optional[str]:
    """Locate the adb executable on the system."""
    global RESOLVED_ADB_PATH
    if custom_path:
        if os.path.isfile(custom_path):
            RESOLVED_ADB_PATH = os.path.abspath(custom_path)
            return RESOLVED_ADB_PATH
        raise FileNotFoundError(f"Custom ADB path does not exist: {custom_path}")

    if RESOLVED_ADB_PATH and os.path.isfile(RESOLVED_ADB_PATH):
        return RESOLVED_ADB_PATH

    # Check environment variable
    env_adb = os.environ.get("ADB_PATH")
    if env_adb and os.path.isfile(env_adb):
        RESOLVED_ADB_PATH = os.path.abspath(env_adb)
        return RESOLVED_ADB_PATH

    # Check system PATH
    which_adb = shutil.which("adb")
    if which_adb:
        RESOLVED_ADB_PATH = os.path.abspath(which_adb)
        return RESOLVED_ADB_PATH

    # Common Windows installation locations
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        os.path.expandvars(r"%ANDROID_HOME%\platform-tools\adb.exe"),
        os.path.expandvars(r"%ANDROID_SDK_ROOT%\platform-tools\adb.exe"),
        r"C:\platform-tools\adb.exe",
        r"C:\Android\platform-tools\adb.exe",
        r"C:\Program Files\Android\platform-tools\adb.exe",
        r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
    ]
    for cand in candidates:
        if cand and os.path.isfile(cand):
            RESOLVED_ADB_PATH = os.path.abspath(cand)
            return RESOLVED_ADB_PATH

    return None


def run_adb(args: List[str], timeout: float = 5, device: Optional[str] = None, adb_path: Optional[str] = None):
    """Run an ADB command safely with process window suppression on Windows."""
    exe = adb_path or find_adb()
    if not exe:
        raise FileNotFoundError(
            "ADB executable not found. Please ensure Android SDK Platform Tools is installed "
            "or specify --adb-path."
        )

    cmd = [exe]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(args)

    creationflags = 0
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        creationflags=creationflags,
    )


def list_connected_devices(adb_path: Optional[str] = None) -> Tuple[List[str], str]:
    """Return list of authorized device IDs and raw adb output."""
    p = run_adb(["devices"], timeout=6, adb_path=adb_path)
    raw_output = p.stdout.decode(errors="replace")
    devices = []
    for line in raw_output.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices, raw_output


def capture_screen(device: Optional[str] = None, adb_path: Optional[str] = None) -> np.ndarray:
    """Return BGR screenshot from the connected Android device."""
    p = run_adb(["exec-out", "screencap", "-p"], timeout=8, device=device, adb_path=adb_path)
    if p.returncode != 0 or not p.stdout:
        msg = p.stderr.decode(errors="replace").strip()
        raise RuntimeError("ADB screenshot failed. " + msg)

    arr = np.frombuffer(p.stdout, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    # Fallback for Windows carriage-return translation on older ADB versions
    if frame is None and p.stdout:
        clean_bytes = p.stdout.replace(b"\r\r\n", b"\r\n").replace(b"\r\n", b"\n")
        frame = cv2.imdecode(np.frombuffer(clean_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)

    if frame is None:
        raise RuntimeError("Could not decode screenshot returned by ADB.")
    return frame


def classify_crop(crop):
    """
    Roughly classify one candidate crop using color ratios.
    Returns (label, confidence). Confidence is only a heuristic score.
    """
    if crop is None or crop.size == 0:
        return "UNKNOWN", 0.0

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    b, g, r = cv2.split(crop)
    h, s, v = cv2.split(hsv)

    total = max(1, crop.shape[0] * crop.shape[1])
    warm = ((h <= 28) & (s > 70) & (v > 90))
    # Include reddish hues that wrap around HSV zero.
    warm |= ((h >= 170) & (s > 70) & (v > 90))
    white = (s < 75) & (v > 190)
    dark = (v < 75)
    red_eye = ((h <= 10) | (h >= 170)) & (s > 100) & (v > 80) & (r > g * 1.25)

    warm_ratio = float(np.count_nonzero(warm)) / total
    white_ratio = float(np.count_nonzero(white)) / total
    dark_ratio = float(np.count_nonzero(dark)) / total
    red_ratio = float(np.count_nonzero(red_eye)) / total

    # Devil/skull candidates: dark face plus red details and/or warm outline.
    if dark_ratio > 0.12 and red_ratio > 0.008 and warm_ratio > 0.025:
        score = min(0.95, 0.45 + dark_ratio * 0.6 + red_ratio * 5)
        return "BOMB", score

    # Fireball candidates: bright/white head and warm flame/trail.
    if white_ratio > 0.035 and warm_ratio > 0.08:
        score = min(0.92, 0.45 + white_ratio * 0.8 + warm_ratio * 0.35)
        return "FIREBALL", score

    # If there is a lot of dark and warm color, treat as a possible hazard.
    if dark_ratio > 0.20 and warm_ratio > 0.04:
        return "UNKNOWN", 0.35

    return "UNKNOWN", 0.0


def detect_objects(frame):
    """
    Build candidate blobs from warm flame pixels plus bright head pixels.
    Morphology joins nearby trail/head pixels; tune kernel sizes if needed.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    warm = (((h <= 28) | (h >= 170)) & (s > 65) & (v > 90)).astype(np.uint8) * 255
    white = ((s < 80) & (v > 205)).astype(np.uint8) * 255

    # Restrict white pixels to those near warm-colored pixels to reduce UI noise.
    warm_near = cv2.dilate(warm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    combined = cv2.bitwise_or(warm, cv2.bitwise_and(white, warm_near))

    # Join small flame segments into object candidates.
    combined = cv2.morphologyEx(
        combined, cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    )
    combined = cv2.dilate(
        combined, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
        iterations=1
    )

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = frame.shape[:2]
    detections = []

    for contour in contours:
        x, y, w, h_box = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if area < 90 or w < 14 or h_box < 14:
            continue
        if w > W * 0.75 or h_box > H * 0.8:
            continue

        # Padding lets the classifier inspect the center and outer flame.
        pad = max(6, int(max(w, h_box) * 0.15))
        x0, y0 = max(0, x-pad), max(0, y-pad)
        x1, y1 = min(W, x+w+pad), min(H, y+h_box+pad)
        label, score = classify_crop(frame[y0:y1, x0:x1])
        detections.append(Detection((x0, y0, x1-x0, y1-y0), label, score))

    # Prefer larger candidates; avoid flooding the preview with tiny fragments.
    detections.sort(key=lambda d: d.box[2] * d.box[3], reverse=True)
    return detections[:40]


def segment_distance_to_rect(x1, y1, x2, y2, rect):
    """Conservative approximate safety check using expanded swipe bounding box."""
    rx, ry, rw, rh = rect
    margin = 55
    left, top = rx - margin, ry - margin
    right, bottom = rx + rw + margin, ry + rh + margin
    sx1, sx2 = min(x1, x2), max(x1, x2)
    sy1, sy2 = min(y1, y2), max(y1, y2)
    return not (sx2 < left or sx1 > right or sy2 < top or sy1 > bottom)


def send_swipe(x1, y1, x2, y2, duration_ms=100, device: Optional[str] = None, adb_path: Optional[str] = None):
    """Send an automated touch swipe event via ADB."""
    p = run_adb([
        "shell", "input", "swipe",
        str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)),
        str(int(duration_ms))
    ], timeout=5, device=device, adb_path=adb_path)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode(errors="replace").strip() or "ADB swipe failed")


class DemoSimulator:
    """Simulates real-time gameplay objects for demo and test runs."""

    def __init__(self, width: int = 540, height: int = 960):
        self.width = width
        self.height = height
        self.objects = []
        self.swipes = []  # active visual swipe animations
        self.last_spawn = time.time()

    def _spawn_object(self):
        kind = random.choices(["FIREBALL", "BOMB"], weights=[0.75, 0.25])[0]
        x = random.randint(int(self.width * 0.2), int(self.width * 0.8))
        y = self.height + 20
        vx = random.uniform(-2.5, 2.5)
        vy = random.uniform(-19, -15)
        self.objects.append({
            "x": x, "y": y, "vx": vx, "vy": vy,
            "kind": kind, "alive": True
        })

    def trigger_swipe(self, x1, y1, x2, y2):
        self.swipes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "alpha": 1.0})
        # Check if any fireball was sliced
        for obj in self.objects:
            if obj["kind"] == "FIREBALL" and obj["alive"]:
                ox, oy = obj["x"], obj["y"]
                if min(x1, x2) - 30 <= ox <= max(x1, x2) + 30 and abs(oy - y1) < 40:
                    obj["alive"] = False

    def next_frame(self) -> np.ndarray:
        now = time.time()
        if now - self.last_spawn > random.uniform(1.0, 1.8):
            self._spawn_object()
            self.last_spawn = now

        # Dark sleek background
        frame = np.full((self.height, self.width, 3), (22, 18, 28), dtype=np.uint8)

        # Update and render objects
        gravity = 0.42
        for obj in self.objects:
            obj["x"] += obj["vx"]
            obj["y"] += obj["vy"]
            obj["vy"] += gravity

            ox, oy = int(obj["x"]), int(obj["y"])
            if not obj["alive"]:
                continue

            if obj["kind"] == "FIREBALL":
                # Outer warm flame
                cv2.ellipse(frame, (ox, oy + 8), (22, 34), 0, 0, 360, (25, 130, 255), -1)
                # Bright white core
                cv2.circle(frame, (ox, oy), 13, (255, 255, 255), -1)
            else:
                # Bomb: dark body with warm outline & red eyes
                cv2.circle(frame, (ox, oy), 26, (15, 95, 230), 4)
                cv2.circle(frame, (ox, oy), 22, (32, 32, 32), -1)
                cv2.circle(frame, (ox - 7, oy - 4), 3, (15, 15, 240), -1)
                cv2.circle(frame, (ox + 7, oy - 4), 3, (15, 15, 240), -1)

        # Remove fallen objects
        self.objects = [o for o in self.objects if o["y"] < self.height + 60 and o["alive"]]

        # Draw swipe trails
        active_swipes = []
        for s in self.swipes:
            p1 = (int(s["x1"]), int(s["y1"]))
            p2 = (int(s["x2"]), int(s["y2"]))
            color = (int(255 * s["alpha"]), int(255 * s["alpha"]), int(255 * s["alpha"]))
            cv2.line(frame, p1, p2, color, max(1, int(4 * s["alpha"])))
            s["alpha"] -= 0.15
            if s["alpha"] > 0:
                active_swipes.append(s)
        self.swipes = active_swipes

        return frame


def process_image_file(image_path: str):
    """Test object detection heuristics on a static screenshot file."""
    if not os.path.isfile(image_path):
        print(f"Error: Screenshot file not found: {image_path}")
        sys.exit(1)

    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not decode image at {image_path}")
        sys.exit(1)

    print(f"Analyzing {image_path} ({frame.shape[1]}x{frame.shape[0]})...")
    detections = detect_objects(frame)
    print(f"Found {len(detections)} candidate detections:")

    for i, d in enumerate(detections, 1):
        x, y, w, h = d.box
        print(f"  [{i}] {d.kind:<9} conf={d.confidence:.2f} box=(x={x}, y={y}, w={w}, h={h})")
        color = (0, 0, 255) if d.kind == "BOMB" else ((0, 220, 0) if d.kind == "FIREBALL" else (0, 190, 255))
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, f"{d.kind} {d.confidence:.2f}", (x, max(20, y-6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    window_name = f"Slice Bot Analysis - {os.path.basename(image_path)}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, frame)
    print("\nPress any key in the image window to close.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="USB-connected Slice game bot starter for Android")
    parser.add_argument("--auto", action="store_true",
                        help="enable experimental swipes (disabled by default)")
    parser.add_argument("--min-confidence", type=float, default=0.68,
                        help="minimum heuristic fireball score for auto mode")
    parser.add_argument("--cooldown", type=float, default=0.65,
                        help="minimum seconds between automated swipes")
    parser.add_argument("--device", "-s", type=str, default=None,
                        help="target specific ADB device serial if multiple devices are attached")
    parser.add_argument("--adb-path", type=str, default=None,
                        help="explicit path to adb executable")
    parser.add_argument("--demo", action="store_true",
                        help="run interactive simulation mode without needing an Android device")
    parser.add_argument("--image", type=str, default=None,
                        help="analyze a single static screenshot image and display detections")
    parser.add_argument("--preview-scale", type=float, default=None,
                        help="scale preview window display size (e.g. 0.6 for high-res screens)")
    args = parser.parse_args()

    # Mode 1: Static Image Inspection
    if args.image:
        process_image_file(args.image)
        return

    # Check / Locate ADB
    adb_exe = None
    if not args.demo:
        adb_exe = find_adb(args.adb_path)
        print("Checking ADB environment...")
        if adb_exe:
            print(f"ADB located at: {adb_exe}")
        else:
            print("\n[!] ADB executable was not found on PATH or standard Android SDK locations.")
            print("To run with an Android device:")
            print("  1. Download Android Platform Tools: https://developer.android.com/tools/releases/platform-tools")
            print("  2. Pass --adb-path <path_to_adb.exe> or add it to your system PATH.")
            print("\nTip: You can run with '--demo' to test the bot's detection and UI preview right now without a device!\n")
            sys.exit(1)

        # Check connected devices
        try:
            connected_devices, raw_devices_out = list_connected_devices(adb_exe)
            print(raw_devices_out.strip())
        except Exception as exc:
            print(f"Error querying ADB devices: {exc}")
            sys.exit(1)

        if not connected_devices:
            print("\n[!] No authorized Android device found.")
            print("Troubleshooting checklist:")
            print("  1. Enable Developer Options on phone (tap Build Number 7 times).")
            print("  2. Turn on 'USB Debugging'.")
            print("  3. Unlock phone and tap 'Allow USB debugging' on the prompt.")
            print("  4. Check USB cable and mode (File Transfer / MTP).")
            print("\nTip: Run with '--demo' to test the bot and CV detection right now without a phone!\n")
            sys.exit(1)

        target_device = args.device or connected_devices[0]
        if len(connected_devices) > 1 and not args.device:
            print(f"Multiple devices detected. Using primary device: {target_device}")
            print(f"Use --device <serial> to choose another.")
        else:
            print(f"Targeting device: {target_device}")
    else:
        print("\n--- RUNNING IN DEMO / SIMULATION MODE ---")
        print("Simulating game screen with flying fireballs and bombs.")
        print("Testing real-time heuristic detection and swipe decision logic.\n")
        target_device = None

    if args.auto:
        print("AUTO MODE ENABLED. Experimental heuristic swipes are active.")
        print("Keep the phone visible and be ready to stop with Q or Ctrl+C.")
    else:
        print("OBSERVE-ONLY MODE: no physical swipes will be sent.")
        print("Press Q or close preview window to quit.")

    window_name = "Slice Bot - Q to quit"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    demo_sim = DemoSimulator() if args.demo else None
    last_swipe = 0.0
    frame_count = 0
    fps = 0.0
    fps_timer = time.time()

    try:
        while True:
            # Check if user closed the OpenCV window
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

            # Acquire frame
            if args.demo:
                frame = demo_sim.next_frame()
            else:
                try:
                    frame = capture_screen(device=target_device, adb_path=adb_exe)
                except Exception as cap_err:
                    print(f"Screen capture warning: {cap_err}. Retrying...")
                    time.sleep(0.5)
                    continue

            # Run detection pipeline
            detections = detect_objects(frame)
            bombs = [d for d in detections if d.kind in ("BOMB", "UNKNOWN")]
            fireballs = [d for d in detections if d.kind == "FIREBALL"]

            # Calculate FPS
            frame_count += 1
            if time.time() - fps_timer >= 1.0:
                fps = frame_count / (time.time() - fps_timer)
                frame_count = 0
                fps_timer = time.time()

            # Annotate detections
            preview = frame.copy()
            for d in detections:
                x, y, w, h = d.box
                if d.kind == "BOMB":
                    color = (0, 0, 255)
                elif d.kind == "FIREBALL":
                    color = (0, 220, 0)
                else:
                    color = (0, 190, 255)
                label = f"{d.kind} {d.confidence:.2f}"
                cv2.rectangle(preview, (x, y), (x+w, y+h), color, 2)
                cv2.putText(preview, label, (x, max(20, y-6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            status = "AUTO ON" if args.auto else "OBSERVE ONLY"
            demo_tag = " [DEMO]" if args.demo else ""
            header = f"{status}{demo_tag} | FPS: {fps:.1f} | Detections: {len(detections)}"
            cv2.putText(preview, header, (12, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Experimental swipe action
            now = time.time()
            if args.auto and fireballs and now - last_swipe >= args.cooldown:
                fireballs.sort(key=lambda d: d.confidence, reverse=True)
                target = fireballs[0]
                if target.confidence >= args.min_confidence:
                    x, y, w, h = target.box
                    cx, cy = x + w // 2, y + h // 2
                    x1, y1 = max(1, cx - max(12, w // 4)), cy
                    x2, y2 = min(frame.shape[1]-2, cx + max(12, w // 4)), cy

                    blocked = any(
                        segment_distance_to_rect(x1, y1, x2, y2, d.box)
                        for d in bombs
                    )
                    if not blocked:
                        if args.demo:
                            demo_sim.trigger_swipe(x1, y1, x2, y2)
                            print(f"[Demo] Simulated swipe at ({cx}, {cy}) score={target.confidence:.2f}")
                        else:
                            send_swipe(x1, y1, x2, y2, 100, device=target_device, adb_path=adb_exe)
                            print(f"Experimental swipe at ({cx}, {cy}) score={target.confidence:.2f}")
                        last_swipe = now

            # Scale preview if requested or if height is large
            display_frame = preview
            H, W = preview.shape[:2]
            scale = args.preview_scale
            if scale is None and H > 1000:
                scale = 750.0 / H
            if scale and scale != 1.0:
                new_w = int(W * scale)
                new_h = int(H * scale)
                display_frame = cv2.resize(preview, (new_w, new_h), interpolation=cv2.INTER_AREA)

            cv2.imshow(window_name, display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break

            time.sleep(0.03 if args.demo else 0.04)

    except KeyboardInterrupt:
        print("\nStopping.")
    except Exception as exc:
        print(f"\nError: {exc}")
        if not args.demo:
            print("Verify adb devices and that the phone is unlocked.")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
