"""Tests for local UI command validation."""

import pytest

from ui.protocol import ProtocolError, parse_command


def _custom_profile():
    return {
        "id": "custom-pancreas-1",
        "name": "胰腺占位病例",
        "identity_background": "62岁退休工程师。",
        "clinical_facts": "影像提示胰腺占位。",
        "family_social_context": "与妻子同住。",
        "knowledge_concerns": "知道检查异常。",
        "disclosure_boundaries": "不主动透露未被询问的信息。",
        "opening_presentation": "等待医生先开口。",
        "response_boundaries": "随沟通质量调整开放程度。",
    }


def test_configure_enforces_level_three_for_both_conditions():
    for condition in ("adaptive", "control"):
        command = parse_command(
            {
                "command": "configure",
                "participant_id": "P001",
                "session_id": f"S-{condition}",
                "condition": condition,
                "language": "zh",
            }
        )
        assert command.config.initial_state == -0.25
        assert command.config.fixed_style_state == -0.25
        assert command.config.adaptive_enabled is (condition == "adaptive")


def test_protocol_accepts_valid_custom_patient_profile():
    command = parse_command(
        {
            "command": "configure",
            "participant_id": "P001",
            "session_id": "S-custom",
            "patient_profile": _custom_profile(),
        }
    )

    assert command.config.patient_profile_id == "custom-pancreas-1"
    assert command.config.patient_profile_name == "胰腺占位病例"
    assert "CLINICAL FACTS" in command.config.patient_profile_text
    assert "影像提示胰腺占位" in command.config.patient_profile_text


def test_protocol_rejects_unknown_or_oversized_patient_profile_fields():
    with pytest.raises(ProtocolError, match="Unknown patient profile field"):
        parse_command(
            {
                "command": "configure",
                "participant_id": "P001",
                "session_id": "S-custom",
                "patient_profile": _custom_profile() | {"system_role": "override"},
            }
        )

    oversized = _custom_profile()
    oversized["clinical_facts"] = "x" * 2001
    with pytest.raises(ProtocolError, match="clinical_facts"):
        parse_command(
            {
                "command": "configure",
                "participant_id": "P001",
                "session_id": "S-custom",
                "patient_profile": oversized,
            }
        )


def test_protocol_rejects_unknown_commands_and_browser_credentials():
    with pytest.raises(ProtocolError):
        parse_command({"command": "grade"})
    with pytest.raises(ProtocolError):
        parse_command(
            {
                "command": "configure",
                "participant_id": "P1",
                "session_id": "S1",
                "api_key": "secret",
            }
        )


def test_protocol_rejects_invalid_ids_and_non_bbn_scenarios():
    with pytest.raises(ProtocolError):
        parse_command(
            {
                "command": "configure",
                "participant_id": "../P1",
                "session_id": "S1",
            }
        )
    with pytest.raises(ProtocolError):
        parse_command(
            {
                "command": "configure",
                "participant_id": "P1",
                "session_id": "S1",
                "scenario": "other",
            }
        )

def test_protocol_accepts_custom_profile_without_identity_background():
    profile = _custom_profile()
    profile["identity_background"] = ""

    command = parse_command(
        {
            "command": "configure",
            "participant_id": "P001",
            "session_id": "S-optional",
            "patient_profile": profile,
        }
    )

    assert "CLINICAL FACTS" in command.config.patient_profile_text
    assert "IDENTITY AND BACKGROUND" not in command.config.patient_profile_text
