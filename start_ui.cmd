@echo off
setlocal
cd /d "%~dp0"

netstat -ano | findstr /R /C:"127.0.0.1:7860 .*LISTENING" >nul
if not errorlevel 1 (
    start "" "http://127.0.0.1:7860/"
    exit /b 0
)

if not exist ".venv\Scripts\python.exe" (
    echo The local Python environment was not found:
    echo %CD%\.venv\Scripts\python.exe
    echo.
    echo Install the project dependencies before starting the interface.
    pause
    exit /b 1
)

start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:7860/'"
title Realtime Voice Virtual Patient
".venv\Scripts\python.exe" "ui_server.py"

if errorlevel 1 (
    echo.
    echo The local interface stopped with an error.
    pause
)
