"""Executable checks for the 7-level style mapper.

The expected boundary behavior follows specs/affective_interaction_mapping.md:
Level 5 includes +0.40 and Level 6 includes +0.70.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rstm.style_mapper import StyleMapper


def test_boundary_values():
    test_cases = [
        (-1.0, 1),
        (-0.70, 2),
        (-0.40, 3),
        (-0.10, 4),
        (0.10, 4),
        (0.10 + 0.0001, 5),
        (0.40, 5),
        (0.40 + 0.0001, 6),
        (0.70, 6),
        (0.70 + 0.0001, 7),
        (1.0, 7),
    ]

    for state, expected_level in test_cases:
        style = StyleMapper.map_state_to_style(state)
        assert style["level"] == expected_level


def test_range_values():
    test_cases = [
        (-0.85, 1),
        (-0.55, 2),
        (-0.25, 3),
        (0.0, 4),
        (0.25, 5),
        (0.55, 6),
        (0.85, 7),
    ]

    for state, expected_level in test_cases:
        style = StyleMapper.map_state_to_style(state)
        assert style["level"] == expected_level


def test_style_details_are_present():
    for state in [-0.85, -0.55, -0.25, 0.0, 0.25, 0.55, 0.85]:
        style = StyleMapper.map_state_to_style(state)
        assert style["name"]
        assert style["interaction_style"]
        assert style["behavioral_cues"]
        assert style["characteristics"]


def test_level_three_name_matches_bbn_baseline():
    style = StyleMapper.map_state_to_style(-0.25)
    assert style["name"] == "Concerned / Downcast"


def test_style_prompt_contains_selected_style():
    prompt = StyleMapper.get_style_prompt(0.25)
    assert "Mildly Positive / Encouraging" in prompt
    assert "Level 5" in prompt
    assert "Warm" in prompt


def test_opening_only_style_prompt_limits_level_three_to_opening():
    zh_prompt = StyleMapper.get_opening_only_style_prompt(-0.25, "zh")
    en_prompt = StyleMapper.get_opening_only_style_prompt(-0.25, "en")

    assert "Level 3" in zh_prompt
    assert "仅用于开场" in zh_prompt
    assert "后续" in zh_prompt
    assert "自然回应" in zh_prompt
    assert "Level 3" in en_prompt
    assert "opening only" in en_prompt.lower()
    assert "respond naturally" in en_prompt.lower()
