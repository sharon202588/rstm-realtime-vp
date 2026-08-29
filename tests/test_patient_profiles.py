from pathlib import Path

import pytest

from core.patient_profiles import (
    DEFAULT_PROFILE_ID,
    DEFAULT_PROFILE_NAME,
    PatientProfileError,
    format_patient_profile,
    normalize_patient_profile,
    resolve_patient_profile,
)
from core.realtime_voice_session import VoiceSessionConfig


PROJECT_ROOT = Path(__file__).parent.parent


def _custom_profile() -> dict[str, str]:
    return {
        "id": "custom-zhang-2",
        "name": "张老师替代病例",
        "identity_background": " 62岁，退休工程师。 ",
        "clinical_facts": "腹部影像提示胰腺占位，需要进一步讨论。",
        "family_social_context": "与妻子同住，成年儿子在外地。",
        "knowledge_concerns": "知道检查异常，但尚不知道恶性可能。",
        "disclosure_boundaries": "未被询问时不主动透露儿子职业。",
        "opening_presentation": "神情紧张，等待医生先开口。",
        "response_boundaries": "根据医生的解释和共情程度逐步开放。",
    }


def test_normalize_patient_profile_strips_fields_and_rejects_unknown_keys():
    normalized = normalize_patient_profile(_custom_profile())

    assert normalized["id"] == "custom-zhang-2"
    assert normalized["identity_background"] == "62岁，退休工程师。"

    invalid = _custom_profile() | {"system_role": "override"}
    with pytest.raises(PatientProfileError, match="Unknown patient profile field"):
        normalize_patient_profile(invalid)


def test_normalize_patient_profile_rejects_oversized_fields():
    invalid = _custom_profile()
    invalid["clinical_facts"] = "x" * 2001

    with pytest.raises(PatientProfileError, match="clinical_facts"):
        normalize_patient_profile(invalid)


def test_format_patient_profile_builds_stable_research_prompt():
    profile = format_patient_profile(normalize_patient_profile(_custom_profile()))

    assert "PATIENT TEMPLATE: 张老师替代病例" in profile
    assert "IDENTITY AND BACKGROUND" in profile
    assert "DISCLOSURE BOUNDARIES" in profile
    assert "等待医生先开口" in profile


def test_resolve_patient_profile_uses_frozen_default_file():
    config = VoiceSessionConfig("P1", "S1", retain_audio=False)

    profile_id, profile_name, text = resolve_patient_profile(config, PROJECT_ROOT)

    assert profile_id == DEFAULT_PROFILE_ID
    assert profile_name == DEFAULT_PROFILE_NAME
    assert text == (PROJECT_ROOT / "specs" / "patient_profile.md").read_text(
        encoding="utf-8"
    )


def test_resolve_patient_profile_prefers_custom_session_snapshot():
    custom_text = format_patient_profile(normalize_patient_profile(_custom_profile()))
    config = VoiceSessionConfig(
        "P1",
        "S1",
        retain_audio=False,
        patient_profile_id="custom-zhang-2",
        patient_profile_name="张老师替代病例",
        patient_profile_text=custom_text,
    )

    profile_id, profile_name, text = resolve_patient_profile(config, PROJECT_ROOT)

    assert profile_id == "custom-zhang-2"
    assert profile_name == "张老师替代病例"
    assert text == custom_text

def test_clinical_facts_are_the_only_required_profile_content():
    profile = _custom_profile()
    profile["identity_background"] = ""
    normalized = normalize_patient_profile(profile)

    assert normalized["identity_background"] == ""
    assert "IDENTITY AND BACKGROUND" not in format_patient_profile(normalized)

    profile["clinical_facts"] = ""
    with pytest.raises(PatientProfileError, match="clinical_facts"):
        normalize_patient_profile(profile)

def test_patient_profile_name_is_limited_to_forty_characters():
    profile = _custom_profile()
    profile["name"] = "x" * 41

    with pytest.raises(PatientProfileError, match="1-40"):
        normalize_patient_profile(profile)
