@echo off
setlocal
cd /d "%~dp0"

netstat -ano | findstr /R /C:"127.0.0.1:7860 .*LISTENING" >nul
if not errorlevel 1 (
    start "" "http://127.0.0.1:7860/"
    exit /b 0
)

start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:7860/'"
title Realtime Voice Virtual Patient
"%~dp0RealtimeVoiceVP.exe"
if errorlevel 1 (
    echo.
    echo The portable application stopped with an error.
    pause
)