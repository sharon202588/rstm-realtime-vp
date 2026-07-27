(function exposeUIModel(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.RSTMUI = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function createUIModel() {
  const COPY = {
    zh: {
      pageTitle: "实时语音虚拟患者",
      brandName: "实时语音虚拟患者",
      brandSubtitle: "RSTM-SP · 医学沟通训练",
      bridgeConnecting: "正在连接本地服务",
      bridgeConnected: "本地服务已连接",
      bridgeError: "本地服务连接异常",
      sessionSetup: "会话设置",
      participant: "受试者",
      sessionId: "会话编号",
      newSession: "生成新会话",
      patientMode: "患者交互模式",
      modeAdaptive: "自适应患者",
      modeFixed: "固定 Level 3",
      conversationLanguage: "交流语言",
      saveAudio: "保存会话音频",
      audioFormats: "医生与患者 WAV",
      researcherProfile: "研究者查看患者设定",
      connections: "连接状态",
      localBridge: "本地桥接",
      realtimeSession: "实时会话",
      speechRecognition: "语音识别",
      patientVoice: "患者语音",
      waiting: "等待",
      startConversation: "开始对话",
      stop: "停止",
      forceReset: "强制重置",
      scenarioTitle: "坏消息告知模拟",
      notStarted: "尚未开始",
      emptyTitle: "准备进行实时语音对话",
      emptyBody: "开始后直接与虚拟患者说话。系统会自动转写、回复并在后台完成评分。",
      resetTitle: "已重置，准备新一轮会话",
      resetBody: "所有互动状态已恢复到 Level 3。点击开始后直接与虚拟患者对话。",
      micOff: "麦克风未启用",
      micCapturing: "麦克风实时采集中",
      listening: "正在聆听",
      patientResponding: "患者正在回应",
      requestingMic: "请求麦克风权限",
      connectingPatient: "正在连接实时患者",
      interactionState: "互动状态",
      modeAdaptiveShort: "自适应",
      modeFixedShort: "固定 Level 3",
      modeAdaptiveNote: "CPAS评分会更新RSTM并改变患者互动状态。",
      modeFixedNote: "固定 Level 3；CPAS仅记录，不改变患者。",
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
      turns: "{count}轮",
      sessionLog: "会话记录",
      audioPending: "音频待保存",
      logWaiting: "等待会话开始。",
      profileTitle: "模拟患者完整设定",
      profileSource: "研究者信息 · 来源：冻结患者设定文件",
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
      gradePending: "评分中",
      gradeScored: "已评分",
      gradeUnscorable: "无法评分",
      gradeError: "评分异常",
      conversationStarted: "实时语音对话已开始",
      conversationStopped: "对话已停止",
      resetAudit: "已强制重置至 Level 3",
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
      brandSubtitle: "RSTM-SP · Clinical Communication Training",
      bridgeConnecting: "Connecting to local service",
      bridgeConnected: "Local service connected",
      bridgeError: "Local service connection error",
      sessionSetup: "Session Setup",
      participant: "Participant",
      sessionId: "Session ID",
      newSession: "New Session",
      patientMode: "Patient Interaction Mode",
      modeAdaptive: "Adaptive Patient",
      modeFixed: "Fixed Level 3",
      conversationLanguage: "Conversation Language",
      saveAudio: "Save Session Audio",
      audioFormats: "Clinician and patient WAV",
      researcherProfile: "Researcher Patient Profile",
      connections: "Connection Status",
      localBridge: "Local Bridge",
      realtimeSession: "Realtime Session",
      speechRecognition: "Speech Recognition",
      patientVoice: "Patient Voice",
      waiting: "Waiting",
      startConversation: "Start Conversation",
      stop: "Stop",
      forceReset: "Force Reset",
      scenarioTitle: "Breaking Bad News Simulation",
      notStarted: "Not started",
      emptyTitle: "Ready for a realtime voice conversation",
      emptyBody: "Speak directly to the virtual patient. Transcription, response, and scoring run automatically.",
      resetTitle: "Reset complete",
      resetBody: "The interaction state is back at Level 3. Start a new conversation when ready.",
      micOff: "Microphone inactive",
      micCapturing: "Microphone streaming",
      listening: "Listening",
      patientResponding: "Patient responding",
      requestingMic: "Requesting microphone access",
      connectingPatient: "Connecting to realtime patient",
      interactionState: "Interaction State",
      modeAdaptiveShort: "Adaptive",
      modeFixedShort: "Fixed Level 3",
      modeAdaptiveNote: "CPAS updates RSTM and can change the patient interaction state.",
      modeFixedNote: "Fixed at Level 3; CPAS is recorded but does not alter the patient.",
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
      turns: "{count} turns",
      sessionLog: "Session Log",
      audioPending: "Audio pending",
      logWaiting: "Waiting for the session to start.",
      profileTitle: "Complete Simulated Patient Profile",
      profileSource: "Researcher information · Source: frozen patient profile",
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
      gradePending: "Scoring",
      gradeScored: "Scored",
      gradeUnscorable: "Unscorable",
      gradeError: "Scoring error",
      conversationStarted: "Realtime voice conversation started",
      conversationStopped: "Conversation stopped",
      resetAudit: "Force reset to Level 3",
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

  return {
    COPY,
    t,
    upsertGrade,
    isNearBottom,
    scoreTone,
    styleDescription,
  };
}));
