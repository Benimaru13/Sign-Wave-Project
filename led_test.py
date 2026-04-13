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

# === CONFIGURATION ===
LED_PINS = [17,27,22]    # GPIO pin your LED is wired to
PORT    = 5005  # Must match the Mac script

def setup_gpio():
    GPIO.setmode(GPIO.BCM)        # Use BCM pin numbering (matches GPIO 17 label)
    GPIO.setup(LED_PINS, GPIO.OUT) # Set pin as output
    GPIO.output(LED_PINS, GPIO.LOW) # Start with LED off
    print(f"  GPIO {LED_PINS} ready — LED off")


def main():
    setup_gpio()

    # UDP socket — listen on all network interfaces
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))

    print(f"\n💡  LED Server listening on port {PORT}")
    print(f"   Ctrl+C to quit\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            command = data.decode().strip()
            print(f"  Received '{command}' from {addr[0]}")

            if command == "ON":
                GPIO.output(LED_PINS[0], GPIO.HIGH)
                print("  💡 LED ON")
            elif command == "OFF":
                GPIO.output(LED_PINS[0], GPIO.LOW)
                print("  💡 LED OFF")
            else:
                print(f"  ⚠ Unknown command: {command}")

    except KeyboardInterrupt:
        print("\n  Shutting down...")
    finally:
        GPIO.output(LED_PINS, GPIO.LOW)  # Make sure LED is off on exit
        GPIO.cleanup()                  # Release GPIO pins
        sock.close()


if __name__ == '__main__':
    main()
