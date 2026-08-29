"""Behavioral tests for CPAS grading jobs and normalized results."""

from core.grading import (
    GRADER_VERSION,
    GradingJob,
    format_grader_prompt,
    normalize_grade_result,
)


def test_valid_zero_is_an_rstm_control_score():
    result = normalize_grade_result(
        {
            "final_cpas_score": 0,
            "inferred_phase": "P",
            "safety_check": {"status": "Safe", "missing_elements": "None"},
            "scoring_breakdown": {
                "track_a_task": 0,
                "track_b_empathy": 0,
            },
            "reasoning": "The question is scorable but neutral.",
        },
        doctor_turn_id="D-0001",
    )

    assert result["display_score"] == 0
    assert result["control_score"] == 0
    assert result["grading_status"] == "scored"
    assert result["applied_to_rstm"] is False


def test_unscorable_audio_displays_zero_without_an_rstm_control_score():
    result = normalize_grade_result(
        {
            "grading_status": "unscorable",
            "reasoning": "Final ASR text was unavailable.",
        },
        doctor_turn_id="D-0002",
    )

    assert result["display_score"] == 0
    assert result["control_score"] is None
    assert result["grading_status"] == "unscorable"
    assert result["applied_to_rstm"] is False


def test_grader_prompt_separates_target_from_complete_preceding_history():
    job = GradingJob(
        doctor_turn_id="D-0007",
        target_utterance="您愿意现在听我说明检查结果吗？",
        preceding_history=(
            {"role": "Patient", "content": "我有些担心。"},
            {"role": "Doctor", "content": "您现在对检查了解多少？"},
            {"role": "Patient", "content": "我只知道肺部有阴影。"},
        ),
        submitted_at="2026-07-26T10:00:00+00:00",
    )

    prompt = format_grader_prompt(job)

    assert GRADER_VERSION == "1.2"
    assert "D-0007" in prompt
    assert "您愿意现在听我说明检查结果吗？" in prompt
    assert "Patient: 我有些担心。" in prompt
    assert "Doctor: 您现在对检查了解多少？" in prompt
    assert "deterministic CPAS grader" in prompt
    assert "Stage-specific calibration" in prompt
    assert "turn 3 in this case" not in prompt
    assert "Turns 1 & 2" not in prompt


def test_out_of_range_score_is_not_applied_as_zero():
    result = normalize_grade_result(
        {"final_cpas_score": 8, "reasoning": "Malformed score."},
        doctor_turn_id="D-0003",
    )

    assert result["display_score"] == 0
    assert result["control_score"] is None
    assert result["grading_status"] == "error"

