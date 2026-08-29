"""Regression tests for browser disconnects during voice-session cleanup."""

import asyncio
import json

from websockets.exceptions import ConnectionClosedOK

import ui.server as server_module
from ui.server import LocalVoiceUIServer


class ClosingBrowser:
    def __init__(self):
        self.closed = False
        self.sent = []
        self.messages = [
            json.dumps(
                {
                    "command": "configure",
                    "participant_id": "P-disconnect",
                    "session_id": "S-disconnect",
                }
            ),
            json.dumps({"command": "start"}),
        ]

    def __aiter__(self):
        return self._messages()

    async def _messages(self):
        for message in self.messages:
            yield message
        self.closed = True

    async def send(self, payload):
        if self.closed:
            raise ConnectionClosedOK(None, None)
        self.sent.append(payload)


class CleanupSession:
    def __init__(self, config, ws_client, rest_client, event_sink):
        del config, ws_client, rest_client
        self.event_sink = event_sink
        self.is_started = False

    async def start(self):
        self.is_started = True

    async def stop(self):
        await self.event_sink(
            {
                "type": "audio",
                "retained": True,
                "files": ["clinician.wav", "patient.wav"],
            }
        )


def test_browser_disconnect_does_not_fail_session_cleanup(monkeypatch, tmp_path):
    monkeypatch.setattr(server_module, "RealtimeVoiceSession", CleanupSession)
    monkeypatch.chdir(tmp_path)
    browser = ClosingBrowser()

    asyncio.run(LocalVoiceUIServer()._handler(browser))

    assert browser.closed is True
