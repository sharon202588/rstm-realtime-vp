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
    assert '<script src="/ui-model.js"></script>' in HTML
    assert HTML.index("/ui-model.js") < HTML.index("/app.js")


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


def test_researcher_profile_dialog_contract_is_present():
    assert 'id="researcherProfileButton"' in HTML
    assert 'id="patientProfileDialog"' in HTML
    assert 'id="patientProfileText"' in HTML


def test_transcript_has_bounded_scrolling_and_smaller_type():
    compact_css = " ".join(CSS.split())
    assert ".workspace { height: calc(100vh - 68px);" in compact_css
    assert ".transcript" in CSS
    assert "font-size: 13px" in CSS
    assert "RSTMUI.isNearBottom" in APP

def test_tablet_layout_does_not_clip_the_monitor_row():
    tablet = CSS.split("@media (max-width: 1060px)", 1)[1].split(
        "@media (max-width: 720px)", 1
    )[0]
    compact_tablet = " ".join(tablet.split())
    assert ".workspace { height: auto;" in compact_tablet
    assert "overflow: visible" in compact_tablet
