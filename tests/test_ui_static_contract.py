"""Static contracts for the local research voice interface."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
HTML = (PROJECT_ROOT / "ui" / "static" / "index.html").read_text(encoding="utf-8")
CSS = (PROJECT_ROOT / "ui" / "static" / "styles.css").read_text(encoding="utf-8")
APP = (PROJECT_ROOT / "ui" / "static" / "app.js").read_text(encoding="utf-8")


def test_product_naming_and_language_hooks_are_present():
    assert "实时语音虚拟患者" in HTML
    assert "测试台" not in HTML
    assert 'data-i18n="brandName"' in HTML
    assert 'data-i18n="patientMode"' in HTML
    assert 'data-i18n="conversationLanguage"' in HTML
    assert '<script src="/ui-model.js?v=' in HTML
    assert '<script src="/app.js?v=' in HTML
    assert HTML.index("/ui-model.js?v=") < HTML.index("/app.js?v=")


def test_cpas_two_track_history_and_mode_explanation_are_present():
    for element_id in (
        "trackAScore",
        "trackBScore",
        "scoreHistoryBody",
        "scoreHistoryEmpty",
        "modeExplanation",
    ):
        assert f'id="{element_id}"' in HTML
    assert "RSTMUI.upsertGrade" in APP
    assert 'id="scoreSection"' in HTML
    assert 't("cpasNotUsed")' in APP
    assert 'event.status === "limit_reached"' in APP


def test_researcher_profile_dialog_contract_is_present():
    assert 'id="researcherProfileButton"' in HTML
    assert 'id="patientProfileDialog"' in HTML
    assert 'id="patientProfileText"' in HTML


def test_transcript_has_bounded_scrolling_and_smaller_type():
    compact_css = " ".join(CSS.split())
    assert ".workspace { height: calc(100vh - 68px);" in compact_css
    assert ".transcript" in CSS
    assert "--font-reading: 14px;" in CSS
    assert "RSTMUI.isNearBottom" in APP

def test_tablet_layout_does_not_clip_the_monitor_row():
    tablet = CSS.split("@media (max-width: 1060px)", 1)[1].split(
        "@media (max-width: 720px)", 1
    )[0]
    compact_tablet = " ".join(tablet.split())
    assert ".workspace { height: auto;" in compact_tablet
    assert "overflow: visible" in compact_tablet


def test_new_session_is_the_single_full_reset_action():
    assert 'id="newParticipantSessionButton"' in HTML
    assert 'id="newSessionButton"' not in HTML
    assert 'id="resetButton"' not in HTML
    assert 'newParticipantSessionButton").addEventListener("click", newParticipantSession)' in APP


def test_conditions_use_concise_bilingual_labels_without_level_name():
    model = (PROJECT_ROOT / "ui" / "static" / "ui-model.js").read_text(encoding="utf-8")
    assert 'data-i18n="modeAdaptive">自适应</button>' in HTML
    assert 'data-i18n="modeFixed">非自适应</button>' in HTML
    assert 'modeAdaptive: "Adaptive"' in model
    assert 'modeFixed: "Non-adaptive"' in model
    assert "Fixed Interaction" not in model


def test_patient_template_controls_and_profile_payload_are_present():
    for element_id in (
        "patientTemplateSelect",
        "patientTemplateForm",
        "patientTemplateName",
        "createPatientTemplateButton",
        "savePatientTemplateButton",
        "deletePatientTemplateButton",
        "deleteSelectedPatientTemplateButton",
    ):
        assert f'id="{element_id}"' in HTML
    assert "patient_profile" in APP
    assert "RSTMUI.loadPatientTemplates" in APP
    assert 'fetch("/api/patient-templates"' in APP
    assert 'method: "PUT"' in APP
    assert "loadPersistedPatientTemplates" in APP
    assert APP.count("await persistPatientTemplates()") >= 3

def test_custom_patient_delete_is_visible_and_active_delete_resets_to_default():
    setup_start = HTML.index('<aside class="setup-panel">')
    setup_end = HTML.index('</aside>', setup_start)
    setup_html = HTML[setup_start:setup_end]
    model = (PROJECT_ROOT / "ui" / "static" / "ui-model.js").read_text(encoding="utf-8")

    assert 'id="deleteSelectedPatientTemplateButton"' in setup_html
    assert 'data-i18n="deletePatientTemplate"' in setup_html
    assert 'RSTMUI.patientTemplateDeletion(' in APP
    assert 'await newParticipantSession({ skipConfirm: true })' in APP
    assert 'confirmDeleteActiveTemplate' in APP
    assert 'confirmDeleteActiveTemplate: "Deleting the active patient profile will end the current conversation and switch to the default case. Delete it?"' in model


def test_patient_profile_activation_controls_are_explicit():
    assert 'id="confirmPatientTemplateButton"' in HTML
    assert 'id="cloneDefaultProfileButton"' in HTML
    assert 'id="activatePatientTemplateButton"' in HTML
    assert 'data-i18n-placeholder="templateNamePlaceholder"' in HTML
    assert 'data-i18n-placeholder="clinicalFactsPlaceholder"' in HTML
    assert 'data-profile-field="clinical_facts" maxlength="2000" required' in HTML
    assert 'id="patientTemplateName" maxlength="100" required' not in HTML
    assert '"__add_patient_profile__"' in APP
    assert "activePatientTemplateId" in APP
    assert "usePatientTemplateAndCreateSession" in APP


def test_reader_facing_header_and_default_case_copy_are_clinically_named():
    model = (PROJECT_ROOT / "ui" / "static" / "ui-model.js").read_text(encoding="utf-8")
    assert "RSTM-SP" not in HTML
    assert 'brandSubtitle: "医学沟通训练"' in model
    assert 'defaultPatientTemplate: "肺部检查异常复诊（张老师）"' in model
    assert 'defaultPatientTemplate: "Follow-up for Abnormal Lung Findings (Mr Zhang)"' in model

def test_patient_template_name_and_selector_cannot_expand_the_sidebar():
    compact_css = " ".join(CSS.split())
    assert 'id="patientTemplateName" maxlength="40"' in HTML
    assert ".select-control { width: 100%; min-width: 0; max-width: 100%;" in compact_css
    assert "text-overflow: ellipsis" in compact_css

def test_sidebar_actions_are_bounded_and_visually_distinct():
    compact_css = " ".join(CSS.split())
    assert 'class="danger-button session-stop-button" id="stopButton"' in HTML
    assert 'class="secondary-button new-session-button" id="newParticipantSessionButton"' in HTML
    assert ".setup-panel > * { min-width: 0; max-width: 100%;" in compact_css
    assert ".control-row { display: grid; grid-template-columns: minmax(0, 0.78fr) minmax(0, 1.22fr);" in compact_css
    assert ".control-row > button { width: 100%; min-width: 0;" in compact_css
    assert ".session-stop-button" in compact_css
    assert ".new-session-button" in compact_css


def test_sidebar_width_and_button_labels_are_optimized_for_both_languages():
    compact_css = " ".join(CSS.split())
    model = (PROJECT_ROOT / "ui" / "static" / "ui-model.js").read_text(encoding="utf-8")
    assert "grid-template-columns: 296px minmax(420px, 1fr) 340px;" in compact_css
    assert 'usePatientAndNewSession: "使用此患者"' in model
    assert 'usePatientAndNewSession: "Use This Patient"' in model
    assert 'researcherProfile: "管理患者设定"' in model
    assert 'researcherProfile: "Manage Profiles"' in model
    assert ".primary-button, .secondary-button, .danger-button" in compact_css
    assert "font-size: var(--font-reading);" in compact_css
    assert "white-space: nowrap;" in compact_css

def test_approved_patient_presence_and_compact_research_layout():
    compact_css = " ".join(CSS.split())
    assert 'class="patient-presence"' in HTML
    assert 'src="/assets/virtual-patient-mr-zhang.png"' in HTML
    assert 'id="patientPresenceName"' in HTML
    assert ".turn { max-width: min(72%, 820px); margin: 0 0 16px;" in compact_css
    assert ".turn-content" in compact_css and "line-height: 1.5" in compact_css
    assert ".score-history table { width: 100%; border-collapse: collapse; font-size: var(--font-caption);" in compact_css
    assert ".audit-log { max-height: 94px; overflow-y: auto; color: var(--muted); font-size: var(--font-caption);" in compact_css
    assert ".setup-panel { border-right: 1px solid var(--line); padding: 16px 18px;" in compact_css
    assert ".setup-panel .metadata-row, .setup-panel .connection-row { min-height: 30px;" in compact_css


def test_audio_setting_is_in_the_bottom_control_area_and_is_functional():
    control_start = HTML.index('<div class="control-stack">')
    control_end = HTML.index('</aside>', control_start)
    control_html = HTML[control_start:control_end]
    assert 'id="retainAudioSwitch" role="switch" aria-checked="false"' in control_html
    assert 'class="toggle checked" id="retainAudioSwitch"' not in control_html
    assert 'id="audioStatus" data-i18n="audioNotRetained"' in HTML
    assert "retainAudio: false" in APP
    assert 'retain_audio: state.retainAudio' in APP
    assert 'retainAudioSwitch").addEventListener("click"' in APP


def test_unscorable_copy_and_active_session_reset_confirmation_are_explicit():
    assert 'if (!skipConfirm && !window.confirm(t("confirmNewSession"))) return false;' in APP
    assert 'latest.status === "unscorable"' in APP
    assert 't("gradeUnscorableReason")' in APP
    assert '.status-tag.unscorable' in CSS

def test_listening_and_patient_response_use_distinct_accessible_indicators():
    compact_css = " ".join(CSS.split())
    assert 'class="voice-indicator" aria-hidden="true"><i></i><i></i><i></i>' in HTML
    assert ".voice-state.live .voice-indicator i" in compact_css
    assert ".voice-state.patient .voice-indicator i" in compact_css
    assert "@keyframes listeningBars" in CSS
    assert "@keyframes respondingDots" in CSS
    assert "@media (prefers-reduced-motion: reduce)" in CSS

def test_brand_icon_header_identifiers_and_type_scale_are_compact():
    compact_css = " ".join(CSS.split())
    setup_start = HTML.index('<aside class="setup-panel">')
    setup_end = HTML.index('</aside>', setup_start)
    setup_html = HTML[setup_start:setup_end]
    assert '>RS<' not in HTML
    assert 'class="brand-mark" src="/assets/realtime-virtual-patient-app-icon.png"' in HTML
    assert 'rel="icon" href="/assets/realtime-virtual-patient-app-icon.png"' in HTML
    assert 'class="header-identifiers"' in HTML
    assert 'id="participantId"' not in setup_html
    assert 'id="sessionId"' not in setup_html
    assert 'RSTMUI.sessionIdentifiers' in APP
    for token in (
        "--font-caption: 12px;",
        "--font-body: 13px;",
        "--font-reading: 14px;",
        "--font-section: 15px;",
        "--font-title: 24px;",
    ):
        assert token in CSS
    assert ".segment" in compact_css
    assert "font-size: var(--font-reading);" in compact_css
    assert ".header-identifiers" in compact_css


def test_rstm_trajectory_has_a_labeled_y_axis_and_system_events_are_collapsible():
    assert "const trajectoryGridValues = [-1, -0.7, -0.4, -0.1, 0, 0.1, 0.4, 0.7, 1];" in APP
    assert "const trajectoryLabelValues = [-1, 0, 1];" in APP
    assert "ctx.fillText(trajectoryTickLabel(value)" in APP
    assert 'data-i18n-aria="rstmTrajectoryAria"' in HTML
    assert '<details class="metric-section audit-section" id="auditSection">' in HTML
    assert '<summary class="section-heading collapsible-heading">' in HTML
    assert 'data-i18n="systemEvents"' in HTML
    assert '<details class="metric-section audit-section" id="auditSection" open>' not in HTML
    assert ".audit-section[open] .collapse-chevron" in CSS