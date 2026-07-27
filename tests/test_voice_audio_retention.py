"""Integration test for voice-session test-mode audio retention."""

import asyncio
import wave

from core.realtime_voice_session import RealtimeVoiceSession, VoiceSessionConfig


class FakeWebSocket:
    def __init__(self):
        self.audio = []
        self._gate = asyncio.Event()

    async def connect(self):
        return None

    async def start_session(self, **kwargs):
        return None

    async def send_audio(self, chunk):
        self.audio.append(chunk)

    async def listen(self, callback=None):
        await self._gate.wait()

    async def finish_session(self):
        return None

    async def finish_connection(self):
        return None

    async def disconnect(self):
        return None


class FakeGrader:
    def grade_prompt(self, prompt):
        return {"grading_status": "unscorable"}


def test_test_mode_retains_clinician_and_patient_pcm(tmp_path):
    events = []

    async def scenario():
        session = RealtimeVoiceSession(
            VoiceSessionConfig(
                participant_id="P1",
                session_id="S1",
                retain_audio=True,
                audio_root=str(tmp_path),
            ),
            FakeWebSocket(),
            FakeGrader(),
            event_sink=events.append,
        )
        await session.start()
        await session.send_audio(b"\x01\x00\x02\x00")
        await session.handle_doubao_event(
            {"type": "TTSResponse", "data": b"\x03\x00\x04\x00"}
        )
        await session.stop()

    asyncio.run(scenario())

    clinician = tmp_path / "S1" / "audio" / "clinician_session.wav"
    patient = tmp_path / "S1" / "audio" / "patient_session.wav"
    with wave.open(str(clinician), "rb") as recording:
        assert recording.getframerate() == 16000
        assert recording.readframes(2) == b"\x01\x00\x02\x00"
    with wave.open(str(patient), "rb") as recording:
        assert recording.getframerate() == 24000
        assert recording.readframes(2) == b"\x03\x00\x04\x00"

    audio_event = next(event for event in events if event.get("type") == "audio")
    assert len(audio_event["files"]) == 2
