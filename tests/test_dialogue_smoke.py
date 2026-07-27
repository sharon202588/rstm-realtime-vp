"""Fast no-network smoke test for the dialogue manager Phase A-D loop."""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dialogue_manager import DialogueManager
from core.session_logger import SessionLogger


class FakeRESTClient:
    def __init__(self):
        self.last_messages = None

    def chat_completion(self, messages, reasoning_effort=None):
        self.last_messages = messages
        return {
            "choices": [
                {
                    "message": {
                        "content": "I understand. Could you explain what the test result means?"
                    }
                }
            ]
        }

    def grade_dialogue(self, dialogue_history, grader_prompt, reasoning_effort=None):
        return {
            "final_cpas_score": 2,
            "scoring_breakdown": {
                "track_a_task": 1,
                "track_b_empathy": 1,
            },
            "safety_check": {"status": "Safe"},
        }


def test_process_doctor_turn_text_mode_without_network(tmp_path):
    manager = DialogueManager(
        ark_api_key=None,
        doubao_realtime_app_id=None,
        doubao_realtime_access_key=None,
        initial_cci=0,
        state_file=str(tmp_path / "state.json"),
    )
    manager.rest_client = FakeRESTClient()

    result = asyncio.run(
        manager.process_doctor_turn(
            doctor_message="Hello, I would like to understand what you know so far.",
            use_voice=False,
        )
    )

    assert result["phase_a"]["patient_response"]
    assert result["phase_b"]["final_cpas_score"] == 2
    assert result["phase_c"]["turn"] == 1
    assert result["phase_c"]["state"] > 0
    assert result["phase_d"]["style"]["level"] in range(1, 8)
    assert len(manager.dialogue_history) == 2


def test_bbn_opening_is_available_but_not_automatic(tmp_path):
    manager = DialogueManager(
        ark_api_key=None,
        doubao_realtime_app_id=None,
        doubao_realtime_access_key=None,
        initial_state=-0.25,
        state_file=str(tmp_path / "state.json"),
        language="zh",
        scenario="breaking_bad_news",
    )
    assert manager.dialogue_history == []

    opening = manager.start_with_opening()

    assert opening == "医生，我这次检查结果是不是不太好？我这几天一直有点担心。"
    assert manager.dialogue_history == [
        {
            "role": "Patient",
            "content": opening,
            "turn": 1,
        }
    ]

    manager.rest_client = FakeRESTClient()
    result = asyncio.run(
        manager.process_doctor_turn(
            doctor_message="我们先了解一下您现在对检查结果的理解。",
            use_voice=False,
        )
    )

    assert result["transcript"][0]["role"] == "Patient"
    assert result["transcript"][0]["content"] == opening
    assert result["transcript"][1]["role"] == "Doctor"


def test_case_context_is_added_to_generation_prompt(tmp_path):
    fake_client = FakeRESTClient()
    manager = DialogueManager(
        ark_api_key=None,
        doubao_realtime_app_id=None,
        doubao_realtime_access_key=None,
        initial_state=-0.25,
        state_file=str(tmp_path / "state.json"),
        language="zh",
        scenario="breaking_bad_news",
        case_context="本次测试病例：患者刚完成肺部CT复查，但医生尚未说明结果。",
    )
    manager.rest_client = fake_client

    asyncio.run(
        manager.process_doctor_turn(
            doctor_message="张老师，您好，我们先聊聊您对检查的了解。",
            use_voice=False,
        )
    )

    assert fake_client.last_messages is not None
    assert "本次测试病例" in fake_client.last_messages[0]["content"]


def test_non_adaptive_condition_does_not_update_rstm(tmp_path):
    manager = DialogueManager(
        ark_api_key=None,
        doubao_realtime_app_id=None,
        doubao_realtime_access_key=None,
        initial_cci=0,
        state_file=str(tmp_path / "state.json"),
        adaptive_enabled=False,
        fixed_style_state=0.0,
    )
    manager.rest_client = FakeRESTClient()

    result = asyncio.run(
        manager.process_doctor_turn(
            doctor_message="I need to tell you about your scan results.",
            use_voice=False,
        )
    )

    assert result["phase_a"]["style_level"] == 4
    assert result["phase_c"]["adaptive_enabled"] is False
    assert result["phase_c"]["state"] == 0.0
    assert manager.state_manager.turn_count == 0
    assert manager.state_manager.get_current_state() == 0.0


def test_session_logger_keeps_text_and_no_audio_by_default(tmp_path):
    logger = SessionLogger(
        session_id="session-001",
        participant_id="participant-001",
        condition="adaptive",
        language="zh",
        scenario="breaking_bad_news",
        log_root=str(tmp_path),
        retain_audio=False,
    )
    manager = DialogueManager(
        ark_api_key=None,
        doubao_realtime_app_id=None,
        doubao_realtime_access_key=None,
        initial_cci=0,
        state_file=str(tmp_path / "state.json"),
        language="zh",
        scenario="breaking_bad_news",
        session_logger=logger,
    )
    manager.rest_client = FakeRESTClient()

    asyncio.run(
        manager.process_doctor_turn(
            doctor_message="请告诉我检查结果。",
            use_voice=False,
        )
    )

    lines = logger.turns_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["transcript"][0]["role"] == "Doctor"
    assert record["transcript"][1]["role"] == "Patient"
    assert record["cpas"]["raw_output"]["final_cpas_score"] == 2
    assert "brief_rationale" in record["cpas"]
    assert record["rstm_trajectory"]["state"] > 0
    assert record["audio"]["retained"] is False
    assert record["audio"]["files"] == []
