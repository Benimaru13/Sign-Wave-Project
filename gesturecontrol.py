#!/usr/bin/env python3
"""
Mac-side gesture controller.
Detects open palm / closed fist and sends ON/OFF to the Raspberry Pi.

Usage:
    python3 gesturecontrol.py --pi-ip 10.84.73.85

Requirements:
    pip3 install mediapipe opencv-python
"""

import argparse
import socket
import time
import cv2
import mediapipe as mp
from pathlib import Path
from typing import Optional, List, Tuple

# === CONFIGURATION ===
current_directory = Path(__file__).parent
MODEL_PATH = current_directory / 'gesture_recognizer.task'
PI_PORT = 5005  # Must match the Pi script

# === GESTURES TO COMMANDS ===
# Map MediaPipe gesture category names to LED commands
GESTURE_MAP = {
    "Open_Palm":   "ON",
    "Closed_Fist": "OFF",
    # "Thumbs_Up":  "OFF",
}

# === MediaPipe shortcuts ===
BaseOptions             = mp.tasks.BaseOptions
GestureRecognizer       = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
RunningMode             = mp.tasks.vision.RunningMode
Image                   = mp.Image

# === Shared state ===
_latest_gesture: Optional[str] = None
_latest_landmarks_norm: Optional[List[Tuple[float, float]]] = None

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]


def send_command(sock: socket.socket, pi_ip: str, command: str) -> None:
    """Send a UDP command string to the Pi."""
    try:
        sock.sendto(command.encode(), (pi_ip, PI_PORT))
        print(f"  → Sent: {command}")
    except Exception as e:
        print(f"  ✗ Failed to send command: {e}")


def make_result_callback(sock: socket.socket, pi_ip: str):
    """
    Returns a callback closure that has access to the socket and Pi IP.
    We use a closure here because MediaPipe's callback signature is fixed
    (result, output_image, timestamp_ms) — we can't add extra arguments.
    So we 'bake in' sock and pi_ip by wrapping it in an outer function.
    """
    last_command = {"value": None}  # dict so we can mutate inside closure

    def callback(result, output_image, timestamp_ms: int):
        global _latest_gesture, _latest_landmarks_norm

        gesture_label = None
        command = None

        if result and result.gestures:
            gesture = result.gestures[0][0]
            handedness = result.handedness[0][0].category_name
            gesture_label = f"{handedness} hand - {gesture.category_name} ({gesture.score:.2f})"
            print(f"Recognized: {gesture_label}")

            # Map gesture to LED command
            command = GESTURE_MAP.get(gesture.category_name)

        _latest_gesture = gesture_label

        # Store landmarks for drawing
        if result and getattr(result, 'hand_landmarks', None):
            hand0 = result.hand_landmarks[0]
            _latest_landmarks_norm = [(lm.x, lm.y) for lm in hand0]
        else:
            _latest_landmarks_norm = None

        # Only send if command changed (avoid flooding the Pi)
        if command and command != last_command["value"]:
            send_command(sock, pi_ip, command)
            last_command["value"] = command

    return callback


def main():
    parser = argparse.ArgumentParser(description="Gesture-controlled LED over WiFi.")
    parser.add_argument("--pi-ip", required=True, help="IP address of your Raspberry Pi e.g. 192.168.1.42")
    args = parser.parse_args()

    print(f"\n🖐  Gesture Controller")
    print(f"   Pi IP   : {args.pi_ip}:{PI_PORT}")
    print(f"   Gestures: Open Palm = ON | Closed Fist = OFF")
    print(f"   Press q to quit\n")

    # UDP socket — fire and forget, no connection needed
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=RunningMode.LIVE_STREAM,
        result_callback=make_result_callback(sock, args.pi_ip),
    )

    with GestureRecognizer.create_from_options(options) as recognizer:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: could not open camera")
            return

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_flipped = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = int(time.time() * 1000)
                recognizer.recognize_async(mp_image, timestamp_ms)

                # Draw gesture label
                if _latest_gesture:
                    cv2.putText(frame_flipped, _latest_gesture, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

                # Draw landmarks
                if _latest_landmarks_norm:
                    h, w = frame_flipped.shape[:2]
                    pts = [(int((1.0 - x) * w), int(y * h)) for (x, y) in _latest_landmarks_norm]
                    for a, b in HAND_CONNECTIONS:
                        if a < len(pts) and b < len(pts):
                            cv2.line(frame_flipped, pts[a], pts[b], (0, 0, 0), 10, cv2.LINE_AA)
                            cv2.line(frame_flipped, pts[a], pts[b], (0, 255, 0), 6, cv2.LINE_AA)
                    for (x_px, y_px) in pts:
                        cv2.circle(frame_flipped, (x_px, y_px), 10, (0, 0, 0), -1)
                        cv2.circle(frame_flipped, (x_px, y_px), 6, (0, 0, 255), -1)

                cv2.imshow('Gesture Controller', frame_flipped)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
            sock.close()


if __name__ == '__main__':
    main()
