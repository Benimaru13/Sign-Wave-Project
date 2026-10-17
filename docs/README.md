# SignWave

**A hand-gesture-controlled toy car prototype built with Python, MediaPipe, OpenCV and a Raspberry Pi.**

SignWave connects webcam-based gesture recognition to physical movement. A controller computer recognizes three static hand gestures and sends short UDP commands over a local network. A Raspberry Pi receives those commands and drives the car's motors through a PCA9685-based interface.

The team's final working demo used this three-gesture car-control path.

The project demonstrates computer-vision integration, network messaging and embedded motor control. It uses a supplied MediaPipe gesture-recognition model; the main control path does not train a custom model or translate sign language.

## Main control path

```text
Controller computer                         Raspberry Pi / car
Webcam -> OpenCV -> MediaPipe -> UDP:5005 -> motor_server.py
            preview + landmarks                |
                                           motor.py
                                               |
                                         pca9685.py / I2C
                                               |
                                           car motors
```

Camera frames are processed on the **controller computer**, not streamed to the Pi. Only command strings cross the network. The current controller opens the default local webcam with `cv2.VideoCapture(0)`.

| Recognized gesture | UDP command | Car action |
|---|---|---|
| Open palm (`Open_Palm`) | `FORWARD` | Drive all four motor channels at `1000` |
| Closed fist (`Closed_Fist`) | `BACKWARD` | Drive all four motor channels at `-1000` |
| Thumbs up (`Thumb_Up`) | `OFF` | Set all four motor commands to zero |

These are motor-controller command values, not measured speed or distance. The gesture interface does not implement steering, variable-speed control or autonomous navigation.

### What the code implements

- Asynchronous MediaPipe Gesture Recognizer inference in `LIVE_STREAM` mode.
- A mirrored OpenCV preview with the detected gesture, confidence score, handedness and hand-landmark overlay.
- Mapping of the first returned hand's top gesture prediction to one of three movement commands.
- UDP transmission when the mapped command changes, avoiding repeated identical commands.
- A Pi-side receiver that dispatches commands to the four-motor controller.
- A stop command in the motor server's cleanup path when it exits normally or handles `Ctrl+C`.

The repository does not include measured recognition accuracy, end-to-end latency or reliability benchmarks. A displayed model confidence score is not an accuracy measurement.

## Repository guide

Paths below are relative to the repository root.

| File / directory | Purpose |
|---|---|
| [`gesturecontrol.py`](../gesturecontrol.py) | Main webcam gesture controller; sends `FORWARD`, `BACKWARD` and `OFF` |
| [`motor_server.py`](../motor_server.py) | Pi-side UDP receiver for the car |
| [`motor.py`](../motor.py) | Four-motor control and direction/PWM mapping |
| [`pca9685.py`](../pca9685.py) | PCA9685 I2C driver; uses bus 1 and address `0x40` by default |
| [`gesture_recognizer.task`](../gesture_recognizer.task) | Model asset loaded by the MediaPipe scripts |
| [`demo.py`](../demo.py) | Webcam gesture-recognition visualization without car commands |
| [`software/testcamera.py`](../software/testcamera.py) | Manual check of the default OpenCV camera feed |
| [`gesture_test.py`](../gesture_test.py), [`led_test.py`](../led_test.py) | Three-gesture LED experiment using `PALM`, `FIST` and `UP` |
| [`led_server.py`](../led_server.py) | Earlier single-LED receiver accepting `ON` and `OFF` |
| [`hagrid_model/`](../hagrid_model/) | Separate HaGRID code and documentation; not imported by the main MediaPipe car-control scripts |
| [`docs/requirements.txt`](requirements.txt) | Existing dependency pins for vision and GPIO experimentation |

The scripts with `test` in their names are manual hardware experiments, not an automated test suite. Some experimental scripts retain older comments and command mappings; use `gesturecontrol.py` with `motor_server.py` for the car path.

## Hardware and software requirements

**Controller computer**

- Python environment compatible with MediaPipe and OpenCV.
- A working webcam, GUI/display access and camera permission.
- Network access to the Pi on UDP port `5005`.

**Raspberry Pi / car**

- Raspberry Pi OS with Python and I2C enabled.
- PCA9685-compatible motor-control hardware at I2C address `0x40`, accessible on bus 1.
- Four motors, a suitable motor-driver/power arrangement and wiring matching the channel assignments in `motor.py`.
- Python's `smbus` module for the I2C driver.

A complete wiring diagram, motor-driver board specification and verified Pi/camera model are not documented here. Check your actual hardware before running the motor receiver. The PCA9685 provides control signals; motors require appropriate driver circuitry and power.

## Running the car prototype

Run the following commands from the **repository root** after cloning:

```bash
# Download the project and enter the directory containing the entry points.
git clone https://github.com/Benimaru13/Sign-Wave-Project.git
cd Sign-Wave-Project
```

### 1. Prepare the controller computer

The existing requirements file pins `opencv-python==4.13.0.92` and `mediapipe==0.10.33`. It also lists `gpiozero`, which the main laptop controller does not use. A minimal controller environment can be created with:

```bash
# Isolate the camera/recognition dependencies from other Python projects.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install opencv-python==4.13.0.92 mediapipe==0.10.33

# Check camera access first, then try gesture visualization without moving hardware.
python software/testcamera.py
python demo.py
```

Keep `gesture_recognizer.task` beside `gesturecontrol.py` and `demo.py`; both resolve the asset relative to their own location. Press `q` to close either camera window.

### 2. Prepare and start the Pi receiver

Make the repository available on the Pi, enable I2C in Raspberry Pi configuration and install the OS-provided `python3-smbus` package if needed. Confirm the driver board address, motor wiring and power supply before continuing.

```bash
# Start on the Pi, from the repository root, after checking the hardware setup.
python3 motor_server.py
```

The server binds to `0.0.0.0:5005`. Run only one receiver on that port at a time; the LED experiments use the same port.

### 3. Start gesture control

In a separate terminal on the controller computer:

```bash
# Replace this example address with the Pi's actual local-network IP address.
python gesturecontrol.py --pi-ip 192.168.1.42
```

Use an open palm for forward, a closed fist for backward and thumbs up for stop. Keep the car raised with its wheels clear while checking the mapping. Press `Ctrl+C` in the **Pi server terminal** to exit the server and execute its motor-stop cleanup.

## Current limitations and operating behaviour

- **No automatic stop on hand loss or connection loss.** An unrecognized gesture or absent hand sends no command. The receiver retains its last motor setting until another recognized command arrives or the server exits through its cleanup path.
- **Closing the controller does not send `OFF`.** Pressing `q`, losing camera frames or closing the laptop process releases its local resources but does not stop the Pi server's motors.
- **UDP delivery is not confirmed.** There are no acknowledgements, retries or heartbeat packets. Because the controller sends only on command changes, a dropped packet may leave the car in its previous state; repeatedly holding the same gesture does not resend the command.
- **Local-network prototype.** The receiver accepts packets without authentication. Use it on a trusted network; it is not designed for internet exposure.
- **Limited recognition/control logic.** No project-specific confidence threshold or gesture debounce is configured. Only three recognized categories control the car; other model categories have no mapped action.
- **Hardware-dependent setup.** Dependency installation alone is insufficient: I2C configuration, wiring, compatible drivers and power are required. The vision requirements file does not list the `smbus` dependency used by the car driver.

These limitations describe the checked-in code. They are not claims that particular failure scenarios or hardware configurations have been experimentally validated.

## LED and HaGRID experiments

The LED files preserve an earlier stage of the project. `gesture_test.py` sends `PALM`, `FIST` and `UP`, matching `led_test.py`'s three-LED outputs on BCM pins 17, 27 and 22. It also performs a `raspberrypi.local` lookup even though `--pi-ip` is required, so that experiment has an additional hostname-resolution dependency. `led_server.py` expects `ON`/`OFF` instead and is not a matching receiver for those gesture labels.

Srija explored a more robust model using HaGRID to support additional gesture inputs. This exploratory work was the furthest the team progressed toward expanding recognition; it was not integrated into the final working three-gesture car demo.

The included HaGRID directory contains a separate dataset/model workflow. Its training instructions and published dataset results should not be interpreted as SignWave's own model training or evaluation. See its [README](../hagrid_model/README.md) and license documents for that material.

## Team

The original project documentation lists:

- **Software:** Srija, Chibueze and Sarah.
- **Electronics and hardware:** Hongyi and James.

Srija also led the HaGRID-based exploration of expanded gesture recognition. The remaining credits are team-level; a detailed breakdown of other individual contributions is not documented.

## Possible next steps

- Add a Pi-side command timeout and controller-side stop-on-exit behaviour.
- Add acknowledgement/retry or heartbeat handling, plus gesture confidence/debounce controls.
- Document the actual hardware, wiring, verified environment and demonstration procedure.
- Measure recognition performance and command latency before making quantitative claims.

These are proposed improvements, not implemented features.

## Attribution and licensing

The main controller uses MediaPipe and OpenCV. HaGRID material retains its own documentation and license files. No top-level license for SignWave's project-specific code is currently included; an educational purpose statement alone does not grant a reuse license.
