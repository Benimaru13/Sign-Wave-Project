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
from motor import Ordinary_Car
PWD = Ordinary_Car()

# Create motor controller object
car = Ordinary_Car()

# UDP port (must match sender device)
PORT = 5005


def main():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Listen on all network interfaces
    sock.bind(("0.0.0.0", PORT))

    print(f"\nCar Controller Server running on port {PORT}")
    print("Waiting for commands...\n")

    try:
        while True:
            # Wait for incoming UDP message
            data, addr = sock.recvfrom(1024)

            # Convert bytes to string command
            command = data.decode().strip()

            print(f"Received '{command}' from {addr[0]}")

            # Handle movement commands
            if command == "FORWARD":
                car.set_motor_model(1000, 1000, 1000, 1000)
                print("Moving forward")

            elif command == "BACKWARD":
                car.set_motor_model(-1000, -1000, -1000, -1000)
                print("Moving backward")

            elif command == "OFF":
                car.set_motor_model(0, 0, 0, 0)
                print("Car stopped")

    except KeyboardInterrupt:
        # Allows safe exit with Ctrl+C
        print("\nShutting down...")

    finally:
        # Always stop motors before exiting
        car.set_motor_model(0, 0, 0, 0)
        sock.close()


if __name__ == "__main__":
    main()
