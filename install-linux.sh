#!/bin/bash
set -e

# Find python executable
PYTHON_BIN=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON_BIN" ]; then
    echo "Python not installed or not found in PATH. Install python or python3 and add to PATH!"
    exit 1
fi

# Create virtual environment
$PYTHON_BIN -m venv .venv

# Activate venv
source .venv/bin/activate

# Install required packages
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

chmod +x launch-linux.sh
chmod +x main.py

echo "Installation complete, you can now execute 'launch-linux.sh' to start the game."