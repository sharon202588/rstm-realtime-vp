@echo off
setlocal
cd /d "%~dp0"
title Build Realtime Voice VP Release
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_portable.ps1"
if errorlevel 1 (
    echo.
    echo The release build failed. Review the message above.
    pause
    exit /b 1
)
echo.
echo The new version folder is ready. Its location is shown above.
pause