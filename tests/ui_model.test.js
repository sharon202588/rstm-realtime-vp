const assert = require("node:assert/strict");
const test = require("node:test");

const UI = require("../ui/static/ui-model.js");

test("interface copy follows the conversation language", () => {
  assert.equal(UI.t("zh", "brandName"), "实时语音虚拟患者");
  assert.equal(UI.t("en", "brandName"), "Realtime Voice Virtual Patient");
  assert.equal(UI.t("zh", "modeAdaptive"), "自适应");
  assert.equal(UI.t("zh", "modeFixed"), "非自适应");
  assert.equal(UI.t("en", "modeAdaptive"), "Adaptive");
  assert.equal(UI.t("en", "modeFixed"), "Non-adaptive");
  assert.equal(UI.t("en", "usePatientAndNewSession"), "Use This Patient");
  assert.equal(UI.t("en", "researcherProfile"), "Manage Profiles");
  assert.equal(UI.t("en", "deletePatientTemplate"), "Delete");
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
const CUSTOM_TEMPLATE = {
  id: "custom-pancreas-1",
  name: "Pancreatic finding",
  identity_background: " 62-year-old retired engineer. ",
  clinical_facts: "Imaging suggests a pancreatic lesion.",
  family_social_context: "Lives with spouse.",
  knowledge_concerns: "Knows the scan was abnormal.",
  disclosure_boundaries: "Do not volunteer unasked family details.",
  opening_presentation: "Waits for the clinician to begin.",
  response_boundaries: "Opens gradually with clear and empathic communication.",
};

test("patient template storage falls back safely when local data is corrupt", () => {
  assert.deepEqual(UI.loadPatientTemplates("{not-json"), []);
  assert.deepEqual(UI.loadPatientTemplates(JSON.stringify([{ id: "broken" }])), []);
});

test("patient templates are normalized and replaced by stable id", () => {
  let templates = UI.upsertPatientTemplate([], CUSTOM_TEMPLATE);
  assert.equal(templates.length, 1);
  assert.equal(templates[0].identity_background, "62-year-old retired engineer.");

  templates = UI.upsertPatientTemplate(templates, {
    ...CUSTOM_TEMPLATE,
    name: "Updated case",
  });
  assert.equal(templates.length, 1);
  assert.equal(templates[0].name, "Updated case");
});

test("patient templates can be removed and converted to a backend payload", () => {
  const payload = UI.patientProfilePayload(CUSTOM_TEMPLATE);
  assert.equal(payload.id, "custom-pancreas-1");
  assert.equal(payload.identity_background, "62-year-old retired engineer.");

  const templates = UI.removePatientTemplate([payload], "custom-pancreas-1");
  assert.deepEqual(templates, []);
});
test("deleting the active custom patient falls back to the frozen default", () => {
  const result = UI.patientTemplateDeletion(
    [CUSTOM_TEMPLATE],
    "custom-pancreas-1",
    "custom-pancreas-1",
  );

  assert.deepEqual(result.templates, []);
  assert.equal(result.activeId, "default-bbn-zhang");
  assert.equal(result.selectedId, "default-bbn-zhang");
  assert.equal(result.deletedActive, true);
});

test("deleting another custom patient keeps the active patient", () => {
  const other = { ...CUSTOM_TEMPLATE, id: "custom-other", name: "Other case" };
  const result = UI.patientTemplateDeletion(
    [CUSTOM_TEMPLATE, other],
    "custom-other",
    "custom-pancreas-1",
  );

  assert.deepEqual(result.templates.map((item) => item.id), ["custom-pancreas-1"]);
  assert.equal(result.activeId, "custom-pancreas-1");
  assert.equal(result.selectedId, "custom-pancreas-1");
  assert.equal(result.deletedActive, false);
});

test("the frozen default patient cannot be deleted", () => {
  assert.throws(
    () => UI.patientTemplateDeletion(
      [CUSTOM_TEMPLATE],
      "default-bbn-zhang",
      "default-bbn-zhang",
    ),
    /default patient/i,
  );
});
test("blank patient template names are generated locally from clinical facts", () => {
  assert.equal(
    UI.generatedPatientTemplateName(
      "例行体检发现肺部阴影，经CT提示右上肺异常。",
      [],
    ),
    "例行体检发现肺部阴影",
  );
  assert.equal(
    UI.generatedPatientTemplateName("abcdefghijklmnopqrstuvwxYZ", []),
    "abcdefghijklmnopqrstuvwx…",
  );
  assert.equal(
    UI.generatedPatientTemplateName("肺部检查异常", ["肺部检查异常", "肺部检查异常（2）"]),
    "肺部检查异常（3）",
  );
});

test("clinical facts are the only required patient profile content", () => {
  const normalized = UI.normalizePatientTemplate({
    ...CUSTOM_TEMPLATE,
    name: "",
    identity_background: "",
    clinical_facts: "乳腺活检结果需要沟通。",
  });

  assert.equal(normalized.name, "乳腺活检结果需要沟通");
  assert.equal(normalized.identity_background, "");
  assert.throws(
    () => UI.normalizePatientTemplate({ ...CUSTOM_TEMPLATE, clinical_facts: "" }),
    /clinical facts/i,
  );
});
test("reader-facing patient profile copy uses the approved clinical naming", () => {
  assert.equal(UI.t("zh", "brandSubtitle"), "医学沟通训练");
  assert.equal(UI.t("zh", "defaultPatientTemplate"), "肺部检查异常复诊（张老师）");
  assert.equal(
    UI.t("en", "defaultPatientTemplate"),
    "Follow-up for Abnormal Lung Findings (Mr Zhang)",
  );
});
test("manual patient template names are limited to forty characters", () => {
  assert.equal(
    UI.normalizePatientTemplate({ ...CUSTOM_TEMPLATE, name: "x".repeat(40) }).name.length,
    40,
  );
  assert.throws(
    () => UI.normalizePatientTemplate({ ...CUSTOM_TEMPLATE, name: "x".repeat(41) }),
    /name/i,
  );
});
test("approved unscorable and reset copy is bilingual", () => {
  assert.equal(UI.t("zh", "gradeUnscorable"), "本轮未评分");
  assert.equal(
    UI.t("zh", "gradeUnscorableReason"),
    "未获得完整的医生语音转写，RSTM状态保持不变。",
  );
  assert.equal(UI.t("en", "gradeUnscorable"), "Not scored");
  assert.match(UI.t("zh", "confirmNewSession"), /当前会话将结束/);
  assert.match(UI.t("en", "confirmNewSession"), /current session will end/i);
});
test("non-adaptive and turn-limit messages are explicit in both languages", () => {
  assert.equal(UI.t("zh", "cpasNotUsed"), "非自适应模式不进行CPAS评分。");
  assert.equal(
    UI.t("en", "cpasNotUsed"),
    "CPAS scoring is not used in non-adaptive mode.",
  );
  assert.equal(UI.t("zh", "initialInteractionState"), "初始互动状态");
  assert.equal(UI.t("en", "initialInteractionState"), "Initial Interaction State");
  assert.match(UI.t("zh", "modeFixedNote"), /仅开场采用.*Level 3/);
  assert.match(UI.t("en", "modeFixedNote"), /opening only.*Level 3/i);
  assert.match(UI.t("zh", "turnLimitReached"), /100个完整来回/);
  assert.match(UI.t("en", "turnLimitReached"), /100 complete exchanges/i);
});
test("compact participant and session identifiers preserve date time and one token", () => {
  assert.deepEqual(
    UI.sessionIdentifiers(new Date(2026, 6, 28, 20, 4, 27), "90a5eec7"),
    {
      participantId: "P-260728-90A5EE",
      sessionId: "S-200427-90A5EE",
    },
  );
});

test("system event and trajectory accessibility copy is bilingual", () => {
  assert.equal(UI.t("zh", "systemEvents"), "\u8fd0\u884c\u8bb0\u5f55");
  assert.equal(UI.t("en", "systemEvents"), "System Events");
  assert.match(UI.t("zh", "rstmTrajectoryAria"), /S\(t\)/);
  assert.match(UI.t("en", "rstmTrajectoryAria"), /vertical axis/i);
});
