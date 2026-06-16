#!/usr/bin/env python3
"""
Mac-side gesture controller.

Uses MediaPipe to detect hand gestures from a webcam and sends
corresponding commands to a Raspberry Pi over UDP.

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

# Path to the MediaPipe gesture recognition model
MODEL_PATH = current_directory / 'software' / 'gesture_recognizer.task'

# UDP port used to communicate with the Raspberry Pi
PI_PORT = 5005  # Must match the Pi script

# === GESTURES TO COMMANDS ===
# Maps MediaPipe gesture names to commands sent to the Raspberry Pi.
GESTURE_MAP = {
    "Open_Palm":   "FORWARD",
    "Closed_Fist": "BACKWARD",
    "Thumb_Up":    "OFF",
}

# === MediaPipe shortcuts ===
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
RunningMode = mp.tasks.vision.RunningMode
Image = mp.Image

# === Shared state ===
# These values are updated by MediaPipe's callback and
# displayed in the main OpenCV rendering loop.
_latest_gesture: Optional[str] = None
_latest_landmarks_norm: Optional[List[Tuple[float, float]]] = None

# Landmark index pairs used to draw a hand skeleton overlay.
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]


def send_command(sock: socket.socket, pi_ip: str, command: str) -> None:
    """
    Send a UDP command to the Raspberry Pi.
    """
    try:
        sock.sendto(command.encode(), (pi_ip, PI_PORT))
        print(f"  → Sent: {command}")
    except Exception as e:
        print(f"  ✗ Failed to send command: {e}")


def make_result_callback(sock: socket.socket, pi_ip: str):
    """
    Creates MediaPipe's result callback.

    MediaPipe's callback signature is fixed, so a closure is used
    to give the callback access to the socket and Pi IP address.
    """

    # Stores the most recently sent command so we only send
    # updates when the gesture changes.
    last_command = {"value": None}

    def callback(result, output_image, timestamp_ms: int):
        global _latest_gesture, _latest_landmarks_norm

        gesture_label = None
        command = None

        if result and result.gestures:

            # Use the highest-confidence gesture prediction.
            gesture = result.gestures[0][0]

            # Determine whether the detected hand is left or right.
            handedness = result.handedness[0][0].category_name

            gesture_label = (
                f"{handedness} hand - "
                f"{gesture.category_name} ({gesture.score:.2f})"
            )

            print(f"Recognized: {gesture_label}")

            # Convert the recognized gesture into a command.
            command = GESTURE_MAP.get(gesture.category_name)

        _latest_gesture = gesture_label

        # Save landmark coordinates so they can be drawn
        # on the camera feed in the main loop.
        if result and getattr(result, 'hand_landmarks', None):
            hand0 = result.hand_landmarks[0]
            _latest_landmarks_norm = [(lm.x, lm.y) for lm in hand0]
        else:
            _latest_landmarks_norm = None

        # Only send a command when the gesture changes
        # to avoid flooding the network with duplicate packets.
        if command and command != last_command["value"]:
            send_command(sock, pi_ip, command)
            last_command["value"] = command

    return callback


def main():
    parser = argparse.ArgumentParser(
        description="Gesture-controlled Raspberry Pi interface."
    )

    # Raspberry Pi IP address supplied when launching the script.
    parser.add_argument(
        "--pi-ip",
        required=True,
        help="IP address of your Raspberry Pi (e.g. 192.168.1.42)"
    )

    args = parser.parse_args()

    print("\n🖐 Gesture Controller")
    print(f"   Pi IP   : {args.pi_ip}:{PI_PORT}")
    print("   Gestures:")
    print("      Open Palm   → FORWARD")
    print("      Closed Fist → BACKWARD")
    print("      Thumb Up    → OFF")
    print("   Press q to quit\n")

    # UDP socket used to send commands to the Raspberry Pi.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Configure MediaPipe for continuous webcam processing.
    options = GestureRecognizerOptions(
        base_options=BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=RunningMode.LIVE_STREAM,
        result_callback=make_result_callback(sock, args.pi_ip),
    )

    with GestureRecognizer.create_from_options(options) as recognizer:

        # Open the default webcam.
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: could not open camera")
            return

        try:
            while True:

                # Read a frame from the webcam.
                ret, frame = cap.read()

                if not ret:
                    break

                # Mirror the image so movement feels natural.
                frame_flipped = cv2.flip(frame, 1)

                # OpenCV uses BGR, but MediaPipe expects RGB.
                rgb_frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                # Create a MediaPipe image object.
                mp_image = Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame
                )

                # LIVE_STREAM mode requires timestamps.
                timestamp_ms = int(time.time() * 1000)

                # Process the frame asynchronously.
                # Results are returned through the callback.
                recognizer.recognize_async(
                    mp_image,
                    timestamp_ms
                )

                # Display the most recently recognized gesture.
                if _latest_gesture:
                    cv2.putText(
                        frame_flipped,
                        _latest_gesture,
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )

                # Draw the hand skeleton and landmark points.
                if _latest_landmarks_norm:

                    h, w = frame_flipped.shape[:2]

                    # Convert normalized coordinates (0-1)
                    # into pixel coordinates on the frame.
                    pts = [
                        (int((1.0 - x) * w), int(y * h))
                        for (x, y) in _latest_landmarks_norm
                    ]

                    # Draw skeleton connections.
                    for a, b in HAND_CONNECTIONS:
                        if a < len(pts) and b < len(pts):

                            cv2.line(
                                frame_flipped,
                                pts[a],
                                pts[b],
                                (0, 0, 0),
                                10,
                                cv2.LINE_AA
                            )

                            cv2.line(
                                frame_flipped,
                                pts[a],
                                pts[b],
                                (0, 255, 0),
                                6,
                                cv2.LINE_AA
                            )

                    # Draw a circle at each landmark location.
                    for (x_px, y_px) in pts:

                        cv2.circle(
                            frame_flipped,
                            (x_px, y_px),
                            10,
                            (0, 0, 0),
                            -1
                        )

                        cv2.circle(
                            frame_flipped,
                            (x_px, y_px),
                            6,
                            (0, 0, 255),
                            -1
                        )

                # Display the annotated webcam feed.
                cv2.imshow('Gesture Controller', frame_flipped)

                # Exit when the user presses 'q'.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            # Release resources before exiting.
            cap.release()
            cv2.destroyAllWindows()
            sock.close()


if __name__ == '__main__':
    main()