// ═══════════════════════════════════════════════════════════════════════════════
// LifeOS — Premium Dashboard Controller v3.0
// ═══════════════════════════════════════════════════════════════════════════════

// ─── Auth ───────────────────────────────────────────────────────────────────
const currentUser = localStorage.getItem('lifeos-user');
if (!currentUser) window.location.href = '/login';
document.getElementById('profileName').textContent = currentUser;
document.getElementById('modalName').textContent = currentUser;
document.getElementById('heroName').textContent = `${currentUser}'s Digital Life`;
const uAv = localStorage.getItem('lifeos-avatar') || '🧑‍🚀';
document.getElementById('profileAvatar').textContent = uAv;
document.getElementById('modalAvatar').textContent = uAv;

// ─── State ──────────────────────────────────────────────────────────────────
let stepCount = 0, isDone = false, isInitialized = false, currentStats = {};
let prevStats = {};
let autoPilotInterval = null;
let maxSteps = 100;
let rewardHistory = [];
let eventLog = [];
let decisionLog = [];
let lifetimeStats = JSON.parse(localStorage.getItem('lifeos-stats') || '{"runs":0,"peak":0,"capital":0,"steps":0}');
let badges = JSON.parse(localStorage.getItem('lifeos-badges') || '{"wealth":false,"zen":false,"hustle":false,"survivor":false}');

// ─── Constants ──────────────────────────────────────────────────────────────
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 26; // r=26 from SVG

const STAT_CFG = {
  health:        { label:'Health',    max:100,    col:'#10b981', icon:'❤️',  gradId:'healthGrad' },
  money:         { label:'Money',     max:100000, col:'#f59e0b', icon:'💰',  gradId:'moneyGrad' },
  stress:        { label:'Stress',    max:100,    col:'#ef4444', icon:'😰',  gradId:'stressGrad' },
  career:        { label:'Career',    max:100,    col:'#3b82f6', icon:'🚀',  gradId:'careerGrad' },
  relationships: { label:'Relations', max:100,    col:'#8b5cf6', icon:'💜',  gradId:'relationsGrad' },
  happiness:     { label:'Happiness', max:100,    col:'#ec4899', icon:'😊',  gradId:'happinessGrad' },
};

const ACTION_MSGS = {
  work_overtime:     {t:"Overtime Completed",    m:"Capital injected. Stress spiked.",          c:"var(--info)"},
  exercise:          {t:"Physical Protocol",     m:"Health boosted. Neural pathways optimized.",c:"var(--success)"},
  invest_money:      {t:"Asset Allocation",      m:"Capital deployed to markets.",              c:"var(--info)"},
  learn_skill:       {t:"Data Acquisition",      m:"Career trajectory steepened.",              c:"var(--info)"},
  socialize:         {t:"Synergy Network",       m:"Social bonds strengthened.",                c:"var(--success)"},
  rest:              {t:"System Standby",        m:"Deep recalibration complete.",              c:"var(--success)"},
  start_side_hustle: {t:"Aggressive Expansion",  m:"Massive capital at extreme stress cost.",   c:"var(--warning)"},
  take_vacation:     {t:"Sensory Reset",         m:"Full biological reset. Peace attained.",    c:"var(--success)"},
  meditate:          {t:"Zen Protocol",          m:"Inner equilibrium achieved.",               c:"var(--success)"},
  gamble:            {t:"Calculated Volatility", m:"Probability matrix engaged.",               c:"var(--warning)"},
};

// ─── DOM Refs ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const terminal = $('terminalFeed');

// ═══════════════════════════════════════════════════════════════════════════════
// PARTICLE SYSTEM — Ambient floating orbs
// ═══════════════════════════════════════════════════════════════════════════════
(function initParticles() {
  const canvas = $('particleCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  const PARTICLE_COUNT = 35;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 2.5 + 0.5;
      this.speedX = (Math.random() - 0.5) * 0.3;
      this.speedY = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.4 + 0.05;
      this.hue = Math.random() > 0.5 ? 240 : 280;
    }
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      if (this.x < -10 || this.x > canvas.width + 10 || this.y < -10 || this.y > canvas.height + 10) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue}, 75%, 65%, ${this.opacity})`;
      ctx.fill();
      // Glow
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size * 3, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue}, 75%, 65%, ${this.opacity * 0.15})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle());

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(99, 102, 241, ${0.04 * (1 - dist / 150)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(animate);
  }
  animate();
})();

// ═══════════════════════════════════════════════════════════════════════════════
// CIRCULAR GAUGE RENDERING
// ═══════════════════════════════════════════════════════════════════════════════
function setGauge(key, pct) {
  const el = $('gauge-' + key);
  if (!el) return;
  const offset = GAUGE_CIRCUMFERENCE * (1 - Math.min(1, Math.max(0, pct / 100)));
  el.style.strokeDashoffset = offset;
  // Add glow filter based on percentage
  const cfg = STAT_CFG[key];
  if (cfg) {
    el.style.filter = `drop-shadow(0 0 ${Math.max(2, pct / 15)}px ${cfg.col}40)`;
  }
}

function setScoreRing(score) {
  const ring = $('scoreRing');
  if (!ring) return;
  const circumference = 2 * Math.PI * 40;
  const pct = Math.max(0, Math.min(1, (score + 1) / 2)); // map [-1,1] to [0,1]
  ring.style.strokeDashoffset = circumference * (1 - pct);
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODAL / THEME / PROFILE
// ═══════════════════════════════════════════════════════════════════════════════
$('profileBadge').onclick = e => { e.preventDefault(); $('profileOverlay').classList.add('active'); renderProfileStats(); };
$('closeProfile').onclick = () => $('profileOverlay').classList.remove('active');
$('logoutBtn').onclick = () => { localStorage.clear(); window.location.reload(); };
$('themeToggle').onclick = () => {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  timelineChart.update('none');
  rewardsChart.update('none');
};

// ─── Sidebar Range Sliders ──────────────────────────────────────────────────
$('cfgMaxSteps').oninput = function() { $('maxStepsVal').textContent = this.value; maxSteps = +this.value; };
$('cfgSpeed').oninput = function() { $('speedVal').textContent = (+this.value).toFixed(2); };

// ─── Tabs ───────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    $('tab-' + btn.dataset.tab).classList.add('active');
  };
});

// ═══════════════════════════════════════════════════════════════════════════════
// CHARTS — Enhanced with gradients
// ═══════════════════════════════════════════════════════════════════════════════
const chartFont = { family: "'Inter', sans-serif", size: 10 };
const chartOpts = {
  responsive: true,
  maintainAspectRatio: false,
  elements: { point: { radius: 0, hoverRadius: 4 } },
  plugins: { legend: { labels: { color: '#8892b0', font: chartFont, boxWidth: 10, padding: 12 } } },
  interaction: { mode: 'index', intersect: false },
};

function makeGradient(ctx, color, opacity = 0.12) {
  const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
  gradient.addColorStop(0, color.replace(')', `,${opacity})`).replace('rgb', 'rgba'));
  gradient.addColorStop(1, 'rgba(0,0,0,0)');
  return gradient;
}

const timelineChart = new Chart($('timelineChart').getContext('2d'), {
  type: 'line',
  data: { labels: [], datasets: [
    { label: 'Health',    data: [], borderColor: '#10b981', borderWidth: 2, tension: 0.4, fill: true, backgroundColor: 'rgba(16,185,129,0.06)' },
    { label: 'Money/1k',  data: [], borderColor: '#f59e0b', borderWidth: 2, tension: 0.4, fill: true, backgroundColor: 'rgba(245,158,11,0.06)' },
    { label: 'Stress',    data: [], borderColor: '#ef4444', borderWidth: 2, tension: 0.4, fill: true, backgroundColor: 'rgba(239,68,68,0.06)' },
    { label: 'Career',    data: [], borderColor: '#3b82f6', borderWidth: 2, tension: 0.4, fill: true, backgroundColor: 'rgba(59,130,246,0.06)' },
    { label: 'Relations', data: [], borderColor: '#8b5cf6', borderWidth: 2, tension: 0.4, fill: true, backgroundColor: 'rgba(139,92,246,0.06)' },
    { label: 'Happiness', data: [], borderColor: '#ec4899', borderWidth: 2, tension: 0.4, fill: true, backgroundColor: 'rgba(236,72,153,0.06)' },
  ]},
  options: {
    ...chartOpts,
    scales: {
      y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.025)' }, ticks: { color: '#4a5275', font: chartFont } },
      x: { grid: { color: 'rgba(255,255,255,0.025)' }, ticks: { color: '#4a5275', font: chartFont } }
    }
  }
});

const rewardsChart = new Chart($('rewardsChart').getContext('2d'), {
  type: 'line',
  data: { labels: [], datasets: [{
    label: 'Reward',
    data: [],
    borderColor: '#6366f1',
    borderWidth: 2,
    tension: 0.35,
    fill: true,
    backgroundColor: 'rgba(99,102,241,0.08)',
    pointBackgroundColor: '#6366f1',
  }] },
  options: {
    ...chartOpts,
    scales: {
      y: { min: -1, max: 1, grid: { color: 'rgba(255,255,255,0.025)' }, ticks: { color: '#4a5275', font: chartFont } },
      x: { grid: { color: 'rgba(255,255,255,0.025)' }, ticks: { color: '#4a5275', font: chartFont } }
    }
  }
});

function pushHistory(s, reward) {
  const lbl = stepCount;
  timelineChart.data.labels.push(lbl);
  timelineChart.data.datasets[0].data.push(s.health);
  timelineChart.data.datasets[1].data.push(Math.min(100, (s.money || 0) / 1000));
  timelineChart.data.datasets[2].data.push(s.stress);
  timelineChart.data.datasets[3].data.push(s.career);
  timelineChart.data.datasets[4].data.push(s.relationships);
  timelineChart.data.datasets[5].data.push(s.happiness || 0);
  if (timelineChart.data.labels.length > 60) {
    timelineChart.data.labels.shift();
    timelineChart.data.datasets.forEach(d => d.data.shift());
  }
  timelineChart.update('none');

  if (reward !== undefined) {
    rewardsChart.data.labels.push(lbl);
    rewardsChart.data.datasets[0].data.push(reward);
    if (rewardsChart.data.labels.length > 60) {
      rewardsChart.data.labels.shift();
      rewardsChart.data.datasets[0].data.shift();
    }
    rewardsChart.update('none');
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// RENDER STATS — Circular gauges + deltas
// ═══════════════════════════════════════════════════════════════════════════════
function renderStats(state) {
  for (const [key, cfg] of Object.entries(STAT_CFG)) {
    const val = state[key] ?? 0;
    const pct = Math.min(100, (val / cfg.max) * 100);
    const display = key === 'money' ? `$${Math.round(val).toLocaleString()}` : val.toFixed(1);
    const card = $('sc-' + key);
    if (!card) continue;

    // Update value text
    card.querySelector('.stat-value').textContent = display;

    // Update circular gauge
    setGauge(key, pct);

    // Delta indicator
    const deltaEl = $('delta-' + key);
    if (deltaEl && prevStats[key] !== undefined) {
      const diff = val - prevStats[key];
      if (Math.abs(diff) > 0.1) {
        const sign = diff > 0 ? '+' : '';
        const formattedDiff = key === 'money' ? `${sign}$${Math.round(diff).toLocaleString()}` : `${sign}${diff.toFixed(1)}`;
        const isPositive = (key === 'stress') ? diff < 0 : diff > 0;
        deltaEl.textContent = `${isPositive ? '▲' : '▼'} ${formattedDiff}`;
        deltaEl.className = `stat-delta ${isPositive ? 'positive' : 'negative'}`;
      } else {
        deltaEl.textContent = '';
        deltaEl.className = 'stat-delta';
      }
    }

    // Flash animation on significant change
    if (currentStats[key] !== undefined) {
      const diff = val - currentStats[key];
      if (Math.abs(diff) > 1) {
        const type = (key === 'stress' ? diff < 0 : diff > 0) ? 'positive' : 'negative';
        card.classList.remove('flash-positive', 'flash-negative');
        void card.offsetWidth;
        card.classList.add('flash-' + type);
      }
    }

    prevStats[key] = currentStats[key] ?? val;
    currentStats[key] = val;
  }

  // Update sidebar info
  $('infoStep').textContent = stepCount;
  $('infoAge').textContent = (state.age || (20 + stepCount * 0.5)).toFixed(1) + ' yrs';
  $('infoWeek').textContent = stepCount;
}

// ═══════════════════════════════════════════════════════════════════════════════
// BADGES
// ═══════════════════════════════════════════════════════════════════════════════
function evaluateBadges(s) {
  let changed = false;
  if (s.money >= 50000 && !badges.wealth) { badges.wealth = true; changed = true; showToast('🏆 Achievement!', '💎 Wealth Builder unlocked!', 'var(--accent-1)'); }
  if (s.stress <= 10 && (s.happiness || 0) > 80 && !badges.zen) { badges.zen = true; changed = true; showToast('🏆 Achievement!', '🧘 Zen Master unlocked!', 'var(--accent-1)'); }
  if (s.career > 85 && !badges.hustle) { badges.hustle = true; changed = true; showToast('🏆 Achievement!', '🔥 Hustler unlocked!', 'var(--accent-1)'); }
  if (s.stress >= 90 && s.health > 10 && !badges.survivor) { badges.survivor = true; changed = true; showToast('🏆 Achievement!', '🩸 Survivor unlocked!', 'var(--accent-1)'); }
  if (changed) {
    localStorage.setItem('lifeos-badges', JSON.stringify(badges));
    renderProfileStats();
  }
}

function renderProfileStats() {
  $('statRuns').textContent = lifetimeStats.runs;
  $('statPeak').textContent = lifetimeStats.peak.toFixed(2);
  $('statCap').textContent = `$${(lifetimeStats.capital / 1000).toFixed(1)}k`;
  $('statSteps').textContent = lifetimeStats.steps;
  if (badges.wealth) $('badge-wealth').classList.add('unlocked');
  if (badges.zen) $('badge-zen').classList.add('unlocked');
  if (badges.hustle) $('badge-hustle').classList.add('unlocked');
  if (badges.survivor) $('badge-survivor').classList.add('unlocked');
}
renderProfileStats();

// ═══════════════════════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════════════════════
function showToast(title, msg, color = "var(--accent-1)") {
  const t = document.createElement('div');
  t.className = 'toast';
  t.style.borderLeftColor = color;
  t.innerHTML = `<strong style="color:${color};display:block;margin-bottom:3px;font-family:var(--font-heading);letter-spacing:1.5px;text-transform:uppercase;font-size:0.6rem">${title}</strong><span style="color:var(--text-secondary)">${msg}</span>`;
  $('toastContainer').appendChild(t);
  setTimeout(() => t.remove(), 4200);
}

// ═══════════════════════════════════════════════════════════════════════════════
// TERMINAL
// ═══════════════════════════════════════════════════════════════════════════════
function logTerminal(msg) {
  terminal.innerHTML += `<div class="terminal-line">> ${msg}</div>`;
  if (terminal.childElementCount > 50) terminal.firstElementChild.remove();
  terminal.scrollTop = terminal.scrollHeight;
}

// ═══════════════════════════════════════════════════════════════════════════════
// LOG ENTRIES
// ═══════════════════════════════════════════════════════════════════════════════
function addEventLog(step, text) {
  const list = $('eventsLog');
  if (list.querySelector('.log-empty')) list.innerHTML = '';
  list.innerHTML += `<div class="log-entry"><span class="log-step">#${step}</span><span class="log-icon">⚡</span><span class="log-text">${text}</span></div>`;
  list.scrollTop = list.scrollHeight;
}
function addDecisionLog(step, action, reasoning) {
  const list = $('decisionsLog');
  if (list.querySelector('.log-empty')) list.innerHTML = '';
  list.innerHTML += `<div class="log-entry"><span class="log-step">#${step}</span><span class="log-icon">🧠</span><span class="log-text"><strong>${action.toUpperCase()}</strong> — ${reasoning}</span></div>`;
  list.scrollTop = list.scrollHeight;
}

// ═══════════════════════════════════════════════════════════════════════════════
// API CALLS
// ═══════════════════════════════════════════════════════════════════════════════
async function initEnv() {
  const task = $('cfgTask').value;
  const personality = $('cfgPersonality').value;
  const seed = +$('cfgSeed').value;
  maxSteps = +$('cfgMaxSteps').value;

  await fetch('/reset', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task, personality, seed }) });
  const resFull = await fetch('/state_full', { method: 'POST' });
  const st = await resFull.json();

  stepCount = 0; isDone = false; isInitialized = true;
  currentStats = {}; prevStats = {}; rewardHistory = [];

  // Clear charts
  timelineChart.data.labels = [];
  timelineChart.data.datasets.forEach(d => d.data = []);
  timelineChart.update('none');
  rewardsChart.data.labels = [];
  rewardsChart.data.datasets[0].data = [];
  rewardsChart.update('none');

  // Clear logs
  $('eventsLog').innerHTML = '<div class="log-empty">No events triggered yet.</div>';
  $('decisionsLog').innerHTML = '<div class="log-empty">No AI decisions yet.</div>';

  // Reset score ring
  setScoreRing(0);
  $('scoreValue').textContent = '0.00';

  renderStats(st);
  pushHistory(st);

  $('navStatusText').textContent = 'Running';
  $('infoStatus').textContent = 'Active';
  $('infoStatus').style.color = 'var(--success)';
  $('welcomeOverlay').classList.add('hidden');

  logTerminal(`<span style="color:var(--accent-1)">[SYS] Environment initialized — Task: ${task.toUpperCase()}, Personality: ${personality}</span>`);
  showToast('🚀 Initialized', `Task: ${task} | Personality: ${personality}`, 'var(--accent-1)');
  document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
}

async function takeAction(action) {
  if (isDone || !isInitialized) return;
  if (stepCount >= maxSteps) { isDone = true; endSimulation('max_steps'); return; }

  const res = await fetch('/step', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) });
  const data = await res.json();
  const st = data.info.full_state;
  stepCount++;
  lifetimeStats.steps++;

  const moneyEarned = st.money - (currentStats.money || st.money);
  if (moneyEarned > 0) lifetimeStats.capital += moneyEarned;
  localStorage.setItem('lifeos-stats', JSON.stringify(lifetimeStats));

  renderStats(st);
  pushHistory(st, data.reward);
  evaluateBadges(st);

  // Update score
  $('scoreValue').textContent = data.reward.toFixed(2);
  setScoreRing(data.reward);

  const am = ACTION_MSGS[action];
  if (am) showToast(am.t, am.m, am.c);

  if (data.info.event_description) {
    showToast('⚠️ ANOMALY', data.info.event_description, 'var(--warning)');
    addEventLog(stepCount, data.info.event_description);
    logTerminal(`<span style="color:var(--warning)">[EVENT] ${data.info.event_description}</span>`);
  }

  if (data.done) { isDone = true; endSimulation(data.info.termination_reason); }
}

function endSimulation(reason) {
  logTerminal(`<span style="color:var(--danger)">[FATAL] TERMINATED: ${reason}</span>`);
  showToast('💀 Simulation Over', `Reason: ${reason}`, 'var(--danger)');
  $('infoStatus').textContent = 'Ended';
  $('infoStatus').style.color = 'var(--danger)';
  $('navStatusText').textContent = 'Terminated';
  document.querySelectorAll('.action-btn').forEach(b => b.disabled = true);
  if (autoPilotInterval) toggleAutoPilot();
  lifetimeStats.runs++;
  lifetimeStats.peak = Math.max(lifetimeStats.peak, parseFloat($('scoreValue').textContent) || 0);
  localStorage.setItem('lifeos-stats', JSON.stringify(lifetimeStats));
}

// ═══════════════════════════════════════════════════════════════════════════════
// AUTO PILOT
// ═══════════════════════════════════════════════════════════════════════════════
async function runAutoPilotStep() {
  if (isDone || !isInitialized) { if (autoPilotInterval) toggleAutoPilot(); return; }
  const stRes = await fetch('/state_full', { method: 'POST' });
  const st = await stRes.json();
  const aiRes = await fetch('/auto_step', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ state: st }) });
  const ai = await aiRes.json();

  logTerminal(`<span style="color:var(--accent-3)">[AI]</span> ${ai.reasoning}`);
  logTerminal(`<span style="color:var(--text-primary)">[SYS]</span> Executing: <span style="color:var(--accent-1);font-weight:700">${ai.action.toUpperCase()}</span>`);
  addDecisionLog(stepCount + 1, ai.action, ai.reasoning);

  const btn = document.querySelector(`[data-action="${ai.action}"]`);
  if (btn) {
    btn.classList.add('flash-positive');
    setTimeout(() => btn.classList.remove('flash-positive'), 500);
  }
  await takeAction(ai.action);
}

function toggleAutoPilot() {
  const btn = $('btnAutoExec');
  if (autoPilotInterval) {
    clearInterval(autoPilotInterval);
    autoPilotInterval = null;
    btn.textContent = '🤖 Auto-Run';
    btn.classList.remove('active');
    logTerminal("<span style='color:var(--warning)'>[SYS] Manual control restored.</span>");
    $('infoStatus').textContent = 'Active';
    $('infoStatus').style.color = 'var(--success)';
  } else {
    if (!isInitialized) { showToast('⚠️ Not Ready', 'Initialize first!', 'var(--warning)'); return; }
    const speed = parseFloat($('cfgSpeed').value) * 1000;
    logTerminal("<span style='color:var(--accent-1)'>[SYS] AUTONOMOUS MODE ENGAGED.</span>");
    btn.textContent = '⏹ Stop AI';
    btn.classList.add('active');
    $('infoStatus').textContent = 'Auto-AI';
    $('infoStatus').style.color = 'var(--warning)';
    runAutoPilotStep();
    autoPilotInterval = setInterval(runAutoPilotStep, speed);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CONTROLS
// ═══════════════════════════════════════════════════════════════════════════════
$('btnInit').onclick = initEnv;
$('welcomeStartBtn').onclick = () => {
  if ($('wcTask')) $('cfgTask').value = $('wcTask').value;
  if ($('wcPersonality')) $('cfgPersonality').value = $('wcPersonality').value;
  initEnv();
};
$('sidebarToggle').onclick = () => {
  const sidebar = document.querySelector('.sidebar');
  sidebar.classList.toggle('collapsed');
};
$('btnReset').onclick = () => { if (autoPilotInterval) toggleAutoPilot(); initEnv(); };
$('btnStepAI').onclick = () => {
  if (!isInitialized) { showToast('⚠️', 'Initialize first!', 'var(--warning)'); return; }
  runAutoPilotStep();
};
$('btnAutoExec').onclick = toggleAutoPilot;
$('cfgMode').onchange = function() {
  if (this.value === 'auto' && isInitialized) toggleAutoPilot();
  else if (this.value === 'manual' && autoPilotInterval) toggleAutoPilot();
};

// Manual action clicks
document.querySelectorAll('.action-btn').forEach(btn => {
  btn.onclick = () => {
    if (!autoPilotInterval && isInitialized) takeAction(btn.dataset.action);
  };
});

// ═══════════════════════════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS
// ═══════════════════════════════════════════════════════════════════════════════
document.addEventListener('keydown', (e) => {
  // Don't trigger if user is typing in an input/select
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;

  switch (e.code) {
    case 'Space':
      e.preventDefault();
      if (isInitialized && !isDone) runAutoPilotStep();
      else if (!isInitialized) initEnv();
      break;
    case 'KeyA':
      e.preventDefault();
      if (isInitialized) toggleAutoPilot();
      break;
    case 'KeyR':
      e.preventDefault();
      if (autoPilotInterval) toggleAutoPilot();
      initEnv();
      break;
    case 'KeyI':
      e.preventDefault();
      initEnv();
      break;
    case 'Escape':
      $('profileOverlay').classList.remove('active');
      break;
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// INITIAL GAUGE RENDER (set initial values)
// ═══════════════════════════════════════════════════════════════════════════════
setGauge('health', 80);
setGauge('money', 5);
setGauge('stress', 20);
setGauge('career', 10);
setGauge('relationships', 50);
setGauge('happiness', 60);
