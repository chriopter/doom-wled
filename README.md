# 3D FPS Game on WLED Matrix

Stream a playable retro-style FPS game to your 16x8 WLED matrix!

## Features

- **Playable on PC**: Full keyboard controls with Arrow Keys and WASD
- **Live Preview**: See the game in a window on your PC
- **Real-time Streaming**: Simultaneously streams to your WLED matrix
- **Raycasting Engine**: Classic 3D rendering with pixel art weapon
- **Shooting**: Fire your weapon with muzzle flash effects

## Quick Start

```bash
# Use the launcher (auto-creates venv and installs dependencies)
./play.sh
```

Or manually:
```bash
source doom_venv/bin/activate
python3 wled_game.py
```

## Controls

- **Arrow Keys** or **WASD**: Move forward/backward/strafe
- **Left/Right Arrows**: Rotate view
- **SPACE**: Shoot weapon
- **ESC**: Quit game

## Calibration (IMPORTANT!)

If your display looks wrong (two 8x8 panels), run calibration first:

```bash
source doom_venv/bin/activate
python3 calibrate_wled.py
```

This tests 5 different wiring patterns with visual tests. Pick the one that looks correct!

## Files

- `wled_game.py` - Main 3D FPS game with raycaster and weapon
- `play.sh` - Launcher script (auto-setup)
- `calibrate_wled.py` - Matrix calibration tool
- `test_wled_mapping.py` - LED mapping test tool

## Configuration

Edit the top of `wled_game.py` to change:
- `WLED_IP`: Your WLED device IP (default: 192.168.30.119)
- `MATRIX_WIDTH` / `MATRIX_HEIGHT`: Matrix dimensions (default: 16x8)
- `SCALE`: Window scale factor (default: 3x = 960x600 window)

## Troubleshooting

**Can't connect to WLED:**
- Verify WLED is at http://192.168.30.119
- Check matrix is configured as 16x8 in WLED settings

**Game runs slow:**
- Reduce window scale in the code (change SCALE = 2)
- Lower WLED streaming FPS (change wled_frame_time)

**Matrix colors look wrong:**
- Check if your matrix uses a different wiring pattern
- Try adjusting the `rgb_to_wled_index()` function

## How It Works

1. Renders a 320x200 Doom-like 3D view using raycasting
2. Displays scaled view (960x600) in pygame window
3. Downscales to 16x8 using high-quality Lanczos resampling
4. Streams RGB data to WLED via JSON API at ~20 FPS
5. Handles zigzag matrix wiring pattern automatically

Enjoy your 3D FPS game on the LED matrix!
