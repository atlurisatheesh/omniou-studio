"""
CLONEAI ULTRA — Capture & Generate Router
============================================
Serves a beautiful capture page that:
  1. Records webcam photo
  2. Records voice sample (with script prompt)
  3. Uploads both to the server
  4. Starts video generation from narration scripts
"""

import base64
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import structlog
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from ..config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/capture", tags=["Capture"])

UPLOAD_DIR = Path("uploads")
PHOTO_DIR = UPLOAD_DIR / "photos"
VOICE_DIR = UPLOAD_DIR / "voices"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)
VOICE_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def capture_page():
    """Serve the webcam + voice capture page."""
    return CAPTURE_HTML


@router.post("/upload-photo")
async def upload_capture_photo(file: UploadFile = File(...)):
    """Upload a webcam-captured photo."""
    file_id = uuid.uuid4().hex[:12]
    ext = ".jpg"
    filename = f"capture_{file_id}{ext}"
    filepath = PHOTO_DIR / filename

    content = await file.read()
    with open(str(filepath), "wb") as f:
        f.write(content)

    logger.info("capture.photo_uploaded", path=str(filepath), size=len(content))
    return {"status": "ok", "path": str(filepath), "filename": filename}


@router.post("/upload-voice")
async def upload_capture_voice(file: UploadFile = File(...)):
    """Upload a recorded voice sample."""
    file_id = uuid.uuid4().hex[:12]
    ext = ".webm"
    if file.filename and "." in file.filename:
        ext = "." + file.filename.rsplit(".", 1)[-1]
    filename = f"voice_{file_id}{ext}"
    filepath = VOICE_DIR / filename

    content = await file.read()
    with open(str(filepath), "wb") as f:
        f.write(content)

    logger.info("capture.voice_uploaded", path=str(filepath), size=len(content))
    return {"status": "ok", "path": str(filepath), "filename": filename}


# ── Load scripts from markdown ──

def _load_scripts():
    script_path = Path(__file__).parent.parent.parent.parent / "VIDEO_NARRATION_SCRIPTS.md"
    if not script_path.exists():
        # Try alternative paths
        for p in [
            Path("d:/ominou-studio/VIDEO_NARRATION_SCRIPTS.md"),
            Path("../VIDEO_NARRATION_SCRIPTS.md"),
        ]:
            if p.exists():
                script_path = p
                break

    if not script_path.exists():
        return []

    import re
    content = script_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"## VIDEO (\d+):\s*(.+?)\s*\((.+?)\)\s*\n.*?\n### Script:\s*\n```\s*\n(.*?)```",
        re.DOTALL,
    )

    videos = []
    for m in pattern.finditer(content):
        videos.append({
            "index": int(m.group(1)),
            "title": m.group(2).strip(),
            "duration": m.group(3).strip(),
            "script": m.group(4).strip(),
            "words": len(m.group(4).strip().split()),
        })
    return videos


@router.get("/scripts")
async def get_scripts():
    """Return all narration scripts."""
    return _load_scripts()


# ──────────────────────────────────────────────────────────────────────
# The full HTML capture page (inline for simplicity)
# ──────────────────────────────────────────────────────────────────────

CAPTURE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CloneAI Ultra — Capture Studio</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0f;
    --card: rgba(20, 20, 35, 0.8);
    --border: rgba(100, 100, 180, 0.15);
    --purple: #8b5cf6;
    --cyan: #06b6d4;
    --green: #10b981;
    --red: #ef4444;
    --yellow: #f59e0b;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --gradient: linear-gradient(135deg, #8b5cf6, #06b6d4);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Animated background */
  body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
      radial-gradient(ellipse at 20% 50%, rgba(139,92,246,0.08) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 20%, rgba(6,182,212,0.06) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 80%, rgba(16,185,129,0.04) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 30px 24px;
    position: relative;
    z-index: 1;
  }

  /* Header */
  .header {
    text-align: center;
    margin-bottom: 40px;
  }

  .header h1 {
    font-size: 2.5rem;
    font-weight: 800;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
  }

  .header p {
    color: var(--text-dim);
    font-size: 1.1rem;
  }

  /* Steps indicator */
  .steps {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 40px;
  }

  .step-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .step-num {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    transition: all 0.3s;
  }

  .step-num.active { background: var(--purple); color: white; box-shadow: 0 0 20px rgba(139,92,246,0.4); }
  .step-num.done { background: var(--green); color: white; }
  .step-num.pending { background: rgba(60,60,80,0.6); color: var(--text-dim); }

  .step-label { font-size: 0.85rem; color: var(--text-dim); }
  .step-connector { width: 40px; height: 2px; background: rgba(100,100,180,0.2); align-self: center; }

  /* Cards */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 32px;
    backdrop-filter: blur(20px);
    margin-bottom: 24px;
    transition: all 0.3s;
  }

  .card:hover { border-color: rgba(139,92,246,0.3); }

  .card h2 {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .card h2 .icon { font-size: 1.8rem; }

  .card .subtitle { color: var(--text-dim); margin-bottom: 24px; }

  /* Webcam */
  .webcam-container {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    background: #000;
    aspect-ratio: 4/3;
    max-width: 640px;
    margin: 0 auto 20px;
  }

  #webcam {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 16px;
  }

  #capturedPhoto {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 16px;
    display: none;
  }

  .webcam-overlay {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 12px;
  }

  /* Buttons */
  .btn {
    padding: 12px 28px;
    border: none;
    border-radius: 12px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .btn:hover { transform: translateY(-1px); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

  .btn-primary {
    background: var(--gradient);
    color: white;
    box-shadow: 0 4px 15px rgba(139,92,246,0.3);
  }

  .btn-success {
    background: linear-gradient(135deg, var(--green), #059669);
    color: white;
    box-shadow: 0 4px 15px rgba(16,185,129,0.3);
  }

  .btn-danger {
    background: linear-gradient(135deg, var(--red), #dc2626);
    color: white;
  }

  .btn-outline {
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border);
  }

  .btn-large {
    padding: 18px 40px;
    font-size: 1.1rem;
    border-radius: 16px;
  }

  /* Voice Recording */
  .voice-section {
    text-align: center;
  }

  .script-prompt {
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.2);
    border-radius: 16px;
    padding: 24px;
    margin: 20px auto;
    max-width: 700px;
    line-height: 1.8;
    font-size: 1.05rem;
    color: var(--text);
    text-align: left;
  }

  .script-prompt .label {
    color: var(--purple);
    font-weight: 700;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
    display: block;
  }

  /* Recording indicator */
  .recording-indicator {
    display: none;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 20px 0;
    font-weight: 600;
    color: var(--red);
  }

  .recording-indicator.active { display: flex; }

  .recording-dot {
    width: 14px;
    height: 14px;
    background: var(--red);
    border-radius: 50%;
    animation: pulse 1s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
  }

  /* Waveform */
  .waveform {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3px;
    margin: 20px auto;
    max-width: 400px;
  }

  .wave-bar {
    width: 4px;
    background: var(--purple);
    border-radius: 4px;
    transition: height 0.1s;
  }

  /* Script selector */
  .script-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
    margin-top: 20px;
  }

  .script-card {
    background: rgba(30,30,50,0.6);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .script-card:hover { border-color: var(--purple); transform: translateY(-2px); }
  .script-card.selected { border-color: var(--green); background: rgba(16,185,129,0.08); }

  .script-card .title {
    font-weight: 700;
    margin-bottom: 6px;
  }

  .script-card .meta {
    font-size: 0.8rem;
    color: var(--text-dim);
  }

  .script-card .preview {
    font-size: 0.85rem;
    color: var(--text-dim);
    margin-top: 8px;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Status badges */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .badge-success { background: rgba(16,185,129,0.15); color: var(--green); }
  .badge-pending { background: rgba(100,100,180,0.15); color: var(--text-dim); }

  /* Generation progress */
  .gen-progress {
    background: rgba(30,30,50,0.6);
    border-radius: 16px;
    padding: 24px;
    margin-top: 20px;
  }

  .progress-bar {
    height: 8px;
    background: rgba(60,60,80,0.4);
    border-radius: 4px;
    overflow: hidden;
    margin: 12px 0;
  }

  .progress-fill {
    height: 100%;
    background: var(--gradient);
    border-radius: 4px;
    transition: width 0.5s;
    width: 0%;
  }

  /* Hide sections */
  .section { display: none; }
  .section.active { display: block; }

  /* Captured preview */
  .captured-preview {
    display: flex;
    gap: 20px;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    margin: 20px 0;
  }

  .captured-preview img {
    width: 160px;
    height: 160px;
    object-fit: cover;
    border-radius: 16px;
    border: 3px solid var(--green);
  }

  .captured-preview audio {
    height: 40px;
  }

  /* Timer */
  .timer {
    font-size: 2rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    color: var(--purple);
  }
</style>
</head>
<body>

<div class="container">
  <!-- Header -->
  <div class="header">
    <h1>🎬 CloneAI Capture Studio</h1>
    <p>Record your face & voice → Generate identity-locked videos</p>
  </div>

  <!-- Steps -->
  <div class="steps">
    <div class="step-item"><div class="step-num active" id="step1dot">1</div><span class="step-label">Capture Photo</span></div>
    <div class="step-connector"></div>
    <div class="step-item"><div class="step-num pending" id="step2dot">2</div><span class="step-label">Record Voice</span></div>
    <div class="step-connector"></div>
    <div class="step-item"><div class="step-num pending" id="step3dot">3</div><span class="step-label">Select Script</span></div>
    <div class="step-connector"></div>
    <div class="step-item"><div class="step-num pending" id="step4dot">4</div><span class="step-label">Generate</span></div>
  </div>

  <!-- STEP 1: Webcam Capture -->
  <div class="section active" id="section1">
    <div class="card">
      <h2><span class="icon">📸</span> Capture Your Face</h2>
      <p class="subtitle">Look directly at the camera. This photo will be your identity anchor for ALL generated videos.</p>

      <div class="webcam-container">
        <video id="webcam" autoplay playsinline muted></video>
        <img id="capturedPhoto" alt="Captured" />
        <canvas id="photoCanvas" style="display:none"></canvas>
      </div>

      <div style="text-align:center">
        <button class="btn btn-primary btn-large" id="captureBtn" onclick="capturePhoto()">📸 Capture Photo</button>
        <button class="btn btn-outline btn-large" id="retakeBtn" onclick="retakePhoto()" style="display:none">🔄 Retake</button>
        <button class="btn btn-success btn-large" id="usePhotoBtn" onclick="usePhoto()" style="display:none">✅ Use This Photo → Next</button>
      </div>
    </div>
  </div>

  <!-- STEP 2: Voice Recording -->
  <div class="section" id="section2">
    <div class="card">
      <h2><span class="icon">🎙️</span> Record Your Voice</h2>
      <p class="subtitle">Read the script below naturally. This captures your voice identity for all videos.</p>

      <div class="script-prompt">
        <span class="label">📖 Read this aloud (10-15 seconds)</span>
        Welcome to AtluriIn AI — the most advanced AI-powered interview preparation platform.
        Whether you're preparing for a technical interview at Google, a behavioral round at Amazon,
        or a system design challenge at Meta — our platform gives you an unfair advantage.
        Here's what makes us different.
      </div>

      <div style="text-align:center">
        <div class="timer" id="voiceTimer">00:00</div>

        <div class="waveform" id="waveform"></div>

        <div class="recording-indicator" id="recordingIndicator">
          <div class="recording-dot"></div>
          <span>Recording...</span>
        </div>

        <div style="margin-top:16px">
          <button class="btn btn-danger btn-large" id="recordBtn" onclick="toggleRecording()">🎙️ Start Recording</button>
          <button class="btn btn-success btn-large" id="useVoiceBtn" onclick="useVoice()" style="display:none">✅ Use This Recording → Next</button>
        </div>

        <audio id="voicePlayback" controls style="display:none; margin: 16px auto;"></audio>
      </div>
    </div>
  </div>

  <!-- STEP 3: Script Selection -->
  <div class="section" id="section3">
    <div class="card">
      <h2><span class="icon">📝</span> Choose a Video Script</h2>
      <p class="subtitle">Select which video to generate. Your face & voice will be identity-locked across all scenes.</p>

      <div class="captured-preview" id="previewPanel">
        <!-- Filled dynamically -->
      </div>

      <div class="script-grid" id="scriptGrid">
        <!-- Filled dynamically -->
      </div>

      <div style="text-align:center; margin-top:24px">
        <button class="btn btn-success btn-large" id="generateBtn" onclick="startGeneration()" disabled>
          🚀 Generate Video
        </button>
      </div>
    </div>
  </div>

  <!-- STEP 4: Generation -->
  <div class="section" id="section4">
    <div class="card">
      <h2><span class="icon">⚡</span> Generating Your Video</h2>
      <p class="subtitle" id="genStatus">Creating identity anchor and splitting script into scenes...</p>

      <div class="gen-progress">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px">
          <span id="genStage">Initializing...</span>
          <span id="genPercent">0%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" id="genProgressBar"></div>
        </div>
        <div style="margin-top:12px; color: var(--text-dim); font-size:0.85rem" id="genDetails"></div>
      </div>
    </div>
  </div>
</div>

<script>
// ── State ──
let photoBlob = null;
let photoPath = null;
let voiceBlob = null;
let voicePath = null;
let selectedScript = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let timerInterval = null;
let timerSeconds = 0;
let audioCtx = null;
let analyser = null;
let webcamStream = null;

// ── Init Webcam ──
async function initWebcam() {
  try {
    webcamStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720, facingMode: 'user' },
      audio: false
    });
    document.getElementById('webcam').srcObject = webcamStream;
  } catch(e) {
    alert('Camera access denied. Please allow camera access and reload.');
  }
}

// ── Capture Photo ──
function capturePhoto() {
  const video = document.getElementById('webcam');
  const canvas = document.getElementById('photoCanvas');
  const img = document.getElementById('capturedPhoto');

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);

  canvas.toBlob(blob => {
    photoBlob = blob;
    img.src = URL.createObjectURL(blob);
    img.style.display = 'block';
    video.style.display = 'none';

    document.getElementById('captureBtn').style.display = 'none';
    document.getElementById('retakeBtn').style.display = 'inline-flex';
    document.getElementById('usePhotoBtn').style.display = 'inline-flex';
  }, 'image/jpeg', 0.92);
}

function retakePhoto() {
  document.getElementById('webcam').style.display = 'block';
  document.getElementById('capturedPhoto').style.display = 'none';
  document.getElementById('captureBtn').style.display = 'inline-flex';
  document.getElementById('retakeBtn').style.display = 'none';
  document.getElementById('usePhotoBtn').style.display = 'none';
  photoBlob = null;
}

async function usePhoto() {
  // Upload photo
  const form = new FormData();
  form.append('file', photoBlob, 'capture.jpg');

  try {
    const res = await fetch('/api/v1/capture/upload-photo', { method: 'POST', body: form });
    const data = await res.json();
    photoPath = data.path;

    // Stop webcam
    if (webcamStream) webcamStream.getTracks().forEach(t => t.stop());

    // Move to step 2
    updateStep(2);
  } catch(e) {
    alert('Upload failed: ' + e.message);
  }
}

// ── Voice Recording ──
async function toggleRecording() {
  if (!isRecording) {
    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      audioChunks = [];

      // Setup waveform
      audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      initWaveform();

      mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
      mediaRecorder.onstop = () => {
        voiceBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const playback = document.getElementById('voicePlayback');
        playback.src = URL.createObjectURL(voiceBlob);
        playback.style.display = 'block';
        document.getElementById('useVoiceBtn').style.display = 'inline-flex';
        stream.getTracks().forEach(t => t.stop());
      };

      mediaRecorder.start(100);
      isRecording = true;

      document.getElementById('recordBtn').innerHTML = '⏹️ Stop Recording';
      document.getElementById('recordBtn').className = 'btn btn-outline btn-large';
      document.getElementById('recordingIndicator').classList.add('active');
      document.getElementById('useVoiceBtn').style.display = 'none';
      document.getElementById('voicePlayback').style.display = 'none';

      // Timer
      timerSeconds = 0;
      timerInterval = setInterval(() => {
        timerSeconds++;
        const m = String(Math.floor(timerSeconds / 60)).padStart(2, '0');
        const s = String(timerSeconds % 60).padStart(2, '0');
        document.getElementById('voiceTimer').textContent = m + ':' + s;
        drawWaveform();
      }, 1000);

    } catch(e) {
      alert('Microphone access denied: ' + e.message);
    }
  } else {
    // Stop recording
    mediaRecorder.stop();
    isRecording = false;
    clearInterval(timerInterval);
    document.getElementById('recordBtn').innerHTML = '🎙️ Re-record';
    document.getElementById('recordBtn').className = 'btn btn-danger btn-large';
    document.getElementById('recordingIndicator').classList.remove('active');
  }
}

function initWaveform() {
  const container = document.getElementById('waveform');
  container.innerHTML = '';
  for (let i = 0; i < 32; i++) {
    const bar = document.createElement('div');
    bar.className = 'wave-bar';
    bar.style.height = '4px';
    container.appendChild(bar);
  }
}

function drawWaveform() {
  if (!analyser) return;
  const data = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(data);
  const bars = document.querySelectorAll('.wave-bar');
  bars.forEach((bar, i) => {
    const val = data[i] || 0;
    bar.style.height = Math.max(4, val / 4) + 'px';
  });
}

async function useVoice() {
  if (timerSeconds < 3) {
    alert('Please record at least 3 seconds of voice.');
    return;
  }

  const form = new FormData();
  form.append('file', voiceBlob, 'voice.webm');

  try {
    const res = await fetch('/api/v1/capture/upload-voice', { method: 'POST', body: form });
    const data = await res.json();
    voicePath = data.path;
    updateStep(3);
    loadScripts();
  } catch(e) {
    alert('Upload failed: ' + e.message);
  }
}

// ── Script Selection ──
async function loadScripts() {
  // Show preview
  const preview = document.getElementById('previewPanel');
  preview.innerHTML = `
    <img src="${URL.createObjectURL(photoBlob)}" alt="Your face" />
    <div>
      <div class="badge badge-success">📸 Photo captured</div><br><br>
      <div class="badge badge-success">🎙️ Voice recorded (${timerSeconds}s)</div>
    </div>
  `;

  // Load scripts
  try {
    const res = await fetch('/api/v1/capture/scripts');
    const scripts = await res.json();

    const grid = document.getElementById('scriptGrid');
    grid.innerHTML = '';

    scripts.forEach(s => {
      const card = document.createElement('div');
      card.className = 'script-card';
      card.onclick = () => selectScript(s, card);
      card.innerHTML = `
        <div class="title">🎬 VIDEO ${s.index}: ${s.title}</div>
        <div class="meta">${s.duration} • ${s.words} words</div>
        <div class="preview">${s.script.substring(0, 120)}...</div>
      `;
      grid.appendChild(card);
    });
  } catch(e) {
    console.error('Failed to load scripts:', e);
  }
}

function selectScript(script, card) {
  selectedScript = script;
  document.querySelectorAll('.script-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  document.getElementById('generateBtn').disabled = false;
}

// ── Generation ──
async function startGeneration() {
  if (!photoPath || !voicePath || !selectedScript) return;

  updateStep(4);

  try {
    // Call quick-generate API
    const res = await fetch('/api/v1/quick-generate/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        photo_path: photoPath,
        voice_path: voicePath,
        script_text: selectedScript.script,
        emotion: 'professional',
        name: selectedScript.title,
      }),
    });

    const data = await res.json();

    if (data.project_id) {
      document.getElementById('genStatus').textContent =
        `Project created! Generating ${data.total_scenes} scenes (~${(data.estimated_duration_seconds/60).toFixed(1)} min)...`;
      document.getElementById('genDetails').textContent = `Project ID: ${data.project_id}`;

      // Poll progress
      pollProgress(data.project_id);
    } else {
      document.getElementById('genStatus').textContent = 'Error: ' + JSON.stringify(data);
    }
  } catch(e) {
    document.getElementById('genStatus').textContent = 'Error: ' + e.message;
  }
}

async function pollProgress(projectId) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/v1/project/${projectId}/progress`);
      const prog = await res.json();

      document.getElementById('genStage').textContent =
        `Scene ${prog.completed_scenes}/${prog.total_scenes}`;
      document.getElementById('genPercent').textContent =
        Math.round(prog.progress_percent) + '%';
      document.getElementById('genProgressBar').style.width =
        prog.progress_percent + '%';

      if (prog.status === 'completed' || prog.status === 'failed') {
        clearInterval(interval);
        document.getElementById('genStatus').textContent =
          prog.status === 'completed'
            ? '✅ Video generated successfully!'
            : '❌ Generation failed.';

        if (prog.overall_identity_score) {
          document.getElementById('genDetails').textContent +=
            ` | Identity: ${Math.round(prog.overall_identity_score * 100)}%`;
        }
      }
    } catch(e) { /* retry */ }
  }, 3000);
}

// ── Step Navigation ──
function updateStep(step) {
  // Update dots
  for (let i = 1; i <= 4; i++) {
    const dot = document.getElementById(`step${i}dot`);
    const section = document.getElementById(`section${i}`);
    if (i < step) { dot.className = 'step-num done'; dot.textContent = '✓'; }
    else if (i === step) { dot.className = 'step-num active'; }
    else { dot.className = 'step-num pending'; }

    section.classList.toggle('active', i === step);
  }
}

// ── Init ──
initWebcam();
</script>

</body>
</html>
"""
