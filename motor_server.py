#!/usr/bin/env python3
"""
Raspberry Pi Motor controller.
Listens for ON/OFF commands over UDP and controls a smart car's motors.

Run this on the Pi:
    python3 motor_server.py

Requirements (already on Pi OS):
    RPi.GPIO (built in to Raspberry Pi OS)
"""

import socket
#import RPi.GPIO as GPIO
from motor import Ordinary_Car
# Initialize the car object
PWD = Ordinary_Car()

# === CONFIGURATION ===
PORT    = 5005  # Must match the Mac script


def main():
   # UDP socket — listen on all network interfaces
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))

    print(f"\n Motor Server listening on port {PORT}")
    print(f"   Thumb Up (Like)  → Car moving forward")
    print(f"   Thumb Down (Dislike) → Car moving backward")
    print(f"   Palm together (stop) - Car stops:")
    print(f"   index, middle pointing left with thumb open (three_gun) - Car turns left")
    print(f"   index, middle pointing right with thumb open (three_gun) - Car turns right")
    print(f"   Ctrl+C to quit\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            command = data.decode().strip()
            print(f"  Received '{command}' from {addr[0]}")
            print(f"  Command bytes: {data}")  # DEBUG PRINT LINE

            
            if command == "FORWARD":
                # move forward
                PWD.set_motor_model(2000,2000,2000,2000)
                print("Car moving forward")

            elif command == "BACKWARD":
                # move backward
                PWD.set_motor_model(-2000,-2000,-2000,-2000)
                print("Car moving backward")
                
            elif command == "OFF":
                # turn off motors
                PWD.set_motor_model(0,0,0,0)
                print("Car stopped")

            elif command == "LEFT":
                # turn left
                PWD.set_motor_model(-2000,-2000,2000,2000)
                print("Car turning left")

            elif command == "RIGHT":
                # turn right
                PWD.set_motor_model(2000,2000,-2000,-2000)
                print("Car turning right")

    except KeyboardInterrupt:
        print("\n  Shutting down...")

    finally:
        # Make sure motors are off on exit
        PWD.set_motor_model(0,0,0,0)  
        sock.close()


if __name__ == '__main__':
    main()
