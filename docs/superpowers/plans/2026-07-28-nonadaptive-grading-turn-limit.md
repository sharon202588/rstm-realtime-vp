# Non-Adaptive Grading and Turn Limit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skip CPAS entirely in non-adaptive sessions, use compact D/P turn identifiers, stop after 100 complete exchanges, and finish the approved global type-scale update.

**Architecture:** `RealtimeVoiceSession` remains the source of truth for turn numbering, grading dispatch, and the 100-exchange boundary. The browser only renders condition-specific status and responds to backend limit events. The legacy text manager receives the same non-adaptive grader guard.

**Tech Stack:** Python 3.11, asyncio, pytest, browser JavaScript, Node test runner, HTML/CSS.

## Global Constraints

- Adaptive sessions grade complete clinician turns asynchronously.
- Non-adaptive sessions do not create or execute CPAS jobs.
- Turn identifiers are `D-01`/`P-01` through `D-100`/`P-100`.
- Stop only after the `P-100` reply reaches `TTSEnded`.
- Caption/body/reading/section/title sizes are 12/13/14/15/24px.
- Backend commands, patient profiles, and Doubao connection protocol remain unchanged.

---

### Task 1: Realtime Condition and Turn Boundary

**Files:**
- Modify: `core/realtime_voice_session.py`
- Test: `tests/test_realtime_voice_session.py`

**Interfaces:**
- Produces: `MAX_COMPLETE_EXCHANGES = 100`
- Produces: compact turn ids and a `session` event with `status="limit_reached"`

- [ ] Add failing tests asserting non-adaptive sessions never call `grade_prompt`.
- [ ] Add failing tests for `D-01`, `P-01`, `D-100`, and `P-100`.
- [ ] Add a failing test that `P-100` waits for `TTSEnded`, then stops and emits the limit status.
- [ ] Guard grading dispatch with `config.adaptive_enabled`.
- [ ] Disable clinician upload at `P-100` and schedule a safe stop after `TTSEnded`.
- [ ] Run `pytest tests/test_realtime_voice_session.py -q`.

### Task 2: Legacy Text Condition

**Files:**
- Modify: `core/dialogue_manager.py`
- Test: `tests/test_dialogue_smoke.py`

**Interfaces:**
- Consumes: `DialogueManager.adaptive_enabled`
- Produces: `phase_b=None` and non-adaptive `phase_c` metadata without grader use

- [ ] Add a failing test whose non-adaptive grader raises if called.
- [ ] Move the CPAS branch behind `adaptive_enabled`.
- [ ] Preserve patient generation, transcript logging, and fixed Level 3 style.
- [ ] Run `pytest tests/test_dialogue_smoke.py -q`.

### Task 3: Condition-Specific UI

**Files:**
- Modify: `ui/static/ui-model.js`
- Modify: `ui/static/app.js`
- Modify: `ui/static/index.html`
- Modify: `ui/static/styles.css`
- Test: `tests/ui_model.test.js`
- Test: `tests/test_ui_static_contract.py`

**Interfaces:**
- Consumes: `session.status` values `limit_reached` and `stopped`
- Produces: bilingual CPAS-not-used and 100-exchange completion messages

- [ ] Add failing bilingual copy and DOM contract tests.
- [ ] Change mode options to `自适应`/`非自适应` and `Adaptive`/`Non-adaptive`.
- [ ] Render the CPAS panel as not used when the configured condition is non-adaptive.
- [ ] Stop microphone capture on the limit event while preserving queued patient playback.
- [ ] Apply the approved 12/13/14/15/24px type tokens and version static assets.
- [ ] Run `node --test tests/ui_model.test.js` and `pytest tests/test_ui_static_contract.py -q`.

### Task 4: Integrated Verification

**Files:**
- Verify only.

**Interfaces:**
- Consumes: all prior task outputs.

- [ ] Run `pytest -q`.
- [ ] Run `node --test tests/ui_model.test.js`.
- [ ] Run `node --check ui/static/ui-model.js` and `node --check ui/static/app.js`.
- [ ] Run `git diff --check`.
- [ ] Verify `http://127.0.0.1:7860/` serves the new versioned assets when the local service is running.
