const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const aiBtn = document.getElementById('ai-btn');
const keyModal = document.getElementById('key-modal');
const saveKey = document.getElementById('save-key');
const keyInput = document.getElementById('key-input');
const webQ = document.getElementById('web-q');
const webSearchBtn = document.getElementById('web-search');
const webAI = document.getElementById('web-ai');
const webResults = document.getElementById('web-results');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');
const chatLog = document.getElementById('chat-log');
const chatStatus = document.getElementById('chat-status');
let sessionLimit = null;
let currentChatController = null;

function toast(msg) {
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

for (const tab of tabs) {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    const target = document.getElementById(tab.dataset.tab);
    target.classList.add('active');
    if (tab.dataset.tab === 'courses') {
      loadThemes();
    }
    if (tab.dataset.tab === 'flash') {
      loadDueCards();
    }
    if (tab.dataset.tab === 'exercises') {
      loadExercises();
    }
  });
}

// === Pomodoro Pro ===
const WORK_BLOCK_MIN = 25;
const BREAK_BLOCK_MIN = 5;

let targetMinutes = parseInt(document.getElementById('session-minutes').value || '25', 10);
let mode = 'work';
let remaining = WORK_BLOCK_MIN * 60;
let elapsedTotal = 0;
let running = false;
let tickHandle = null;

const timerEl = document.getElementById('timer');
const labelEl = document.getElementById('timer-label');
const startBtn = document.getElementById('timer-start');
const pauseBtn = document.getElementById('timer-pause');
const resumeBtn = document.getElementById('timer-resume');
const resetBtn = document.getElementById('timer-reset');
const sessionSel = document.getElementById('session-minutes');

function fmt(sec) {
  const m = String(Math.floor(sec / 60)).padStart(2, '0');
  const s = String(sec % 60).padStart(2, '0');
  return `${m}:${s}`;
}

function updateDisplay() {
  if (timerEl) timerEl.textContent = fmt(remaining);
  if (labelEl) labelEl.textContent = mode === 'work' ? 'Travail' : 'Pause';
}

function switchMode(next) {
  mode = next;
  remaining = (mode === 'work' ? WORK_BLOCK_MIN : BREAK_BLOCK_MIN) * 60;
  updateDisplay();
}

function stopTick() {
  if (tickHandle) {
    clearInterval(tickHandle);
    tickHandle = null;
  }
  running = false;
}

function startTick() {
  if (running) return;
  running = true;
  tickHandle = setInterval(() => {
    if (remaining > 0) {
      remaining--;
      elapsedTotal++;
      updateDisplay();
    } else {
      if (mode === 'work') {
        switchMode('break');
        alert('⏸️ Pause 5 minutes !');
      } else {
        switchMode('work');
      }
    }
    const elapsedMin = Math.floor(elapsedTotal / 60);
    if (elapsedMin >= targetMinutes && mode === 'work' && remaining === (WORK_BLOCK_MIN * 60 - 1)) {
      stopTick();
      alert(`Session terminée (${targetMinutes} min) ✅`);
    }
  }, 1000);
}

startBtn?.addEventListener('click', () => {
  stopTick();
  targetMinutes = parseInt(sessionSel.value || '25', 10);
  elapsedTotal = 0;
  mode = 'work';
  remaining = WORK_BLOCK_MIN * 60;
  updateDisplay();
  startTick();
});

pauseBtn?.addEventListener('click', () => stopTick());
resumeBtn?.addEventListener('click', () => startTick());
resetBtn?.addEventListener('click', () => {
  stopTick();
  elapsedTotal = 0;
  mode = 'work';
  remaining = WORK_BLOCK_MIN * 60;
  updateDisplay();
});

sessionSel?.addEventListener('change', () => {
  targetMinutes = parseInt(sessionSel.value || '25', 10);
});

updateDisplay();

// offline analyze
const btn = document.getElementById('analyze-btn');
const uploadBtn = document.getElementById('upload-btn');

function renderDrafts(list, meta) {
  const drafts = document.getElementById('drafts');
  drafts.innerHTML = '';
  if (meta) {
    const info = document.createElement('div');
    info.className = 'analysis-meta';
    info.textContent = `Lisibilité ${(meta.readability * 100).toFixed(0)}% · Densité ${meta.density.toFixed(2)}`;
    drafts.appendChild(info);
  }
  list.forEach(d => {
    const div = document.createElement('div');
    div.className = 'draft';
    div.textContent = `${d.payload.front || d.payload.q}`;
    const accept = document.createElement('button');
    accept.textContent = 'Accepter';
    accept.onclick = async () => {
      await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: [d] })
      });
      accept.disabled = true;
      toast('✅ Ajouté (Flashcards > dues)');
    };
    const reject = document.createElement('button');
    reject.textContent = 'Rejeter';
    reject.onclick = () => div.remove();
    div.appendChild(document.createElement('br'));
    div.appendChild(accept);
    div.appendChild(reject);
    drafts.appendChild(div);
  });
}

btn?.addEventListener('click', async () => {
  const text = document.getElementById('source-text').value;
  const resp = await fetch('/api/offline/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  const data = await resp.json();
  renderDrafts(data.drafts, data.meta);
});

// Enhanced file upload with drag-and-drop
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadProgress = document.getElementById('upload-progress');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

let uploadAbortController = null;

function showUploadProgress(show = true) {
  if (!uploadProgress) return;
  uploadProgress.classList.toggle('hidden', !show);
}

function updateUploadProgress(percent, text = 'Téléchargement...') {
  if (progressFill) progressFill.style.width = `${percent}%`;
  if (progressText) {
    progressText.textContent = text;
    progressText.className = `progress-text ${percent < 100 ? 'loading' : ''}`;
  }
}

function resetUploadState() {
  showUploadProgress(false);
  updateUploadProgress(0);
  if (dropZone) dropZone.classList.remove('dragover');
  if (uploadAbortController) {
    uploadAbortController.abort();
    uploadAbortController = null;
  }
}

function validateFile(file) {
  const maxSize = 50 * 1024 * 1024; // 50MB
  const allowedTypes = [
    'text/plain',
    'text/markdown',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
  ];
  
  if (file.size > maxSize) {
    throw new Error('Le fichier est trop volumineux (max 50MB)');
  }
  
  if (!allowedTypes.includes(file.type) && !file.name.match(/\.(txt|md|pdf|docx|doc)$/i)) {
    throw new Error('Type de fichier non supporté. Utilisez PDF, DOCX, TXT ou Markdown');
  }
  
  return true;
}

async function uploadFile(file) {
  try {
    validateFile(file);
    
    uploadAbortController = new AbortController();
    showUploadProgress(true);
    updateUploadProgress(0, 'Préparation...');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('use_ai', document.getElementById('use-ai-upload')?.checked ? 'true' : 'false');
    formData.append('session_minutes', document.getElementById('session-minutes')?.value || '25');
    
    updateUploadProgress(25, 'Téléchargement...');
    
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
      signal: uploadAbortController.signal
    });
    
    updateUploadProgress(75, 'Traitement...');
    
    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    updateUploadProgress(100, 'Terminé!');
    
    setTimeout(() => {
      resetUploadState();
      toast(`✅ ${result.saved} éléments ajoutés depuis "${file.name}"`);
    }, 1000);
    
    // Refresh relevant data
    loadThemes();
    loadDueCards();
    
  } catch (error) {
    resetUploadState();
    
    if (error.name === 'AbortError') {
      toast('❌ Téléchargement annulé');
    } else {
      toast(`❌ Erreur: ${error.message}`);
      console.error('Upload error:', error);
    }
  }
}

// Drag and drop event handlers
if (dropZone) {
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    if (!dropZone.contains(e.relatedTarget)) {
      dropZone.classList.remove('dragover');
    }
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  });
}

// File input change handler
if (fileInput) {
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      uploadFile(file);
    }
  });
}

// Update the existing upload button handler
uploadBtn?.addEventListener('click', async () => {
  const file = fileInput?.files[0];
  if (!file) {
    fileInput?.click(); // Open file dialog if no file selected
    return;
  }
  uploadFile(file);
});

aiBtn?.addEventListener('click', async () => {
  const text = document.getElementById('source-text').value;
  const resp = await fetch('/api/ai/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, force: true, reason: 'user' })
  });
  const data = await resp.json();
  renderDrafts(data.drafts, data.meta);
});

webSearchBtn?.addEventListener('click', async () => {
  const q = (webQ.value || '').trim();
  if (!q) return;
  webResults.textContent = 'Recherche...';
  const r = await fetch(`/api/web/search?q=${encodeURIComponent(q)}`);
  const data = await r.json();
  webResults.innerHTML = '';
  data.results.forEach(res => {
    const div = document.createElement('div');
    div.className = 'draft';
    div.innerHTML = `<b>${res.title}</b> — <a href="${res.url}" target="_blank">source</a><br>${res.excerpt}`;
    webResults.appendChild(div);
  });
  const enrichBtn = document.createElement('button');
  enrichBtn.textContent = 'Ajouter ces résultats à mes fiches';
  enrichBtn.onclick = async () => {
    enrichBtn.disabled = true;
    const resp = await fetch('/api/web/enrich', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, use_ai: webAI.checked })
    });
    const out = await resp.json();
    alert(`Ajouté: ${out.added} items.\nSources:\n- ${out.citations.map(c=>c.title).join('\n- ')}`);
  };
  webResults.appendChild(enrichBtn);
});

// --- FICHES DE COURS ---

async function loadThemes() {
  const resp = await fetch('/api/themes');
  const data = await resp.json();
  renderThemes(data.themes);
}

function renderThemes(themes) {
  const container = document.getElementById('themes');
  container.innerHTML = '';
  themes.forEach(t => {
    const btn = document.createElement('button');
    btn.textContent = `${t.name} (${t.cards}/${t.exercises})`;
    btn.onclick = () => loadCourseCards(t.name);
    container.appendChild(btn);
  });
}

async function loadCourseCards(theme) {
  const resp = await fetch(`/api/fiches/${encodeURIComponent(theme)}`);
  const data = await resp.json();
  renderCourseCards(theme, data);
}

function renderCourseCards(theme, data) {
  const container = document.getElementById('course-cards');
  container.innerHTML = '';
  const { cards = [], courses = [], exercises = [] } = data;
  if (!cards.length && !courses.length && !exercises.length) {
    container.textContent = 'Aucune fiche.';
    return;
  }
  courses.forEach(c => {
    const div = document.createElement('div');
    div.className = 'course-item';
    const title = document.createElement('h3');
    title.textContent = c.payload.title;
    const summary = document.createElement('p');
    summary.textContent = c.payload.summary;
    const ul = document.createElement('ul');
    (c.payload.bullets || []).forEach(b => {
      const li = document.createElement('li');
      li.textContent = b;
      ul.appendChild(li);
    });
    div.appendChild(title);
    div.appendChild(summary);
    div.appendChild(ul);
    container.appendChild(div);
  });
  cards.forEach(d => {
    const card = document.createElement('div');
    card.className = 'flashcard';
    const inner = document.createElement('div');
    inner.className = 'inner';
    const front = document.createElement('div');
    front.className = 'front';
    front.textContent = d.payload.front;
    const back = document.createElement('div');
    back.className = 'back';
    back.textContent = d.payload.back || d.payload.answer || '';
    inner.appendChild(front);
    inner.appendChild(back);
    card.appendChild(inner);
    const elab = document.createElement('div');
    elab.className = 'elab';
    elab.textContent = 'Pourquoi ?';
    elab.style.display = 'none';
    card.addEventListener('click', () => {
      card.classList.toggle('flip');
      elab.style.display = card.classList.contains('flip') ? 'block' : 'none';
    });
    const actions = document.createElement('div');
    const elaborer = document.createElement('button');
    elaborer.textContent = 'Élaborer';
    elaborer.onclick = () => prompt('Pourquoi ?');
    const ok = document.createElement('button');
    ok.textContent = 'Maîtrisée';
    ok.onclick = () => updateStatus(d.id, 'mastered');
    const again = document.createElement('button');
    again.textContent = 'À revoir';
    again.onclick = () => updateStatus(d.id, 'review');
    actions.appendChild(elaborer);
    actions.appendChild(ok);
    actions.appendChild(again);
    container.appendChild(card);
    container.appendChild(elab);
    container.appendChild(actions);
  });
  if (exercises.length) {
    const exDiv = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = 'Exercices';
    const inner = document.createElement('div');
    exDiv.appendChild(title);
    exDiv.appendChild(inner);
    container.appendChild(exDiv);
    renderExercises(exercises, inner);
  }
}

async function updateStatus(id, status) {
  await fetch(`/api/card/${id}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
}

// --- FLASHCARDS DUES ---

async function loadDueCards() {
  const resp = await fetch('/api/due');
  const data = await resp.json();
  let list = data.cards;
  if (sessionLimit) {
    list = list.slice(0, sessionLimit);
  }
  renderDueCards(list);
}

function renderDueCards(list) {
  const container = document.getElementById('due-cards');
    container.innerHTML = '';
  if (!list.length) {
    container.textContent = 'Aucune carte à réviser.';
    return;
  }
  shuffle(list);
  list.forEach(c => {
    const card = document.createElement('div');
    card.className = 'flashcard';
    const inner = document.createElement('div');
    inner.className = 'inner';
    const front = document.createElement('div');
    front.className = 'front';
    front.textContent = c.front;
    const back = document.createElement('div');
    back.className = 'back';
    back.textContent = c.back || c.answer || '';
    inner.appendChild(front);
    inner.appendChild(back);
    card.appendChild(inner);
    const elab = document.createElement('div');
    elab.className = 'elab';
    elab.textContent = 'Pourquoi ?';
    elab.style.display = 'none';
    card.addEventListener('click', () => {
      card.classList.toggle('flip');
      elab.style.display = card.classList.contains('flip') ? 'block' : 'none';
    });

    const actions = document.createElement('div');
    ['0','1','2','3','4','5'].forEach(q => {
      const b = document.createElement('button');
      b.textContent = q;
      b.onclick = () => reviewCard(c.id, Number(q));
      actions.appendChild(b);
    });

    container.appendChild(card);
    container.appendChild(elab);
    container.appendChild(actions);
  });
}

async function loadExercises() {
  const resp = await fetch('/api/due');
  const data = await resp.json();
  renderExercises(data.exercises);
}

function renderExercises(list, targetDiv) {
  const container = targetDiv || document.getElementById('exercise-list');
  container.innerHTML = '';
  if (!list.length) {
    container.textContent = 'Aucun exercice.';
    return;
  }
  list.forEach((e, i) => {
    const div = document.createElement('div');
    div.className = 'exercise';
    const q = document.createElement('p');
    q.textContent = e.q || e.recto || '';
    div.appendChild(q);
    if (e.type === 'QCM') {
      e.options.forEach(opt => {
        const label = document.createElement('label');
        const inp = document.createElement('input');
        inp.type = 'radio';
        inp.name = 'qcm' + i;
        label.appendChild(inp);
        label.append(opt);
        div.appendChild(label);
      });
      const btn = document.createElement('button');
      btn.textContent = 'Vérifier';
      btn.onclick = () => {
        const sel = div.querySelector('input[type=radio]:checked');
        const val = sel ? sel.nextSibling.textContent : '';
        alert(val === e.answer ? 'Correct' : `Faux: ${e.answer}`);
      };
      div.appendChild(btn);
    } else {
      const inp = document.createElement('input');
      const btn = document.createElement('button');
      btn.textContent = 'Correction';
      btn.onclick = () => alert(`Réponse: ${e.answer}`);
      div.appendChild(inp);
      div.appendChild(btn);
    }
    container.appendChild(div);
  });
}

async function reviewCard(id, quality) {
  await fetch(`/api/review/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quality })
  });
  loadDueCards();
}

// Enhanced chat functionality with streaming support
function createChatMessage(content, className) {
  const div = document.createElement('div');
  div.className = className;
  div.innerHTML = formatChatMessage(content);
  return div;
}

function formatChatMessage(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

function showChatStatus(message, isLoading = false) {
  if (!chatStatus) return;
  chatStatus.textContent = message;
  chatStatus.className = `chat-status ${isLoading ? 'loading' : ''}`;
  chatStatus.classList.remove('hidden');
}

function hideChatStatus() {
  if (!chatStatus) return;
  chatStatus.classList.add('hidden');
}

function setChatInputState(enabled) {
  if (chatInput) chatInput.disabled = !enabled;
  if (chatSend) chatSend.disabled = !enabled;
}

async function sendChatMessage() {
  const msg = (chatInput?.value || '').trim();
  if (!msg || !chatInput || !chatLog) return;
  
  // Cancel any existing request
  if (currentChatController) {
    currentChatController.abort();
  }
  currentChatController = new AbortController();
  
  // Add user message
  const userMsg = createChatMessage(msg, 'chat-user');
  chatLog.appendChild(userMsg);
  chatInput.value = '';
  
  // Create bot response container
  const botMsg = createChatMessage('', 'chat-bot streaming');
  chatLog.appendChild(botMsg);
  chatLog.scrollTop = chatLog.scrollHeight;
  
  setChatInputState(false);
  showChatStatus('Génération de la réponse...', true);
  
  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
      signal: currentChatController.signal
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              fullResponse += data.content;
              botMsg.innerHTML = formatChatMessage(fullResponse);
              chatLog.scrollTop = chatLog.scrollHeight;
            }
            if (data.done) {
              botMsg.classList.remove('streaming');
              hideChatStatus();
              setChatInputState(true);
              chatInput.focus();
              return;
            }
          } catch (e) {
            // Skip malformed JSON
          }
        }
      }
    }
  } catch (error) {
    botMsg.classList.remove('streaming');
    
    if (error.name === 'AbortError') {
      botMsg.innerHTML = '<em>Requête annulée</em>';
      showChatStatus('Requête annulée');
    } else {
      botMsg.innerHTML = '<em>Erreur lors de la génération de la réponse. Essayez à nouveau.</em>';
      showChatStatus(`Erreur: ${error.message}`);
      console.error('Chat error:', error);
    }
    
    setTimeout(hideChatStatus, 3000);
  } finally {
    setChatInputState(true);
    currentChatController = null;
    if (chatInput) chatInput.focus();
  }
}

// Event listeners for chat
chatSend?.addEventListener('click', sendChatMessage);

chatInput?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
});

// Cancel current request on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && currentChatController) {
    currentChatController.abort();
    showChatStatus('Requête annulée');
    setTimeout(hideChatStatus, 2000);
  }
});

// --- API key handling ---
async function checkKey() {
  const resp = await fetch('/api/config');
  const data = await resp.json();
  if (!data.has_key) {
    keyModal.classList.remove('hidden');
  } else {
    aiBtn.disabled = false;
  }
}

saveKey?.addEventListener('click', async () => {
  const key = keyInput.value.trim();
  if (!key) return;
  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key })
  });
  keyModal.classList.add('hidden');
  aiBtn.disabled = false;
});

checkKey();
