import asyncio

"""Tests for the official realtime dialogue authentication contract."""

from doubao.websocket_client import DoubaoWebSocketClient


def test_realtime_credentials_use_official_dialogue_headers(monkeypatch):
    monkeypatch.setenv("DOUBAO_REALTIME_APP_ID", "realtime-app-id")
    monkeypatch.setenv("DOUBAO_REALTIME_ACCESS_KEY", "realtime-access-key")

    client = DoubaoWebSocketClient()
    headers = client._headers()

    assert headers["X-Api-App-ID"] == "realtime-app-id"
    assert headers["X-Api-Access-Key"] == "realtime-access-key"
    assert headers["X-Api-App-Key"] == client.FIXED_APP_KEY
    assert headers["X-Api-Resource-Id"] == "volc.speech.dialog"
    assert "X-Api-Key" not in headers


def test_old_environment_variable_names_are_not_accepted(monkeypatch):
    monkeypatch.delenv("DOUBAO_REALTIME_APP_ID", raising=False)
    monkeypatch.delenv("DOUBAO_REALTIME_ACCESS_KEY", raising=False)
    monkeypatch.setenv("DOUBAO_APP_ID", "old-app-id")
    monkeypatch.setenv("DOUBAO_APP_KEY", "old-access-token")

    try:
        DoubaoWebSocketClient()
    except ValueError as exc:
        assert "DOUBAO_REALTIME_APP_ID" in str(exc)
    else:
        raise AssertionError("old realtime credential variables must not be accepted")

def test_each_physical_connection_uses_a_new_connect_id(monkeypatch):
    class Socket:
        async def close(self):
            return None

    captured_ids = []

    async def fake_connect(endpoint, **kwargs):
        captured_ids.append(kwargs["extra_headers"]["X-Api-Connect-Id"])
        return Socket()

    async def scenario():
        monkeypatch.setattr("doubao.websocket_client.websockets.connect", fake_connect)
        client = DoubaoWebSocketClient(
            realtime_app_id="realtime-app-id",
            realtime_access_key="realtime-access-key",
        )
        await client.connect()
        await client.disconnect()
        await client.connect()
        await client.disconnect()

    asyncio.run(scenario())
    assert len(captured_ids) == 2
    assert captured_ids[0] != captured_ids[1]