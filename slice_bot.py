"""
Slice game bot starter for Windows + Android USB/ADB.

Default mode is OBSERVE ONLY. It captures the phone screen and draws
heuristic candidate boxes. Automated swipes are disabled unless --auto
is explicitly supplied.

Detection is a starter heuristic, not a trained classifier. Calibrate it
against real gameplay before enabling actions.
"""
import argparse
import subprocess
import sys
import time
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Detection:
    box: tuple  # x, y, w, h
    kind: str   # FIREBALL, BOMB, UNKNOWN
    confidence: float


def run_adb(args, timeout=5):
    return subprocess.run(
        ["adb", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def capture_screen():
    """Return BGR screenshot from the connected Android device."""
    p = run_adb(["exec-out", "screencap", "-p"], timeout=8)
    if p.returncode != 0 or not p.stdout:
        msg = p.stderr.decode(errors="replace").strip()
        raise RuntimeError("ADB screenshot failed. " + msg)
    arr = np.frombuffer(p.stdout, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
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


def send_swipe(x1, y1, x2, y2, duration_ms=100):
    p = run_adb([
        "shell", "input", "swipe",
        str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)),
        str(int(duration_ms))
    ], timeout=5)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode(errors="replace").strip() or "ADB swipe failed")


def main():
    parser = argparse.ArgumentParser(description="USB-connected Slice game bot starter")
    parser.add_argument("--auto", action="store_true",
                        help="enable experimental swipes (disabled by default)")
    parser.add_argument("--min-confidence", type=float, default=0.68,
                        help="minimum heuristic fireball score for auto mode")
    parser.add_argument("--cooldown", type=float, default=0.65,
                        help="minimum seconds between automated swipes")
    args = parser.parse_args()

    print("Checking ADB device...")
    devices = run_adb(["devices"])
    print(devices.stdout.decode(errors="replace"))
    if devices.returncode != 0 or b"\tdevice" not in devices.stdout:
        print("\nNo authorized Android device found.")
        print("Check USB debugging, accept the phone's authorization prompt, then retry.")
        sys.exit(1)

    if args.auto:
        print("\nAUTO MODE ENABLED. Experimental heuristic detection may be wrong.")
        print("Keep the phone visible and be ready to stop with Q or Ctrl+C.")
    else:
        print("\nOBSERVE-ONLY MODE: no swipes will be sent.")
        print("Press Q in the preview window to quit.")

    last_swipe = 0.0
    try:
        while True:
            frame = capture_screen()
            detections = detect_objects(frame)

            bombs = [d for d in detections if d.kind in ("BOMB", "UNKNOWN")]
            fireballs = [d for d in detections if d.kind == "FIREBALL"]

            for d in detections:
                x, y, w, h = d.box
                if d.kind == "BOMB":
                    color = (0, 0, 255)
                elif d.kind == "FIREBALL":
                    color = (0, 220, 0)
                else:
                    color = (0, 190, 255)
                label = f"{d.kind} {d.confidence:.2f}"
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, label, (x, max(20, y-6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            status = "AUTO ON" if args.auto else "OBSERVE ONLY"
            cv2.putText(frame, status, (12, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("Slice Bot - Q to quit", frame)

            # Experimental action: short swipe across the central area of a
            # confident candidate. Any bomb/unknown candidate near its path blocks it.
            now = time.time()
            if args.auto and fireballs and now - last_swipe >= args.cooldown:
                fireballs.sort(key=lambda d: d.confidence, reverse=True)
                target = fireballs[0]
                if target.confidence >= args.min_confidence:
                    x, y, w, h = target.box
                    cx, cy = x + w // 2, y + h // 2
                    # Short horizontal swipe near the detected center.
                    x1, y1 = max(1, cx - max(12, w // 4)), cy
                    x2, y2 = min(frame.shape[1]-2, cx + max(12, w // 4)), cy

                    blocked = any(
                        segment_distance_to_rect(x1, y1, x2, y2, d.box)
                        for d in bombs
                    )
                    if not blocked:
                        send_swipe(x1, y1, x2, y2, 100)
                        last_swipe = now
                        print(f"Experimental swipe at ({cx}, {cy}) score={target.confidence:.2f}")

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break

            # Small pause to reduce CPU usage. Capture cadence depends on USB/device.
            time.sleep(0.04)

    except KeyboardInterrupt:
        print("\nStopping.")
    except Exception as exc:
        print(f"\nError: {exc}")
        print("Verify adb devices and that the phone is unlocked.")
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
