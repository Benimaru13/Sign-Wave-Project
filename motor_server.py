#!/usr/bin/env python3
"""
Raspberry Pi LED controller.
Listens for ON/OFF commands over UDP and controls an LED on GPIO 17.

Run this on the Pi:
    python3 led_server.py

Requirements (already on Pi OS):
    RPi.GPIO (built in to Raspberry Pi OS)
"""

import socket
import RPi.GPIO as GPIO
from motor import Ordinary_Car
PWD = Ordinary_Car()

# === CONFIGURATION ===
LED_PIN = 17    # GPIO pin your LED is wired to
PORT    = 5005  # Must match the Mac script

# def setup_gpio():
#     GPIO.setmode(GPIO.BCM)        # Use BCM pin numbering (matches GPIO 17 label)
#     GPIO.setup(LED_PIN, GPIO.OUT) # Set pin as output
#     GPIO.output(LED_PIN, GPIO.LOW) # Start with LED off
#     print(f"  GPIO {LED_PIN} ready — LED off")


def main():
    setup_gpio()

    # UDP socket — listen on all network interfaces
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))

    print(f"\n💡  LED Server listening on port {PORT}")
    print(f"   Open Palm  → Car moving forward")
    print(f"   Closed Fist → Car moving backward")
    print(f"   Ctrl+C to quit\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            command = data.decode().strip()
            print(f"  Received '{command}' from {addr[0]}")

            if command == "ON":
                # Change output
                PWD.set_motor_model(1000,1000,1000,1000)
                print("Car moving forward")
            elif command == "OFF":
                # Change output
                PWD.set_motor_model(-1000,-1000,-1000,-1000)
                print("Car moving backward")
            else:
                print(f"  ⚠ Unknown command: {command}")

    except KeyboardInterrupt:
        print("\n  Shutting down...")
    finally:
        PWD.set_motor_model(0,0,0,0)  # Make sure motors are off on exit
        # GPIO.cleanup()                  # Release GPIO pins
        sock.close()


if __name__ == '__main__':
    main()
