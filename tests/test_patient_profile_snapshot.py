import json
from pathlib import Path

from core.realtime_voice_session import VoiceSessionConfig
from ui.server import ResearchEventLog, build_patient_profile_snapshot


PROJECT_ROOT = Path(__file__).parent.parent


def test_research_log_records_resolved_patient_profile_snapshot(tmp_path):
    config = VoiceSessionConfig(
        participant_id="P1",
        session_id="S1",
        retain_audio=False,
        audio_root=str(tmp_path),
        patient_profile_id="custom-case",
        patient_profile_name="Custom Case",
        patient_profile_text="PATIENT TEMPLATE: Custom Case\n\nCLINICAL FACTS:\nFacts",
    )

    event_log = ResearchEventLog(config)
    event_log.write(build_patient_profile_snapshot(config))

    record = json.loads(event_log.path.read_text(encoding="utf-8").strip())
    assert record["type"] == "patient_profile_snapshot"
    assert record["template_id"] == "custom-case"
    assert record["template_name"] == "Custom Case"
    assert "CLINICAL FACTS" in record["profile"]


def test_default_snapshot_uses_frozen_profile():
    config = VoiceSessionConfig("P1", "S1", retain_audio=False)

    snapshot = build_patient_profile_snapshot(config)

    assert snapshot["template_id"] == "default-bbn-zhang"
    assert snapshot["template_name"] == "肺部检查异常复诊（张老师）"
    assert snapshot["profile"] == (
        PROJECT_ROOT / "specs" / "patient_profile.md"
    ).read_text(encoding="utf-8")
