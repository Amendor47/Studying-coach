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
let sessionLimit = null;

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
  timerEl.textContent = fmt(remaining);
  labelEl.textContent = mode === 'work' ? 'Travail' : 'Pause';
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

startBtn.addEventListener('click', () => {
  stopTick();
  targetMinutes = parseInt(sessionSel.value || '25', 10);
  elapsedTotal = 0;
  mode = 'work';
  remaining = WORK_BLOCK_MIN * 60;
  updateDisplay();
  startTick();
});

pauseBtn.addEventListener('click', () => stopTick());
resumeBtn.addEventListener('click', () => startTick());
resetBtn.addEventListener('click', () => {
  stopTick();
  elapsedTotal = 0;
  mode = 'work';
  remaining = WORK_BLOCK_MIN * 60;
  updateDisplay();
});

sessionSel.addEventListener('change', () => {
  targetMinutes = parseInt(sessionSel.value || '25', 10);
});

updateDisplay();

// offline analyze
const btn = document.getElementById('analyze-btn');
const uploadBtn = document.getElementById('upload-btn');

async function renderDrafts(list) {
  const drafts = document.getElementById('drafts');
  drafts.innerHTML = '';
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

btn.addEventListener('click', async () => {
  const text = document.getElementById('source-text').value;
  const resp = await fetch('/api/offline/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  const data = await resp.json();
  renderDrafts(data.drafts);
});

uploadBtn.addEventListener('click', async () => {
  const fileInput = document.getElementById('file-input');
  const file = fileInput.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  form.append('use_ai', document.getElementById('use-ai-upload').checked);
  form.append('session_minutes', document.getElementById('session-minutes').value);
  const resp = await fetch('/api/upload', { method: 'POST', body: form });
  const data = await resp.json();
  toast(`✅ ${data.saved} fiches ajoutées`);
  sessionLimit = Math.min(Math.ceil((data.minutes || 0) / 1.5), data.due.length);
  document.querySelector('.tab[data-tab="flash"]').click();
  loadDueCards();
});

aiBtn.addEventListener('click', async () => {
  const text = document.getElementById('source-text').value;
  const resp = await fetch('/api/ai/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, force: true, reason: 'user' })
  });
  const data = await resp.json();
  renderDrafts(data.drafts);
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
    back.textContent = d.payload.back;
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
    back.textContent = c.back;
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

saveKey.addEventListener('click', async () => {
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
