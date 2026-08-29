"""Durable custom patient-template storage inside the application folder."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from core.patient_profiles import DEFAULT_PROFILE_ID, PatientProfileError, normalize_patient_profile


MAX_TEMPLATES = 100


class PatientTemplateStoreError(ValueError):
    """A patient-template file cannot be read or safely updated."""


class PatientTemplateStore:
    def __init__(self, application_root: str | Path):
        self.path = Path(application_root) / "data" / "patient_templates.json"
        self._lock = threading.Lock()

    def _normalize(self, values: Any) -> list[dict[str, str]]:
        if not isinstance(values, list):
            raise PatientTemplateStoreError("Patient templates must be a list.")
        if len(values) > MAX_TEMPLATES:
            raise PatientTemplateStoreError(
                f"Patient templates cannot exceed {MAX_TEMPLATES} entries."
            )

        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for value in values:
            try:
                template = normalize_patient_profile(value)
            except PatientProfileError as exc:
                raise PatientTemplateStoreError(str(exc)) from exc
            if template["id"] == DEFAULT_PROFILE_ID:
                raise PatientTemplateStoreError(
                    "The frozen default patient cannot be stored as a custom template."
                )
            if template["id"] in seen:
                raise PatientTemplateStoreError("Patient template ids must be unique.")
            seen.add(template["id"])
            normalized.append(template)
        return normalized

    def load(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return self._normalize(payload)
        except (OSError, json.JSONDecodeError, PatientTemplateStoreError) as exc:
            raise PatientTemplateStoreError(
                f"Unable to read patient templates from {self.path.name}."
            ) from exc

    def save(self, values: Any) -> list[dict[str, str]]:
        normalized = self._normalize(values)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(normalized, ensure_ascii=False, indent=2) + "\n"
        temporary_path: Path | None = None
        with self._lock:
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    newline="\n",
                    dir=self.path.parent,
                    prefix="patient_templates.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    stream.write(serialized)
                    stream.flush()
                    os.fsync(stream.fileno())
                    temporary_path = Path(stream.name)
                temporary_path.replace(self.path)
            except OSError as exc:
                raise PatientTemplateStoreError(
                    f"Unable to write patient templates to {self.path.name}."
                ) from exc
            finally:
                if temporary_path and temporary_path.exists():
                    temporary_path.unlink(missing_ok=True)
        return normalized
