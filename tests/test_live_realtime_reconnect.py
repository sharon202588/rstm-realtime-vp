"""Opt-in live smoke test for Doubao physical WebSocket reconnection."""

import asyncio
import os

import pytest
from dotenv import load_dotenv

from doubao.websocket_client import DoubaoWebSocketClient


RUN_LIVE = os.getenv("RUN_LIVE_DOUBAO") == "1"


@pytest.mark.skipif(not RUN_LIVE, reason="set RUN_LIVE_DOUBAO=1 to call the live API")
def test_live_reconnect_preserves_dialog_context_after_active_audio():
    async def wait_for_session_started(client):
        while True:
            message = await asyncio.wait_for(client.receive_message(), timeout=15)
            if message.get("type") == "ERROR":
                pytest.fail(f"Doubao returned an error: {message.get('payload')}")
            if message.get("type") == "SessionStarted":
                return message

    async def scenario():
        load_dotenv(override=True)
        client = DoubaoWebSocketClient()
        dialog_id = None
        connect_ids = []
        started_dialog_ids = []

        for _ in range(2):
            await client.connect()
            connect_ids.append(client.connect_id)
            try:
                await client.start_session(
                    system_prompt="你是一名用于医学沟通测试的虚拟患者。",
                    speaking_style="语气担忧、低落，但保持自然交流。",
                    input_mod="audio",
                    model="O",
                    end_smooth_window_ms=500,
                    dialog_id=dialog_id,
                )
                started = await wait_for_session_started(client)
                dialog_id = started.get("dialog_id") or dialog_id
                assert dialog_id
                started_dialog_ids.append(dialog_id)

                for _ in range(25):
                    await client.send_audio(b"\x00" * 640)
                    await asyncio.sleep(0.02)

                await client.finish_session()
                try:
                    await client.finish_connection()
                except Exception:
                    pass
            finally:
                await client.disconnect()

        assert connect_ids[0] != connect_ids[1]
        assert started_dialog_ids[0] == started_dialog_ids[1]

    asyncio.run(scenario())
