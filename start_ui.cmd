@echo off
setlocal
cd /d "%~dp0"
title Realtime Voice Virtual Patient
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap_ui.ps1"
if errorlevel 1 (
    echo.
    echo The interface could not be started. Review the message above.
    pause
)