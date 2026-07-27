"""Tests for the local researcher-only patient profile endpoint."""

import json
from pathlib import Path
from urllib.request import urlopen

from ui.server import LocalVoiceUIServer


PROJECT_ROOT = Path(__file__).parent.parent


def test_patient_profile_endpoint_returns_the_frozen_profile_verbatim():
    server = LocalVoiceUIServer(http_port=0, ws_port=0)
    server.start_http()
    try:
        port = server._http_server.server_address[1]
        with urlopen(f"http://127.0.0.1:{port}/api/patient-profile") as response:
            assert response.status == 200
            assert response.headers.get_content_type() == "application/json"
            payload = json.loads(response.read().decode("utf-8"))

        expected = (PROJECT_ROOT / "specs" / "patient_profile.md").read_text(
            encoding="utf-8"
        )
        assert payload == {"profile": expected}
    finally:
        server.stop_http()
