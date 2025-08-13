const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const aiBtn = document.getElementById('ai-btn');
const keyModal = document.getElementById('key-modal');
const saveKey = document.getElementById('save-key');
const keyInput = document.getElementById('key-input');

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
  });
}

// simple pomodoro timer
let seconds = 25 * 60;
const timerEl = document.getElementById('timer');
setInterval(() => {
  const m = String(Math.floor(seconds / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  timerEl.textContent = `${m}:${s}`;
  if (seconds > 0) seconds--;
}, 1000);

// offline analyze
const btn = document.getElementById('analyze-btn');

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
    btn.textContent = `${t.name} (${t.count})`;
    btn.onclick = () => loadCourseCards(t.name);
    container.appendChild(btn);
  });
}

async function loadCourseCards(theme) {
  const resp = await fetch(`/api/fiches/${encodeURIComponent(theme)}`);
  const data = await resp.json();
  renderCourseCards(theme, data.fiches);
}

function renderCourseCards(theme, list) {
  const container = document.getElementById('course-cards');
  container.innerHTML = '';
  if (!list.length) {
    container.textContent = 'Aucune fiche.';
    return;
  }
  list.forEach(d => {
    if (d.kind !== 'card') return;
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
  renderDueCards(data.cards);
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
