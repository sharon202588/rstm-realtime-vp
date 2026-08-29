"""CPAS grading jobs, prompt formatting, and result normalization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


GRADER_VERSION = "1.2"
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_GRADER_PROMPT = PROJECT_ROOT / "specs" / "grader_prompt.md"


@dataclass(frozen=True)
class GradingJob:
    """Immutable snapshot of one clinician utterance to grade."""

    doctor_turn_id: str
    target_utterance: str
    preceding_history: Sequence[Mapping[str, Any]]
    submitted_at: str


def _format_history(history: Sequence[Mapping[str, Any]]) -> str:
    lines = []
    for item in history:
        role = str(item.get("role", "Unknown"))
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(No preceding dialogue.)"


def format_grader_prompt(
    job: GradingJob,
    prompt_path: Optional[str | Path] = None,
) -> str:
    """Render the frozen grader template for one target doctor turn."""

    template_path = Path(prompt_path) if prompt_path else DEFAULT_GRADER_PROMPT
    template = template_path.read_text(encoding="utf-8")
    return (
        template.replace("{{TARGET_DOCTOR_TURN_ID}}", job.doctor_turn_id)
        .replace("{{TARGET_DOCTOR_UTTERANCE}}", job.target_utterance)
        .replace("{{PRECEDING_DIALOGUE_HISTORY}}", _format_history(job.preceding_history))
    )


def _numeric_score(value: Any) -> Optional[float | int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        score = value
    elif isinstance(value, str):
        try:
            score = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if not -8 <= score <= 5:
        return None
    if isinstance(score, float) and score.is_integer():
        return int(score)
    return score


def normalize_grade_result(
    raw_result: Mapping[str, Any],
    doctor_turn_id: str,
) -> dict[str, Any]:
    """Normalize grader output without treating unavailable data as score zero."""

    declared_status = str(raw_result.get("grading_status", "")).lower()
    score = _numeric_score(raw_result.get("final_cpas_score"))

    if declared_status == "unscorable":
        status = "unscorable"
        control_score = None
    elif score is not None:
        status = "scored"
        control_score = score
    else:
        status = "error"
        control_score = None

    return {
        "doctor_turn_id": doctor_turn_id,
        "grader_version": GRADER_VERSION,
        "display_score": control_score if control_score is not None else 0,
        "control_score": control_score,
        "grading_status": status,
        "applied_to_rstm": False,
        "inferred_stage": raw_result.get("inferred_stage") or raw_result.get("inferred_phase"),
        "safety_check": raw_result.get("safety_check"),
        "scoring_breakdown": raw_result.get("scoring_breakdown"),
        "brief_rationale": (
            raw_result.get("brief_rationale")
            or raw_result.get("reasoning")
            or raw_result.get("rationale")
            or raw_result.get("raw_response")
            or ""
        ),
        "raw_output": dict(raw_result),
    }

