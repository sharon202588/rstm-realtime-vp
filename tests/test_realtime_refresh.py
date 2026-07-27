"""Tests for non-blocking realtime style updates and reconnect fallback."""

import asyncio

from core.realtime_voice_session import RealtimeVoiceSession, VoiceSessionConfig


class VoiceClient:
    def __init__(self):
        self.started_sessions = []
        self.updated_configs = []
        self.finished_sessions = 0
        self.connect_count = 0
        self.disconnect_count = 0
        self._gate = asyncio.Event()

    async def connect(self):
        self.connect_count += 1

    async def start_session(self, **kwargs):
        self.started_sessions.append(kwargs)

    async def update_config(self, **kwargs):
        self.updated_configs.append(kwargs)

    async def send_audio(self, chunk):
        return None

    async def listen(self, callback=None):
        await self._gate.wait()

    async def finish_session(self):
        self.finished_sessions += 1

    async def finish_connection(self):
        return None

    async def disconnect(self):
        self.disconnect_count += 1


class Grader:
    def __init__(self, score=2):
        self.score = score

    def grade_prompt(self, prompt):
        return {"final_cpas_score": self.score, "reasoning": "clear"}


async def wait_for_update(voice):
    for _ in range(20):
        if voice.updated_configs:
            return
        await asyncio.sleep(0)
    raise AssertionError("UpdateConfig was not sent")


def make_session(voice, score=2):
    return RealtimeVoiceSession(
        VoiceSessionConfig("P1", "S1", retain_audio=False),
        voice,
        Grader(score=score),
    )


async def submit_scored_turn(session):
    await session.handle_doubao_event(
        {
            "type": "ASRResponse",
            "results": [{"is_interim": False, "text": "Please explain the result."}],
        }
    )
    await session.handle_doubao_event({"type": "ASREnded"})
    await session.wait_until_grades_idle()


def test_fast_grade_waits_for_tts_then_hot_updates_without_reconnect():
    async def scenario():
        voice = VoiceClient()
        session = make_session(voice)
        await session.start()
        await session.handle_doubao_event(
            {"type": "SessionStarted", "dialog_id": "dialog-1"}
        )

        await submit_scored_turn(session)
        await asyncio.sleep(0)
        assert session.current_style["level"] == 4
        assert voice.updated_configs == []
        assert voice.finished_sessions == 0

        await session.handle_doubao_event({"type": "TTSEnded", "reply_id": "R1"})
        await wait_for_update(voice)

        update = voice.updated_configs[0]
        assert update["dialog_id"] == "dialog-1"
        assert update["system_role"]
        assert "Level 4" in update["speaking_style"]
        assert update["tts_config"]["speaker"]

        await session.handle_doubao_event({"type": "ConfigUpdated"})
        await session.wait_until_refresh_idle()

        assert voice.finished_sessions == 0
        assert voice.disconnect_count == 0
        assert voice.connect_count == 1
        assert len(voice.started_sessions) == 1
        assert voice.started_sessions[0]["end_smooth_window_ms"] == 1500
        assert voice.started_sessions[0]["enable_custom_vad"] is True
        await session.stop()

    asyncio.run(scenario())


def test_hot_update_confirmation_failure_reconnects_with_same_dialog_id():
    async def scenario():
        voice = VoiceClient()
        session = make_session(voice)
        session.STYLE_UPDATE_ACK_TIMEOUT_SECONDS = 0.01
        await session.start()
        await session.handle_doubao_event(
            {"type": "SessionStarted", "dialog_id": "dialog-1"}
        )
        await submit_scored_turn(session)
        await session.handle_doubao_event({"type": "TTSEnded", "reply_id": "R1"})
        await session.wait_until_refresh_idle()

        assert len(voice.updated_configs) == 1
        assert voice.finished_sessions == 1
        assert voice.disconnect_count == 1
        assert voice.connect_count == 2
        assert len(voice.started_sessions) == 2
        assert voice.started_sessions[1]["dialog_id"] == "dialog-1"
        assert voice.started_sessions[1]["end_smooth_window_ms"] == 1500
        assert voice.started_sessions[1]["enable_custom_vad"] is True
        await session.stop()

    asyncio.run(scenario())


def test_hot_update_error_reconnects_immediately_with_same_dialog_id():
    async def scenario():
        voice = VoiceClient()
        session = make_session(voice)
        session.STYLE_UPDATE_ACK_TIMEOUT_SECONDS = 10
        await session.start()
        await session.handle_doubao_event(
            {"type": "SessionStarted", "dialog_id": "dialog-1"}
        )
        await submit_scored_turn(session)
        await session.handle_doubao_event({"type": "TTSEnded", "reply_id": "R1"})
        await wait_for_update(voice)

        await session.handle_doubao_event(
            {"type": "ERROR", "payload": {"error": "config rejected"}}
        )
        await session.wait_until_refresh_idle()

        assert voice.disconnect_count == 1
        assert voice.connect_count == 2
        assert voice.started_sessions[1]["dialog_id"] == "dialog-1"
        await session.stop()

    asyncio.run(scenario())

def test_same_level_rstm_update_does_not_touch_remote_config():
    async def scenario():
        voice = VoiceClient()
        session = make_session(voice, score=-2)
        await session.start()
        await submit_scored_turn(session)
        await session.handle_doubao_event({"type": "TTSEnded", "reply_id": "R1"})
        await session.wait_until_refresh_idle()

        assert session.current_style["level"] == 3
        assert voice.updated_configs == []
        assert voice.finished_sessions == 0
        assert voice.disconnect_count == 0
        assert voice.connect_count == 1
        await session.stop()

    asyncio.run(scenario())


def test_audio_is_not_forwarded_until_remote_config_is_ready():
    async def scenario():
        voice = VoiceClient()
        sent_audio = []

        async def capture_audio(chunk):
            sent_audio.append(chunk)

        voice.send_audio = capture_audio
        session = make_session(voice)
        await session.start()

        await session.send_audio(b"before-ready")
        await session.handle_doubao_event(
            {"type": "SessionStarted", "dialog_id": "dialog-1"}
        )
        await session.send_audio(b"ready")

        session._remote_audio_enabled = False
        await session.send_audio(b"during-update")

        assert sent_audio == [b"ready"]
        await session.stop()

    asyncio.run(scenario())