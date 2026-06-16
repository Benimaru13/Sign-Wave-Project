"""
 gesture controller:
Detects gestures and sends commands to the smart car.

Usage:
    go into the virtual environment for python 3.11, go into the hagrid_model directory and run the demo.py file
    command: 
    .venv311\Scripts\activate
    cd hagrid_model
    python demo.py -p configs/SSDLiteMobileNetV3Large.yaml --landmarks     

    # dont forget to change the PI_IP variable in the demo.py file to the IP address of your Raspberry Pi


Requirements:
    install python 3.11 version
    pip install torch torchvision opencv-python albumentations omegaconf "mediapipe==0.10.21" torchmetrics
"""

import argparse
import logging
import time
from typing import Optional, Tuple

import albumentations as A
import cv2
import mediapipe as mp
import numpy as np
import socket
import torch
from albumentations.pytorch import ToTensorV2
from omegaconf import DictConfig, OmegaConf
from torch import Tensor

from mediapipe.python.solutions import drawing_utils as mp_drawing
from mediapipe.python.solutions import drawing_styles as mp_drawing_styles

# mp_drawing = mp.solutions.drawing_utils
# mp_drawing_styles = mp.solutions.drawing_styles

from constants import targets
from custom_utils.utils import build_model

# === CONFIGURATION ===
PI_IP = "10.0.0.16"  # e.g. "10.84.73.85"
PI_PORT = 5005

# === GESTURE TO COMMAND MAP ===
GESTURE_MAP = {
    "like": "FORWARD",
    "dislike": "BACKWARD",
    "stop": "OFF",
}

logging.basicConfig(format="[LINE:%(lineno)d] %(levelname)-8s [%(asctime)s]  %(message)s", level=logging.INFO)

COLOR = (0, 255, 0)
FONT = cv2.FONT_HERSHEY_SIMPLEX

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
last_command = {"value": None}

class Demo:
    @staticmethod
    def preprocess(img: np.ndarray, transform) -> Tuple[Tensor, Tuple[int, int], Tuple[int, int]]:
        """
        Preproc image for model input
        Parameters
        ----------
        img: np.ndarray
            input image
        transform :
            albumentation transforms
        """
        height, width = img.shape[0], img.shape[1]
        transformed_image = transform(image=img)
        processed_image = transformed_image["image"] / 255.0
        return processed_image, (width, height)

    @staticmethod
    def get_transform_for_inf(transform_config: DictConfig):
        """
        Create list of transforms from config
        Parameters
        ----------
        transform_config: DictConfig
            config with test transforms
        """
        transforms_list = [getattr(A, key)(**params) for key, params in transform_config.items()]
        transforms_list.append(ToTensorV2())
        return A.Compose(transforms_list)

    @staticmethod
    def run(detector, transform, conf, num_hands=2, threshold=0.5, landmarks=False, sock=None, last_command=None):
        """
        Run detection model and draw bounding boxes on frame
        Parameters
        ----------
        detector : TorchVisionModel
            Detection model
        transform :
            albumentation transforms
        transform_config: DictConfig
            config with test transforms
        num_hands:
            Min hands to detect
        threshold : float
            Confidence threshold
        landmarks : bool
            Detect landmarks
        """

        if landmarks:
            hands = mp.solutions.hands.Hands(
                model_complexity=0, static_image_mode=False, max_num_hands=2, min_detection_confidence=0.8
            )

        cap = cv2.VideoCapture(0)

        t1 = cnt = 0
        while cap.isOpened():
            delta = time.time() - t1
            t1 = time.time()

            ret, frame = cap.read()
            if ret:
                processed_image, size = Demo.preprocess(frame, transform)
                with torch.no_grad():
                    output = detector([processed_image])[0]
                boxes = output["boxes"][:num_hands]
                scores = output["scores"][:num_hands]
                labels = output["labels"][:num_hands]

                hand_label = None

                if landmarks:
                    results = hands.process(frame[:, :, ::-1])
                    if results.multi_hand_landmarks:
                        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                            hand_label = handedness.classification[0].label  # "Left" or "Right"
                            mp_drawing.draw_landmarks(
                                frame,
                                hand_landmarks,
                                mp.solutions.hands.HAND_CONNECTIONS,
                                mp_drawing_styles.DrawingSpec(color=[0, 255, 0], thickness=2, circle_radius=1),
                                mp_drawing_styles.DrawingSpec(color=[255, 255, 255], thickness=1, circle_radius=1),
                            )
                for i in range(min(num_hands, len(boxes))):
                    if scores[i] > threshold:
                        width, height = size
                        scale = max(width, height) / conf.LongestMaxSize.max_size
                        padding_w = abs(conf.PadIfNeeded.min_width - width // scale) // 2
                        padding_h = abs(conf.PadIfNeeded.min_height - height // scale) // 2
                        x1 = int((boxes[i][0] - padding_w) * scale)
                        y1 = int((boxes[i][1] - padding_h) * scale)
                        x2 = int((boxes[i][2] - padding_w) * scale)
                        y2 = int((boxes[i][3] - padding_h) * scale)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR, thickness=3)
                        cv2.putText(
                            frame,
                            targets[int(labels[i])],
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            2,
                            (0, 0, 255),
                            thickness=3,
                        )

                        # Send command to Pi if gesture is recognized
                        gesture_name = targets[int(labels[i])]
                        if gesture_name == "three_gun":
                            print(f"hand_label: {hand_label}")
                            command = "LEFT" if hand_label == "Right" else "RIGHT"
                            print(f"command after handedness: {command}")
                        else:
                            command = GESTURE_MAP.get(gesture_name)
                        print(f"Detected: {gesture_name}, Command: {command}")
                        if command and command != last_command["value"]:
                            sock.sendto(command.encode(), (PI_IP, PI_PORT))
                            last_command["value"] = command
                            print(f"Sent: {command}")

                fps = 1 / delta
                cv2.putText(frame, f"FPS: {fps :02.1f}, Frame: {cnt}", (30, 30), FONT, 1, COLOR, 2)
                cnt += 1

                cv2.imshow("Frame", frame)

                key = cv2.waitKey(1)
                if key == ord("q"):
                    return
            else:
                cap.release()
                cv2.destroyAllWindows()


def parse_arguments(params: Optional[Tuple] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo detection...")

    parser.add_argument("-p", "--path_to_config", required=True, type=str, help="Path to config")

    parser.add_argument("-lm", "--landmarks", required=False, action="store_true", help="Use landmarks")

    known_args, _ = parser.parse_known_args(params)
    return known_args


if __name__ == "__main__":
    args = parse_arguments()
    conf = OmegaConf.load(args.path_to_config)
    model = build_model(conf)
    transform = Demo.get_transform_for_inf(conf.test_transforms)
    if conf.model.checkpoint is not None:
        snapshot = torch.load(conf.model.checkpoint, map_location=torch.device("cpu"))
        model.load_state_dict(snapshot["MODEL_STATE"])

    model.eval()
    if model is not None:
        Demo.run(model, transform, conf.test_transforms, num_hands=100, threshold=0.8, landmarks=args.landmarks, sock=sock, last_command=last_command)