"""Validation and prompt formatting for per-session patient templates."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping


DEFAULT_PROFILE_ID = "default-bbn-zhang"
DEFAULT_PROFILE_NAME = "肺部检查异常复诊（张老师）"
PROFILE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
PROFILE_FIELDS = (
    "identity_background",
    "clinical_facts",
    "family_social_context",
    "knowledge_concerns",
    "disclosure_boundaries",
    "opening_presentation",
    "response_boundaries",
)
PROFILE_HEADINGS = {
    "identity_background": "IDENTITY AND BACKGROUND",
    "clinical_facts": "CLINICAL FACTS",
    "family_social_context": "FAMILY AND SOCIAL CONTEXT",
    "knowledge_concerns": "PATIENT KNOWLEDGE AND CONCERNS",
    "disclosure_boundaries": "DISCLOSURE BOUNDARIES",
    "opening_presentation": "OPENING PRESENTATION",
    "response_boundaries": "RESPONSE BOUNDARIES",
}
MAX_FIELD_LENGTH = 2000
MAX_TOTAL_LENGTH = 10000


class PatientProfileError(ValueError):
    """A custom patient profile is incomplete or unsafe to accept."""


def normalize_patient_profile(value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise PatientProfileError("Patient profile must be an object.")

    allowed = {"id", "name", *PROFILE_FIELDS}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise PatientProfileError(f"Unknown patient profile field: {unknown[0]}")

    normalized: dict[str, str] = {}
    for key in allowed:
        raw = value.get(key, "")
        if not isinstance(raw, str):
            raise PatientProfileError(f"Patient profile field {key} must be text.")
        normalized[key] = raw.strip()

    if not PROFILE_ID_PATTERN.fullmatch(normalized["id"]):
        raise PatientProfileError(
            "Patient profile id must use 1-64 letters, numbers, _ or -."
        )
    if not normalized["name"] or len(normalized["name"]) > 40:
        raise PatientProfileError("Patient profile name must use 1-40 characters.")

    for key in PROFILE_FIELDS:
        if len(normalized[key]) > MAX_FIELD_LENGTH:
            raise PatientProfileError(
                f"Patient profile field {key} exceeds {MAX_FIELD_LENGTH} characters."
            )

    if not normalized["clinical_facts"]:
        raise PatientProfileError("Patient profile field clinical_facts is required.")

    total = sum(len(normalized[key]) for key in PROFILE_FIELDS)
    if total > MAX_TOTAL_LENGTH:
        raise PatientProfileError(
            f"Patient profile exceeds {MAX_TOTAL_LENGTH} total characters."
        )
    return normalized


def format_patient_profile(fields: Mapping[str, str]) -> str:
    sections = [f"PATIENT TEMPLATE: {fields['name']}"]
    for key in PROFILE_FIELDS:
        content = fields.get(key, "").strip()
        if content:
            sections.append(f"{PROFILE_HEADINGS[key]}:\n{content}")
    return "\n\n".join(sections)


def resolve_patient_profile(
    config: Any, project_root: Path
) -> tuple[str, str, str]:
    custom_text = str(getattr(config, "patient_profile_text", "") or "").strip()
    if custom_text:
        return (
            str(getattr(config, "patient_profile_id", "") or DEFAULT_PROFILE_ID),
            str(getattr(config, "patient_profile_name", "") or DEFAULT_PROFILE_NAME),
            custom_text,
        )

    configured_path = getattr(config, "patient_profile_path", None)
    profile_path = (
        Path(configured_path)
        if configured_path
        else project_root / "specs" / "patient_profile.md"
    )
    return (
        str(getattr(config, "patient_profile_id", "") or DEFAULT_PROFILE_ID),
        str(getattr(config, "patient_profile_name", "") or DEFAULT_PROFILE_NAME),
        profile_path.read_text(encoding="utf-8"),
    )
