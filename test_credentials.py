"""
API key configuration checker for the RSTM-SP workspace.

This script verifies that the required Doubao/ARK credentials are present so
that automated tests and runtime components can authenticate successfully.

If run as a script, it exits with 0 on success or 1 on failure. Importing the
module allows other test scripts to reuse the credential check without raising
SystemExit.
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


def load_environment() -> None:
    """Load .env variables if python-dotenv is available."""
    if load_dotenv is not None:
        load_dotenv()
        print("Loaded .env file")
    else:
        print("python-dotenv is not available, using existing environment variables")
        print("  Install with: pip install python-dotenv")


def report_file_status() -> None:
    """Report whether a .env file exists in the working directory."""
    env_file = Path(".env")
    if env_file.exists():
        print(f"Found .env file at {env_file.absolute()}")
        print("  Tip: keep .env inside .gitignore to avoid committing secrets")
    else:
        print("No .env file found")
        print("  Recommend creating .env and populating it with required keys")


def check_api_credentials() -> bool:
    """Check that required credentials exist in the environment."""
    keys = {
        "ARK_API_KEY": os.getenv("ARK_API_KEY"),
        "DOUBAO_REALTIME_APP_ID": os.getenv("DOUBAO_REALTIME_APP_ID"),
        "DOUBAO_REALTIME_ACCESS_KEY": os.getenv("DOUBAO_REALTIME_ACCESS_KEY"),
    }

    print("\n" + "=" * 60)
    print("API key configuration check")
    print("=" * 60)

    results = []
    for name, value in keys.items():
        if value:
            masked = value[:20] + "..." if len(value) > 20 else value
            print(f"[OK] {name}: {masked}")
            results.append(True)
        else:
            print(f"[MISSING] {name}")
            results.append(False)

    report_file_status()

    success = all(results)
    if success:
        print("\nAll credentials are configured.")
    else:
        print("\nSome credentials are missing. Please configure them as follows:")
        print("1. Create a .env file with the entries from env.example (preferred)")
        print("2. Or set the values via system environment variables")
        print("3. Consult docs/api_credentials_setup.md for details")

    return success


def main() -> int:
    """Entry point when running as a script."""
    load_environment()
    success = check_api_credentials()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
