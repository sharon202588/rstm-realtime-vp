"""Tests for server-side model and realtime endpoint configuration."""

from doubao.rest_client import DoubaoRESTClient
from doubao.websocket_client import DoubaoWebSocketClient


def test_clients_read_model_and_endpoint_from_environment(monkeypatch):
    monkeypatch.setenv("DOUBAO_GRADER_MODEL", "grader-endpoint-id")
    monkeypatch.setenv(
        "DOUBAO_API_ENDPOINT",
        "wss://openspeech.bytedance.com/api/v3/realtime/dialogue",
    )

    grader = DoubaoRESTClient(api_key="key")
    voice = DoubaoWebSocketClient(realtime_app_id="app", realtime_access_key="access")

    assert grader.model == "grader-endpoint-id"
    assert voice.endpoint.endswith("/api/v3/realtime/dialogue")

def test_grader_default_uses_active_seed_2_lite(monkeypatch):
    monkeypatch.delenv("DOUBAO_GRADER_MODEL", raising=False)
    grader = DoubaoRESTClient(api_key="key")
    assert grader.model == "doubao-seed-2-0-lite-260428"
