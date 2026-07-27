"""Session logging for study runs.

The logger stores text-only interaction records by default. Audio retention is
represented as an explicit setting so it can be enabled later without changing
the session metadata shape.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class SessionLogger:
    """Write participant/session logs as JSON and JSONL."""

    def __init__(
        self,
        session_id: str,
        participant_id: str,
        condition: str,
        language: str,
        scenario: str,
        log_root: str = "logs",
        retain_audio: bool = False,
        initial_state: Optional[float] = None,
        case_context: str = "",
    ):
        self.session_id = session_id
        self.participant_id = participant_id
        self.condition = condition
        self.language = language
        self.scenario = scenario
        self.retain_audio = retain_audio
        self.initial_state = initial_state
        self.case_context = case_context
        self.session_dir = Path(log_root) / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.turns_path = self.session_dir / "turns.jsonl"
        self.summary_path = self.session_dir / "summary.json"

        self._write_json(
            self.summary_path,
            {
                "session_id": session_id,
                "participant_id": participant_id,
                "condition": condition,
                "language": language,
                "scenario": scenario,
                "retain_audio": retain_audio,
                "audio_storage_enabled": retain_audio,
                "initial_state": initial_state,
                "case_context": case_context,
                "started_at": self._now(),
                "turn_count": 0,
            },
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _compact_grade(grade_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(grade_result, dict):
            return {}

        rationale = (
            grade_result.get("brief_rationale")
            or grade_result.get("rationale")
            or grade_result.get("reason")
            or grade_result.get("explanation")
            or grade_result.get("raw_response", "")
        )
        if isinstance(rationale, str):
            rationale = rationale.strip()[:500]
        else:
            rationale = str(rationale)[:500]

        return {
            "final_cpas_score": grade_result.get("final_cpas_score"),
            "inferred_stage": grade_result.get("inferred_stage"),
            "safety_check": grade_result.get("safety_check"),
            "scoring_breakdown": grade_result.get("scoring_breakdown"),
            "brief_rationale": rationale,
            "raw_output": grade_result,
        }

    @staticmethod
    def _compact_state(
        phase_c: Optional[Dict[str, Any]],
        phase_d: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(phase_c, dict):
            return {}

        style = {}
        if isinstance(phase_d, dict) and isinstance(phase_d.get("style"), dict):
            style = phase_d["style"]

        return {
            "turn": phase_c.get("turn"),
            "cci": phase_c.get("cci"),
            "state": phase_c.get("state"),
            "target_state": phase_c.get("target_state"),
            "style_level": style.get("level"),
            "style_name": style.get("name"),
            "adaptive_enabled": phase_c.get("adaptive_enabled", True),
            "skipped": phase_c.get("skipped"),
        }

    def log_turn(self, result: Dict[str, Any]) -> None:
        phase_a = result.get("phase_a") or {}
        record = {
            "logged_at": self._now(),
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "condition": self.condition,
            "language": self.language,
            "scenario": self.scenario,
            "transcript": result.get("transcript", []),
            "patient_response": phase_a.get("patient_response"),
            "style_at_response": {
                "state": phase_a.get("current_state"),
                "level": phase_a.get("style_level"),
                "name": phase_a.get("style_name"),
            },
            "cpas": self._compact_grade(result.get("phase_b")),
            "rstm_trajectory": self._compact_state(result.get("phase_c"), result.get("phase_d")),
            "audio": {
                "retained": self.retain_audio,
                "files": result.get("audio_files", []) if self.retain_audio else [],
            },
        }

        with self.turns_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        summary = {}
        if self.summary_path.exists():
            with self.summary_path.open("r", encoding="utf-8") as f:
                summary = json.load(f)
        summary["turn_count"] = int(summary.get("turn_count", 0)) + 1
        summary["last_updated_at"] = self._now()
        summary["latest_state"] = record["rstm_trajectory"]
        self._write_json(self.summary_path, summary)
