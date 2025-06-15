@echo off
setlocal

:: Suche nach Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python ist nicht installiert.
    pause
    exit /b 1
)

:: Erstelle venv
python -m venv .venv

:: Aktiviere venv
call .venv\Scripts\activate

:: Installiere Abhängigkeiten
python -m pip install --upgrade pip
pip install -r requirements.txt