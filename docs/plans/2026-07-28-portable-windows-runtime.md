# Portable Windows Runtime Implementation Plan

**Goal:** Make the realtime virtual-patient project runnable after copying one folder to another Windows 10/11 64-bit computer.

**Architecture:** Keep a source-folder launcher that bootstraps a local virtual environment when Python is available, and add a PyInstaller one-folder build for computers without Python. Resolve writable application data from the executable folder and bundled static resources from the PyInstaller resource folder. Persist custom patient profiles to a JSON file inside the copied folder while retaining browser storage as an offline fallback.

**Tech stack:** Python, PowerShell, Windows batch, PyInstaller, vanilla JavaScript, pytest.

## Global Constraints

- Bind HTTP and WebSocket services to localhost only.
- Never print API credential values.
- Keep `.env` external to the executable and copy it only into a trusted portable folder.
- Default audio retention remains disabled.
- Preserve the frozen default patient profile.
- Target Windows 10/11 64-bit.

## Tasks

1. Add `requirements-runtime.txt` containing only UI runtime dependencies.
2. Add a PowerShell bootstrapper and make `start_ui.cmd` delegate to it.
3. Add tested runtime path resolution for source and frozen execution.
4. Add a local JSON patient-profile store and HTTP API, with browser local storage fallback.
5. Add PyInstaller build scripts and a portable launcher.
6. Build the one-folder artifact and copy `.env` without exposing its values.
7. Start a copied artifact on alternate ports and verify HTTP, WebSocket, static resources, and patient-profile persistence.
8. Run the full Python and Node test suites and document migration limitations.
