#!/bin/bash
cd "$(dirname "$0")"

# Check if venv exists, if not create it
if [ ! -d "doom_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv doom_venv
    source doom_venv/bin/activate
    echo "Installing dependencies..."
    pip install pillow numpy requests mss pygame
else
    source doom_venv/bin/activate
fi

python3 wled_game.py
