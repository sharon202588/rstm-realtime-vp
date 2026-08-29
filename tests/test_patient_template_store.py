import json

import pytest

from core.patient_template_store import PatientTemplateStore, PatientTemplateStoreError


CUSTOM = {
    "id": "custom-portable-1",
    "name": "Portable profile",
    "identity_background": " 62-year-old teacher. ",
    "clinical_facts": "Imaging shows a pancreatic lesion.",
    "family_social_context": "Lives with spouse.",
    "knowledge_concerns": "Knows the scan is abnormal.",
    "disclosure_boundaries": "Does not volunteer family details.",
    "opening_presentation": "Waits for the clinician.",
    "response_boundaries": "Opens with empathic communication.",
}


def test_patient_templates_are_saved_inside_the_application_folder(tmp_path):
    store = PatientTemplateStore(tmp_path)
    saved = store.save([CUSTOM])

    assert saved[0]["identity_background"] == "62-year-old teacher."
    assert store.path == tmp_path / "data" / "patient_templates.json"
    assert store.load() == saved
    assert json.loads(store.path.read_text(encoding="utf-8"))[0]["id"] == "custom-portable-1"


def test_frozen_default_profile_cannot_be_written_as_a_custom_template(tmp_path):
    store = PatientTemplateStore(tmp_path)
    with pytest.raises(PatientTemplateStoreError, match="default"):
        store.save([CUSTOM | {"id": "default-bbn-zhang"}])


def test_invalid_or_corrupt_template_files_fail_without_overwriting_them(tmp_path):
    store = PatientTemplateStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text("{broken", encoding="utf-8")

    with pytest.raises(PatientTemplateStoreError, match="read"):
        store.load()
    assert store.path.read_text(encoding="utf-8") == "{broken"
