"""Validation for browser-to-backend control messages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from core.realtime_voice_session import VoiceSessionConfig


ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
COMMANDS = {"configure", "start", "stop", "reset", "ping"}
FORBIDDEN_KEYS = {"api_key", "app_id", "app_key", "ark_api_key"}


class ProtocolError(ValueError):
    """A browser command is invalid or unsafe."""


@dataclass(frozen=True)
class BrowserCommand:
    name: str
    config: VoiceSessionConfig | None = None


def parse_command(message: Mapping[str, Any]) -> BrowserCommand:
    if not isinstance(message, Mapping):
        raise ProtocolError("Command must be a JSON object.")
    name = str(message.get("command", "")).strip().lower()
    if name not in COMMANDS:
        raise ProtocolError(f"Unknown command: {name or '(empty)'}")
    if FORBIDDEN_KEYS.intersection(message):
        raise ProtocolError("API credentials are server-side only.")
    if name != "configure":
        return BrowserCommand(name=name)

    participant_id = str(message.get("participant_id", "")).strip()
    session_id = str(message.get("session_id", "")).strip()
    if not ID_PATTERN.fullmatch(participant_id):
        raise ProtocolError("Participant ID must use 1-64 letters, numbers, _ or -.")
    if not ID_PATTERN.fullmatch(session_id):
        raise ProtocolError("Session ID must use 1-64 letters, numbers, _ or -.")

    language = str(message.get("language", "zh")).lower()
    if language not in {"zh", "en"}:
        raise ProtocolError("Language must be zh or en.")

    condition = str(message.get("condition", "adaptive")).lower()
    if condition not in {"adaptive", "control"}:
        raise ProtocolError("Condition must be adaptive or control.")

    scenario = str(message.get("scenario", "breaking_bad_news")).lower()
    if scenario != "breaking_bad_news":
        raise ProtocolError("Only breaking_bad_news is available in this build.")

    config = VoiceSessionConfig(
        participant_id=participant_id,
        session_id=session_id,
        adaptive_enabled=condition == "adaptive",
        language=language,
        scenario=scenario,
        case_context=str(message.get("case_context", "")).strip(),
        initial_state=-0.25,
        fixed_style_state=-0.25,
        retain_audio=bool(message.get("retain_audio", True)),
    )
    return BrowserCommand(name=name, config=config)
