"""Opt-in live smoke test for hot style update with reconnect fallback."""

import asyncio
import os

import pytest
from dotenv import load_dotenv

from core.realtime_voice_session import RealtimeVoiceSession, VoiceSessionConfig
from doubao.websocket_client import DoubaoWebSocketClient


RUN_LIVE = os.getenv("RUN_LIVE_DOUBAO") == "1"


class UnusedGrader:
    def grade_prompt(self, prompt):
        raise AssertionError("The live style-update smoke test must not call CPAS.")


@pytest.mark.skipif(not RUN_LIVE, reason="set RUN_LIVE_DOUBAO=1 to call the live API")
def test_live_level_change_hot_updates_or_recovers_with_same_dialog_id():
    async def scenario():
        load_dotenv(override=True)
        events = []
        connected = asyncio.Event()

        async def sink(event):
            events.append(event)
            if (
                event.get("type") == "connection"
                and event.get("component") == "realtime_session"
                and event.get("status") == "connected"
            ):
                connected.set()

        client = DoubaoWebSocketClient()
        session = RealtimeVoiceSession(
            VoiceSessionConfig("LIVE", "LIVE-UPDATE", retain_audio=False),
            client,
            UnusedGrader(),
            event_sink=sink,
        )

        await session.start()
        await asyncio.wait_for(connected.wait(), timeout=15)
        original_dialog_id = session.dialog_id
        original_connect_id = client.connect_id
        assert original_dialog_id

        connected.clear()
        await session._apply_grade(
            {
                "doctor_turn_id": "D-LIVE-0001",
                "grading_status": "scored",
                "control_score": 2,
                "brief_rationale": "live protocol smoke test",
            }
        )
        await session.wait_until_refresh_idle()
        await asyncio.wait_for(connected.wait(), timeout=15)

        assert session.current_style["level"] == 4
        assert session.dialog_id == original_dialog_id
        assert any(
            event.get("type") == "connection"
            and event.get("component") == "realtime_session"
            and event.get("status") == "updating"
            for event in events
        )

        used_hot_update = any(event.get("update_mode") == "hot" for event in events)
        used_fallback = any(
            event.get("status") == "fallback_reconnecting" for event in events
        )
        assert used_hot_update or used_fallback
        print(f"live_update_path={'hot' if used_hot_update else 'fallback_reconnect'}")
        if used_hot_update:
            assert client.connect_id == original_connect_id
        if used_fallback:
            assert client.connect_id != original_connect_id

        await session.stop()

    asyncio.run(scenario())
