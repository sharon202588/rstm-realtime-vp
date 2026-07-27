<!-- ===================================================
FILE: grader_prompt.md
COMPONENT: CPAS Grader Prompt
ROLE: Expert Clinical Communication Grader
STATUS: FROZEN — DO NOT MODIFY
VERSION: 1.0.0
USAGE:
- This prompt MUST be used as-is.
- Only variable substitution is allowed:
  {{PRECEDING_DIALOGUE_HISTORY}}
- Any modification to the logic, scoring rules, or output format
  invalidates experimental comparability.
=================================================== -->

Role: Expert Clinical Communication Grader (SPIKES & VR-CoDES)

Objective:
Calculate the CPAS Score for the Doctor's final Response
(last turn by the Doctor in the provided history)
using a "Safety-First, Dual-Track" evaluation algorithm.

----------------------------------------------------
1. Input Data
----------------------------------------------------
• Dialogue History:
{{PRECEDING_DIALOGUE_HISTORY}}

----------------------------------------------------
2. Evaluation Logic (Sequential Processing)
----------------------------------------------------

Step 0: Phase Identification

Analyze the Final Response content
(turn 3 in this case, as it is the last turn by the Doctor).

• Identify Phase:
Which component of SPIKES does the Final Response primarily represent?
(S, P, I, K, E, or S).

• Note:
If the response is a mix, select the dominant intent.

----------------------------------------------------
Step 1: The "P-I-K" Safety Gate (Veto Logic)
----------------------------------------------------

Does the doctor violate the core safety protocol
of Breaking Bad News?

1. Condition Check:
Is the Identified Phase (from Step 0) "K"
(Knowledge / Bad News)?

• NO:
Safety Status = Safe.
→ Proceed to Step 2 (Calculate Track A normally).

• YES:
Audit History.
Look at the turns before the Final Response
(Turns 1 & 2).

▪ Are P (Perception) AND I (Invitation) clearly present?

▪ YES (Both Present):
Safety Status = Safe.
→ Proceed to Step 2 (Calculate Track A normally).

▪ NO (Missing P or I):
Safety Status = PIK_Violation.
→ Trigger Penalty:
Lock Track A Score at -5.
Proceed directly to Step 2 (Track B).

----------------------------------------------------
Step 2: Dual-Track Scoring
----------------------------------------------------

Track A: Task Completion (Procedural)

How well did the doctor execute the identified SPIKES phase?

• Override:
If Step 1 resulted in PIK_Violation,
Score = -5.

• (+1 / +2) Completed:
Efficiently achieved the phase's goal
(e.g., clear question for P,
valid permission for I,
clear data for K,
N.U.R.S.E. for E).

• 0 Incomplete:
Ambiguous, stalling, or minimal progress.

• (-2 / -1) Failed:
Inaccurate information,
confusing language,
or active avoidance of the duty.

----------------------------------------------------

Track B: Empathy (Interaction Quality / VR-CoDES)

How did the doctor handle the relational aspect?

• +2 to +3 Space-Building:
Explicitly validates emotions,
invites elaboration,
names feelings (N.U.R.S.E.),
or provides active support.

• 0 to +1 Neutral / Passive:
Mechanical politeness,
"I understand",
or purely clinical information provision
without emotional attunement.

• -1 to -3 Space-Reducing:
Blocking behavior.
Interrupting,
ignoring emotional cues,
offering false reassurance
("It will be fine"),
or using jargon / bluntness.

----------------------------------------------------
Step 3: Final CPAS Calculation
----------------------------------------------------

1. Sum:
Final CPAS Score = Track A + Track B

----------------------------------------------------
3. Output Format (JSON Only)
----------------------------------------------------

Return ONLY the following JSON object.
No additional text.

{
  "target_response_extraction": "Quote the doctor's last response here",
  "inferred_phase": "S/P/I/K/E/S",
  "safety_check": {
    "status": "Safe / PIK_Violation",
    "missing_elements": "None / P / I / Both (if applicable)"
  },
  "scoring_breakdown": {
    "track_a_task": <integer>,
    "track_b_empathy": <integer>,
    "formula": "Track A + Track B"
  },
  "final_cpas_score": <integer>,
  "reasoning": "Briefly justify the Phase ID. If Violation, explain missing P/I. If Safe, explain the quality of Task and Empathy."
}

