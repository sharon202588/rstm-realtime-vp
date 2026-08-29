const RSTMUI = window.RSTMUI;
const UI = RSTMUI;

const state = {
  socket: null,
  condition: "adaptive",
  language: "zh",
  running: false,
  sessionLimitReached: false,
  retainAudio: false,
  uploadEnabled: false,
  stream: null,
  captureContext: null,
  captureSource: null,
  worklet: null,
  silentGain: null,
  playbackContext: null,
  playbackSources: new Set(),
  nextPlaybackTime: 0,
  trajectory: [-0.25],
  rstmTurnCount: 0,
  gradeHistory: [],
  connectionStatus: {},
  auditStarted: false,
  profileLoaded: false,
  patientTemplates: [],
  selectedPatientTemplateId: "default-bbn-zhang",
  activePatientTemplateId: "default-bbn-zhang",
  activePatientProfile: null,
  editingPatientTemplateId: null,
  currentStyle: { level: 3, name: "Concerned / Downcast", description: "" },
  toastTimer: null,
};

const $ = (id) => document.getElementById(id);
const t = (key, values) => UI.t(state.language, key, values);
const PATIENT_TEMPLATE_STORAGE_KEY = "rstm.patientTemplates.v1";
const ADD_PATIENT_PROFILE_OPTION = "__add_patient_profile__";
const DEFAULT_PATIENT_TEMPLATE_DRAFT = {
  name: "肺部检查异常复诊（张老师）副本",
  identity_background: "张老师，58岁，男性，高中教师。已婚，与妻子和12岁女儿共同生活，并照顾住在附近的82岁母亲。",
  clinical_facts: "例行体检发现肺部阴影，CT提示右上肺Ⅱ期癌变可能，等待活检确认与治疗计划。",
  family_social_context: "普通工薪家庭，生活尚可但无积蓄；重视家庭责任，不愿让家人担心。",
  knowledge_concerns: "知道检查结果异常，担心是否为恶性疾病以及自己能否继续承担家庭责任。",
  disclosure_boundaries: "不主动确认尚未由医生说明的诊断；未被询问时不主动展开家庭经济压力。",
  opening_presentation: "神情克制但紧张，等待医生先说明检查情况。",
  response_boundaries: "医生解释清楚并表达共情时逐步开放；表达含糊或生硬时会追问并更加担忧。",
};

const STATUS_KEYS = {
  waiting: "waiting",
  connected: "statusConnected",
  connecting: "statusConnecting",
  listening: "statusListening",
  speaking: "statusSpeaking",
  updating: "statusUpdating",
  refreshing: "statusRefreshing",
  fallback_reconnecting: "statusFallback",
  idle: "statusIdle",
  stopped: "statusStopped",
  error: "statusError",
};

const GRADE_KEYS = {
  pending: "gradePending",
  scored: "gradeScored",
  unscorable: "gradeUnscorable",
  error: "gradeError",
};

function statusLabel(status) {
  return t(STATUS_KEYS[status] || status);
}

function gradeLabel(status) {
  return t(GRADE_KEYS[status] || "noScore");
}

function createSessionIds() {
  const suffix = globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID().replace(/-/g, "").slice(0, 6)
    : Math.random().toString(36).slice(2, 8).padEnd(6, "0");
  const identifiers = RSTMUI.sessionIdentifiers(new Date(), suffix);
  $("participantId").textContent = identifiers.participantId;
  $("sessionId").textContent = identifiers.sessionId;
}

function applyLanguage() {
  document.documentElement.lang = state.language === "en" ? "en" : "zh-CN";
  document.title = t("pageTitle");
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAria));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });
  document.querySelectorAll("[data-component]").forEach((badge) => {
    const status = badge.dataset.status || "waiting";
    badge.textContent = statusLabel(status);
  });
  refreshTurnLabels();
  renderMode();
  renderPatientTemplateOptions();
  renderGradeHistory();
  renderTurnCount();
  $("styleDescription").textContent = UI.styleDescription(state.language, state.currentStyle);
  const localStatus = state.connectionStatus.local_bridge;
  if (localStatus) updateBridgeLabel(localStatus);
}

function showToast(message, error = false) {
  const toast = $("toast");
  toast.textContent = message;
  toast.className = `toast show${error ? " error" : ""}`;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { toast.className = "toast"; }, 4500);
}

function addAudit(message) {
  const log = $("auditLog");
  if (!state.auditStarted) {
    log.innerHTML = "";
    state.auditStarted = true;
  }
  const line = document.createElement("p");
  const locale = state.language === "en" ? "en-GB" : "zh-CN";
  line.textContent = `${new Date().toLocaleTimeString(locale, { hour12: false })}  ${message}`;
  log.prepend(line);
}

function updateBridgeLabel(status) {
  $("bridgeDot").className = `status-dot ${status === "connected" ? "online" : status === "error" ? "error" : ""}`;
  $("bridgeLabel").textContent = status === "connected"
    ? t("bridgeConnected")
    : status === "connecting"
      ? t("bridgeConnecting")
      : t("bridgeError");
}

function setConnection(component, status) {
  state.connectionStatus[component] = status;
  const badge = document.querySelector(`[data-component="${component}"]`);
  if (badge) {
    badge.dataset.status = status;
    badge.textContent = statusLabel(status);
    badge.className = `status-tag ${status}`;
  }
  if (component === "local_bridge") updateBridgeLabel(status);
}

function socketUrl() {
  const host = window.location.hostname || "127.0.0.1";
  const port = new URLSearchParams(window.location.search).get("wsPort") || "8765";
  return `ws://${host}:${port}`;
}

function connectSocket() {
  if (state.socket && state.socket.readyState === WebSocket.OPEN) return Promise.resolve();
  setConnection("local_bridge", "connecting");
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(socketUrl());
    socket.binaryType = "arraybuffer";
    socket.onopen = () => {
      state.socket = socket;
      setConnection("local_bridge", "connected");
      resolve();
    };
    socket.onerror = () => {
      setConnection("local_bridge", "error");
      reject(new Error(t("bridgeError")));
    };
    socket.onclose = () => {
      setConnection("local_bridge", "error");
      if (state.running) stopCapture();
      state.socket = null;
    };
    socket.onmessage = handleSocketMessage;
  });
}

function sendCommand(command) {
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
    throw new Error(t("serviceNotConnected"));
  }
  state.socket.send(JSON.stringify(command));
}

async function prepareCapture() {
  state.stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
  state.captureContext = new AudioContext();
  await state.captureContext.audioWorklet.addModule("/audio-worklet.js");
  state.captureSource = state.captureContext.createMediaStreamSource(state.stream);
  state.worklet = new AudioWorkletNode(state.captureContext, "pcm16-downsampler");
  state.silentGain = state.captureContext.createGain();
  state.silentGain.gain.value = 0;
  state.worklet.connect(state.silentGain).connect(state.captureContext.destination);
  state.worklet.port.onmessage = ({ data }) => {
    updateMeter(data.peak || 0);
    if (state.running && state.uploadEnabled && state.socket?.readyState === WebSocket.OPEN) {
      state.socket.send(data.pcm);
    }
  };
}

function setSetupLocked(locked) {
  document.querySelectorAll("[data-condition], [data-language]").forEach((button) => {
    button.disabled = locked;
  });
  $("patientTemplateSelect").disabled = locked;
  $("retainAudioSwitch").disabled = locked;
  $("researcherProfileButton").disabled = locked;
  $("confirmPatientTemplateButton").disabled = locked;
  if (!locked) updatePatientTemplateActions();
}

function beginCapture() {
  if (!state.captureSource || !state.worklet) return;
  try { state.captureSource.connect(state.worklet); } catch (_) {}
  state.running = true;
  state.uploadEnabled = true;
  setSetupLocked(true);
  $("voiceState").className = "voice-state live";
  $("voiceStateText").textContent = t("listening");
  $("liveCaption").textContent = t("micCapturing");
  $("startButton").disabled = true;
  $("stopButton").disabled = false;
}

async function stopCapture() {
  state.running = false;
  state.uploadEnabled = false;
  try { state.captureSource?.disconnect(); } catch (_) {}
  state.stream?.getTracks().forEach((track) => track.stop());
  if (state.captureContext && state.captureContext.state !== "closed") {
    await state.captureContext.close();
  }
  state.stream = null;
  state.captureContext = null;
  state.captureSource = null;
  state.worklet = null;
  state.silentGain = null;
  updateMeter(0);
  setSetupLocked(false);
  $("voiceState").className = "voice-state";
  $("voiceStateText").textContent = t("statusStopped");
  $("liveCaption").textContent = t("micOff");
  $("startButton").disabled = state.sessionLimitReached;
  $("stopButton").disabled = true;
}

function updateMeter(peak) {
  const bars = [...$("levelMeter").children];
  const active = Math.round(Math.min(1, peak * 3.5) * bars.length);
  bars.forEach((bar, index) => {
    const on = index < active;
    bar.style.height = `${5 + (on ? (index % 5) * 3 + 8 : 0)}px`;
    bar.style.background = on ? "#176b4d" : "#aab2ad";
  });
}

async function playPcm16(buffer) {
  if (!state.playbackContext) state.playbackContext = new AudioContext();
  await state.playbackContext.resume();
  const pcm = new Int16Array(buffer);
  const audioBuffer = state.playbackContext.createBuffer(1, pcm.length, 24000);
  const channel = audioBuffer.getChannelData(0);
  for (let index = 0; index < pcm.length; index += 1) channel[index] = pcm[index] / 32768;
  const source = state.playbackContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(state.playbackContext.destination);
  const startAt = Math.max(state.playbackContext.currentTime + 0.02, state.nextPlaybackTime);
  state.nextPlaybackTime = startAt + audioBuffer.duration;
  state.playbackSources.add(source);
  source.onended = () => state.playbackSources.delete(source);
  source.start(startAt);
  $("voiceState").className = "voice-state patient";
  $("voiceStateText").textContent = t("patientResponding");
}

function stopPlayback() {
  state.playbackSources.forEach((source) => {
    try { source.stop(); } catch (_) {}
  });
  state.playbackSources.clear();
  state.nextPlaybackTime = 0;
}

function refreshTurnLabels() {
  document.querySelectorAll(".turn-meta[data-role]").forEach((meta) => {
    const role = meta.dataset.role === "Doctor" ? t("doctor") : t("virtualPatient");
    meta.textContent = `${role} · ${meta.dataset.turnId}`;
  });
}

function appendTurn(turn) {
  const transcript = $("transcript");
  const followNewTurn = !transcript.querySelector(".turn") || RSTMUI.isNearBottom(transcript);
  $("emptyState")?.remove();
  const item = document.createElement("article");
  const roleClass = turn.role === "Doctor" ? "doctor" : "patient";
  item.className = `turn ${roleClass}`;
  const meta = document.createElement("div");
  meta.className = "turn-meta";
  meta.dataset.role = turn.role;
  meta.dataset.turnId = turn.turn_id;
  const content = document.createElement("div");
  content.className = "turn-content";
  content.textContent = turn.content;
  item.append(meta, content);
  transcript.append(item);
  refreshTurnLabels();
  if (followNewTurn) requestAnimationFrame(() => { transcript.scrollTop = transcript.scrollHeight; });
}


function renderTurnCount() {
  $("turnCount").textContent = t("turns", { count: state.rstmTurnCount });
}

function updateState(value, style, turn) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return;
  $("stateValue").textContent = numeric.toFixed(3);
  $("stateMarker").style.left = `${Math.max(0, Math.min(100, (numeric + 1) * 50))}%`;
  if (style) {
    state.currentStyle = style;
    $("levelValue").textContent = style.level ?? "3";
    $("styleName").textContent = style.name || "Concerned / Downcast";
    $("styleDescription").textContent = UI.styleDescription(state.language, style);
  }
  if (state.trajectory[state.trajectory.length - 1] !== numeric) state.trajectory.push(numeric);
  state.rstmTurnCount = Number.isFinite(Number(turn)) ? Number(turn) : state.trajectory.length - 1;
  renderTurnCount();
  drawTrajectory();
}

function renderMode() {
  const adaptive = state.condition === "adaptive";
  $("interactionStateHeading").textContent = t(
    adaptive ? "interactionState" : "initialInteractionState",
  );
  $("conditionBadge").textContent = t(adaptive ? "modeAdaptiveShort" : "modeFixedShort");
  $("modeExplanation").textContent = t(adaptive ? "modeAdaptiveNote" : "modeFixedNote");
  $("scoreSection").classList.toggle("not-used", !adaptive);
  renderGradeHistory();
  const empty = $("emptyState");
  if (empty?.querySelector("h2")?.dataset.i18n === "emptyTitle") renderEmptyState(false);
}

async function persistPatientTemplates() {
  localStorage.setItem(PATIENT_TEMPLATE_STORAGE_KEY, JSON.stringify(state.patientTemplates));
  try {
    const response = await fetch("/api/patient-templates", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ templates: state.patientTemplates }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    state.patientTemplates = RSTMUI.loadPatientTemplates(payload.templates);
    localStorage.setItem(PATIENT_TEMPLATE_STORAGE_KEY, JSON.stringify(state.patientTemplates));
    return true;
  } catch (_) {
    return false;
  }
}

async function loadPersistedPatientTemplates() {
  const localTemplates = RSTMUI.loadPatientTemplates(
    localStorage.getItem(PATIENT_TEMPLATE_STORAGE_KEY),
  );
  try {
    const response = await fetch("/api/patient-templates");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const folderTemplates = RSTMUI.loadPatientTemplates(payload.templates);
    state.patientTemplates = folderTemplates.length ? folderTemplates : localTemplates;
    if (!folderTemplates.length && localTemplates.length) {
      await persistPatientTemplates();
    } else {
      localStorage.setItem(PATIENT_TEMPLATE_STORAGE_KEY, JSON.stringify(state.patientTemplates));
    }
  } catch (_) {
    state.patientTemplates = localTemplates;
  }
}

function patientTemplateById(id) {
  return state.patientTemplates.find((item) => item.id === id) || null;
}

function selectedPatientTemplate() {
  return patientTemplateById(state.selectedPatientTemplateId);
}

function activePatientTemplate() {
  return patientTemplateById(state.activePatientTemplateId);
}

function updatePatientTemplateActions() {
  const selected = selectedPatientTemplate();
  const deleteButton = $("deleteSelectedPatientTemplateButton");
  if (deleteButton) deleteButton.disabled = !selected;
  const savedDraftChanged = selected
    && selected.id === state.activePatientTemplateId
    && state.activePatientProfile
    && JSON.stringify(RSTMUI.patientProfilePayload(selected)) !== JSON.stringify(state.activePatientProfile);
  const hasChange = state.selectedPatientTemplateId !== ADD_PATIENT_PROFILE_OPTION
    && (state.selectedPatientTemplateId !== state.activePatientTemplateId || savedDraftChanged);
  $("confirmPatientTemplateButton").disabled = state.running || !hasChange;
  const dialogButton = $("activatePatientTemplateButton");
  if (dialogButton) {
    const editingDraft = !$("patientTemplateForm").hidden;
    dialogButton.disabled = state.running
      || (!editingDraft && state.selectedPatientTemplateId === state.activePatientTemplateId);
  }
}

function renderPatientTemplateOptions() {
  const select = $("patientTemplateSelect");
  if (!select) return;
  if (state.activePatientTemplateId !== "default-bbn-zhang" && !activePatientTemplate()) {
    state.activePatientTemplateId = "default-bbn-zhang";
  }
  if (state.selectedPatientTemplateId !== "default-bbn-zhang" && !selectedPatientTemplate()) {
    state.selectedPatientTemplateId = state.activePatientTemplateId;
  }
  select.replaceChildren();
  const defaultOption = document.createElement("option");
  defaultOption.value = "default-bbn-zhang";
  defaultOption.textContent = `${t("defaultPatientTemplate")}${state.activePatientTemplateId === "default-bbn-zhang" ? t("activePatientSuffix") : ""}`;
  select.append(defaultOption);
  state.patientTemplates.forEach((template) => {
    const option = document.createElement("option");
    option.value = template.id;
    option.textContent = `${template.name}${template.id === state.activePatientTemplateId ? t("activePatientSuffix") : ""}`;
    select.append(option);
  });
  const addOption = document.createElement("option");
  addOption.value = ADD_PATIENT_PROFILE_OPTION;
  addOption.textContent = t("addPatientTemplate");
  select.append(addOption);
  select.value = state.selectedPatientTemplateId;
  const active = activePatientTemplate();
  $("patientPresenceName").textContent = active?.name || t("defaultPatientTemplate");
  updatePatientTemplateActions();
}

async function loadDefaultPatientProfile() {
  const profileText = $("patientProfileText");
  if (state.profileLoaded) return;
  profileText.dataset.i18n = "profileLoading";
  profileText.textContent = t("profileLoading");
  try {
    const response = await fetch("/api/patient-profile");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    profileText.removeAttribute("data-i18n");
    profileText.textContent = String(payload.profile || "");
    state.profileLoaded = true;
  } catch (_) {
    profileText.dataset.i18n = "profileLoadError";
    profileText.textContent = t("profileLoadError");
  }
}

function showPatientTemplateEditor(template = null) {
  $("defaultProfileView").hidden = true;
  const form = $("patientTemplateForm");
  form.hidden = false;
  form.reset();
  state.editingPatientTemplateId = template?.id || null;
  $("patientTemplateName").value = template?.name || "";
  UI.PATIENT_PROFILE_FIELDS.forEach((field) => {
    const input = form.querySelector(`[data-profile-field="${field}"]`);
    input.value = template?.[field] || "";
  });
  $("cloneDefaultProfileButton").hidden = true;
  $("savePatientTemplateButton").hidden = false;
  $("activatePatientTemplateButton").hidden = false;
  $("deletePatientTemplateButton").hidden = !template?.id;
  updatePatientTemplateActions();
}

function showDefaultPatientProfile() {
  state.editingPatientTemplateId = null;
  $("defaultProfileView").hidden = false;
  $("patientTemplateForm").hidden = true;
  $("cloneDefaultProfileButton").hidden = false;
  $("savePatientTemplateButton").hidden = true;
  $("deletePatientTemplateButton").hidden = true;
  $("activatePatientTemplateButton").hidden = false;
  updatePatientTemplateActions();
  loadDefaultPatientProfile();
}

function renderPatientProfileDialog() {
  const template = selectedPatientTemplate();
  if (template) showPatientTemplateEditor(template);
  else showDefaultPatientProfile();
}

function openPatientProfile() {
  if (state.running) return;
  $("patientProfileDialog").showModal();
  renderPatientProfileDialog();
}

function createPatientTemplate() {
  showPatientTemplateEditor();
  $("patientTemplateName").focus();
}

function cloneDefaultPatientProfile() {
  showPatientTemplateEditor(DEFAULT_PATIENT_TEMPLATE_DRAFT);
  $("patientTemplateName").select();
}

async function savePatientTemplate() {
  const form = $("patientTemplateForm");
  const template = {
    id: state.editingPatientTemplateId || `custom-${Date.now()}`,
    name: $("patientTemplateName").value,
  };
  UI.PATIENT_PROFILE_FIELDS.forEach((field) => {
    template[field] = form.querySelector(`[data-profile-field="${field}"]`).value;
  });
  try {
    state.patientTemplates = RSTMUI.upsertPatientTemplate(state.patientTemplates, template);
    const saved = state.patientTemplates[0];
    state.selectedPatientTemplateId = saved.id;
    state.editingPatientTemplateId = saved.id;
    const savedToFolder = await persistPatientTemplates();
    renderPatientTemplateOptions();
    showPatientTemplateEditor(saved);
    showToast(t(savedToFolder ? "templateSaved" : "templateFolderSaveFailed"), !savedToFolder);
    return saved;
  } catch (_) {
    showToast(t("templateInvalid"), true);
    form.querySelector('[data-profile-field="clinical_facts"]').focus();
    return null;
  }
}
async function deletePatientTemplate() {
  const template = selectedPatientTemplate();
  if (!template) return;
  const deletingActive = template.id === state.activePatientTemplateId;
  const confirmation = deletingActive
    ? t("confirmDeleteActiveTemplate")
    : t("confirmDeleteTemplate");
  if (!window.confirm(confirmation)) return;
  const result = RSTMUI.patientTemplateDeletion(
    state.patientTemplates,
    template.id,
    state.activePatientTemplateId,
  );
  state.patientTemplates = result.templates;
  state.activePatientTemplateId = result.activeId;
  state.selectedPatientTemplateId = result.selectedId;
  if (result.deletedActive) state.activePatientProfile = null;
  const savedToFolder = await persistPatientTemplates();
  renderPatientTemplateOptions();
  if ($("patientProfileDialog").open) $("patientProfileDialog").close();
  if (result.deletedActive) {
    await newParticipantSession({ skipConfirm: true });
  }
  showToast(t(savedToFolder ? "templateDeleted" : "templateFolderSaveFailed"), !savedToFolder);
}
async function usePatientTemplateAndCreateSession() {
  if (state.running && !window.confirm(t("confirmNewSession"))) return;
  let selectedId = state.selectedPatientTemplateId;
  if (!$("patientTemplateForm").hidden && $("patientProfileDialog").open) {
    const saved = await savePatientTemplate();
    if (!saved) return;
    selectedId = saved.id;
  }
  if (selectedId === ADD_PATIENT_PROFILE_OPTION) return;
  state.activePatientTemplateId = selectedId;
  state.selectedPatientTemplateId = selectedId;
  const selected = patientTemplateById(selectedId);
  state.activePatientProfile = selected
    ? RSTMUI.patientProfilePayload(selected)
    : null;
  renderPatientTemplateOptions();
  if ($("patientProfileDialog").open) $("patientProfileDialog").close();
  await newParticipantSession({ skipConfirm: true });
}

function buildConfigureCommand() {
  const command = {
    command: "configure",
    participant_id: $("participantId").textContent,
    session_id: $("sessionId").textContent,
    condition: state.condition,
    language: state.language,
    scenario: "breaking_bad_news",
    retain_audio: state.retainAudio,
  };
  if (state.activePatientProfile) {
    command.patient_profile = { ...state.activePatientProfile };
  }
  return command;
}
function formatScore(value, pending = false) {
  if (pending) return "…";
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "--";
  const numeric = Number(value);
  return numeric > 0 ? `+${numeric}` : String(numeric);
}

function setScoreValue(element, value, pending = false) {
  element.textContent = formatScore(value, pending);
  element.className = `score-value ${pending ? "unavailable" : UI.scoreTone(value)}`;
}

function isProcessViolation(item) {
  return item.safetyStatus.toLowerCase().includes("pik");
}

function renderGradeHistory() {
  const body = $("scoreHistoryBody");
  body.replaceChildren();
  const cpasEnabled = state.condition === "adaptive";
  $("scoreSection").classList.toggle("not-used", !cpasEnabled);
  if (!cpasEnabled) {
    $("scoreHistoryEmpty").hidden = true;
    $("scoreValue").textContent = "--";
    setScoreValue($("trackAScore"), null);
    setScoreValue($("trackBScore"), null);
    $("gradeStatus").textContent = t("cpasNotUsedStatus");
    $("gradeStatus").className = "status-tag";
    $("gradeStatus").dataset.gradeStatus = "not-used";
    $("gradeMessage").className = "grade-message unscorable-message";
    $("gradeMessage").textContent = t("cpasNotUsed");
    $("gradeMessage").hidden = false;
    return;
  }
  $("scoreHistoryEmpty").textContent = t("noGradeHistory");
  state.gradeHistory.forEach((item) => {
    const pending = item.status === "pending";
    const row = document.createElement("tr");
    const turnCell = document.createElement("td");
    turnCell.textContent = item.doctorTurnId;
    if (isProcessViolation(item)) {
      const warning = document.createElement("span");
      warning.className = "process-warning";
      warning.textContent = t("processPrerequisiteMissing");
      turnCell.append(warning);
    }
    const values = [item.trackA, item.trackB, item.total];
    row.append(turnCell);
    values.forEach((value) => {
      const cell = document.createElement("td");
      cell.className = `score-cell ${pending ? "unavailable" : UI.scoreTone(value)}`;
      cell.textContent = formatScore(value, pending);
      row.append(cell);
    });
    body.append(row);
  });
  $("scoreHistoryEmpty").hidden = state.gradeHistory.length > 0;

  const latest = state.gradeHistory[0];
  if (!latest) {
    $("scoreValue").textContent = "--";
    setScoreValue($("trackAScore"), null);
    setScoreValue($("trackBScore"), null);
    $("gradeStatus").textContent = t("noScore");
    $("gradeStatus").className = "status-tag";
    $("gradeStatus").dataset.gradeStatus = "none";
    $("gradeMessage").hidden = true;
    return;
  }

  const pending = latest.status === "pending";
  $("scoreValue").textContent = formatScore(latest.total, pending);
  setScoreValue($("trackAScore"), latest.trackA, pending);
  setScoreValue($("trackBScore"), latest.trackB, pending);
  $("gradeStatus").textContent = gradeLabel(latest.status);
  $("gradeStatus").className = `status-tag ${latest.status}`;
  $("gradeStatus").dataset.gradeStatus = latest.status;

  const message = latest.status === "unscorable"
    ? t("gradeUnscorableReason")
    : latest.status === "error"
      ? latest.reason
      : isProcessViolation(latest)
        ? t("processPrerequisiteMissing")
        : "";
  $("gradeMessage").className = `grade-message${latest.status === "unscorable" ? " unscorable-message" : ""}`;
  $("gradeMessage").textContent = message;
  $("gradeMessage").hidden = !message;
}

function trajectoryTickLabel(value) {
  if (value > 0) return `+${value}`;
  return String(value);
}

function drawTrajectory() {
  const canvas = $("trajectory");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const plot = { left: 48, right: 14, top: 34, bottom: 24 };
  const plotWidth = width - plot.left - plot.right;
  const plotHeight = height - plot.top - plot.bottom;
  const trajectoryGridValues = [-1, -0.7, -0.4, -0.1, 0, 0.1, 0.4, 0.7, 1];
  const trajectoryLabelValues = [-1, 0, 1];
  const yFor = (value) => plot.top + (1 - (value + 1) / 2) * plotHeight;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#f8faf8";
  ctx.fillRect(0, 0, width, height);

  trajectoryGridValues.forEach((value) => {
    const y = yFor(value);
    ctx.strokeStyle = value === 0 ? "#9da9a2" : "#e1e7e3";
    ctx.lineWidth = value === 0 ? 2 : 1;
    ctx.beginPath();
    ctx.moveTo(plot.left, y);
    ctx.lineTo(width - plot.right, y);
    ctx.stroke();
  });

  ctx.strokeStyle = "#b3bdb7";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(plot.left, plot.top);
  ctx.lineTo(plot.left, height - plot.bottom);
  ctx.stroke();

  ctx.fillStyle = "#68736d";
  ctx.font = '20px "Segoe UI", "Microsoft YaHei", Arial, sans-serif';
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  trajectoryLabelValues.forEach((value) => {
    ctx.fillText(trajectoryTickLabel(value), plot.left - 9, yFor(value));
  });
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillText("S(t)", 6, 3);

  const points = state.trajectory.map((value) => Math.max(-1, Math.min(1, Number(value))));
  ctx.strokeStyle = "#176b4d";
  ctx.lineWidth = 4;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  points.forEach((value, index) => {
    const x = points.length === 1
      ? plot.left
      : plot.left + index * plotWidth / (points.length - 1);
    const y = yFor(value);
    if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  if (points.length === 1) ctx.lineTo(plot.left + 1, yFor(points[0]));
  ctx.stroke();

  ctx.fillStyle = "#176b4d";
  points.forEach((value, index) => {
    const x = points.length === 1
      ? plot.left
      : plot.left + index * plotWidth / (points.length - 1);
    ctx.beginPath();
    ctx.arc(x, yFor(value), 5, 0, Math.PI * 2);
    ctx.fill();
  });
}

function renderEmptyState(reset = false) {
  const transcript = $("transcript");
  transcript.innerHTML = "";
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.id = "emptyState";
  const mic = document.createElement("div");
  mic.className = "mic-symbol";
  mic.setAttribute("aria-hidden", "true");
  const title = document.createElement("h2");
  title.dataset.i18n = reset ? "resetTitle" : "emptyTitle";
  const body = document.createElement("p");
  body.dataset.i18n = reset ? "resetBody" : state.condition === "adaptive" ? "emptyBodyAdaptive" : "emptyBodyControl";
  empty.append(mic, title, body);
  transcript.append(empty);
  title.textContent = t(title.dataset.i18n);
  body.textContent = t(body.dataset.i18n);
}

function handleEvent(event) {
  if (event.type === "connection") {
    if (event.component === "realtime_session" && ["updating", "refreshing", "fallback_reconnecting"].includes(event.status)) state.uploadEnabled = false;
    if (event.component === "realtime_session" && event.status === "connected" && state.running) state.uploadEnabled = true;
    setConnection(event.component, event.status);
    addAudit(`${event.component}: ${statusLabel(event.status)}`);
    if (event.component === "tts" && event.status === "idle" && state.running) {
      $("voiceState").className = "voice-state live";
      $("voiceStateText").textContent = t("listening");
    }
  } else if (event.type === "session") {
    if (event.status === "started") {
      state.sessionLimitReached = false;
      beginCapture();
      updateState(event.state, event.style, 0);
      addAudit(t("conversationStarted"));
    } else if (event.status === "configured") {
      state.condition = event.adaptive_enabled ? "adaptive" : "control";
      state.sessionLimitReached = false;
      state.gradeHistory = [];
      updateState(event.state, event.style, 0);
      renderMode();
    } else if (event.status === "limit_reached") {
      state.sessionLimitReached = true;
      state.uploadEnabled = false;
      stopCapture();
      addAudit(t("turnLimitReached"));
      showToast(t("turnLimitReached"));
    } else if (event.status === "stopped") {
      stopCapture();
      addAudit(t("conversationStopped"));
    } else if (event.status === "reset") {
      updateState(-0.25, event.style, 0);
      addAudit(t("resetAudit"));
    }
  } else if (event.type === "transcript") {
    appendTurn(event.turn);
  } else if (event.type === "grade" && state.condition === "adaptive") {
    state.gradeHistory = RSTMUI.upsertGrade(state.gradeHistory, event);
    renderGradeHistory();
    addAudit(t("cpasAudit", { turn: event.doctor_turn_id || "", status: gradeLabel(event.grading_status) }));
  } else if (event.type === "rstm") {
    updateState(event.state, event.style, event.turn);
    addAudit(t("rstmUpdated", { state: Number(event.state).toFixed(3) }));
  } else if (event.type === "audio") {
    $("audioStatus").textContent = t("filesSaved", { count: event.files?.length || 0 });
    addAudit(t("audioSaved"));
  } else if (event.type === "error") {
    addAudit(t("errorAudit", { message: event.message }));
    showToast(event.message || t("runtimeError"), true);
    if (event.component === "runtime") stopCapture();
  }
}

function handleSocketMessage(message) {
  if (message.data instanceof ArrayBuffer) {
    playPcm16(message.data).catch((error) => showToast(error.message, true));
    return;
  }
  try { handleEvent(JSON.parse(message.data)); }
  catch (_) { showToast(t("unreadableMessage"), true); }
}

async function startTest() {
  try {
    const configureCommand = buildConfigureCommand();
    $("startButton").disabled = true;
    $("voiceStateText").textContent = t("requestingMic");
    await connectSocket();
    await prepareCapture();
    sendCommand(configureCommand);
    sendCommand({ command: "start" });
    $("voiceStateText").textContent = t("connectingPatient");
    setConnection("realtime_session", "connecting");
  } catch (error) {
    await stopCapture();
    showToast(error.name === "NotAllowedError" ? t("microphoneDenied") : error.message, true);
  }
}

async function stopTest() {
  await stopCapture();
  stopPlayback();
  try { sendCommand({ command: "stop" }); } catch (_) {}
}

function resetAudit() {
  state.auditStarted = false;
  $("auditLog").innerHTML = `<p data-i18n="logWaiting">${t("logWaiting")}</p>`;
}

async function newParticipantSession({ skipConfirm = false } = {}) {
  if (!skipConfirm && !window.confirm(t("confirmNewSession"))) return false;
  state.sessionLimitReached = false;
  await stopCapture();
  stopPlayback();
  try { sendCommand({ command: "reset" }); } catch (_) {}
  state.trajectory = [-0.25];
  state.rstmTurnCount = 0;
  state.gradeHistory = [];
  updateState(-0.25, { level: 3, name: "Concerned / Downcast", description: "担忧 / 低落" }, 0);
  renderGradeHistory();
  renderEmptyState(true);
  resetAudit();
  $("audioStatus").textContent = t(state.retainAudio ? "audioPending" : "audioNotRetained");
  createSessionIds();
  showToast(t("newSessionCreated"));
  return true;
}

document.querySelectorAll("[data-condition]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-condition]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.condition = button.dataset.condition;
    state.gradeHistory = [];
    renderMode();
  });
});

document.querySelectorAll("[data-language]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-language]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.language = button.dataset.language;
    applyLanguage();
  });
});

$("startButton").addEventListener("click", startTest);
$("stopButton").addEventListener("click", stopTest);
$("newParticipantSessionButton").addEventListener("click", newParticipantSession);
$("retainAudioSwitch").addEventListener("click", () => {
  if (state.running) return;
  state.retainAudio = !state.retainAudio;
  $("retainAudioSwitch").classList.toggle("checked", state.retainAudio);
  $("retainAudioSwitch").setAttribute("aria-checked", String(state.retainAudio));
  $("audioStatus").textContent = t(state.retainAudio ? "audioPending" : "audioNotRetained");
});
$("researcherProfileButton").addEventListener("click", openPatientProfile);
$("createPatientTemplateButton").addEventListener("click", createPatientTemplate);
$("cloneDefaultProfileButton").addEventListener("click", cloneDefaultPatientProfile);
$("savePatientTemplateButton").addEventListener("click", savePatientTemplate);
$("deletePatientTemplateButton").addEventListener("click", deletePatientTemplate);
$("deleteSelectedPatientTemplateButton").addEventListener("click", deletePatientTemplate);
$("activatePatientTemplateButton").addEventListener("click", usePatientTemplateAndCreateSession);
$("confirmPatientTemplateButton").addEventListener("click", usePatientTemplateAndCreateSession);
$("patientTemplateSelect").addEventListener("change", (event) => {
  if (event.target.value === ADD_PATIENT_PROFILE_OPTION) {
    state.selectedPatientTemplateId = state.activePatientTemplateId;
    renderPatientTemplateOptions();
    $("patientProfileDialog").showModal();
    createPatientTemplate();
    return;
  }
  state.selectedPatientTemplateId = event.target.value;
  renderPatientTemplateOptions();
  if ($("patientProfileDialog").open) renderPatientProfileDialog();
});
$("closePatientProfileButton").addEventListener("click", () => $("patientProfileDialog").close());
$("patientProfileDialog").addEventListener("click", (event) => {
  if (event.target === $("patientProfileDialog")) $("patientProfileDialog").close();
});

async function initializeInterface() {
  await loadPersistedPatientTemplates();
  createSessionIds();
  applyLanguage();
  drawTrajectory();
  connectSocket().catch(() => showToast(t("serviceUnavailable"), true));
}

initializeInterface();
