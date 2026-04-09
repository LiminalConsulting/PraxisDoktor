// PraxisDoktor — app.js

const FIELD_DEFS = [
  { key: "nachname",       label: "Nachname" },
  { key: "vorname",        label: "Vorname" },
  { key: "geburtsdatum",   label: "Geburtsdatum" },
  { key: "geschlecht",     label: "Geschlecht" },
  { key: "titel",          label: "Titel" },
  { key: "anrede",         label: "Anrede" },
  { key: "strasse",        label: "Straße" },
  { key: "hausnr",         label: "Hausnummer" },
  { key: "plz",            label: "PLZ" },
  { key: "ort",            label: "Ort" },
  { key: "telefon_privat", label: "Telefon privat" },
  { key: "telefon_mobil",  label: "Telefon mobil" },
  { key: "email",          label: "E-Mail" },
  { key: "muttersprache",  label: "Muttersprache" },
];

let currentSession = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let sseSource = null;
let wakeLock = null;
let silentAudio = null;

// --- Elements ---
const startBtn        = document.getElementById("start-btn");
const doctorSelect    = document.getElementById("doctor-select");
const patientRef      = document.getElementById("patient-ref");
const recordSection   = document.getElementById("recording-section");
const recordBtn       = document.getElementById("record-btn");
const recordLabel     = document.getElementById("record-label");
const stopBtn         = document.getElementById("stop-btn");
const statusBar       = document.getElementById("status-bar");
const dropZone        = document.getElementById("drop-zone");
const formFile        = document.getElementById("form-file");
const ocrBlock        = document.getElementById("ocr-block");
const ocrToggle       = document.getElementById("ocr-toggle");
const ocrText         = document.getElementById("ocr-text");
const emptyState      = document.getElementById("empty-state");
const fieldsContainer = document.getElementById("fields-container");
const fieldsGrid      = document.getElementById("fields-grid");
const doneBtn         = document.getElementById("done-btn");
const historyToggle   = document.getElementById("history-toggle");
const historyList     = document.getElementById("history-list");
const historyArrow    = document.getElementById("history-arrow");
const diarizedBlock   = document.getElementById("diarized-block");
const diarizedContent = document.getElementById("diarized-content");

// Settings
const settingsBtn       = document.getElementById("settings-btn");
const settingsPanel     = document.getElementById("settings-panel");
const settingsOverlay   = document.getElementById("settings-overlay");
const settingsClose     = document.getElementById("settings-close");
const vocabTags         = document.getElementById("vocab-tags");
const vocabInput        = document.getElementById("vocab-input");
const vocabAddBtn       = document.getElementById("vocab-add-btn");
const doctorList        = document.getElementById("doctor-list");
const doctorInput       = document.getElementById("doctor-input");
const doctorAddBtn      = document.getElementById("doctor-add-btn");
const diarizationToggle = document.getElementById("diarization-toggle");

// Enroll modal
const enrollOverlay     = document.getElementById("enroll-overlay");
const enrollModal       = document.getElementById("enroll-modal");
const enrollTitle       = document.getElementById("enroll-title");
const enrollClose       = document.getElementById("enroll-close");
const enrollRecordBtn   = document.getElementById("enroll-record-btn");
const enrollRecordLabel = document.getElementById("enroll-record-label");
const enrollStatus      = document.getElementById("enroll-status");

let enrollDoctorName = null;
let enrollRecorder = null;
let enrollChunks = [];
let enrollRecording = false;

// --- Wake lock: keep screen/audio alive on Android ---
async function acquireWakeLock() {
  // Try Screen Wake Lock API first (Chrome Android 84+)
  if ("wakeLock" in navigator) {
    try {
      wakeLock = await navigator.wakeLock.request("screen");
      return;
    } catch (_) {}
  }
  // Fallback: play a looping silent audio to prevent background tab suspension
  if (!silentAudio) {
    // 1 second of silence as base64 MP3
    const silentMp3 = "data:audio/mpeg;base64,SUQzBAAAAAABEVRYWFgAAAAtAAADY29tbWVudABCaWdTb3VuZEJhbmsuY29tIC8gTGFTb25vdGhlcXVlLm9yZwBURU5DAAAAHQAAA1N3aXRjaCBQbHVzIMKpIE5DSCBTb2Z0d2FyZQBUSVQyAAAABgAAAzIyMzUAVFNTRQAAAA8AAANMYXZmNTcuODMuMTAwAAAAAAAAAAAAAAD/80DEAAAAA0gAAAAATEFNRTMuMTAwVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQsRbAAABpAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV";
    silentAudio = new Audio(silentMp3);
    silentAudio.loop = true;
    silentAudio.volume = 0.001;
  }
  silentAudio.play().catch(() => {});
}

function releaseWakeLock() {
  if (wakeLock) { wakeLock.release().catch(() => {}); wakeLock = null; }
  if (silentAudio) { silentAudio.pause(); }
}

// Re-acquire wake lock if page becomes visible again (Android Chrome releases it on tab switch)
document.addEventListener("visibilitychange", async () => {
  if (isRecording && document.visibilityState === "visible" && "wakeLock" in navigator) {
    try { wakeLock = await navigator.wakeLock.request("screen"); } catch (_) {}
  }
});

// --- Session start ---
startBtn.addEventListener("click", async () => {
  const ref = patientRef.value.trim();
  if (!ref) { patientRef.focus(); return; }

  const fd = new FormData();
  fd.append("patient_ref", ref);
  fd.append("doctor_name", doctorSelect.value || "");
  const resp = await fetch("/sessions", { method: "POST", body: fd });
  const session = await resp.json();
  loadSession(session);
  recordSection.style.display = "block";
  startBtn.disabled = true;
  patientRef.disabled = true;
  doctorSelect.disabled = true;
  setStatus("processing", "Bereit zur Aufnahme");
});

// --- Recording ---
recordBtn.addEventListener("click", async () => {
  if (isRecording) {
    stopRecording();
  } else {
    await startRecording();
  }
});

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.start(1000);
    isRecording = true;
    recordBtn.classList.add("recording");
    recordLabel.textContent = "Aufnahme läuft...";
    stopBtn.disabled = false;
    await acquireWakeLock();
  } catch (err) {
    setStatus("error", "Mikrofon-Zugriff verweigert: " + err.message);
  }
}

function stopRecording() {
  if (!mediaRecorder) return;
  mediaRecorder.stop();
  mediaRecorder.stream.getTracks().forEach(t => t.stop());
  isRecording = false;
  recordBtn.classList.remove("recording");
  recordLabel.textContent = "Aufnahme beendet";
  releaseWakeLock();
}

stopBtn.addEventListener("click", async () => {
  stopRecording();
  stopBtn.disabled = true;
  recordBtn.disabled = true;

  await new Promise(r => setTimeout(r, 400));
  const mimeType = mediaRecorder?.mimeType || "audio/webm";
  const ext = mimeType.includes("ogg") ? ".ogg" : mimeType.includes("mp4") ? ".mp4" : ".webm";
  const blob = new Blob(audioChunks, { type: mimeType });

  setStatus("processing", "Transkription läuft...");

  const fd = new FormData();
  fd.append("file", blob, `recording${ext}`);
  await fetch(`/sessions/${currentSession.id}/audio`, { method: "POST", body: fd });
});

// --- OCR drop zone ---
dropZone.addEventListener("click", () => formFile.click());
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave",  () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault(); dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) uploadForm(file);
});
formFile.addEventListener("change", () => {
  if (formFile.files[0]) uploadForm(formFile.files[0]);
});

async function uploadForm(file) {
  if (!currentSession) return;
  setStatus("processing", "OCR läuft...");
  const fd = new FormData();
  fd.append("file", file, file.name);
  await fetch(`/sessions/${currentSession.id}/form`, { method: "POST", body: fd });
}

// --- OCR toggle ---
ocrToggle.addEventListener("click", () => {
  const visible = ocrText.style.display === "block";
  ocrText.style.display = visible ? "none" : "block";
  ocrToggle.textContent = (visible ? "▶" : "▼") + " OCR-Text anzeigen";
});

// --- SSE ---
function connectSSE(sid) {
  if (sseSource) sseSource.close();
  sseSource = new EventSource(`/sessions/${sid}/stream`);
  sseSource.onmessage = e => {
    const msg = JSON.parse(e.data);
    handleSSE(msg);
  };
  sseSource.onerror = () => {};
}

function handleSSE(msg) {
  if (msg.type === "snapshot") {
    applySession(msg.session);
  } else if (msg.type === "transcript") {
    setStatus("processing", msg.message || "Auswertung läuft...");
  } else if (msg.type === "ocr") {
    showOCR(msg.ocr_text);
    setStatus("processing", msg.message || "OCR abgeschlossen");
  } else if (msg.type === "extracted") {
    renderFields(msg.extracted || {});
    setStatus("ready", msg.message || "Bereit");
  } else if (msg.type === "diarized") {
    showDiarized(msg.diarized);
    setStatus("ready", msg.message || "Bereit");
  } else if (msg.type === "status") {
    setStatus(msg.status, msg.message);
  } else if (msg.type === "error") {
    setStatus("error", msg.message);
  }
}

function applySession(session) {
  currentSession = session;
  if (session.ocr_text) showOCR(session.ocr_text);
  if (session.extracted) {
    try { renderFields(JSON.parse(session.extracted)); } catch {}
  }
  if (session.diarized) showDiarized(session.diarized);
  setStatus(session.status, statusLabel(session.status));
  if (session.status === "done") markDoneUI();
}

function statusLabel(s) {
  return { processing: "Wird verarbeitet...", ready: "Bereit", done: "In MediOffice übertragen", error: "Fehler" }[s] || s;
}

// --- Fields ---
function renderFields(data) {
  emptyState.style.display = "none";
  fieldsContainer.style.display = "block";
  fieldsGrid.innerHTML = "";
  for (const { key, label } of FIELD_DEFS) {
    const val = data[key];
    const card = document.createElement("div");
    card.className = "field-card" + (val ? " has-value" : "");
    card.innerHTML = `
      <div class="field-label">${label}</div>
      <div class="field-row">
        <div class="field-value${val ? "" : " empty"}">${val || "–"}</div>
        ${val ? `<button class="copy-btn" data-val="${escHtml(val)}">Kopieren</button>` : ""}
      </div>`;
    fieldsGrid.appendChild(card);
  }
  fieldsGrid.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(btn.dataset.val).then(() => {
        btn.textContent = "✓";
        btn.classList.add("copied");
        setTimeout(() => { btn.textContent = "Kopieren"; btn.classList.remove("copied"); }, 1500);
      });
    });
  });
}

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// --- Diarized transcript ---
function showDiarized(text) {
  if (!text) return;
  diarizedBlock.style.display = "block";
  diarizedContent.innerHTML = "";
  // Format: "ARZT: text\nPATIENT: text\n..."
  const lines = text.split("\n");
  for (const line of lines) {
    if (!line.trim()) continue;
    const colonIdx = line.indexOf(":");
    if (colonIdx > 0) {
      const speaker = line.slice(0, colonIdx).trim();
      const speech = line.slice(colonIdx + 1).trim();
      const div = document.createElement("div");
      div.className = "diarized-line";
      div.innerHTML = `<span class="diarized-speaker">${escHtml(speaker)}</span><span class="diarized-text">${escHtml(speech)}</span>`;
      diarizedContent.appendChild(div);
    } else {
      const div = document.createElement("div");
      div.className = "diarized-line";
      div.innerHTML = `<span class="diarized-text">${escHtml(line)}</span>`;
      diarizedContent.appendChild(div);
    }
  }
}

// --- Done button ---
doneBtn.addEventListener("click", async () => {
  if (!currentSession || doneBtn.classList.contains("done-state")) return;
  await fetch(`/sessions/${currentSession.id}/done`, { method: "POST" });
  markDoneUI();
  loadHistory();
});

function markDoneUI() {
  doneBtn.textContent = "✓ In MediOffice übertragen";
  doneBtn.classList.add("done-state");
}

// --- Status bar ---
function setStatus(type, message) {
  statusBar.className = "status-bar " + (type || "");
  const spin = (type === "processing") ? `<div class="spinner"></div>` : "";
  statusBar.innerHTML = spin + (message || "");
}

// --- OCR display ---
function showOCR(text) {
  if (!text) return;
  ocrBlock.style.display = "block";
  ocrText.textContent = text;
}

// --- Load session into UI ---
function loadSession(session) {
  currentSession = session;
  connectSSE(session.id);
  emptyState.style.display = "none";
  fieldsContainer.style.display = "block";
  fieldsGrid.innerHTML = "";
  diarizedBlock.style.display = "none";
  for (const { key, label } of FIELD_DEFS) {
    const card = document.createElement("div");
    card.className = "field-card";
    card.innerHTML = `<div class="field-label">${label}</div><div class="field-row"><div class="field-value empty">–</div></div>`;
    fieldsGrid.appendChild(card);
  }
}

// --- History ---
historyToggle.addEventListener("click", () => {
  historyList.classList.toggle("open");
  historyArrow.textContent = historyList.classList.contains("open") ? "▲" : "▼";
});

async function loadHistory() {
  const sessions = await fetch("/sessions").then(r => r.json());
  historyList.innerHTML = "";
  for (const s of sessions) {
    const row = document.createElement("div");
    row.className = "history-row";
    const date = new Date(s.created_at).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
    row.innerHTML = `
      <span class="h-date">${date}</span>
      <span class="h-name">${escHtml(s.patient_ref || "(kein Name)")}</span>
      ${s.doctor_name ? `<span class="h-doctor">${escHtml(s.doctor_name)}</span>` : ""}
      <span class="badge badge-${s.status}">${badgeLabel(s.status)}</span>`;
    row.addEventListener("click", () => restoreSession(s));
    historyList.appendChild(row);
  }
}

function badgeLabel(s) {
  return { processing: "Läuft", ready: "Bereit", done: "Übertragen", error: "Fehler" }[s] || s;
}

async function restoreSession(session) {
  currentSession = session;
  recordSection.style.display = "block";
  startBtn.disabled = true;
  patientRef.value = session.patient_ref || "";
  patientRef.disabled = true;
  doctorSelect.disabled = true;
  connectSSE(session.id);
  if (session.ocr_text) showOCR(session.ocr_text);
  if (session.extracted) {
    try { renderFields(JSON.parse(session.extracted)); } catch {}
  }
  if (session.diarized) showDiarized(session.diarized);
  if (session.status === "done") markDoneUI();
  setStatus(session.status, statusLabel(session.status));
}

// --- Settings / Vocab ---
settingsBtn.addEventListener("click", openSettings);
settingsClose.addEventListener("click", closeSettings);
settingsOverlay.addEventListener("click", closeSettings);

function openSettings() {
  settingsPanel.classList.add("open");
  settingsOverlay.classList.add("open");
  loadVocab();
  loadDoctorList();
  loadDiarizationToggle();
}
function closeSettings() {
  settingsPanel.classList.remove("open");
  settingsOverlay.classList.remove("open");
}

async function loadVocab() {
  const terms = await fetch("/vocab").then(r => r.json());
  vocabTags.innerHTML = "";
  for (const term of terms) {
    const tag = document.createElement("div");
    tag.className = "vocab-tag";
    tag.innerHTML = `<span>${escHtml(term)}</span><button title="Entfernen">&times;</button>`;
    tag.querySelector("button").addEventListener("click", async () => {
      await fetch(`/vocab/${encodeURIComponent(term)}`, { method: "DELETE" });
      loadVocab();
    });
    vocabTags.appendChild(tag);
  }
}

vocabAddBtn.addEventListener("click", addVocab);
vocabInput.addEventListener("keydown", e => { if (e.key === "Enter") addVocab(); });

async function addVocab() {
  const term = vocabInput.value.trim();
  if (!term) return;
  const fd = new FormData();
  fd.append("term", term);
  await fetch("/vocab", { method: "POST", body: fd });
  vocabInput.value = "";
  loadVocab();
}

// --- Doctors ---
async function loadDoctors() {
  const doctors = await fetch("/doctors").then(r => r.json());
  const prev = doctorSelect.value;
  doctorSelect.innerHTML = '<option value="">— Arzt auswählen —</option>';
  for (const d of doctors) {
    const opt = document.createElement("option");
    opt.value = d.name;
    opt.textContent = d.name;
    doctorSelect.appendChild(opt);
  }
  if (prev) doctorSelect.value = prev;
  return doctors;
}

async function loadDoctorList() {
  const doctors = await loadDoctors();
  doctorList.innerHTML = "";
  for (const d of doctors) {
    const row = document.createElement("div");
    row.className = "doctor-row";

    const nameSpan = document.createElement("span");
    nameSpan.className = "doctor-name";
    nameSpan.textContent = d.name;

    const voiceBtn = document.createElement("button");
    voiceBtn.className = "btn btn-outline btn-sm" + (d.embedding ? " enrolled" : "");
    voiceBtn.title = d.embedding ? "Stimme erneut aufnehmen" : "Stimme aufnehmen";
    voiceBtn.innerHTML = d.embedding
      ? "🎙 Stimme ✓"
      : "🎙 Stimme aufnehmen";
    voiceBtn.addEventListener("click", () => openEnrollModal(d.name));

    const delBtn = document.createElement("button");
    delBtn.className = "btn-icon-del";
    delBtn.title = "Entfernen";
    delBtn.textContent = "×";
    delBtn.addEventListener("click", async () => {
      await fetch(`/doctors/${encodeURIComponent(d.name)}`, { method: "DELETE" });
      loadDoctorList();
    });

    row.appendChild(nameSpan);
    row.appendChild(voiceBtn);
    row.appendChild(delBtn);
    doctorList.appendChild(row);
  }
}

doctorAddBtn.addEventListener("click", addDoctor);
doctorInput.addEventListener("keydown", e => { if (e.key === "Enter") addDoctor(); });

async function addDoctor() {
  const name = doctorInput.value.trim();
  if (!name) return;
  const fd = new FormData();
  fd.append("name", name);
  await fetch("/doctors", { method: "POST", body: fd });
  doctorInput.value = "";
  loadDoctorList();
}

// --- Enrollment modal ---
function openEnrollModal(doctorName) {
  enrollDoctorName = doctorName;
  enrollTitle.textContent = `Stimme aufnehmen – ${doctorName}`;
  enrollRecordBtn.className = "";
  enrollRecordLabel.textContent = "Klicken zum Aufnehmen";
  enrollStatus.style.display = "none";
  enrollStatus.className = "status-bar";
  enrollStatus.textContent = "";
  enrollModal.classList.add("open");
  enrollOverlay.classList.add("open");
}

function closeEnrollModal() {
  if (enrollRecording) stopEnrollRecording(false);
  enrollModal.classList.remove("open");
  enrollOverlay.classList.remove("open");
}

enrollClose.addEventListener("click", closeEnrollModal);
enrollOverlay.addEventListener("click", closeEnrollModal);

enrollRecordBtn.addEventListener("click", async () => {
  if (enrollRecording) {
    await stopEnrollRecording(true);
  } else {
    await startEnrollRecording();
  }
});

async function startEnrollRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    enrollChunks = [];
    enrollRecorder = new MediaRecorder(stream);
    enrollRecorder.ondataavailable = e => { if (e.data.size > 0) enrollChunks.push(e.data); };
    enrollRecorder.start(500);
    enrollRecording = true;
    enrollRecordBtn.classList.add("recording");
    enrollRecordLabel.textContent = "Aufnahme läuft... Klicken zum Beenden";
  } catch (err) {
    setEnrollStatus("error", "Mikrofon-Zugriff verweigert: " + err.message);
  }
}

async function stopEnrollRecording(upload) {
  enrollRecorder.stop();
  enrollRecorder.stream.getTracks().forEach(t => t.stop());
  enrollRecording = false;
  enrollRecordBtn.classList.remove("recording");
  enrollRecordLabel.textContent = "Aufnahme beendet";

  if (!upload) return;

  await new Promise(r => setTimeout(r, 300));
  const mimeType = enrollRecorder?.mimeType || "audio/webm";
  const ext = mimeType.includes("mp4") ? ".mp4" : ".webm";
  const blob = new Blob(enrollChunks, { type: mimeType });

  setEnrollStatus("processing", "Stimmprofil wird erstellt...");

  const fd = new FormData();
  fd.append("file", blob, `enroll${ext}`);
  const resp = await fetch(`/doctors/${encodeURIComponent(enrollDoctorName)}/enroll`, {
    method: "POST", body: fd,
  });

  if (resp.ok) {
    setEnrollStatus("ready", "Stimmprofil gespeichert ✓");
    setTimeout(() => {
      closeEnrollModal();
      loadDoctorList();
    }, 1200);
  } else {
    setEnrollStatus("error", "Fehler beim Speichern.");
  }
}

function setEnrollStatus(type, msg) {
  enrollStatus.style.display = "flex";
  enrollStatus.className = "status-bar " + type;
  const spin = type === "processing" ? '<div class="spinner"></div>' : "";
  enrollStatus.innerHTML = spin + msg;
}

// --- Diarization toggle ---
async function loadDiarizationToggle() {
  const resp = await fetch("/settings/diarization_enabled").then(r => r.json());
  diarizationToggle.checked = (resp.value ?? "true") === "true";
}

diarizationToggle.addEventListener("change", async () => {
  const fd = new FormData();
  fd.append("value", diarizationToggle.checked ? "true" : "false");
  await fetch("/settings/diarization_enabled", { method: "POST", body: fd });
});

// --- Init ---
loadHistory();
loadDoctors();
