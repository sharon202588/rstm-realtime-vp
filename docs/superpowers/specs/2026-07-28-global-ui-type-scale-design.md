# Global UI Type Scale Design

## Goal

Improve readability and bilingual layout consistency across the local realtime
virtual-patient interface without increasing information density, changing
backend behavior, or causing sidebar controls to wrap.

## Approved Terminology

- Field label: `患者交互模式` / `Patient Interaction Mode`
- Adaptive option: `自适应` / `Adaptive`
- Non-adaptive option: `非自适应` / `Non-adaptive`

The full research-condition terminology remains available in the manuscript and
system logic. The interface uses the shorter option labels because the field
label already establishes the virtual-patient context.

## Type Scale

- Caption and secondary metadata: 12px
- Body text and field labels: 13px
- Reading text and primary actions: 14px
- Section headings: 15px
- Main page title: 24px

Large numeric status values remain unchanged because they form a separate
monitoring hierarchy.

## Component Rules

- Apply the type scale through shared CSS variables rather than component-level
  hard-coded values.
- Keep all command buttons at a consistent minimum height and prevent text from
  wrapping inside buttons.
- Increase segmented-control labels to the body size while preserving compact
  control height.
- Apply the larger caption size to score history, technical logs, patient
  metadata, status tags, and patient-profile form labels.
- Keep the 296px desktop sidebar and 272px tablet sidebar.
- Preserve truncation for long patient names and identifiers.
- Do not change backend commands, session behavior, CPAS scoring, or RSTM state
  handling.

## Verification

- Static contracts verify the approved bilingual labels and shared type tokens.
- JavaScript tests verify bilingual copy.
- Full Python and Node test suites remain green.
- The running local service must return the new versioned CSS and copy.
- Syntax and diff checks must pass.
