const RSTMUI = window.RSTMUI;
const UI = RSTMUI;

const state = {
  socket: null,
  condition: "adaptive",
  language: "zh",
  running: false,
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
  currentStyle: { level: 3, name: "Concerned / Downcast", description: "" },
  toastTimer: null,
};

const $ = (id) => document.getElementById(id);
const t = (key, values) => UI.t(state.language, key, values);

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
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  const stamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  $("participantId").textContent = `TEST-${stamp.slice(4, 8)}`;
  $("sessionId").textContent = `VOICE-${stamp}`;
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
  document.querySelectorAll("[data-component]").forEach((badge) => {
    const status = badge.dataset.status || "waiting";
    badge.textContent = statusLabel(status);
  });
  refreshTurnLabels();
  renderMode();
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
  $("newSessionButton").disabled = locked;
  $("researcherProfileButton").disabled = locked;
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
  $("startButton").disabled = false;
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
  $("conditionBadge").textContent = t(adaptive ? "modeAdaptiveShort" : "modeFixedShort");
  $("modeExplanation").textContent = t(adaptive ? "modeAdaptiveNote" : "modeFixedNote");
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

  const message = latest.status === "unscorable" || latest.status === "error"
    ? latest.reason
    : isProcessViolation(latest)
      ? t("processPrerequisiteMissing")
      : "";
  $("gradeMessage").textContent = message;
  $("gradeMessage").hidden = !message;
}

function drawTrajectory() {
  const canvas = $("trajectory");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const pad = 24;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#f8faf8";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#dce2de";
  ctx.lineWidth = 1;
  [-1, -0.4, -0.1, 0.1, 0.4, 0.7, 1].forEach((value) => {
    const y = pad + (1 - (value + 1) / 2) * (height - pad * 2);
    ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(width - pad, y); ctx.stroke();
  });
  const points = state.trajectory;
  ctx.strokeStyle = "#176b4d";
  ctx.lineWidth = 4;
  ctx.lineJoin = "round";
  ctx.beginPath();
  points.forEach((value, index) => {
    const x = points.length === 1 ? pad : pad + index * (width - pad * 2) / (points.length - 1);
    const y = pad + (1 - (value + 1) / 2) * (height - pad * 2);
    if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  if (points.length === 1) ctx.lineTo(pad + 1, pad + (1 - (points[0] + 1) / 2) * (height - pad * 2));
  ctx.stroke();
  ctx.fillStyle = "#176b4d";
  points.forEach((value, index) => {
    const x = points.length === 1 ? pad : pad + index * (width - pad * 2) / (points.length - 1);
    const y = pad + (1 - (value + 1) / 2) * (height - pad * 2);
    ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill();
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
  body.dataset.i18n = reset ? "resetBody" : "emptyBody";
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
      beginCapture();
      updateState(event.state, event.style, 0);
      addAudit(t("conversationStarted"));
    } else if (event.status === "configured") {
      state.condition = event.adaptive_enabled ? "adaptive" : "control";
      updateState(event.state, event.style, 0);
      renderMode();
    } else if (event.status === "stopped") {
      stopCapture();
      addAudit(t("conversationStopped"));
    } else if (event.status === "reset") {
      updateState(-0.25, event.style, 0);
      addAudit(t("resetAudit"));
    }
  } else if (event.type === "transcript") {
    appendTurn(event.turn);
  } else if (event.type === "grade") {
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
    $("startButton").disabled = true;
    $("voiceStateText").textContent = t("requestingMic");
    await connectSocket();
    await prepareCapture();
    sendCommand({
      command: "configure",
      participant_id: $("participantId").textContent,
      session_id: $("sessionId").textContent,
      condition: state.condition,
      language: state.language,
      scenario: "breaking_bad_news",
      retain_audio: true,
    });
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

async function resetTest() {
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
  $("audioStatus").textContent = t("audioPending");
  createSessionIds();
}

async function openPatientProfile() {
  if (state.running) return;
  const dialog = $("patientProfileDialog");
  const profileText = $("patientProfileText");
  dialog.showModal();
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

document.querySelectorAll("[data-condition]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-condition]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    state.condition = button.dataset.condition;
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

$("newSessionButton").addEventListener("click", createSessionIds);
$("startButton").addEventListener("click", startTest);
$("stopButton").addEventListener("click", stopTest);
$("resetButton").addEventListener("click", resetTest);
$("researcherProfileButton").addEventListener("click", openPatientProfile);
$("closePatientProfileButton").addEventListener("click", () => $("patientProfileDialog").close());
$("patientProfileDialog").addEventListener("click", (event) => {
  if (event.target === $("patientProfileDialog")) $("patientProfileDialog").close();
});

createSessionIds();
applyLanguage();
drawTrajectory();
connectSocket().catch(() => showToast(t("serviceUnavailable"), true));
