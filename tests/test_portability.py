"""Contracts for moving the application folder to another Windows computer."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).parent.parent
START_CMD = (ROOT / "start_ui.cmd").read_text(encoding="utf-8")
BOOTSTRAP = ROOT / "scripts" / "bootstrap_ui.ps1"
RUNTIME_REQUIREMENTS = ROOT / "requirements-runtime.txt"


def test_source_launcher_delegates_to_portable_bootstrapper():
    assert 'bootstrap_ui.ps1' in START_CMD
    assert '%~dp0' in START_CMD
    assert 'F:\\' not in START_CMD


def test_bootstrapper_rebuilds_the_environment_and_installs_runtime_dependencies():
    script = BOOTSTRAP.read_text(encoding="utf-8")
    assert '-m venv' in script
    assert '--clear' in script
    assert 'requirements-runtime.txt' in script
    assert '.rstm-runtime.sha256' in script
    assert 'ui_server.py' in script
    assert 'F:\\RSTM-SP' not in script


def test_runtime_requirements_exclude_development_and_native_microphone_packages():
    requirements = RUNTIME_REQUIREMENTS.read_text(encoding="utf-8")
    assert 'requests' in requirements
    assert 'websockets==12.0' in requirements
    assert 'python-dotenv' in requirements
    assert 'pytest' not in requirements
    assert 'sounddevice' not in requirements

def test_portable_builder_bundles_runtime_resources_and_external_configuration():
    script = (ROOT / "scripts" / "build_portable.ps1").read_text(encoding="utf-8")
    assert "PyInstaller" in script
    assert 'ui\\static' in script
    assert 'specs' in script
    assert 'start_portable.cmd' in script
    assert 'Copy-Item -LiteralPath $envPath' in script
    assert 'logs' not in script


def test_portable_launcher_runs_the_bundled_executable_from_its_own_folder():
    launcher = (ROOT / "packaging" / "start_portable.cmd").read_text(encoding="utf-8")
    assert '%~dp0' in launcher
    assert 'RealtimeVoiceVP.exe' in launcher
    assert '.venv' not in launcher
    assert 'python' not in launcher.lower()


def test_ui_server_loads_credentials_from_the_writable_application_root():
    source = (ROOT / "ui_server.py").read_text(encoding="utf-8")
    assert 'APPLICATION_ROOT / ".env"' in source

def test_powershell_scripts_parse_on_windows_powershell():
    for relative_path in ("scripts/bootstrap_ui.ps1", "scripts/build_portable.ps1"):
        command = (
            "[void][scriptblock]::Create("
            f"[IO.File]::ReadAllText('{ROOT / relative_path}'))"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert completed.returncode == 0, completed.stderr

def test_powershell_entry_scripts_are_windows_powershell_safe_encoded():
    for relative_path in ("scripts/bootstrap_ui.ps1", "scripts/build_portable.ps1"):
        raw = (ROOT / relative_path).read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf") or all(byte < 128 for byte in raw)


def _next_release_version(release_root: Path) -> str:
    helper = ROOT / "scripts" / "release_version.ps1"
    command = (
        f". '{helper}'; "
        f"Get-NextReleaseVersion -ReleaseRoot '{release_root}'"
    )
    completed = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def test_release_versions_start_at_one_and_increment_the_latest_patch(tmp_path):
    assert _next_release_version(tmp_path) == "1.0.0"
    (tmp_path / "RealtimeVoiceVP V1.0.0").mkdir()
    (tmp_path / "RealtimeVoiceVP V1.0.9").mkdir()
    (tmp_path / "RealtimeVoiceVP draft").mkdir()
    assert _next_release_version(tmp_path) == "1.0.10"


def test_builder_publishes_new_versioned_sibling_folders_without_overwriting():
    script = (ROOT / "scripts" / "build_portable.ps1").read_text(encoding="utf-8")
    assert 'release_version.ps1' in script
    assert 'RealtimeVoiceVP V$Version' in script
    assert 'VERSION.txt' in script
    assert 'ReleaseRoot' in script
    assert 'Split-Path -Parent $ProjectRoot' in script
    assert 'OutputRoot = "portable"' not in script