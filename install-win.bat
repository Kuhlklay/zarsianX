@echo off
setlocal EnableDelayedExpansion

REM Find Python executable
where python3 >nul 2>&1 && set PYTHON_BIN=python3
if not defined PYTHON_BIN (
    where python >nul 2>&1 && set PYTHON_BIN=python
)
if not defined PYTHON_BIN (
    echo Python not installed. Install python or python3!
    exit /b 1
)

REM Create venv if it doesn't exist
%PYTHON_BIN% -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo Error whilst creating virtual environment.
    exit /b 1
)

REM Activate venv
call .venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo Error whilst activating virtual environment.
    exit /b 1
)

REM Install required packages
.venv\Scripts\pip.exe install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo Error whilst upgrading pip.
    exit /b 1
)
.venv\Scripts\pip.exe install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Error whilst installing requirements.
    exit /b 1
)
echo Installation complete, you can now execute 'launch-win.bat' to start the game.

endlocal