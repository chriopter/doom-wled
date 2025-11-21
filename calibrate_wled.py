#!/usr/bin/env python3
"""
WLED Matrix Calibration Tool - For 2-Panel Setup
Panel 0: Top-Left start, 8x8, Horizontal Serpentine
Panel 1: Bottom-Right start, 8x8, Horizontal Serpentine
"""

import requests
import time

WLED_IP = "192.168.30.119"
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 8
WLED_API_URL = f"http://{WLED_IP}/json/state"

def rgb_to_wled_index(x, y):
    """Convert x,y coordinates to WLED LED index for your 2-panel config"""
    if x < 8:
        # Panel 0: Top-left serpentine
        if y % 2 == 0:
            return y * 8 + x
        else:
            return y * 8 + (7 - x)
    else:
        # Panel 1: Bottom-right serpentine
        px = x - 8
        py_from_bottom = 7 - y
        if py_from_bottom % 2 == 0:
            local_index = py_from_bottom * 8 + (7 - px)
        else:
            local_index = py_from_bottom * 8 + px
        return 64 + local_index

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

def show_xy_pattern(pattern_func):
    """Show a pattern using x,y coordinates"""
    leds = [[0, 0, 0] for _ in range(128)]
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            color = pattern_func(x, y)
            if color:
                idx = rgb_to_wled_index(x, y)
                leds[idx] = color
    send_pattern(leds)

def ask_question(question):
    """Ask yes/no question"""
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        print("Please answer y or n")

def main():
    print("="*60)
    print("WLED Matrix Calibration Tool")
    print(f"Matrix: {MATRIX_WIDTH}x{MATRIX_HEIGHT} @ {WLED_IP}")
    print("="*60)
    print("\nTesting your 2-panel configuration...")
    print("Panel 0: Top-Left, 8x8, Horizontal Serpentine")
    print("Panel 1: Bottom-Right, 8x8, Horizontal Serpentine")
    print("="*60 + "\n")

    # Test 1: Four corners
    print("[Test 1] Four corner test...")
    def corners(x, y):
        if x == 0 and y == 0: return [255, 0, 0]      # RED top-left
        if x == 15 and y == 0: return [0, 255, 0]     # GREEN top-right
        if x == 0 and y == 7: return [0, 0, 255]      # BLUE bottom-left
        if x == 15 and y == 7: return [255, 255, 0]   # YELLOW bottom-right
        return None

    show_xy_pattern(corners)
    time.sleep(2)

    print("\nYou should see:")
    print("  RED = Top-Left")
    print("  GREEN = Top-Right")
    print("  BLUE = Bottom-Left")
    print("  YELLOW = Bottom-Right")

    q1 = ask_question("\nAre ALL four corners correctly positioned?")

    clear_matrix()
    time.sleep(1)

    # Test 2: Horizontal gradient
    print("\n[Test 2] Horizontal gradient test...")
    def gradient(x, y):
        if x < 5:
            return [255, 0, 0]  # RED left
        elif x < 11:
            return [0, 255, 0]  # GREEN middle
        else:
            return [0, 0, 255]  # BLUE right

    show_xy_pattern(gradient)
    time.sleep(2)

    print("\nYou should see:")
    print("  RED on LEFT → GREEN in MIDDLE → BLUE on RIGHT")

    q2 = ask_question("\nDo you see the gradient from LEFT to RIGHT correctly?")

    clear_matrix()
    time.sleep(1)

    # Test 3: Vertical stripes (each column different)
    print("\n[Test 3] Vertical stripe test...")
    def stripes(x, y):
        if x % 4 == 0:
            return [255, 0, 0]  # RED
        elif x % 4 == 1:
            return [0, 255, 0]  # GREEN
        elif x % 4 == 2:
            return [0, 0, 255]  # BLUE
        else:
            return [255, 255, 0]  # YELLOW

    show_xy_pattern(stripes)
    time.sleep(2)

    print("\nYou should see:")
    print("  Vertical stripes: RED-GREEN-BLUE-YELLOW repeating")

    q3 = ask_question("\nDo you see VERTICAL stripes (not horizontal)?")

    clear_matrix()
    time.sleep(1)

    # Test 4: Top and bottom rows
    print("\n[Test 4] Top and bottom row test...")
    def rows(x, y):
        if y == 0:
            return [255, 0, 255]  # MAGENTA top
        elif y == 7:
            return [0, 255, 255]  # CYAN bottom
        return None

    show_xy_pattern(rows)
    time.sleep(2)

    print("\nYou should see:")
    print("  MAGENTA = Top row (all 16 LEDs)")
    print("  CYAN = Bottom row (all 16 LEDs)")

    q4 = ask_question("\nAre top and bottom rows correct?")

    clear_matrix()
    time.sleep(1)

    # Test 5: Left and right panels separate
    print("\n[Test 5] Panel separation test...")
    def panels(x, y):
        if x < 8:
            return [255, 0, 0]  # RED left panel
        else:
            return [0, 0, 255]  # BLUE right panel

    show_xy_pattern(panels)
    time.sleep(2)

    print("\nYou should see:")
    print("  LEFT panel = RED")
    print("  RIGHT panel = BLUE")

    q5 = ask_question("\nAre the two panels clearly separated?")

    clear_matrix()
    time.sleep(1)

    # Final Test: Big "OK" pattern or checkerboard
    print("\n[FINAL TEST] Checkerboard pattern...")
    def checkerboard(x, y):
        if (x + y) % 2 == 0:
            return [255, 255, 255]  # WHITE
        else:
            return [255, 0, 0]  # RED

    show_xy_pattern(checkerboard)
    time.sleep(3)

    print("\nYou should see:")
    print("  A perfect CHECKERBOARD pattern (white and red squares)")
    print("  Pattern should be continuous across both panels")

    q6 = ask_question("\nDoes the checkerboard look perfect (no weird breaks or shifts)?")

    clear_matrix()

    # Results
    print("\n" + "="*60)
    print("CALIBRATION RESULTS")
    print("="*60)

    all_passed = q1 and q2 and q3 and q4 and q5 and q6

    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("\nYour wled_game.py should work correctly.")
        print("The rgb_to_wled_index function is properly configured.")
        print("\nRun: ./play.sh")
    else:
        print("\n❌ Some tests failed:")
        if not q1: print("  - Four corners test failed")
        if not q2: print("  - Horizontal gradient test failed")
        if not q3: print("  - Vertical stripes test failed")
        if not q4: print("  - Top/bottom rows test failed")
        if not q5: print("  - Panel separation test failed")
        if not q6: print("  - Checkerboard test failed")

        print("\n⚠️  The mapping function needs adjustment.")
        print("Run the tests again and describe exactly what you see.")

if __name__ == "__main__":
    main()
