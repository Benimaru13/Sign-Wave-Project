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
PORT    = 5005  # Must match the Mac script

def main():
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
        sock.close()


if __name__ == '__main__':
    main()
