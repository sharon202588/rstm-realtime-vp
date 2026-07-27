# Program Requirements From Manuscript

This note translates the manuscript and supplementary design into engineering
requirements for fast validation and implementation.

## Fixed Research Constraints

- The system must support an RSTM-enabled adaptive virtual patient condition.
- The system must also support a non-adaptive virtual patient condition for
  matched comparison, with no relational-state update applied.
- RSTM parameters are fixed across scenarios and conditions:
  - `K = 5`
  - `lambda = 0.8`
  - `c = 0.10`
  - `DELTA = 0.20`
- CPAS is the turn-level control signal for RSTM.
- CPAS combines:
  - SPIKES-derived task or stage appropriateness.
  - VR-CoDES-informed emotional and interactional quality.
- CPAS final score range is `-8` to `+5`.
- CPAS output should remain structured and include:
  - clinician response
  - inferred SPIKES stage
  - safety-check status
  - Track A score
  - Track B score
  - final CPAS score
  - brief rationale
- The seven-level affective-interaction mapping is fixed and must not be
  changed at runtime.
- Level boundaries must follow Supplementary Table S1:
  - Level 1: `[-1.00, -0.70)`
  - Level 2: `[-0.70, -0.40)`
  - Level 3: `[-0.40, -0.10)`
  - Level 4: `[-0.10, +0.10]`
  - Level 5: `(+0.10, +0.40]`
  - Level 6: `(+0.40, +0.70]`
  - Level 7: `(+0.70, +1.00]`

## Fast Feasibility Tests

- Offline unit tests must run without API credentials.
- A no-network dialogue smoke test must exercise Phase A-D:
  - patient response generation
  - CPAS scoring
  - RSTM update
  - style remapping
- Real API tests should be separated from offline tests to avoid consuming
  model quota during routine validation.
- Runtime tests should use a temporary state file unless persistence is the
  target of the test.

## Needed Product Decisions

Resolved decisions for the current implementation:

- Store complete learner-VP dialogue as text only.
- Store CPAS raw model output plus a compact rationale excerpt.
- Store a short RSTM trajectory per turn.
- Do not retain audio files by default.
- Keep an explicit audio-retention switch for future protocol changes.
- Force reset RSTM state for each participant/session.
- Use Level 3 (`S(t) = -0.25`) as the default starting state for breaking bad
  news sessions, reflecting a concerned/downcast patient baseline before the
  learner's communication has had any effect.
- Use the same Level 3 baseline for the non-adaptive VP unless explicitly
  overridden, but do not apply RSTM updates in that condition. This is an
  implementation-level matching rule derived from the manuscript's matched
  condition design; it is not currently a separate manuscript claim.
- Start each breaking-bad-news session with the learner/clinician speaking
  first by default.
- Keep a fixed patient opening utterance only as an optional test mode, because
  automatic VP opening can over-constrain scenario entry.
- Treat CPAS as an internal control signal, not as a separately validated
  human-auditable score.
- Implement breaking bad news as the initial scenario.
- Keep a scenario parameter for future difficult-communication scenarios.
- Support Chinese and English at the run-entry level.

Remaining decisions before expanding the system beyond smoke tests:

- Training mode:
  - text-only prototype
  - real-time voice
  - both, with text mode as the deterministic fallback
- Experiment condition selection:
  - RSTM-enabled
  - non-adaptive
  - standardized-patient reference data entry only
- Privacy policy:
  - whether transcripts may contain identifiable participant data
  - whether audio is stored
  - whether API prompts/responses are retained

## Runtime Entry Conventions

- `--participant-id <id>`: learner identifier for logs.
- `--session-id <id>`: optional fixed session identifier. If omitted, a new
  identifier is generated.
- `--language zh|en`: response language.
- `--non-adaptive`: run the fixed-style non-adaptive VP condition.
- `--initial-state <float>`: override the scenario default starting state.
- `--fixed-style-state <float>`: override the non-adaptive fixed state.
- `--retain-audio`: keep the audio retention flag enabled for future audio
  file storage; current text logging remains unchanged unless audio file paths
  are supplied by the voice layer.
- `--case-text <text>`: append session-specific case context to the fixed
  patient profile for testing.
- `--case-file <path>`: load session-specific case context from a UTF-8 text
  file for testing.
- `--vp-opens`: optional mode where the VP speaks the fixed opening utterance
  before the clinician's first turn.

## Frozen Breaking-Bad-News Defaults

- Scenario: `breaking_bad_news`
- Initial state: `S(t) = -0.25`
- Initial style: Level 3, `Concerned / Downcast`
- Default first speaker: learner/clinician.
- Optional Chinese VP opening: `医生，我这次检查结果是不是不太好？我这几天一直有点担心。`
- Optional English VP opening: `Doctor, are my test results not good? I have been worried about them these past few days.`
- Audio retention: off by default.
