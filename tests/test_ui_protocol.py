"""Tests for local UI command validation."""

import pytest

from ui.protocol import ProtocolError, parse_command


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
