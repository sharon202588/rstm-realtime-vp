"""No-network tests for the Doubao protocol adapters."""

import asyncio
import json

from doubao.rest_client import DoubaoRESTClient
from doubao.websocket_client import (
    DoubaoWebSocketClient,
    EVENT_ID_TO_NAME,
    EVENT_NAME_TO_ID,
    NO_COMPRESSION,
)


class CapturingWebSocketClient(DoubaoWebSocketClient):
    def __init__(self):
        super().__init__(realtime_app_id="app", realtime_access_key="key")
        self.websocket = object()
        self.requests = []

    async def _send_full_request(self, event_id, payload, session_id=None, **kwargs):
        self.requests.append((event_id, payload, session_id, kwargs))


def test_realtime_event_map_includes_lifecycle_and_chat_end():
    assert EVENT_ID_TO_NAME[50] == "ConnectionStarted"
    assert EVENT_ID_TO_NAME[150] == "SessionStarted"
    assert EVENT_ID_TO_NAME[152] == "SessionFinished"
    assert EVENT_ID_TO_NAME[251] == "ConfigUpdated"
    assert EVENT_ID_TO_NAME[559] == "ChatEnded"
    assert EVENT_NAME_TO_ID["UpdateConfig"] == 201


def test_dialog_id_is_nested_in_start_session_dialog_payload():
    async def scenario():
        client = CapturingWebSocketClient()
        await client.start_session(
            system_prompt="patient",
            speaking_style="concerned",
            end_smooth_window_ms=1500,
            enable_custom_vad=True,
            dialog_id="dialog-123",
        )

        _, payload, _, _ = client.requests[-1]
        assert payload["dialog"]["dialog_id"] == "dialog-123"
        assert "dialog_id" not in payload
        assert payload["asr"]["extra"] == {
            "end_smooth_window_ms": 1500,
            "enable_custom_vad": True,
        }

    asyncio.run(scenario())


def test_update_config_sends_full_uncompressed_session_config():
    async def scenario():
        client = CapturingWebSocketClient()
        client.session_id = "session-123"
        tts_config = {
            "speaker": "zh_male_yunzhou_jupiter_bigtts",
            "audio_config": {"sample_rate": 24000},
        }

        await client.update_config(
            bot_name="RSTM-SP Patient",
            system_role="Stable patient profile",
            speaking_style="Level 4",
            dialog_id="dialog-123",
            tts_config=tts_config,
        )

        event_id, payload, session_id, options = client.requests[-1]
        assert event_id == 201
        assert session_id == "session-123"
        assert payload == {
            "dialog": {
                "bot_name": "RSTM-SP Patient",
                "system_role": "Stable patient profile",
                "speaking_style": "Level 4",
                "dialog_id": "dialog-123",
            },
            "tts": tts_config,
        }
        assert options["compression_type"] == NO_COMPRESSION

    asyncio.run(scenario())


def test_grade_prompt_parses_plain_and_fenced_json():
    client = DoubaoRESTClient(api_key="test")
    expected = {"final_cpas_score": 2, "reasoning": "clear"}

    for content in (json.dumps(expected), f"```json\n{json.dumps(expected)}\n```"):
        client.chat_completion = lambda **kwargs: {
            "choices": [{"message": {"content": content}}]
        }
        assert client.grade_prompt("prompt") == expected
