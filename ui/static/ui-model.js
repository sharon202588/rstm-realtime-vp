(function exposeUIModel(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.RSTMUI = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function createUIModel() {
  const COPY = {
    zh: {
      pageTitle: "实时语音虚拟患者",
      brandName: "实时语音虚拟患者",
      brandSubtitle: "医学沟通训练",
      bridgeConnecting: "正在连接本地服务",
      bridgeConnected: "本地服务已连接",
      bridgeError: "本地服务连接异常",
      sessionSetup: "会话设置",
      participant: "受试者",
      sessionId: "会话编号",
      newParticipantSession: "生成新会话",
      patientMode: "患者交互模式",
      modeAdaptive: "自适应",
      modeFixed: "非自适应",
      conversationLanguage: "交流语言",
      patientTemplate: "患者设定",
      defaultPatientTemplate: "肺部检查异常复诊（张老师）",
      addPatientTemplate: "＋ 新增患者设定…",
      activePatientSuffix: " · 当前",
      usePatientAndNewSession: "使用此患者",
      saveAudio: "保存会话音频",
      audioFormats: "医生与患者 WAV",
      audioNotRetained: "音频不保存",
      researcherProfile: "管理患者设定",
      connections: "连接状态",
      localBridge: "本地桥接",
      realtimeSession: "实时会话",
      speechRecognition: "语音识别",
      patientVoice: "患者语音",
      waiting: "等待",
      startConversation: "开始对话",
      stop: "停止",
      newSessionCreated: "已生成新的受试者与会话",
      confirmNewSession: "当前会话将结束，对话记录和互动状态将重置。是否生成新会话？",
      scenarioTitle: "坏消息告知模拟",
      notStarted: "尚未开始",
      emptyTitle: "准备进行实时语音对话",
      emptyBodyAdaptive: "开始后直接与虚拟患者说话。系统会自动转写、回复并在后台完成评分。",
      emptyBodyControl: "开始后直接与虚拟患者说话。非自适应模式不进行CPAS评分。",
      resetTitle: "新会话已就绪",
      resetBody: "上一轮已结束，互动状态与对话记录均已清空。点击开始后直接与虚拟患者对话。",
      micOff: "麦克风未启用",
      micCapturing: "麦克风实时采集中",
      listening: "正在聆听",
      patientResponding: "患者正在回应",
      requestingMic: "请求麦克风权限",
      connectingPatient: "正在连接实时患者",
      interactionState: "互动状态",
      initialInteractionState: "初始互动状态",
      modeAdaptiveShort: "自适应",
      modeFixedShort: "非自适应",
      modeAdaptiveNote: "CPAS评分会更新RSTM并改变患者互动状态。",
      modeFixedNote: "仅开场采用 Level 3；后续依据病例与对话自然回应，不进行CPAS评分或RSTM更新。",
      concernedDowncast: "担忧 / 低落",
      cpasScore: "CPAS评分",
      noScore: "尚无评分",
      scoreRange: "范围 -8 至 +5",
      clinicalProcess: "流程完成度",
      empathyInteraction: "共情与互动质量",
      scoreHistory: "评分历史",
      turn: "轮次",
      processShort: "流程",
      empathyShort: "共情互动",
      total: "总分",
      noGradeHistory: "完成医生发言后显示逐轮评分。",
      processPrerequisiteMissing: "流程前置缺失",
      rstmTrajectory: "RSTM轨迹",
      rstmTrajectoryAria: "RSTM状态轨迹，纵轴为S(t)，范围-1至+1",
      turns: "{count}轮",
      systemEvents: "运行记录",
      audioPending: "音频待保存",
      logWaiting: "等待会话开始。",
      profileTitle: "患者设定与模板",
      profileSource: "默认病例保持冻结；自定义模板仅保存在本机浏览器",
      templateName: "模板名称（可选）",
      templateNamePlaceholder: "留空时根据临床事实自动生成",
      identityBackgroundPlaceholder: "例如：58岁，高中教师，已婚，有一名女儿",
      clinicalFactsPlaceholder: "必填，例如：CT提示右上肺异常，等待活检确认",
      familySocialContextPlaceholder: "例如：主要照顾年迈母亲，经济压力一般",
      knowledgeConcernsPlaceholder: "例如：知道检查异常，担心是否为恶性疾病",
      disclosureBoundariesPlaceholder: "例如：未被询问时不主动透露家庭压力",
      openingPresentationPlaceholder: "例如：神情紧张，等待医生先开口",
      responseBoundariesPlaceholder: "例如：解释清楚且有共情时逐渐愿意交流",
      identityBackground: "患者身份与背景",
      clinicalFacts: "临床事实",
      familySocialContext: "家庭与社会背景",
      knowledgeConcerns: "已知信息与主要担忧",
      disclosureBoundaries: "信息透露边界",
      openingPresentation: "开场表现",
      responseBoundaries: "患者反应边界",
      createPatientTemplate: "新建自定义模板",
      cloneDefaultProfile: "复制默认病例",
      savePatientTemplate: "保存模板",
      deletePatientTemplate: "删除设定",
      templateSaved: "患者模板已保存",
      templateDeleted: "患者模板已删除",
      templateFolderSaveFailed: "患者设定仅保存在当前浏览器，未写入项目文件夹。",
      templateInvalid: "请填写临床事实。",
      cannotDeleteActiveTemplate: "当前患者正在使用中，请先切换到其他患者。",
      confirmDeleteTemplate: "确定删除这个自定义患者模板吗？",
      confirmDeleteActiveTemplate: "\u5220\u9664\u5f53\u524d\u60a3\u8005\u8bbe\u5b9a\u5c06\u7ed3\u675f\u672c\u6b21\u5bf9\u8bdd\uff0c\u5e76\u5207\u6362\u5230\u9ed8\u8ba4\u75c5\u4f8b\u3002\u786e\u5b9a\u5220\u9664\u5417\uff1f",
      profileLoading: "正在读取患者设定…",
      profileLoadError: "无法读取患者设定。",
      close: "关闭",
      doctor: "医生",
      virtualPatient: "虚拟患者",
      statusConnected: "已连接",
      statusConnecting: "连接中",
      statusListening: "正在识别",
      statusSpeaking: "正在播放",
      statusUpdating: "正在更新患者状态",
      statusRefreshing: "更新中",
      statusFallback: "正在恢复实时会话",
      statusIdle: "就绪",
      statusStopped: "已停止",
      statusError: "异常",
      cpasNotUsedStatus: "不使用",
      cpasNotUsed: "非自适应模式不进行CPAS评分。",
      gradePending: "评分中",
      gradeScored: "已评分",
      gradeUnscorable: "本轮未评分",
      gradeUnscorableReason: "未获得完整的医生语音转写，RSTM状态保持不变。",
      gradeError: "评分异常",
      conversationStarted: "实时语音对话已开始",
      conversationStopped: "对话已停止",
      turnLimitReached: "已完成100个完整来回，会话自动结束。",
      resetAudit: "新会话已建立，互动状态与历史已清空",
      audioSaved: "会话音频已保存",
      filesSaved: "已保存 {count} 个文件",
      microphoneDenied: "麦克风权限被拒绝，请在浏览器地址栏允许后重试。",
unreadableMessage: "收到无法解析的本地服务消息。",
      serviceUnavailable: "本地服务未启动，请先运行 start_ui.cmd。",
      serviceNotConnected: "本地服务尚未连接。",
      runtimeError: "运行异常",
      rstmUpdated: "RSTM更新至 {state}",
      cpasAudit: "CPAS {turn}：{status}",
      errorAudit: "异常：{message}",
      style1: "激动 / 易怒",
      style2: "焦虑 / 担忧",
      style3: "担忧 / 低落",
      style4: "中性",
      style5: "轻度正面 / 鼓励",
      style6: "合作 / 参与",
      style7: "信任 / 安心",
    },
    en: {
      pageTitle: "Realtime Voice Virtual Patient",
      brandName: "Realtime Voice Virtual Patient",
      brandSubtitle: "Clinical Communication Training",
      bridgeConnecting: "Connecting to local service",
      bridgeConnected: "Local service connected",
      bridgeError: "Local service connection error",
      sessionSetup: "Session Setup",
      participant: "Participant",
      sessionId: "Session ID",
      newParticipantSession: "New Session",
      patientMode: "Patient Interaction Mode",
      modeAdaptive: "Adaptive",
      modeFixed: "Non-adaptive",
      conversationLanguage: "Conversation Language",
      patientTemplate: "Patient Profile",
      defaultPatientTemplate: "Follow-up for Abnormal Lung Findings (Mr Zhang)",
      addPatientTemplate: "+ Add Patient Profile…",
      activePatientSuffix: " · Active",
      usePatientAndNewSession: "Use This Patient",
      saveAudio: "Save Session Audio",
      audioFormats: "Clinician and patient WAV",
      audioNotRetained: "Audio not retained",
      researcherProfile: "Manage Profiles",
      connections: "Connection Status",
      localBridge: "Local Bridge",
      realtimeSession: "Realtime Session",
      speechRecognition: "Speech Recognition",
      patientVoice: "Patient Voice",
      waiting: "Waiting",
      startConversation: "Start Conversation",
      stop: "Stop",
      newSessionCreated: "A new participant and session have been created",
      confirmNewSession: "The current session will end, and its transcript and interaction state will be reset. Create a new session?",
      scenarioTitle: "Breaking Bad News Simulation",
      notStarted: "Not started",
      emptyTitle: "Ready for a realtime voice conversation",
      emptyBodyAdaptive: "Speak directly to the virtual patient. Transcription, response, and scoring run automatically.",
      emptyBodyControl: "Speak directly to the virtual patient. CPAS scoring is not used in non-adaptive mode.",
      resetTitle: "New session ready",
      resetBody: "The prior session has ended and its interaction state and transcript have been cleared. Start when ready.",
      micOff: "Microphone inactive",
      micCapturing: "Microphone streaming",
      listening: "Listening",
      patientResponding: "Patient responding",
      requestingMic: "Requesting microphone access",
      connectingPatient: "Connecting to realtime patient",
      interactionState: "Interaction State",
      initialInteractionState: "Initial Interaction State",
      modeAdaptiveShort: "Adaptive",
      modeFixedShort: "Non-adaptive",
      modeAdaptiveNote: "CPAS updates RSTM and can change the patient interaction state.",
      modeFixedNote: "The opening only uses Level 3; subsequent responses follow the case and dialogue naturally, without CPAS scoring or RSTM updates.",
      concernedDowncast: "Concerned / Downcast",
      cpasScore: "CPAS Score",
      noScore: "No score",
      scoreRange: "Range -8 to +5",
      clinicalProcess: "Clinical Process",
      empathyInteraction: "Empathy & Interaction",
      scoreHistory: "Score History",
      turn: "Turn",
      processShort: "Process",
      empathyShort: "Empathy",
      total: "Total",
      noGradeHistory: "Turn-by-turn scores appear after the clinician speaks.",
      processPrerequisiteMissing: "Missing process prerequisites",
      rstmTrajectory: "RSTM Trajectory",
      rstmTrajectoryAria: "RSTM state trajectory; the vertical axis is S(t), ranging from -1 to +1",
      turns: "{count} turns",
      systemEvents: "System Events",
      audioPending: "Audio pending",
      logWaiting: "Waiting for the session to start.",
      profileTitle: "Patient Profiles and Templates",
      profileSource: "The default case is frozen; custom templates are stored only in this browser.",
      templateName: "Template name (optional)",
      templateNamePlaceholder: "Leave blank to generate from clinical facts",
      identityBackgroundPlaceholder: "Example: 58-year-old married high-school teacher",
      clinicalFactsPlaceholder: "Required, e.g. CT shows a right upper-lung abnormality awaiting biopsy",
      familySocialContextPlaceholder: "Example: Primary carer for an elderly parent",
      knowledgeConcernsPlaceholder: "Example: Knows the scan is abnormal and fears malignancy",
      disclosureBoundariesPlaceholder: "Example: Does not volunteer family pressure unless asked",
      openingPresentationPlaceholder: "Example: Appears tense and waits for the clinician to begin",
      responseBoundariesPlaceholder: "Example: Opens gradually when explanations are clear and empathic",
      identityBackground: "Patient identity and background",
      clinicalFacts: "Clinical facts",
      familySocialContext: "Family and social context",
      knowledgeConcerns: "Known information and concerns",
      disclosureBoundaries: "Disclosure boundaries",
      openingPresentation: "Opening presentation",
      responseBoundaries: "Response boundaries",
      createPatientTemplate: "Create Custom Template",
      cloneDefaultProfile: "Clone Default Profile",
      savePatientTemplate: "Save Template",
      deletePatientTemplate: "Delete",
      templateSaved: "Patient template saved",
      templateDeleted: "Patient template deleted",
      templateFolderSaveFailed: "The profile is saved only in this browser and was not written to the application folder.",
      templateInvalid: "Enter the clinical facts.",
      cannotDeleteActiveTemplate: "This patient is active. Switch to another patient before deleting it.",
      confirmDeleteTemplate: "Delete this custom patient template?",
      confirmDeleteActiveTemplate: "Deleting the active patient profile will end the current conversation and switch to the default case. Delete it?",
      profileLoading: "Loading patient profile…",
      profileLoadError: "Unable to load the patient profile.",
      close: "Close",
      doctor: "Clinician",
      virtualPatient: "Virtual Patient",
      statusConnected: "Connected",
      statusConnecting: "Connecting",
      statusListening: "Recognizing",
      statusSpeaking: "Playing",
      statusUpdating: "Updating patient state",
      statusRefreshing: "Updating",
      statusFallback: "Restoring realtime session",
      statusIdle: "Ready",
      statusStopped: "Stopped",
      statusError: "Error",
      cpasNotUsedStatus: "Not used",
      cpasNotUsed: "CPAS scoring is not used in non-adaptive mode.",
      gradePending: "Scoring",
      gradeScored: "Scored",
      gradeUnscorable: "Not scored",
      gradeUnscorableReason: "A complete clinician speech transcript was not available. The RSTM state remains unchanged.",
      gradeError: "Scoring error",
      conversationStarted: "Realtime voice conversation started",
      conversationStopped: "Conversation stopped",
      turnLimitReached: "100 complete exchanges reached. The session ended automatically.",
      resetAudit: "New session created; interaction state and history cleared",
      audioSaved: "Session audio saved",
      filesSaved: "{count} files saved",
      microphoneDenied: "Microphone permission was denied. Allow access in the browser address bar and retry.",
unreadableMessage: "The local service returned an unreadable message.",
      serviceUnavailable: "The local service is not running. Start it with start_ui.cmd.",
      serviceNotConnected: "The local service is not connected.",
      runtimeError: "Runtime error",
      rstmUpdated: "RSTM updated to {state}",
      cpasAudit: "CPAS {turn}: {status}",
      errorAudit: "Error: {message}",
      style1: "Agitated / Irritated",
      style2: "Anxious / Worried",
      style3: "Concerned / Downcast",
      style4: "Neutral",
      style5: "Mildly Positive / Encouraging",
      style6: "Cooperative / Engaged",
      style7: "Trusting / Reassured",
    },
  };

  function sessionIdentifiers(dateValue, tokenValue) {
    const date = dateValue instanceof Date ? dateValue : new Date(dateValue);
    if (Number.isNaN(date.getTime())) throw new Error("A valid session date is required.");
    const token = String(tokenValue || "").replace(/[^A-Za-z0-9]/g, "").toUpperCase().slice(0, 6);
    if (token.length < 6) throw new Error("A six-character session token is required.");
    const pad = (value) => String(value).padStart(2, "0");
    const datePart = `${String(date.getFullYear()).slice(-2)}${pad(date.getMonth() + 1)}${pad(date.getDate())}`;
    const timePart = `${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
    return {
      participantId: `P-${datePart}-${token}`,
      sessionId: `S-${timePart}-${token}`,
    };
  }
  function languageOf(language) {
    return language === "en" ? "en" : "zh";
  }

  function t(language, key, values = {}) {
    const selected = COPY[languageOf(language)];
    const template = selected[key] ?? COPY.zh[key] ?? key;
    return Object.entries(values).reduce(
      (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
      template,
    );
  }

  function numericOrNull(value) {
    if (value === null || value === undefined || value === "") return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function upsertGrade(history, event) {
    const doctorTurnId = String(event.doctor_turn_id || "").trim();
    if (!doctorTurnId) return history.slice();

    const existing = history.find((item) => item.doctorTurnId === doctorTurnId);
    if (existing?.status === "scored" && event.grading_status === "pending") {
      return history.slice();
    }

    const breakdown = event.scoring_breakdown || {};
    const item = {
      doctorTurnId,
      status: String(event.grading_status || "error"),
      trackA: numericOrNull(breakdown.track_a_task),
      trackB: numericOrNull(breakdown.track_b_empathy),
      total: event.grading_status === "scored"
        ? numericOrNull(event.display_score ?? event.control_score)
        : null,
      safetyStatus: String(event.safety_check?.status || ""),
      reason: String(event.brief_rationale || ""),
    };
    return [item, ...history.filter((entry) => entry.doctorTurnId !== doctorTurnId)];
  }

  function isNearBottom(metrics, threshold = 80) {
    const distance = metrics.scrollHeight - metrics.clientHeight - metrics.scrollTop;
    return distance <= threshold;
  }

  function scoreTone(value) {
    const numeric = numericOrNull(value);
    if (numeric === null) return "unavailable";
    if (numeric > 0) return "positive";
    if (numeric < 0) return "negative";
    return "neutral";
  }

  function styleDescription(language, style) {
    const level = Number(style?.level);
    if (Number.isInteger(level) && level >= 1 && level <= 7) {
      return t(language, `style${level}`);
    }
    return style?.description || "";
  }

  const PATIENT_PROFILE_FIELDS = [
    "identity_background",
    "clinical_facts",
    "family_social_context",
    "knowledge_concerns",
    "disclosure_boundaries",
    "opening_presentation",
    "response_boundaries",
  ];

  function generatedPatientTemplateName(clinicalFacts, existingNames = []) {
    const cleaned = String(clinicalFacts || "")
      .trim()
      .replace(/^[\s•*\-—_]+/u, "")
      .split(/[。！？；，,.!?;\r\n]/u, 1)[0]
      .replace(/\s+/gu, " ")
      .trim();
    if (!cleaned) throw new Error("Clinical facts are required.");

    const characters = Array.from(cleaned);
    const base = characters.length > 24
      ? `${characters.slice(0, 24).join("")}…`
      : cleaned;
    const used = new Set((existingNames || []).map((name) => String(name).trim()));
    if (!used.has(base)) return base;
    let suffix = 2;
    while (used.has(`${base}（${suffix}）`)) suffix += 1;
    return `${base}（${suffix}）`;
  }

  function normalizePatientTemplate(value, existingNames = []) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("Patient template must be an object.");
    }

    const id = String(value.id || "").trim();
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(id)) {
      throw new Error("Patient template id is invalid.");
    }

    const normalized = { id, name: "" };
    let totalLength = 0;
    for (const field of PATIENT_PROFILE_FIELDS) {
      const fieldValue = String(value[field] || "").trim();
      if (fieldValue.length > 2000) {
        throw new Error(`Patient template field ${field} is too long.`);
      }
      normalized[field] = fieldValue;
      totalLength += fieldValue.length;
    }

    if (!normalized.clinical_facts) {
      throw new Error("Clinical facts are required.");
    }
    const suppliedName = String(value.name || "").trim();
    normalized.name = suppliedName || generatedPatientTemplateName(
      normalized.clinical_facts,
      existingNames,
    );
    if (Array.from(normalized.name).length > 40) {
      throw new Error("Patient template name is invalid.");
    }
    if (totalLength > 10000) {
      throw new Error("Patient template is too long.");
    }
    return normalized;
  }

  function loadPatientTemplates(raw) {
    try {
      const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
      if (!Array.isArray(parsed)) return [];
      return parsed.flatMap((item) => {
        try {
          return [normalizePatientTemplate(item)];
        } catch {
          return [];
        }
      });
    } catch {
      return [];
    }
  }

  function upsertPatientTemplate(templates, template) {
    const existing = Array.isArray(templates) ? templates : [];
    const existingNames = existing
      .filter((item) => item?.id !== template?.id)
      .map((item) => item?.name || "");
    const normalized = normalizePatientTemplate(template, existingNames);
    return [
      normalized,
      ...existing.filter((item) => item?.id !== normalized.id),
    ];
  }

  function removePatientTemplate(templates, id) {
    if (!Array.isArray(templates)) return [];
    return templates.filter((item) => item?.id !== id);
  }

  function patientTemplateDeletion(templates, selectedId, activeId) {
    const defaultId = "default-bbn-zhang";
    if (selectedId === defaultId) {
      throw new Error("The default patient cannot be deleted.");
    }
    const existing = Array.isArray(templates) ? templates : [];
    if (!existing.some((item) => item?.id === selectedId)) {
      throw new Error("The selected patient template does not exist.");
    }
    const deletedActive = selectedId === activeId;
    const nextActiveId = deletedActive ? defaultId : activeId;
    return {
      templates: removePatientTemplate(existing, selectedId),
      activeId: nextActiveId,
      selectedId: nextActiveId,
      deletedActive,
    };
  }

  function patientProfilePayload(template) {
    return normalizePatientTemplate(template);
  }

  return {
    COPY,
    sessionIdentifiers,
    t,
    upsertGrade,
    isNearBottom,
    scoreTone,
    styleDescription,
    PATIENT_PROFILE_FIELDS,
    generatedPatientTemplateName,
    normalizePatientTemplate,
    loadPatientTemplates,
    upsertPatientTemplate,
    removePatientTemplate,
    patientTemplateDeletion,
    patientProfilePayload,
  };
}));
