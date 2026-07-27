<!-- ===================================================
FILE: affective_interaction_mapping.md
COMPONENT: Affective–Interaction Adaptation Specification
STATUS: FROZEN — DO NOT MODIFY
VERSION: 1.0.0
ROLE:
Defines how the continuous relational state S(t) is
deterministically mapped to discrete affective–interaction
styles that constrain virtual patient behavior.
=================================================== -->

## Overview

This specification defines a deterministic mapping from the
continuous relational state S(t) ∈ (-1, 1) to a set of discrete
affective–interaction styles.

The mapping serves as a control layer between the internal
Relational State Trajectory Model (RSTM) and external language
and speech generation modules.

The mapping itself is rule-based and model-agnostic.

---

## Mapping Principle

- Input: Continuous relational state S(t)
- Output: One and only one affective–interaction style
- The mapping is:
  - Deterministic
  - Mutually exclusive
  - Exhaustive over (-1, 1)
- Adjacent levels differ primarily in affective valence,
  interactional openness, and prosodic engagement.

---

## 7-Level Affective–Interaction Mapping

### Level 1: Agitated / Irritated
**Range:** [-1.00, -0.70)

**Interaction Style:** Reactive  
**Behavioral Cues:**  
Fast, loud, sharp articulation; tense breathing;
abrupt, confrontational responses.

---

### Level 2: Anxious / Worried
**Range:** [-0.70, -0.40)

**Interaction Style:** Anxious  
**Behavioral Cues:**  
Soft but shaky voice; uneven rhythm; nervous hesitations;
uncertain phrasing.

---

### Level 3: Concerned / Downcast
**Range:** [-0.40, -0.10)

**Interaction Style:** Downcast  
**Behavioral Cues:**  
Slow pace; low energy; muffled tone;
long pauses; downward emotional weight.

---

### Level 4: Neutral
**Range:** [-0.10, +0.10]

**Interaction Style:** Flat  
**Behavioral Cues:**  
Even volume; steady pace;
no emotional coloring;
purely factual delivery.

**Note:**  
Neutral is the only closed interval on both ends,
ensuring continuity at the origin.

---

### Level 5: Mildly Positive / Encouraging
**Range:** (+0.10, +0.40]

**Interaction Style:** Warm  
**Behavioral Cues:**  
Light warmth; soft upward pitch;
calm, encouraging phrasing.

---

### Level 6: Cooperative / Engaged
**Range:** (+0.40, +0.70]

**Interaction Style:** Engaged  
**Behavioral Cues:**  
Clear, warm voice; responsive cues;
active engagement; supportive interaction.

---

### Level 7: Trusting / Reassured
**Range:** (+0.70, +1.00]

**Interaction Style:** Reassuring  
**Behavioral Cues:**  
Soft, smooth tone; flowing delivery;
comforting presence; openly trusting.

---

## Usage Constraints

- This mapping MUST be applied after each RSTM update.
- The resulting style constrains:
  - Linguistic tone
  - Interactional openness
  - Prosodic realization (in speech models)
- The mapping does NOT generate language by itself.
- The mapping MUST NOT be altered at runtime.

---

## Design Rationale (Informative)

The seven levels are chosen to balance:
- Perceptual distinguishability
- Emotional continuity
- Pedagogical controllability

This discretization enables interpretable control of
affective fidelity while preserving smooth relational dynamics.

