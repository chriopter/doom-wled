#!/usr/bin/env python3
"""
Test to understand how WLED 2D configuration maps LED indices
"""

import requests
import time

WLED_IP = "192.168.30.119"
WLED_API_URL = f"http://{WLED_IP}/json/state"

def send_pattern(leds):
    """Send LED pattern to WLED"""
    try:
        payload = {
            "on": True,
            "bri": 255,
            "seg": [{"id": 0, "i": leds}]
        }
        response = requests.post(WLED_API_URL, json=payload, timeout=1)
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def clear_matrix():
    """Turn off all LEDs"""
    leds = [[0, 0, 0] for _ in range(128)]
    send_pattern(leds)

print("="*60)
print("WLED 2D Mapping Test")
print("="*60)

# FIRST TEST: Display "OK" text spanning the screen
print("\n[QUICK TEST] Displaying 'OK' text across screen")
print("If this looks correct, we're done!\n")
input("Press Enter to show 'OK'...")

# Simple 5x7 bitmap font for "O" and "K"
FONT_O = [
    "01110",
    "10001",
    "10001",
    "10001",
    "10001",
    "10001",
    "01110",
]

FONT_K = [
    "10010",
    "10100",
    "11000",
    "11000",
    "10100",
    "10010",
    "10001",
]

leds = [[0, 0, 0] for _ in range(128)]

# Draw "O" starting at column 2
for y in range(7):
    for x in range(5):
        if FONT_O[y][x] == "1":
            led_idx = (y + 1) * 16 + (x + 2)
            if led_idx < 128:
                leds[led_idx] = [0, 255, 0]  # GREEN

# Draw "K" starting at column 9
for y in range(7):
    for x in range(5):
        if FONT_K[y][x] == "1":
            led_idx = (y + 1) * 16 + (x + 9)
            if led_idx < 128:
                leds[led_idx] = [0, 255, 0]  # GREEN

send_pattern(leds)

print("\n" + "="*60)
print("You should see the letters 'OK' in GREEN")
print("spanning across both panels")
print("="*60)

final_answer = input("\nDo you see 'OK' clearly? (y/n): ").strip().lower()

clear_matrix()

if final_answer in ['y', 'yes']:
    print("\n" + "="*60)
    print("✅ SUCCESS!")
    print("="*60)
    print("\nWLED 2D mapping works perfectly!")
    print("The fix is simple: LED index = y * 16 + x")
    print("\nGame file (wled_game.py) is ready to use!")
    exit(0)

# If text didn't work, run detailed tests
print("\n" + "="*60)
print("Running detailed diagnostic tests...")
print("="*60)

# Test 1: Sequential LED indices
print("\n[Test 1] Lighting LEDs 0-15 in RED")
print("Should light the FIRST ROW")
input("Press Enter...")

leds = [[0, 0, 0] for _ in range(128)]
for i in range(16):
    leds[i] = [255, 0, 0]
send_pattern(leds)

print("\nWhat do you see?")
answer1 = input("Describe: ")

clear_matrix()
time.sleep(1)

# Test 2: Second row
print("\n[Test 2] Lighting LEDs 16-31 in GREEN")
print("Should light the SECOND ROW")
input("Press Enter...")

leds = [[0, 0, 0] for _ in range(128)]
for i in range(16, 32):
    leds[i] = [0, 255, 0]
send_pattern(leds)

print("\nWhat do you see?")
answer2 = input("Describe: ")

clear_matrix()
time.sleep(1)

# Test 3: Last row
print("\n[Test 3] Lighting LEDs 112-127 in BLUE")
print("Should light the BOTTOM ROW")
input("Press Enter...")

leds = [[0, 0, 0] for _ in range(128)]
for i in range(112, 128):
    leds[i] = [0, 0, 255]
send_pattern(leds)

print("\nWhat do you see?")
answer3 = input("Describe: ")

clear_matrix()

print("\n" + "="*60)
print("Please share these results so we can debug further")
print("="*60)
