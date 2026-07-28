# Non-Adaptive Grading and Turn-Limit Design

## Goal

Keep the non-adaptive condition free of CPAS processing and bound every voice
session to 100 complete clinician-patient exchanges.

## Condition Behavior

- Adaptive sessions create one CPAS job for each complete clinician utterance.
- Non-adaptive sessions never create a CPAS job, call the grader API, emit grade
  events, or update RSTM state.
- The non-adaptive UI keeps the CPAS section visible for layout consistency but
  marks it as not used and explains that this mode does not perform CPAS
  scoring.
- Non-adaptive empty-state copy must not claim that scoring runs automatically.

## Turn Identifiers

- Clinician turns use `D-01` through `D-99`, followed by `D-100`.
- Patient turns use `P-01` through `P-99`, followed by `P-100`.
- Identifiers are unique within a session and reset only with a new session.

## Session Limit

- One complete exchange consists of one committed clinician turn followed by one
  committed patient turn.
- The session limit is 100 complete exchanges.
- When `P-100` is committed, clinician audio upload is disabled immediately.
- The system waits for the matching `TTSEnded` event so the final patient reply
  is not truncated.
- After `TTSEnded`, the backend emits a turn-limit status, stops the remote
  session, closes retained audio files, and emits the normal stopped status.
- No `D-101` or `P-101` turn can be committed.
- Manual stop and reset retain their existing behavior.

## Legacy Text Path

The text-mode dialogue manager follows the same experimental-condition rule:
non-adaptive processing generates the patient response but skips CPAS and RSTM
updates.

## Verification

- Unit tests prove the non-adaptive realtime and text paths do not call graders.
- Unit tests prove two-digit identifiers and the explicit 100th identifier.
- Unit tests prove the limit is enforced only after `P-100` and `TTSEnded`.
- UI tests prove bilingual non-adaptive and turn-limit copy.
- Full Python and JavaScript suites, syntax checks, and diff checks pass.
