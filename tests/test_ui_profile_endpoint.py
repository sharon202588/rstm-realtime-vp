"""Tests for the local researcher-only patient profile endpoint."""

import json
from pathlib import Path
from urllib.request import Request, urlopen

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

def test_static_ui_disables_cache_and_versions_javascript_assets():
    server = LocalVoiceUIServer(http_port=0, ws_port=0)
    server.start_http()
    try:
        port = server._http_server.server_address[1]
        with urlopen(f"http://127.0.0.1:{port}/") as response:
            assert response.status == 200
            assert response.headers["Cache-Control"] == "no-store"
            html = response.read().decode("utf-8")

        assert '/ui-model.js?v=' in html
        assert '/app.js?v=' in html
    finally:
        server.stop_http()

def test_patient_templates_persist_in_the_application_folder(tmp_path):
    server = LocalVoiceUIServer(
        http_port=0,
        ws_port=0,
        resource_root=PROJECT_ROOT,
        application_root=tmp_path,
    )
    server.start_http()
    try:
        port = server._http_server.server_address[1]
        url = f"http://127.0.0.1:{port}/api/patient-templates"
        with urlopen(url) as response:
            assert json.loads(response.read().decode("utf-8")) == {"templates": []}

        template = {
            "id": "custom-portable-http",
            "name": "Portable HTTP profile",
            "identity_background": "",
            "clinical_facts": "Biopsy results require discussion.",
            "family_social_context": "",
            "knowledge_concerns": "",
            "disclosure_boundaries": "",
            "opening_presentation": "",
            "response_boundaries": "",
        }
        request = Request(
            url,
            data=json.dumps({"templates": [template]}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urlopen(request) as response:
            assert response.status == 200

        with urlopen(url) as response:
            assert json.loads(response.read().decode("utf-8")) == {
                "templates": [template]
            }
        assert (tmp_path / "data" / "patient_templates.json").exists()
    finally:
        server.stop_http()
