#!/bin/bash
set -e

# Finde passenden Python-Befehl
PYTHON_BIN=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON_BIN" ]; then
    echo "Python ist nicht installiert."
    exit 1
fi

# Erstelle virtuelle Umgebung
$PYTHON_BIN -m venv .venv

# Aktiviere venv
source .venv/bin/activate

# Installiere Abhängigkeiten
pip install --upgrade pip
pip install -r requirements.txt

# Starte Hauptprogramm
chmod +x main.py