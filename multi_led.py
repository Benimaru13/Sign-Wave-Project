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
# GPIO pin your LED is wired to
LED_PINS = [17,27,22]
# Must match the Mac script
PORT    = 5005  

def setup_gpio():
    # Use BCM pin numbering (matches GPIO 17 label)
    GPIO.setmode(GPIO.BCM)        
    
    for pin in LED_PINS:
        GPIO.setup(pin, GPIO.OUT) # Set pin as output
        GPIO.output(pin, GPIO.LOW) # Start with LED off
        print(f"  GPIO {pin} ready — LED off")


def main():
    setup_gpio()

    # UDP socket — listen on all network interfaces
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))

    print(f"\n LED Server listening on port {PORT}")
    print(f"   Ctrl+C to quit\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            command = data.decode().strip()
            print(f"  Received '{command}' from {addr[0]}")

            for pin in LED_PINS:
                GPIO.output(pin, GPIO.LOW)

            if command == "PALM":
                GPIO.output(LED_PINS[0], GPIO.HIGH)
                print("  LED 1")
            elif command == "FIST":
                GPIO.output(LED_PINS[1], GPIO.HIGH)
                print("  LED 2")
            elif command == "UP":
                GPIO.output(LED_PINS[2], GPIO.HIGH)
                print("  LED 3")
            elif command == "DOWN":
                print("  All LEDs OFF")
            else:
                print(f"  ⚠ Unknown command: {command}")

    except KeyboardInterrupt:
        print("\n  Shutting down...")
    finally:
        for pin in LED_PINS:
            # Make sure LED is off on exit
            GPIO.output(pin, GPIO.LOW)  
        GPIO.cleanup()                  # Release GPIO pins
        sock.close()


if __name__ == '__main__':
    main()
