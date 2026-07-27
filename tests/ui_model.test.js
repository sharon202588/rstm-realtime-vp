const assert = require("node:assert/strict");
const test = require("node:test");

const UI = require("../ui/static/ui-model.js");

test("interface copy follows the conversation language", () => {
  assert.equal(UI.t("zh", "brandName"), "实时语音虚拟患者");
  assert.equal(UI.t("en", "brandName"), "Realtime Voice Virtual Patient");
  assert.equal(UI.t("en", "modeFixed"), "Fixed Level 3");
});

test("interaction style descriptions follow the selected language", () => {
  assert.equal(UI.styleDescription("en", { level: 3 }), "Concerned / Downcast");
  assert.equal(UI.styleDescription("en", { level: 4 }), "Neutral");
  assert.equal(
    UI.styleDescription("en", { description: "Model-provided fallback" }),
    "Model-provided fallback",
  );
});

test("grade history replaces pending with the final result for one doctor turn", () => {
  let history = UI.upsertGrade([], {
    doctor_turn_id: "D-0001",
    grading_status: "pending",
  });
  assert.equal(history.length, 1);
  assert.equal(history[0].status, "pending");
  assert.equal(history[0].total, null);

  history = UI.upsertGrade(history, {
    doctor_turn_id: "D-0001",
    grading_status: "scored",
    display_score: 3,
    scoring_breakdown: {
      track_a_task: 1,
      track_b_empathy: 2,
    },
    safety_check: { status: "Safe" },
  });

  assert.equal(history.length, 1);
  assert.deepEqual(history[0], {
    doctorTurnId: "D-0001",
    status: "scored",
    trackA: 1,
    trackB: 2,
    total: 3,
    safetyStatus: "Safe",
    reason: "",
  });
});

test("newer doctor turns appear first and unscorable values stay empty", () => {
  let history = UI.upsertGrade([], {
    doctor_turn_id: "D-0001",
    grading_status: "scored",
    display_score: 1,
    scoring_breakdown: { track_a_task: 0, track_b_empathy: 1 },
  });
  history = UI.upsertGrade(history, {
    doctor_turn_id: "D-0002",
    grading_status: "unscorable",
    brief_rationale: "Final ASR text was unavailable.",
  });

  assert.deepEqual(history.map((item) => item.doctorTurnId), ["D-0002", "D-0001"]);
  assert.equal(history[0].trackA, null);
  assert.equal(history[0].trackB, null);
  assert.equal(history[0].total, null);
  assert.equal(history[0].reason, "Final ASR text was unavailable.");
});

test("automatic transcript scrolling only follows readers near the bottom", () => {
  assert.equal(
    UI.isNearBottom({ scrollTop: 530, clientHeight: 400, scrollHeight: 1000 }),
    true,
  );
  assert.equal(
    UI.isNearBottom({ scrollTop: 350, clientHeight: 400, scrollHeight: 1000 }),
    false,
  );
});

test("score tone preserves positive, neutral, negative, and unavailable states", () => {
  assert.equal(UI.scoreTone(2), "positive");
  assert.equal(UI.scoreTone(0), "neutral");
  assert.equal(UI.scoreTone(-1), "negative");
  assert.equal(UI.scoreTone(null), "unavailable");
});
