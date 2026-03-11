# Sign-Wave-Project
1.  2. our current raspberry pi model is 3b 3. We have set up the raspberry pi OS but we are figuring out the Arducam (we don't think this will be too difficult ot get out of the way) 4. Python 5. We are at an intermediate level with Python

# 🤙 Sign Wave Project

> Real-time hand gesture recognition using MediaPipe and OpenCV on a Raspberry Pi, mapped to physical LED outputs via GPIO.

---

## 📌 Overview

Sign Wave is an embedded computer vision system that detects hand gestures in real time through a camera module and translates them into physical outputs — specifically, LED light combinations triggered via a Raspberry Pi's GPIO pins.

The project combines computer vision, machine learning, and embedded hardware to create a responsive, gesture-controlled system. Our initial MVP focuses on recognizing **two distinct hand gestures** and mapping each to a unique LED output.

---

## 🎯 MVP Goals

- [ ] Integrate Arducam camera module with Raspberry Pi
- [ ] Capture and process a live video feed using OpenCV
- [ ] Detect and classify two hand gestures using MediaPipe
- [ ] Trigger corresponding LED outputs via Raspberry Pi GPIO pins
- [ ] Achieve stable, real-time performance on device

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Computer Vision | OpenCV |
| Hand Tracking | MediaPipe |
| Hardware | Raspberry Pi 4 |
| Camera | Arducam Module |
| Physical Output | LEDs via GPIO |

---

## 👥 Team

### Software
| Name | Role |
|---|---|
| Srija | Software |
| Chibueze | Software |
| Sarah | Software |

### Hardware
| Name | Role |
|---|---|
| Hongyi | Electronics & Hardware |
| James | Electronics & Hardware |

---

## 📁 Project Structure

```
sign-wave-project/
├── software/
│   ├── gesture_detection/       # MediaPipe hand tracking logic
│   ├── gpio_output/             # GPIO pin control logic
│   └── main.py                  # Entry point
├── hardware/
│   └── wiring_diagrams/         # Circuit diagrams and references
├── tests/
│   └── camera_test.py           # Camera feed validation
├── docs/                        # Additional documentation
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation

> **Note:** Full setup instructions will be updated as the project develops.

### Prerequisites
- Raspberry Pi 4 with Raspberry Pi OS installed
- Arducam camera module connected and enabled
- Python 3.7+

### Install Dependencies
```bash
pip install opencv-python mediapipe RPi.GPIO
```

### Run the Project
```bash
python software/main.py
```

---

## 🚦 How It Works

1. The Arducam captures a live video feed
2. Each frame is passed to MediaPipe's hand landmark detection
3. Landmark data is used to classify the gesture
4. The classification triggers a GPIO output
5. The corresponding LED combination lights up

---

## 🗺️ Roadmap

- **Phase 1 (MVP):** 2 gesture recognition → LED output
- **Phase 2:** Expand gesture vocabulary
- **Phase 3:** Improve response latency and stability
- **Phase 4:** Explore additional output mechanisms beyond LEDs

---

## 📄 License

This project is for educational and development purposes.
