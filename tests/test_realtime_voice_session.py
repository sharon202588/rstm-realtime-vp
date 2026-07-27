"""No-network tests for the realtime voice session core."""

import asyncio
import threading

from core.realtime_voice_session import RealtimeVoiceSession, VoiceSessionConfig


class FakeVoiceWebSocket:
    def __init__(self):
        self.connected = False
        self.started_sessions = []
        self.audio_chunks = []
        self.text_queries = []
        self.session_id = "remote-session-1"
        self._listen_gate = asyncio.Event()

    async def connect(self):
        self.connected = True

    async def start_session(self, **kwargs):
        self.started_sessions.append(kwargs)

    async def send_audio(self, chunk):
        self.audio_chunks.append(chunk)

    async def send_text_query(self, text):
        self.text_queries.append(text)

    async def finish_session(self):
        return None

    async def finish_connection(self):
        return None

    async def disconnect(self):
        self.connected = False

    async def listen(self, callback=None):
        await self._listen_gate.wait()


class FakeGrader:
    def __init__(self, result=None, gate=None):
        self.result = result or {
            "doctor_turn_id": "D-0001",
            "final_cpas_score": 2,
            "inferred_stage": "P",
            "safety_check": {"status": "Safe", "missing_elements": "None"},
            "scoring_breakdown": {
                "track_a_task": 1,
                "track_b_empathy": 1,
            },
            "reasoning": "Clear perception question.",
        }
        self.gate = gate
        self.prompts = []

    def grade_prompt(self, prompt):
        self.prompts.append(prompt)
        if self.gate is not None:
            self.gate.wait(timeout=2)
        return dict(self.result)


def make_session(*, adaptive=True, grader=None, event_sink=None):
    return RealtimeVoiceSession(
        config=VoiceSessionConfig(
            participant_id="P001",
            session_id="S001",
            adaptive_enabled=adaptive,
            language="zh",
            retain_audio=False,
        ),
        ws_client=FakeVoiceWebSocket(),
        rest_client=grader or FakeGrader(),
        event_sink=event_sink,
    )


def test_voice_conditions_share_level_three_start():
    adaptive = make_session(adaptive=True)
    control = make_session(adaptive=False)

    assert adaptive.current_state == -0.25
    assert adaptive.current_style["level"] == 3
    assert control.current_state == -0.25
    assert control.current_style["level"] == 3


def test_audio_mode_commits_final_asr_without_sending_chat_text_query():
    async def scenario():
        session = make_session()
        await session.handle_doubao_event(
            {
                "type": "ASRResponse",
                "results": [
                    {
                        "is_interim": False,
                        "text": "您现在对检查结果了解多少？",
                    }
                ],
            }
        )
        await session.handle_doubao_event({"type": "ASREnded"})

        assert session.dialogue_history == [
            {
                "turn_id": "D-0001",
                "role": "Doctor",
                "content": "您现在对检查结果了解多少？",
            }
        ]
        assert session.pending_grade_count == 1
        assert session.ws_client.text_queries == []

    asyncio.run(scenario())


def test_chat_response_fragments_commit_one_patient_turn():
    async def scenario():
        session = make_session()
        await session.handle_doubao_event(
            {"type": "ChatResponse", "reply_id": "R1", "content": "我只知道"}
        )
        await session.handle_doubao_event(
            {"type": "ChatResponse", "reply_id": "R1", "content": "肺部有阴影。"}
        )
        await session.handle_doubao_event({"type": "ChatEnded", "reply_id": "R1"})
        await session.handle_doubao_event({"type": "TTSEnded", "reply_id": "R1"})

        assert session.dialogue_history == [
            {
                "turn_id": "P-0001",
                "role": "Patient",
                "content": "我只知道 肺部有阴影。",
            }
        ]

    asyncio.run(scenario())


def test_delayed_grader_does_not_block_patient_events():
    grade_gate = threading.Event()
    events = []

    async def scenario():
        session = make_session(
            grader=FakeGrader(gate=grade_gate),
            event_sink=events.append,
        )
        await session.start()
        await session.handle_doubao_event(
            {
                "type": "ASRResponse",
                "results": [
                    {
                        "is_interim": False,
                        "text": "您愿意现在听我说明结果吗？",
                    }
                ],
            }
        )
        await session.handle_doubao_event({"type": "ASREnded"})

        await asyncio.wait_for(
            session.handle_doubao_event(
                {"type": "ChatResponse", "reply_id": "R1", "content": "可以，您说吧。"}
            ),
            timeout=0.2,
        )
        await asyncio.wait_for(
            session.handle_doubao_event({"type": "ChatEnded", "reply_id": "R1"}),
            timeout=0.2,
        )

        assert session.dialogue_history[-1]["role"] == "Patient"
        assert session.current_state == -0.25

        grade_gate.set()
        await session.wait_until_grades_idle()
        assert session.current_state == -0.05
        await session.stop()

    asyncio.run(scenario())


def test_unscorable_asr_displays_zero_without_state_update():
    events = []

    async def scenario():
        session = make_session(event_sink=events.append)
        await session.handle_doubao_event({"type": "ASREnded"})

        assert session.current_state == -0.25
        grade_events = [event for event in events if event.get("type") == "grade"]
        assert grade_events[-1]["grading_status"] == "unscorable"
        assert grade_events[-1]["display_score"] == 0
        assert grade_events[-1]["control_score"] is None

    asyncio.run(scenario())


def test_non_adaptive_valid_grade_does_not_change_level_three():
    async def scenario():
        session = make_session(adaptive=False)
        await session.start()
        await session.handle_doubao_event(
            {
                "type": "ASRResponse",
                "results": [
                    {"is_interim": False, "text": "请告诉我您现在最担心什么。"}
                ],
            }
        )
        await session.handle_doubao_event({"type": "ASREnded"})
        await session.wait_until_grades_idle()

        assert session.current_state == -0.25
        assert session.current_style["level"] == 3
        await session.stop()

    asyncio.run(scenario())

