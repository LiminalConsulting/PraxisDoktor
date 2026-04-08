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

// --- Elements ---
const startBtn      = document.getElementById("start-btn");
const patientRef    = document.getElementById("patient-ref");
const recordSection = document.getElementById("recording-section");
const recordBtn     = document.getElementById("record-btn");
const recordLabel   = document.getElementById("record-label");
const stopBtn       = document.getElementById("stop-btn");
const statusBar     = document.getElementById("status-bar");
const dropZone      = document.getElementById("drop-zone");
const formFile      = document.getElementById("form-file");
const ocrBlock      = document.getElementById("ocr-block");
const ocrToggle     = document.getElementById("ocr-toggle");
const ocrText       = document.getElementById("ocr-text");
const emptyState    = document.getElementById("empty-state");
const fieldsContainer = document.getElementById("fields-container");
const fieldsGrid    = document.getElementById("fields-grid");
const doneBtn       = document.getElementById("done-btn");
const historyToggle = document.getElementById("history-toggle");
const historyList   = document.getElementById("history-list");
const historyArrow  = document.getElementById("history-arrow");

// Settings
const settingsBtn    = document.getElementById("settings-btn");
const settingsPanel  = document.getElementById("settings-panel");
const settingsOverlay= document.getElementById("settings-overlay");
const settingsClose  = document.getElementById("settings-close");
const vocabTags      = document.getElementById("vocab-tags");
const vocabInput     = document.getElementById("vocab-input");
const vocabAddBtn    = document.getElementById("vocab-add-btn");

// --- Session start ---
startBtn.addEventListener("click", async () => {
  const ref = patientRef.value.trim();
  if (!ref) { patientRef.focus(); return; }

  const fd = new FormData();
  fd.append("patient_ref", ref);
  const resp = await fetch("/sessions", { method: "POST", body: fd });
  const session = await resp.json();
  loadSession(session);
  recordSection.style.display = "block";
  startBtn.disabled = true;
  patientRef.disabled = true;
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
}

stopBtn.addEventListener("click", async () => {
  stopRecording();
  stopBtn.disabled = true;
  recordBtn.disabled = true;

  await new Promise(r => setTimeout(r, 400)); // wait for final chunk
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
    renderFields(JSON.parse(msg.extracted !== undefined
      ? JSON.stringify(msg.extracted)
      : "{}"));
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
  // Copy buttons
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
  connectSSE(session.id);
  if (session.ocr_text) showOCR(session.ocr_text);
  if (session.extracted) {
    try { renderFields(JSON.parse(session.extracted)); } catch {}
  }
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

// --- Init ---
loadHistory();
