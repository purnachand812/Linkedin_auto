/**
 * app.js - Antigravity LinkedIn Editorial Hub Client
 * Handles live queue state management, real-time 5-check humanizer detection,
 * trend scouting, visual asset inspection, and toast notifications.
 */

// State
let queueData = { candidates: [] };
let trendsData = [];
let visualsData = [];
let historyData = [];
let currentFilter = 'ALL';
let currentEditingCandidateId = null;

// Slop & Detection Lexicon (mirrors slop.json)
const FORBIDDEN_WORDS = [
  "delve", "leverage", "game-changer", "revolutionary", "unlock", "landscape",
  "groundbreaking", "transformative", "paradigm shift", "unprecedented", "seamless",
  "cutting-edge", "robust", "crucial", "testament to", "beacon", "pivotal",
  "tapestry", "demystify", "spearhead", "foster", "synergy", "holistic",
  "empower", "disruptive", "game changer", "cutting edge", "state-of-the-art",
  "supercharge", "elevate", "unravel", "navigate", "realm", "beacon of",
  "reshaping", "reinventing", "spearheading", "harnessing", "reimagining"
];

const FORBIDDEN_PHRASES = [
  "in today's fast-paced world",
  "let that sink in",
  "here's the thing",
  "thrilled to announce",
  "excited to share",
  "the future is here",
  "ai is transforming",
  "in this rapidly evolving",
  "it goes without saying",
  "at the end of the day"
];

const FORBIDDEN_ENDINGS = [
  "thoughts?", "agree?", "what do you think?", "what are your thoughts?",
  "let me know in the comments", "do you agree?"
];

const DRY_REPLACEMENTS = {
  "delve": "investigate",
  "leverage": "use",
  "robust": "solid",
  "seamless": "smooth",
  "crucial": "important",
  "game-changer": "major update",
  "cutting-edge": "modern",
  "unprecedented": "rare",
  "landscape": "field",
  "supercharge": "speed up",
  "foster": "support"
};

// Global modal controls
window.openLinkedInModal = function() {
  const modal = document.getElementById('linkedin-modal');
  if (modal) {
    modal.classList.add('active');
  }
};

window.closeLinkedInModal = function() {
  const modal = document.getElementById('linkedin-modal');
  if (modal) {
    modal.classList.remove('active');
  }
};

// --- Initialization ---
function initApp() {
  initNavigation();
  initFilters();
  initStudioEvents();
  initModalEvents();
  initAutomationEvents();
  initJobEvents();
  loadAllData();
  checkLinkedInStatus();

  // Restore saved hub mode or default to postings
  const savedMode = localStorage.getItem('active_hub_mode') || 'postings';
  switchHubMode(savedMode);
  fetchAutoApplyStatus();

  // Polling for live daemon heartbeat & telemetry every 15s
  setInterval(() => {
    loadDaemonOnly();
    fetchAutoApplyStatus();
  }, 15000);

  if (window.location.search.includes('linkedin_connected=true')) {
    showToast('🎉 Official LinkedIn Account connected successfully! Ready for 1-click publishing.', 'success');
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
  }

  document.getElementById('btn-sync-queue')?.addEventListener('click', () => {
    loadAllData();
    checkLinkedInStatus();
    showToast('Queue & history synchronized with disk', 'success');
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// --- Hub Mode Switcher (Postings vs Autonomous Jobs) ---
let currentHubMode = 'postings';

function switchHubMode(mode) {
  currentHubMode = mode;
  try { localStorage.setItem('active_hub_mode', mode); } catch(e){}

  const btnPostings = document.getElementById('hub-mode-postings');
  const btnJobs = document.getElementById('hub-mode-jobs');

  if (mode === 'jobs') {
    btnPostings?.classList.remove('active');
    btnJobs?.classList.add('active', 'jobs-active');
    switchTab('jobs');
  } else {
    btnJobs?.classList.remove('active', 'jobs-active');
    btnPostings?.classList.add('active');

    // Switch to active postings sub-tab (or queue by default)
    const activeTab = document.querySelector('#nav-postings-group .nav-tab.active:not([data-tab="jobs"])')?.getAttribute('data-tab') || 'queue';
    switchTab(activeTab);
  }
}

// --- Autonomous Auto-Apply Handlers ---
async function fetchAutoApplyStatus() {
  try {
    const res = await fetch('/api/jobs/auto-apply/status').then(r => r.json());
    if (!res || !res.config) return;
    const cfg = res.config;
    const logs = res.logs || [];

    // Metrics
    const metricApplied = document.getElementById('metric-applied-today');
    if (metricApplied) metricApplied.textContent = `${cfg.applied_today || 0} / ${cfg.daily_limit || 5}`;

    const metricScore = document.getElementById('metric-min-score');
    if (metricScore) metricScore.textContent = `${cfg.min_match_score || 85}%`;

    // Indicators
    const statusText = document.getElementById('auto-apply-status-text');
    const badgeInd = document.getElementById('auto-apply-badge-indicator');
    const dotInd = document.getElementById('auto-apply-dot');
    const toggleBtnText = document.getElementById('btn-toggle-auto-apply-text');
    const hubBadgeText = document.getElementById('badge-jobs-text');

    if (cfg.enabled) {
      if (statusText) statusText.textContent = 'AUTONOMOUS 24/7 ACTIVE';
      if (badgeInd) badgeInd.className = 'auto-apply-pulse-badge';
      if (dotInd) dotInd.className = 'pulse-dot green';
      if (toggleBtnText) toggleBtnText.textContent = 'Pause Auto-Apply';
      if (hubBadgeText) hubBadgeText.textContent = `Auto-Apply 24/7 (${cfg.applied_today || 0} Applied)`;
    } else {
      if (statusText) statusText.textContent = 'AUTO-APPLY PAUSED';
      if (badgeInd) badgeInd.className = 'auto-apply-pulse-badge paused';
      if (dotInd) dotInd.className = 'pulse-dot amber';
      if (toggleBtnText) toggleBtnText.textContent = 'Resume Auto-Apply';
      if (hubBadgeText) hubBadgeText.textContent = 'Auto-Apply PAUSED';
    }

    // Render Logs Stream
    const consoleBody = document.getElementById('auto-apply-console-logs');
    if (consoleBody && logs.length > 0) {
      consoleBody.innerHTML = logs.map(l => `
        <div class="console-line ${l.level || 'INFO'}">
          <span class="ts">[${escapeHtml(l.timestamp)}]</span>
          <span class="msg">${escapeHtml(l.message)}</span>
        </div>
      `).join('');
      consoleBody.scrollTop = consoleBody.scrollHeight;
    }
  } catch (e) {
    console.error('Failed to fetch auto-apply status:', e);
  }
}

async function toggleAutoApply() {
  try {
    const res = await fetch('/api/jobs/auto-apply/toggle', { method: 'POST', body: '{}' }).then(r => r.json());
    if (res.success) {
      const state = res.config.enabled ? 'Enabled (Running 24/7)' : 'Paused';
      showToast(`Autonomous Job Agent ${state}`, res.config.enabled ? 'success' : 'info');
      fetchAutoApplyStatus();
    }
  } catch (e) {
    showToast(`Failed to toggle auto-apply: ${e.message}`, 'error');
  }
}

async function runAutoApplyNow() {
  const btn = document.getElementById('btn-run-auto-apply-now');
  if (btn) btn.disabled = true;
  showToast('⚡ Running autonomous job application batch...', 'info');

  try {
    const res = await fetch('/api/jobs/auto-apply/run-now', { method: 'POST', body: '{}' }).then(r => r.json());
    if (res.success) {
      const count = res.result ? res.result.applied_count : 0;
      showToast(`🎉 Autonomous batch completed! ${count} application(s) processed.`, 'success');
      loadAllData();
      fetchAutoApplyStatus();
    } else {
      showToast(res.error || 'Failed to run auto-apply batch', 'error');
    }
  } catch (e) {
    showToast(`Error running auto-apply: ${e.message}`, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// --- Tab Navigation ---
function initNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.getAttribute('data-tab') === tabId);
  });
  document.querySelectorAll('.tab-content').forEach(c => {
    c.classList.toggle('active', c.id === `tab-${tabId}`);
  });

  // Keep top switcher synchronized
  const btnPostings = document.getElementById('hub-mode-postings');
  const btnJobs = document.getElementById('hub-mode-jobs');
  if (tabId === 'jobs') {
    btnPostings?.classList.remove('active');
    btnJobs?.classList.add('active', 'jobs-active');
    currentHubMode = 'jobs';
    try { localStorage.setItem('active_hub_mode', 'jobs'); } catch(e){}
  } else {
    btnJobs?.classList.remove('active', 'jobs-active');
    btnPostings?.classList.add('active');
    currentHubMode = 'postings';
    try { localStorage.setItem('active_hub_mode', 'postings'); } catch(e){}
  }
}

// --- Filter Handling ---
function initFilters() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter');
      renderCandidates();
    });
  });
}

// --- Quick Daemon Status Fetcher ---
async function loadDaemonOnly() {
  try {
    const daemonRes = await fetch('/api/daemon/status').then(r => r.json()).catch(() => null);
    if (daemonRes) renderDaemonStatus(daemonRes);
  } catch (e) {}
}

// --- Data Fetching ---
async function loadAllData() {
  try {
    const [queueRes, trendsRes, historyRes, visualsRes, calendarRes, statusRes, daemonRes, analyticsRes, repliesRes, jobsRadarRes, jobsAppliedRes] = await Promise.all([
      fetch('/api/queue').then(r => r.json()).catch(() => null),
      fetch('/api/trends').then(r => r.json()).catch(() => null),
      fetch('/api/history').then(r => r.json()).catch(() => null),
      fetch('/api/visuals').then(r => r.json()).catch(() => null),
      fetch('/api/calendar').then(r => r.json()).catch(() => null),
      fetch('/api/status').then(r => r.json()).catch(() => null),
      fetch('/api/daemon/status').then(r => r.json()).catch(() => null),
      fetch('/api/analytics').then(r => r.json()).catch(() => null),
      fetch('/api/replies').then(r => r.json()).catch(() => null),
      fetch('/api/jobs/radar').then(r => r.json()).catch(() => null),
      fetch('/api/jobs/applied').then(r => r.json()).catch(() => null)
    ]);

    if (queueRes) {
      queueData = queueRes;
      updateQueueStats();
      renderCandidates();
    }

    if (trendsRes) {
      trendsData = trendsRes;
      renderTrends();
    }

    if (historyRes) {
      historyData = historyRes.topics || [];
      renderHistory();
      document.getElementById('tab-history-count').textContent = historyData.length;
    }

    if (visualsRes) {
      visualsData = visualsRes;
      renderVisuals();
      const vCount = document.getElementById('tab-visuals-count');
      if (vCount) vCount.textContent = visualsData.length;
    }

    if (calendarRes) {
      renderCalendar(calendarRes);
    }

    if (daemonRes) {
      renderDaemonStatus(daemonRes);
    }

    if (analyticsRes) {
      renderAnalytics(analyticsRes);
    }

    if (repliesRes) {
      renderReplies(repliesRes);
    }

    if (jobsRadarRes) {
      renderJobsData(jobsRadarRes, jobsAppliedRes || []);
    }

    if (statusRes && statusRes.counts) {
      document.getElementById('stat-approved').textContent = statusRes.counts.approved;
      document.getElementById('stat-waiting').textContent = statusRes.counts.waiting;
      document.getElementById('stat-published').textContent = statusRes.counts.published;
    }

  } catch (err) {
    console.error('Error loading dashboard data:', err);
  }
}

function updateQueueStats() {
  const candidates = queueData.candidates || [];
  const approved = candidates.filter(c => c.status === 'APPROVED').length;
  const waiting = candidates.filter(c => c.status === 'WAITING_FOR_APPROVAL').length;
  const published = candidates.filter(c => c.status === 'PUBLISHED').length;

  document.getElementById('count-all').textContent = candidates.length;
  document.getElementById('count-approved').textContent = approved;
  document.getElementById('count-waiting').textContent = waiting;
  document.getElementById('count-published').textContent = published;
  document.getElementById('tab-queue-count').textContent = candidates.length;

  document.getElementById('stat-approved').textContent = approved;
  document.getElementById('stat-waiting').textContent = waiting;
  document.getElementById('stat-published').textContent = published;
}

// --- Render Candidates Queue ---
function renderCandidates() {
  const container = document.getElementById('candidates-container');
  container.innerHTML = '';

  const candidates = queueData.candidates || [];
  const filtered = candidates.filter(c => {
    if (currentFilter === 'ALL') return true;
    return c.status === currentFilter;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 3rem;">
        <p style="color: var(--text-muted);">No candidates match the selected filter (<strong>${currentFilter}</strong>).</p>
      </div>
    `;
    return;
  }

  filtered.forEach(c => {
    const card = document.createElement('div');
    const statusClass = c.status === 'APPROVED' ? 'status-approved' : 
                        c.status === 'WAITING_FOR_APPROVAL' ? 'status-waiting' : 
                        c.status === 'PUBLISHED' ? 'status-published' : '';
    
    card.className = `candidate-card ${statusClass}`;
    card.id = `candidate-card-${c.id}`;

    // Status Badge
    let badgeHtml = '';
    if (c.status === 'APPROVED') {
      badgeHtml = `<span class="badge badge-emerald">APPROVED</span>`;
    } else if (c.status === 'WAITING_FOR_APPROVAL') {
      badgeHtml = `<span class="badge badge-amber">WAITING APPROVAL</span>`;
    } else if (c.status === 'PUBLISHED') {
      badgeHtml = `<span class="badge badge-cyan">PUBLISHED</span>`;
    } else {
      badgeHtml = `<span class="badge badge-purple">${c.status}</span>`;
    }

    // Visual markup
    let visualMarkup = `
      <div class="visual-thumbnail-panel">
        <span class="meta-label">VISUAL ASSET</span>
        <div class="visual-preview-frame" onclick="openVisualModal('${c.visual_url || ''}', '${escapeHtml(c.topic)}')">
          ${c.visual_url ? (
            c.visual_url.endsWith('.svg') 
              ? `<img src="${c.visual_url}" alt="${escapeHtml(c.topic)}" />` 
              : `<img src="${c.visual_url}" alt="${escapeHtml(c.topic)}" />`
          ) : `
            <div style="color: var(--text-dim); font-size: 0.75rem; text-align: center; padding: 1rem;">
              No visual generated<br>(Text-Only Format)
            </div>
          `}
          <div class="visual-expand-overlay">Click to Inspect &amp; Export</div>
        </div>
        <span class="visual-name">${c.visual || 'text-only (dwell-optimized)'}</span>
      </div>
    `;

    // Hook selector tabs
    let hookHtml = '';
    if (c.hooks && c.hooks.length > 0) {
      hookHtml = `
        <div class="hook-tabs-wrapper" style="margin-bottom: 0.5rem;">
          <span class="meta-label" style="display: block; margin-bottom: 0.25rem;">HOOK OPTIONS:</span>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            ${c.hooks.map((h, idx) => `
              <button class="btn btn-secondary btn-sm" onclick="applyHook(${c.id}, ${idx})" style="font-size: 0.72rem; padding: 0.2rem 0.5rem;">
                Hook ${idx + 1}
              </button>
            `).join('')}
          </div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="candidate-top-bar">
        <div class="candidate-id-title">
          <span class="candidate-num">CANDIDATE #${c.id}</span>
          ${badgeHtml}
          <h3 class="candidate-title">${escapeHtml(c.topic)}</h3>
        </div>
        <div class="candidate-state-controls" style="display: flex; gap: 0.35rem; align-items: center; flex-wrap: wrap;">
          <!-- 1-Click LinkedIn Publishing Buttons -->
          <button class="btn btn-primary btn-sm btn-publish-live" onclick="publishToLinkedIn(${c.id}, ${c.visual_exists ? 'true' : 'false'})" style="background: linear-gradient(135deg, #0A66C2, #004182); border-color: #0A66C2; font-weight: 700; display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.35rem 0.75rem;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
            ${c.visual_exists ? 'Publish with Canva Visual' : 'Publish Text-Only'}
          </button>

          ${c.visual_exists ? `
            <button class="btn btn-secondary btn-sm" onclick="publishToLinkedIn(${c.id}, false)" title="Post text-only with GitHub link at the end (no comment needed)" style="font-size: 0.72rem; padding: 0.35rem 0.6rem;">
              Text-Only (Link in Post)
            </button>
          ` : ''}

          ${c.linkedin_post_url ? `
            <a href="${c.linkedin_post_url}" target="_blank" class="btn btn-secondary btn-sm" style="color: #38BDF8; display: inline-flex; align-items: center; gap: 0.25rem;">
              View Live &nearr;
            </a>
          ` : ''}

          ${c.status !== 'APPROVED' ? `
            <button class="btn btn-secondary btn-sm" onclick="setCandidateStatus(${c.id}, 'APPROVED')" style="font-size: 0.72rem;">
              Mark Approved
            </button>
          ` : `
            <button class="btn btn-secondary btn-sm" onclick="setCandidateStatus(${c.id}, 'WAITING_FOR_APPROVAL')" style="font-size: 0.72rem;">
              Pause
            </button>
          `}
        </div>
      </div>

      <div class="candidate-meta-grid">
        <div class="meta-item">
          <span class="meta-label">Beat / Pillar</span>
          <span class="meta-value">${escapeHtml(c.beat || 'Open-Source AI')}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Score</span>
          <span class="meta-value"><strong>${c.score || 90}/100</strong> (Audited)</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">What It Replaces</span>
          <span class="meta-value"><strong>${escapeHtml(c.replaces || 'None specified')}</strong></span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Testing Claim</span>
          <span class="meta-value">${escapeHtml(c.test_status || 'Not tested')}</span>
        </div>
      </div>

      ${hookHtml}

      <div class="post-preview-container">
        <div class="post-body-panel">
          <div class="post-body-header">
            <span class="post-body-label">LINKEDIN POST COPY</span>
            <div style="display: flex; gap: 0.5rem;">
              <button class="btn btn-secondary btn-sm" onclick="copyPostText(${c.id})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                Copy Post
              </button>
            </div>
          </div>
          <div class="post-body-text" id="post-text-${c.id}">${escapeHtml(c.post_text || 'Draft content loading...')}</div>

          <div class="comment-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
              <span class="comment-box-label">FIRST COMMENT (PRIMARY SOURCES)</span>
              <button class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 0.15rem 0.4rem;" onclick="copyFirstComment(${c.id})">
                Copy Comment
              </button>
            </div>
            <div class="comment-box-text" id="comment-text-${c.id}">${escapeHtml(c.sources || 'Primary sources and documentation links...')}</div>
          </div>
        </div>

        ${visualMarkup}
      </div>

      <div class="candidate-actions-bar">
        <div class="action-buttons-group">
          <button class="btn btn-secondary btn-sm" onclick="editInStudio(${c.id})">
            Edit in Studio
          </button>
          <button class="btn btn-secondary btn-sm" onclick="auditCandidateQuality(${c.id})">
            Run Humanizer Audit
          </button>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-dim);">
          Cost: <strong>${escapeHtml(c.cost || 'Free Open Source')}</strong>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

// --- Action Handlers ---
async function setCandidateStatus(id, newStatus) {
  try {
    const res = await fetch('/api/candidate/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, status: newStatus })
    }).then(r => r.json());

    if (res.success) {
      showToast(`Candidate #${id} state updated to ${newStatus}`, 'success');
      loadAllData();
    } else {
      showToast(`Error updating status: ${res.error || 'Server error'}`, 'error');
    }
  } catch (err) {
    showToast('Failed to update status', 'error');
  }
}

function copyPostText(id) {
  const el = document.getElementById(`post-text-${id}`);
  if (el) {
    navigator.clipboard.writeText(el.innerText).then(() => {
      showToast(`Candidate #${id} post text copied to clipboard!`, 'success');
    });
  }
}

function copyFirstComment(id) {
  const el = document.getElementById(`comment-text-${id}`);
  if (el) {
    navigator.clipboard.writeText(el.innerText).then(() => {
      showToast(`Candidate #${id} First Comment copied to clipboard!`, 'success');
    });
  }
}

function editInStudio(id) {
  const c = (queueData.candidates || []).find(item => item.id === id);
  if (!c) return;

  currentEditingCandidateId = id;
  document.getElementById('studio-title').value = c.topic || '';
  document.getElementById('studio-beat').value = c.beat || 'Free & Open-Source AI Agent';
  document.getElementById('studio-replaces').value = c.replaces || '';
  document.getElementById('studio-testing').value = c.test_status || 'Not tested (Based on documentation)';
  document.getElementById('studio-post').value = c.post_text || '';
  document.getElementById('studio-comment').value = c.sources || '';

  switchTab('studio');
  runLiveAudit();
  showToast(`Loaded Candidate #${id} into Drafting Studio`, 'info');
}

function auditCandidateQuality(id) {
  const c = (queueData.candidates || []).find(item => item.id === id);
  if (!c) return;

  editInStudio(id);
  runLiveAudit();
}

function applyHook(candidateId, hookIndex) {
  const c = (queueData.candidates || []).find(item => item.id === candidateId);
  if (!c || !c.hooks || !c.hooks[hookIndex]) return;

  const rawHook = c.hooks[hookIndex];
  // Strip hook option label like "1. [Dry / Sarcastic - Selected]"
  const lines = rawHook.split('\n');
  const hookText = lines.slice(1).join('\n').trim();

  if (hookText) {
    const postEl = document.getElementById(`post-text-${candidateId}`);
    if (postEl) {
      const paragraphs = c.post_text.split('\n\n');
      paragraphs[0] = hookText;
      postEl.innerText = paragraphs.join('\n\n');
      showToast(`Applied Hook ${hookIndex + 1} to preview`, 'info');
    }
  }
}

// --- Render Trends ---
function renderTrends() {
  const container = document.getElementById('trends-container');
  container.innerHTML = '';

  trendsData.forEach(t => {
    const card = document.createElement('div');
    card.className = 'trend-card';
    card.innerHTML = `
      <div class="trend-header">
        <div>
          <span class="meta-label">${escapeHtml(t.beat)}</span>
          <h3 class="trend-title" style="margin-top: 0.25rem;">${escapeHtml(t.title)}</h3>
        </div>
        <span class="trend-score-badge">${t.score}/100</span>
      </div>

      <div class="trend-hook-quote">
        &ldquo;${escapeHtml(t.hook)}&rdquo;
      </div>

      <div class="trend-details">
        <p><strong>Why Now:</strong> ${escapeHtml(t.why_now)}</p>
        <p><strong>Replaces:</strong> ${escapeHtml(t.replaces)}</p>
        <p><strong>License / Activity:</strong> ${escapeHtml(t.license)} &middot; ${escapeHtml(t.stars)}</p>
      </div>

      <div class="trend-footer">
        <a href="${t.repo}" target="_blank" rel="noopener" class="btn btn-secondary btn-sm">
          GitHub Repo
        </a>
        <button class="btn btn-primary btn-sm" onclick="draftFromTrend('${escapeHtml(t.title)}', '${escapeHtml(t.beat)}', '${escapeHtml(t.hook)}', '${escapeHtml(t.replaces)}', '${t.repo}')">
          Draft This Topic
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

function draftFromTrend(title, beat, hook, replaces, repo) {
  document.getElementById('studio-title').value = title;
  document.getElementById('studio-beat').value = beat;
  document.getElementById('studio-replaces').value = replaces;
  document.getElementById('studio-testing').value = 'Not tested (Based on documentation)';
  
  const initialPost = `${hook}

The open-source repository ${repo.replace('https://github.com/', '')} provides...

In practice, the trade-off comes down to...

Don't give an experimental agent your production credentials. Sandbox it first.

I haven't tested this on a production setup yet, but for developers looking for open-source alternatives, it is worth inspecting.`;

  document.getElementById('studio-post').value = initialPost;
  document.getElementById('studio-comment').value = `Primary sources:
1. GitHub Repository: ${repo}
2. Documentation: ${repo}#readme`;

  currentEditingCandidateId = null;
  switchTab('studio');
  runLiveAudit();
  showToast(`Topic loaded into Drafting Studio!`, 'success');
}

// --- Render Visuals Gallery ---
function renderVisuals() {
  const container = document.getElementById('visuals-container');
  container.innerHTML = '';

  visualsData.forEach(v => {
    const card = document.createElement('div');
    card.className = 'visual-card';
    card.innerHTML = `
      <div class="visual-card-frame" onclick="openVisualModal('${v.url}', '${escapeHtml(v.name)}')">
        <img src="${v.url}" alt="${escapeHtml(v.name)}" />
      </div>
      <div class="visual-card-meta">
        <div class="visual-card-title" title="${escapeHtml(v.name)}">${escapeHtml(v.name)}</div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="badge badge-cyan">${v.type}</span>
          <span style="font-size: 0.72rem; color: var(--text-dim);">${Math.round(v.size_bytes / 1024)} KB</span>
        </div>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.25rem;">
          <a href="${v.url}" download="${v.name}" class="btn btn-secondary btn-sm flex-1">Download</a>
          <button class="btn btn-primary btn-sm" onclick="openVisualModal('${v.url}', '${escapeHtml(v.name)}')">Inspect</button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// --- Visual Modal ---
function openVisualModal(url, title) {
  if (!url) {
    showToast('No visual asset available for this post', 'info');
    return;
  }
  const modal = document.getElementById('visual-modal');
  const previewBox = document.getElementById('modal-visual-preview');
  const titleEl = document.getElementById('modal-visual-title');
  const downloadLink = document.getElementById('modal-visual-download');
  const copyBtn = document.getElementById('modal-copy-svg-code');

  titleEl.textContent = title;
  previewBox.innerHTML = `<img src="${url}" style="max-height: 520px; max-width: 100%; object-fit: contain;" />`;
  downloadLink.href = url;

  if (url.endsWith('.svg')) {
    copyBtn.style.display = 'inline-flex';
    copyBtn.onclick = async () => {
      try {
        const text = await fetch(url).then(r => r.text());
        navigator.clipboard.writeText(text);
        showToast('SVG markup copied to clipboard!', 'success');
      } catch (e) {
        showToast('Failed to copy SVG', 'error');
      }
    };
  } else {
    copyBtn.style.display = 'none';
  }

  modal.classList.add('active');
}

function initModalEvents() {
  document.getElementById('btn-close-visual-modal')?.addEventListener('click', () => {
    document.getElementById('visual-modal').classList.remove('active');
  });

  document.getElementById('visual-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'visual-modal') {
      document.getElementById('visual-modal').classList.remove('active');
    }
  });

  // LinkedIn Modal Events
  const linkedinModal = document.getElementById('linkedin-modal');
  document.getElementById('btn-linkedin-auth')?.addEventListener('click', () => {
    linkedinModal?.classList.add('active');
  });
  document.getElementById('btn-close-linkedin-modal')?.addEventListener('click', () => {
    linkedinModal?.classList.remove('active');
  });
  linkedinModal?.addEventListener('click', (e) => {
    if (e.target.id === 'linkedin-modal') {
      linkedinModal.classList.remove('active');
    }
  });

  // Copy redirect url button
  document.getElementById('btn-copy-redirect')?.addEventListener('click', () => {
    const input = document.getElementById('input-linkedin-redirect');
    if (input) {
      navigator.clipboard.writeText(input.value).then(() => {
        showToast('Redirect URI copied to clipboard!', 'success');
      });
    }
  });

  // Form submit for credentials
  document.getElementById('form-linkedin-creds')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const clientId = document.getElementById('input-linkedin-client-id').value.trim();
    const clientSecret = document.getElementById('input-linkedin-client-secret').value.trim();
    const redirectUri = document.getElementById('input-linkedin-redirect').value.trim();

    try {
      const res = await fetch('/api/linkedin/credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, redirect_uri: redirectUri })
      }).then(r => r.json());

      if (res.success) {
        showToast('Credentials saved! Click "Authorize Account" to complete OAuth.', 'success');
        checkLinkedInStatus();
      } else {
        showToast(res.error || 'Failed to save credentials', 'error');
      }
    } catch (err) {
      showToast('Error saving credentials', 'error');
    }
  });

  document.getElementById('btn-create-post-modal')?.addEventListener('click', () => {
    document.getElementById('studio-title').value = '';
    document.getElementById('studio-post').value = '';
    document.getElementById('studio-comment').value = '';
    currentEditingCandidateId = null;
    switchTab('studio');
  });
}

// --- Check Official LinkedIn Status ---
async function checkLinkedInStatus() {
  try {
    const res = await fetch('/api/linkedin/status').then(r => r.json());
    const btn = document.getElementById('btn-linkedin-auth');
    const textEl = document.getElementById('linkedin-status-text');
    const connectedView = document.getElementById('linkedin-modal-connected-view');
    const memberInfo = document.getElementById('linkedin-member-info');
    const authLink = document.getElementById('btn-authorize-linkedin');

    if (!btn || !textEl) return;

    if (res.connected) {
      btn.style.background = '#065F46';
      btn.style.borderColor = '#10B981';
      btn.style.color = '#ECFDF5';
      textEl.innerHTML = `● Connected (${res.days_left}d)`;
      if (connectedView) {
        connectedView.style.display = 'block';
        memberInfo.innerHTML = `Connected as <strong>${escapeHtml(res.member_name || 'Member')}</strong> (${res.member_urn || ''}) &bull; Active for ${res.days_left} more days.`;
      }
      if (authLink) {
        authLink.innerText = 'Re-Authorize Account';
      }
    } else if (res.configured) {
      btn.style.background = '#1E293B';
      btn.style.borderColor = '#38BDF8';
      btn.style.color = '#38BDF8';
      textEl.innerText = 'LinkedIn: Authorize';
      if (connectedView) connectedView.style.display = 'none';
      if (authLink) authLink.innerText = 'Authorize Account →';
    } else {
      btn.style.background = '';
      btn.style.borderColor = '';
      btn.style.color = '';
      textEl.innerText = 'LinkedIn: Setup API';
      if (connectedView) connectedView.style.display = 'none';
      if (authLink) authLink.innerText = 'Authorize Account →';
    }
  } catch (err) {
    console.error('LinkedIn status check error:', err);
  }
}

// --- Publish to Official LinkedIn ---
async function publishToLinkedIn(id, withImage = true) {
  const c = (queueData.candidates || []).find(item => item.id === id);
  const topic = c ? c.topic : `Candidate #${id}`;
  const modeLabel = withImage ? 'with Canva visual' : 'text-only (link in post)';

  showToast(`🚀 Sending "${escapeHtml(topic)}" to LinkedIn (${modeLabel})...`, 'info');

  try {
    const res = await fetch('/api/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id, with_image: withImage })
    }).then(r => r.json());

    if (res.success) {
      showToast(`🎉 Successfully published to your official LinkedIn profile!`, 'success');
      loadAllData();
      if (res.post_url) {
        showToast(`Live URL: <a href="${res.post_url}" target="_blank" style="color: #38BDF8; text-decoration: underline;">Open Post &nearr;</a>`, 'success');
        try {
          window.open(res.post_url, '_blank');
        } catch (e) {}
      }
    } else {
      showToast(`LinkedIn error: ${res.error || res.status || 'Publishing failed'}`, 'error');
      if (res.action_needed === 'connect_linkedin') {
        document.getElementById('linkedin-modal')?.classList.add('active');
      }
    }
  } catch (err) {
    showToast(`Publishing request failed: ${err.message}`, 'error');
  }
}
window.publishToLinkedIn = publishToLinkedIn;

// --- Render Editorial History ---
function renderHistory() {
  const tbody = document.getElementById('history-tbody');
  tbody.innerHTML = '';

  const searchVal = (document.getElementById('history-search').value || '').toLowerCase();

  const filtered = historyData.filter(item => {
    if (!searchVal) return true;
    return (item.title || '').toLowerCase().includes(searchVal) ||
           (item.category || '').toLowerCase().includes(searchVal) ||
           (item.angle || '').toLowerCase().includes(searchVal);
  });

  filtered.forEach(h => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-dim);">${h.date || '2026-10-10'}</td>
      <td><strong>${escapeHtml(h.title)}</strong></td>
      <td><span class="badge badge-purple">${escapeHtml(h.category)}</span></td>
      <td style="font-size: 0.8125rem; color: var(--text-muted);">${escapeHtml(h.angle || '')}</td>
      <td><span class="badge badge-cyan">${h.score || h.quality_score || 90}</span></td>
      <td>
        ${h.published 
          ? `<span class="badge badge-emerald">PUBLISHED</span>` 
          : `<span class="badge badge-amber">SCOUTED</span>`}
      </td>
      <td>
        <a href="${h.primary_source}" target="_blank" rel="noopener" style="color: var(--accent-cyan); text-decoration: none;">
          Source &rarr;
        </a>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

document.getElementById('history-search').addEventListener('input', renderHistory);

// --- Render 7-Day Plan ---
function renderCalendar(calendar) {
  const container = document.getElementById('calendar-container');
  container.innerHTML = '';

  calendar.forEach(item => {
    const card = document.createElement('div');
    card.className = 'calendar-day-card';
    card.innerHTML = `
      <div class="calendar-day-header">
        <span class="day-name">${item.day}</span>
        <span class="badge ${item.status === 'APPROVED' ? 'badge-emerald' : 'badge-amber'}">${item.status}</span>
      </div>
      <span class="calendar-pillar">${item.pillar}</span>
      <div class="calendar-topic">${escapeHtml(item.topic)}</div>
      <div style="margin-top: auto; font-size: 0.72rem; color: var(--text-dim);">
        Format: <strong>${item.format}</strong>
      </div>
    `;
    container.appendChild(card);
  });
}

// --- Live Studio & Humanizer ---
function initStudioEvents() {
  const postArea = document.getElementById('studio-post');
  postArea.addEventListener('input', () => {
    updateWordMetrics();
    runLiveAudit();
  });

  document.getElementById('btn-run-detect').addEventListener('click', runLiveAudit);

  document.getElementById('btn-clean-humanize').addEventListener('click', async () => {
    const text = postArea.value;
    try {
      const res = await fetch('/api/humanize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      }).then(r => r.json());

      if (res.cleaned_text) {
        postArea.value = res.cleaned_text;
        updateWordMetrics();
        runLiveAudit();
        showToast('Text cleaned: em dashes removed, slop words replaced!', 'success');
      }
    } catch (err) {
      // Fallback to client humanize
      let out = text.replace(/—/g, ', ').replace(/–/g, '-');
      out = out.replace(/[“”]/g, '"').replace(/[‘’]/g, "'");
      for (const [w, repl] of Object.entries(DRY_REPLACEMENTS)) {
        const re = new RegExp(`\\b${w}\\b`, 'gi');
        out = out.replace(re, repl);
      }
      postArea.value = out;
      updateWordMetrics();
      runLiveAudit();
      showToast('Text cleaned locally', 'success');
    }
  });

  document.getElementById('btn-save-as-candidate').addEventListener('click', async () => {
    const post_text = postArea.value;
    if (!post_text.trim()) {
      showToast('Post content is empty!', 'error');
      return;
    }

    if (currentEditingCandidateId) {
      const res = await fetch('/api/candidate/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: currentEditingCandidateId, post_text })
      }).then(r => r.json());

      if (res.success) {
        showToast(`Candidate #${currentEditingCandidateId} saved!`, 'success');
        loadAllData();
        switchTab('queue');
      }
    } else {
      showToast('New candidate drafted and saved!', 'success');
      switchTab('queue');
    }
  });

  document.getElementById('btn-studio-publish')?.addEventListener('click', () => {
    const post_text = postArea.value.trim();
    if (!post_text) {
      showToast('Draft content is empty!', 'error');
      return;
    }
    const candId = currentEditingCandidateId || 8;
    publishToLinkedIn(candId, false);
  });
}

function updateWordMetrics() {
  const text = document.getElementById('studio-post').value;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const chars = text.length;
  const readSeconds = Math.round(words / 3.5);

  document.getElementById('post-metrics').textContent = `${words} words | ${chars} chars | ~${readSeconds}s read`;
}

async function runLiveAudit() {
  const text = document.getElementById('studio-post').value;
  if (!text.trim()) return;

  try {
    const res = await fetch('/api/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    }).then(r => r.json());

    updateDetectionPanel(res);
  } catch (e) {
    // Client-side fallback computation
    const fallback = clientSideEvaluate(text);
    updateDetectionPanel(fallback);
  }
}

function updateDetectionPanel(res) {
  document.getElementById('overall-score-val').textContent = res.final_score;
  const circle = document.getElementById('overall-score-circle');
  const verdictTag = document.getElementById('overall-verdict-tag');
  const verdictDesc = document.getElementById('overall-verdict-desc');

  if (res.final_score >= 80) {
    circle.style.borderColor = 'var(--accent-emerald)';
    verdictTag.className = 'verdict-tag pass';
    verdictTag.textContent = 'PASS (Ready to Post)';
    verdictDesc.textContent = 'Meets voice standards: zero slop, varied rhythm, grounded claims.';
  } else {
    circle.style.borderColor = 'var(--accent-amber)';
    verdictTag.className = 'verdict-tag review';
    verdictTag.textContent = 'REVIEW NEEDED';
    verdictDesc.textContent = 'Address highlighted flags (em dashes, slop words, or missing sandboxing warnings).';
  }

  // 1. Burstiness
  document.getElementById('score-burstiness').textContent = `${res.burstiness}/100`;
  document.getElementById('bar-burstiness').style.width = `${res.burstiness}%`;

  // 2. Specificity
  document.getElementById('score-specificity').textContent = `${res.specificity}/100`;
  document.getElementById('bar-specificity').style.width = `${res.specificity}%`;

  // 3. Slop
  document.getElementById('score-slop').textContent = `${res.slop_score}/100`;
  document.getElementById('bar-slop').style.width = `${res.slop_score}%`;
  const slopBox = document.getElementById('slop-detected-box');
  slopBox.innerHTML = '';
  if (res.detected_slop && res.detected_slop.length > 0) {
    res.detected_slop.forEach(item => {
      const p = document.createElement('span');
      p.className = 'flag-pill';
      p.textContent = item;
      slopBox.appendChild(p);
    });
  }

  // 4. Fingerprint
  document.getElementById('score-fingerprint').textContent = `${res.fingerprint}/100`;
  document.getElementById('bar-fingerprint').style.width = `${res.fingerprint}%`;
  const fpBox = document.getElementById('fingerprint-issues-box');
  fpBox.innerHTML = '';
  if (res.fingerprint_issues && res.fingerprint_issues.length > 0) {
    res.fingerprint_issues.forEach(item => {
      const p = document.createElement('span');
      p.className = 'flag-pill';
      p.textContent = item;
      fpBox.appendChild(p);
    });
  }

  // 5. Voice & Tells
  document.getElementById('score-voice').textContent = `${res.voice_score}/100`;
  document.getElementById('bar-voice').style.width = `${res.voice_score}%`;
  const voiceBox = document.getElementById('voice-issues-box');
  voiceBox.innerHTML = '';
  if (res.voice_issues && res.voice_issues.length > 0) {
    res.voice_issues.forEach(item => {
      const p = document.createElement('span');
      p.className = 'flag-pill';
      p.textContent = item;
      voiceBox.appendChild(p);
    });
  }
}

// Client-side fallback detection mirroring detect.py
function clientSideEvaluate(text) {
  const words = text.split(/\s+/).filter(Boolean);
  const sentences = text.split(/[.!?\n]+/).map(s => s.trim()).filter(Boolean);

  // Burstiness
  let burstiness = 50.0;
  if (sentences.length > 1) {
    const lengths = sentences.map(s => s.split(/\s+/).length);
    const mean = lengths.reduce((a, b) => a + b, 0) / lengths.length;
    const variance = lengths.reduce((sum, l) => sum + Math.pow(l - mean, 2), 0) / lengths.length;
    const stdDev = Math.sqrt(variance);
    const cv = mean > 0 ? stdDev / mean : 0;
    burstiness = Math.round(Math.min(100.0, cv * 120.0));
  }

  // Specificity
  const patterns = [
    /\d+(\.\d+)?k?/gi, /\$\d+|\€\d+/gi, 
    /\b(python|docker|gpu|vram|ram|api|mit|apache|llm|ollama|vllm|swe-bench|github|claude|gemini)\b/gi,
    /\b[a-zA-Z0-9_-]+\.(py|json|md|txt|ts|js)\b/gi, /%/g, /\b(tested|untested|benchmark|repo|commit)\b/gi
  ];
  let matches = 0;
  patterns.forEach(p => {
    const f = text.match(p);
    if (f) matches += f.length;
  });
  const density = words.length > 0 ? matches / words.length : 0;
  const specificity = Math.round(Math.min(100.0, density * 650.0));

  // Slop
  let slopCount = 0;
  let detected_slop = [];
  FORBIDDEN_WORDS.forEach(w => {
    const re = new RegExp(`\\b${w}\\b`, 'gi');
    const f = text.match(re);
    if (f) {
      slopCount += f.length;
      detected_slop.push(`Word: '${w}'`);
    }
  });
  const per100 = words.length > 0 ? (slopCount / words.length) * 100 : 0;
  const slop_score = Math.max(0, Math.round(100.0 - (per100 * 25.0)));

  // Fingerprint
  let fpPenalties = 0;
  let fpIssues = [];
  if (text.includes('—')) {
    const c = (text.match(/—/g) || []).length;
    fpPenalties += 30 * c;
    fpIssues.push(`${c} em-dash(es) ('—') detected`);
  }
  if (/[“”‘’]/.test(text)) {
    fpPenalties += 15;
    fpIssues.push('Curly quotes detected');
  }
  const fingerprint = Math.max(0, Math.round(100.0 - fpPenalties));

  // Voice & Security
  let voiceScore = 100.0;
  let voiceIssues = [];
  const lower = text.toLowerCase();
  if (/agent|terminal|code execution|browser automation/.test(lower)) {
    if (!/sandbox|credentials|security|production/.test(lower)) {
      voiceScore -= 25.0;
      voiceIssues.push("Missing required sandboxing warning ('Sandbox it first').");
    }
  }
  if (/repo|tool|model|release|python/.test(lower)) {
    if (!/tested|haven't run|based on|documentation/.test(lower)) {
      voiceScore -= 20.0;
      voiceIssues.push("Missing explicit tested vs untested declaration.");
    }
  }

  const checks = [burstiness, specificity, slop_score, fingerprint, voiceScore];
  const mean = checks.reduce((a, b) => a + b, 0) / checks.length;
  const min = Math.min(...checks);
  const final_score = Math.round((mean * 0.6) + (min * 0.4));

  return {
    final_score,
    burstiness,
    specificity,
    slop_score,
    slop_count: slopCount,
    detected_slop,
    fingerprint,
    fingerprint_issues: fpIssues,
    voice_score: Math.max(0, voiceScore),
    voice_issues: voiceIssues
  };
}

// --- Toast System ---
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span style="display: flex; align-items: center;">${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'all 200ms ease';
    setTimeout(() => toast.remove(), 200);
  }, 3500);
}

// Utility
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// --- 24/7 Daemon & EU Reach Handlers ---
function renderDaemonStatus(data) {
  if (!data) return;
  const timeEl = document.getElementById('daemon-time-cet');
  const nextEl = document.getElementById('daemon-next-drop');
  const appEl = document.getElementById('daemon-approved-count');
  const statusEl = document.getElementById('daemon-status-text');

  if (timeEl && data.current_time_cet) timeEl.textContent = data.current_time_cet.replace(' CET', '');
  if (nextEl && data.next_scheduled_drop) nextEl.textContent = data.next_scheduled_drop;
  if (appEl && data.approved_queue_count !== undefined) appEl.textContent = `${data.approved_queue_count} Posts`;
  if (statusEl) {
    if (data.is_eu_prime_time) {
      statusEl.textContent = `PRIME TIME ACTIVE • ${data.current_window || 'EU Prime'}`;
      statusEl.style.color = '#10B981';
    } else {
      statusEl.textContent = `MONITORING (24/7) • ${data.current_window || 'Off-Peak'}`;
      statusEl.style.color = '#38BDF8';
    }
  }
}

function renderAnalytics(data) {
  if (!data) return;
  const postsContainer = document.getElementById('monitored-posts-container');
  if (postsContainer && data.analytics && data.analytics.posts_analytics) {
    postsContainer.innerHTML = '';
    const posts = data.analytics.posts_analytics;
    if (posts.length === 0) {
      postsContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem; padding: 0.5rem;">No posts published yet.</p>';
    } else {
      posts.forEach(p => {
        const item = document.createElement('div');
        item.style.cssText = 'padding: 0.75rem; background: #0F172A; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #1E293B;';
        item.innerHTML = `
          <div>
            <div style="font-weight: 600; font-size: 0.85rem; color: #F8FAFC;">${escapeHtml(p.topic)}</div>
            <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 0.2rem;">
              Published: ${p.published_at.substring(0, 16).replace('T', ' ')} UTC &bull; ${p.age_hours}h ago
            </div>
          </div>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <span class="badge badge-emerald" style="font-size: 0.68rem;">LIVE</span>
            ${p.post_url ? `<a href="${p.post_url}" target="_blank" class="btn btn-secondary btn-sm" style="font-size: 0.72rem; color: #38BDF8; padding: 0.2rem 0.5rem;">Open &nearr;</a>` : ''}
          </div>
        `;
        postsContainer.appendChild(item);
      });
    }
  }

  // Render learnings if available
  const learningsList = document.getElementById('eu-learnings-list');
  if (learningsList && data.learnings && data.learnings.continuous_rules) {
    learningsList.innerHTML = data.learnings.continuous_rules.map(r => `<li>${escapeHtml(r)}</li>`).join('');
  }
}

function renderReplies(data) {
  const container = document.getElementById('pending-replies-container');
  if (!container) return;
  container.innerHTML = '';

  const replies = (data && data.pending) ? data.pending : [];
  if (replies.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.8rem; padding: 0.5rem;">No pending replies generated yet.</p>';
    return;
  }

  replies.forEach((r, idx) => {
    const card = document.createElement('div');
    card.style.cssText = 'padding: 0.75rem; background: #0B0F19; border-radius: 6px; border: 1px solid #1E293B;';
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
        <span style="font-size: 0.75rem; font-weight: 700; color: #38BDF8;">Candidate #${r.candidate_id} Scenario:</span>
        <span style="font-size: 0.7rem; color: var(--text-dim);">${escapeHtml(r.scenario)}</span>
      </div>
      <p style="font-size: 0.8125rem; color: #CBD5E1; margin-bottom: 0.5rem; line-height: 1.45;">"${escapeHtml(r.suggested_reply)}"</p>
      <div style="display: flex; justify-content: flex-end; gap: 0.5rem;">
        <button class="btn btn-secondary btn-sm" onclick="copyReplyText(${idx})" style="font-size: 0.7rem; padding: 0.2rem 0.5rem;">
          Copy Technical Reply
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

function copyReplyText(idx) {
  fetch('/api/replies').then(r => r.json()).then(data => {
    const replies = data.pending || [];
    if (replies[idx]) {
      navigator.clipboard.writeText(replies[idx].suggested_reply).then(() => {
        showToast('Technical discussion reply copied to clipboard!', 'success');
      });
    }
  });
}
window.copyReplyText = copyReplyText;

function initAutomationEvents() {
  document.getElementById('btn-daemon-run-now')?.addEventListener('click', async () => {
    showToast('Running 24/7 daemon cycle...', 'info');
    try {
      const res = await fetch('/api/daemon/cycle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_publish: false })
      }).then(r => r.json());
      if (res.success) {
        showToast(res.published ? '🎉 Candidate published during cycle!' : 'Cycle complete: monitoring & scheduling updated', 'success');
        loadAllData();
      } else {
        showToast(res.error || 'Cycle run failed', 'error');
      }
    } catch (e) {
      showToast(`Request failed: ${e.message}`, 'error');
    }
  });

  document.getElementById('btn-daemon-force-publish')?.addEventListener('click', async () => {
    if (!confirm('Force publish next approved post right now, bypassing prime-time schedule?')) return;
    showToast('Force publishing next approved candidate...', 'info');
    try {
      const res = await fetch('/api/daemon/cycle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_publish: true })
      }).then(r => r.json());
      if (res.success && res.published) {
        showToast('🎉 Candidate published immediately!', 'success');
        loadAllData();
      } else {
        showToast(res.error || 'No approved candidate ready or publish failed', 'error');
      }
    } catch (e) {
      showToast(`Request failed: ${e.message}`, 'error');
    }
  });
}

// ==========================================================================
// Job Opportunity Radar & ATS Application Studio Logic
// ==========================================================================
let jobsData = { jobs: [] };
let appliedJobsData = [];

function renderJobsData(radarRes, appliedRes) {
  jobsData = radarRes || { jobs: [] };
  appliedJobsData = appliedRes || [];
  
  const jobs = jobsData.jobs || [];
  const badge = document.getElementById('tab-jobs-badge');
  if (badge) badge.textContent = `${jobs.length} Opps`;
  const statCount = document.getElementById('radar-count-stat');
  if (statCount) statCount.textContent = jobs.length;
  const filterStatus = document.getElementById('jobs-filter-status');
  if (filterStatus) filterStatus.textContent = `Showing ${jobs.length} live Berlin opportunities (Easy Apply)`;

  renderJobsRadar(jobs, appliedJobsData);
  renderAppliedHistory(appliedJobsData);
}

function renderJobsRadar(jobs, appliedList) {
  const container = document.getElementById('jobs-container');
  if (!container) return;
  if (!jobs || jobs.length === 0) {
    container.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-dim);">No active opportunities found matching current filters.</div>';
    return;
  }

  const appliedIds = new Set(appliedList.map(a => a.job_id));

  container.innerHTML = '';
  jobs.forEach(job => {
    const isApplied = appliedIds.has(job.id) || job.status === 'APPLIED';
    const card = document.createElement('div');
    card.className = `job-card ${isApplied ? 'applied' : ''}`;
    
    const score = job.match_score || 85;
    const scoreClass = score >= 90 ? 'match-high' : 'match-mid';

    const techTags = (job.tech_stack || []).map(t => `<span class="job-tag primary">${escapeHtml(t)}</span>`).join('');
    const resumeUrl = job.resume_url || `/resumes/resume_${job.id}.html`;

    card.innerHTML = `
      <div class="job-header-row">
        <div>
          <div class="job-role-title">${escapeHtml(job.title)}</div>
          <div class="job-company-row">
            <strong style="color: #F8FAFC;">${escapeHtml(job.company)}</strong>
            <span>&bull;</span>
            <span>${escapeHtml(job.location)}</span>
            <span>&bull;</span>
            <span style="color: #10B981; font-weight: 600;">${escapeHtml(job.salary_range || 'Competitive')}</span>
          </div>
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.35rem;">
          <div class="job-match-badge ${scoreClass}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            ${score}/100 Match
          </div>
          <span style="font-size: 0.7rem; color: var(--text-dim);">${escapeHtml(job.posted_time || 'Recent')} &bull; ${job.applicants_count || 12} applicants</span>
        </div>
      </div>

      <div class="job-tags-row">
        ${techTags}
        ${job.easy_apply ? '<span class="job-tag" style="background: rgba(16, 185, 129, 0.1); color: #10B981; border-color: rgba(16, 185, 129, 0.3);">Easy Apply Supported</span>' : ''}
      </div>

      <p class="job-desc-snippet">${escapeHtml(job.description)}</p>

      ${job.tailored_cover_letter ? `
        <div style="margin: 0.75rem 0;">
          <div style="font-size: 0.75rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.25rem;">Tailored Grounded Pitch:</div>
          <p style="font-size: 0.8rem; color: #94A3B8; font-style: italic; background: #0B0F19; padding: 0.6rem; border-radius: 4px; border: 1px solid #1E293B;">
            "${escapeHtml(job.tailored_cover_letter)}"
          </p>
        </div>
      ` : ''}

      <div class="job-actions-row">
        ${isApplied ? `
          <span class="applied-badge-tag">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Application Tracked
          </span>
        ` : `
          <button class="btn btn-primary" onclick="applyToJob('${job.id}')" style="font-size: 0.85rem; padding: 0.5rem 1rem;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
            1-Click Apply &amp; Track
          </button>
        `}

        <button class="btn btn-secondary" onclick="openResumeModal('${resumeUrl}', '${escapeHtml(job.company)} - Tailored CV')" style="font-size: 0.85rem; padding: 0.5rem 0.85rem;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Tailored Resume
        </button>

        <button class="btn btn-secondary" onclick="openResumeModal('/resumes/cover_letter_${job.id}.html', '${escapeHtml(job.company)} - Tailored Cover Letter')" style="font-size: 0.85rem; padding: 0.5rem 0.85rem; border-color: rgba(16, 185, 129, 0.4);">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          Cover Letter
        </button>

        <button class="btn btn-secondary" onclick="copyRecruiterNote('${job.id}')" style="font-size: 0.85rem; padding: 0.5rem 0.85rem;" title="Copy non-slop recruiter message to clipboard">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          Outreach Note
        </button>

        <a href="${escapeHtml(job.job_url || '#')}" target="_blank" class="btn btn-primary" style="font-size: 0.82rem; padding: 0.45rem 0.85rem; margin-left: auto; background: #0077B5; border-color: #0A66C2; text-decoration: none; display: inline-flex; align-items: center; gap: 0.4rem;" title="Open real-time LinkedIn job posting with Easy Apply">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
          LinkedIn Easy Apply &rarr;
        </a>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderAppliedHistory(historyList) {
  const container = document.getElementById('applied-history-list');
  if (!container) return;

  if (!historyList || historyList.length === 0) {
    container.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-dim); text-align: center; padding: 1rem;">No applications submitted yet.</div>';
    return;
  }

  container.innerHTML = '';
  historyList.forEach(entry => {
    const item = document.createElement('div');
    item.style.cssText = 'padding: 0.6rem; background: #0B0F19; border-radius: 6px; border: 1px solid #1E293B; display: flex; flex-direction: column; gap: 0.35rem;';
    
    const timeStr = entry.applied_at ? new Date(entry.applied_at).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Recently';

    item.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <div style="font-weight: 700; color: #F8FAFC; font-size: 0.85rem;">${escapeHtml(entry.title)}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(entry.company)} &bull; ${escapeHtml(entry.location)}</div>
        </div>
        <span style="font-size: 0.75rem; font-weight: 700; color: #10B981; font-family: var(--font-mono);">${entry.match_score || 90}/100</span>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.25rem;">
        <span style="font-size: 0.7rem; color: var(--text-dim);">${timeStr}</span>
        <div style="display: flex; gap: 0.4rem;">
          ${entry.resume_url ? `<button class="btn btn-secondary btn-sm" onclick="openResumeModal('${escapeHtml(entry.resume_url)}', '${escapeHtml(entry.company)} - Resume')" style="font-size: 0.65rem; padding: 0.15rem 0.4rem; color: #38BDF8;">Resume</button>` : ''}
          <button class="btn btn-secondary btn-sm" onclick="openResumeModal('/resumes/cover_letter_${entry.job_id}.html', '${escapeHtml(entry.company)} - Cover Letter')" style="font-size: 0.65rem; padding: 0.15rem 0.4rem; color: #10B981;">Cover Letter</button>
          <button class="btn btn-secondary btn-sm" onclick="copyRecruiterNote('${entry.job_id}')" style="font-size: 0.65rem; padding: 0.15rem 0.4rem;">Note</button>
        </div>
      </div>
    `;
    container.appendChild(item);
  });
}

async function applyToJob(jobId) {
  showToast('Submitting application & tailoring ATS resume...', 'info');
  try {
    const res = await fetch('/api/jobs/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId })
    }).then(r => r.json());

    if (res.success) {
      showToast('🎉 Application recorded! ATS resume generated and recruiter outreach ready.', 'success');
      loadAllData();
    } else {
      showToast(res.error || 'Failed to submit application', 'error');
    }
  } catch (e) {
    showToast(`Application error: ${e.message}`, 'error');
  }
}

function copyRecruiterNote(jobId) {
  const job = (jobsData.jobs || []).find(j => j.id === jobId);
  const title = job ? job.title : 'AI Engineer';
  const company = job ? job.company : 'the team';
  const loc = job ? job.location : 'Berlin';

  const note = `Hi Hiring Team, I saw ${company}'s opening for ${title} in ${loc}. I am an MSc Data Science student based in Berlin researching hallucination attribution in multi-step LLM agent trajectories. I've also built typed dependency injection middlewares using Pydantic AI and FastAPI. I submitted an application and wanted to share my technical portfolio directly. Happy to connect.`;

  navigator.clipboard.writeText(note).then(() => {
    showToast('High-signal recruiter outreach note copied to clipboard!', 'success');
  });
}

function openResumeModal(resumeUrl, title) {
  const modal = document.getElementById('resume-modal');
  const iframe = document.getElementById('resume-iframe');
  const titleElem = document.getElementById('modal-resume-title');
  const newTabBtn = document.getElementById('modal-resume-newtab');
  const downloadBtn = document.getElementById('modal-resume-download');

  if (modal && iframe) {
    let cleanPath = (resumeUrl || '').trim();
    if (!cleanPath.startsWith('/') && !cleanPath.startsWith('http')) {
      cleanPath = '/resumes/' + cleanPath;
    }
    
    let viewUrl = cleanPath;
    let pdfUrl = cleanPath;
    if (cleanPath.endsWith('.pdf')) {
      viewUrl = cleanPath.slice(0, -4) + '.html';
    } else if (cleanPath.endsWith('.html')) {
      pdfUrl = cleanPath.slice(0, -5) + '.pdf';
    }

    iframe.src = viewUrl;
    if (titleElem) titleElem.textContent = `ATS Preview: ${title || 'Purnachandra Madhukar'}`;
    if (newTabBtn) newTabBtn.href = viewUrl;
    if (downloadBtn) {
      downloadBtn.href = pdfUrl;
      const cleanName = (title || 'Europass_CV_Purna').replace(/[^a-zA-Z0-9_-]/g, '_') + '.pdf';
      downloadBtn.setAttribute('download', cleanName);
    }
    modal.classList.add('active');
  }
}

function closeResumeModal() {
  const modal = document.getElementById('resume-modal');
  if (modal) modal.classList.remove('active');
}

function printResumeIframe() {
  const iframe = document.getElementById('resume-iframe');
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.focus();
    iframe.contentWindow.print();
  }
}

function focusJDScorer() {
  const tabBtn = document.querySelector('.nav-tab[data-tab="jobs"]');
  if (tabBtn) tabBtn.click();
  const textarea = document.getElementById('scorer-jd-text');
  if (textarea) {
    textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
    textarea.focus();
  }
}

async function handleScoreJD(e) {
  e.preventDefault();
  const roleTitle = document.getElementById('scorer-role-title')?.value.trim();
  const company = document.getElementById('scorer-company')?.value.trim();
  const location = document.getElementById('scorer-location')?.value.trim();
  const jdText = document.getElementById('scorer-jd-text')?.value.trim();

  if (!jdText) return;

  const btn = document.getElementById('btn-submit-score');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Evaluating 100-Point Match...';
  }

  try {
    const res = await fetch('/api/jobs/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role_title: roleTitle,
        company: company,
        location: location,
        jd_text: jdText
      })
    }).then(r => r.json());

    const resultBox = document.getElementById('scorer-result-container');
    if (resultBox && res.total_score !== undefined) {
      resultBox.style.display = 'block';
      const scoreClass = res.total_score >= 85 ? '#10B981' : '#06B6D4';
      const techPills = (res.matched_tech || []).map(t => `<span class="job-tag primary">${escapeHtml(t)}</span>`).join(' ');

      resultBox.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <div>
            <span style="font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase;">Match Score</span>
            <div style="font-size: 1.5rem; font-weight: 800; color: ${scoreClass}; font-family: var(--font-mono);">${res.total_score}/100</div>
          </div>
          <span class="badge ${res.total_score >= 85 ? 'badge-emerald' : 'badge-cyan'}">${escapeHtml(res.recommendation)}</span>
        </div>

        <div class="ats-metric-grid">
          <div class="ats-metric-cell">
            <div class="label">Tech Stack Fit</div>
            <div class="value">${res.breakdown ? res.breakdown.tech_stack_fit : 0}/35</div>
          </div>
          <div class="ats-metric-cell">
            <div class="label">Seniority / Thesis</div>
            <div class="value">${res.breakdown ? res.breakdown.role_seniority_fit : 0}/25</div>
          </div>
          <div class="ats-metric-cell">
            <div class="label">EU Work Rights</div>
            <div class="value">${res.breakdown ? res.breakdown.location_work_rights : 0}/20</div>
          </div>
          <div class="ats-metric-cell">
            <div class="label">Urgency / Freshness</div>
            <div class="value">${res.breakdown ? res.breakdown.freshness_urgency : 0}/20</div>
          </div>
        </div>

        <div style="margin-top: 0.75rem;">
          <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.25rem;">Matched Technical Skills:</div>
          <div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">
            ${techPills || '<span style="color: var(--text-muted); font-size: 0.75rem;">General ML/Python</span>'}
          </div>
        </div>
      `;
      showToast(`Scoring Complete: ${res.total_score}/100 (${res.recommendation})`, 'success');
    }
  } catch (err) {
    showToast(`Scoring failed: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Analyze & Calculate Match Score';
    }
  }
}

function initJobEvents() {
  document.getElementById('btn-refresh-jobs')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-refresh-jobs');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite; margin-right: 6px;"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>Scraping Live LinkedIn...`;
    }
    showToast('Scraping fresh real-time LinkedIn jobs in Berlin (<= 4-7 days)...', 'info');
    try {
      const res = await fetch('/api/jobs/radar/refresh', { method: 'POST' }).then(r => r.json());
      if (res.success) {
        showToast(`🎉 Refreshed with ${res.count} live LinkedIn jobs!`, 'success');
        loadAllData();
      } else {
        showToast(res.error || 'Refresh failed', 'error');
      }
    } catch (e) {
      showToast(`Refresh error: ${e.message}`, 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = origHtml;
      }
    }
  });
}

// Window exports
window.openResumeModal = openResumeModal;
window.closeResumeModal = closeResumeModal;
window.printResumeIframe = printResumeIframe;
window.applyToJob = applyToJob;
window.copyRecruiterNote = copyRecruiterNote;
window.focusJDScorer = focusJDScorer;
window.handleScoreJD = handleScoreJD;
window.switchHubMode = switchHubMode;
window.toggleAutoApply = toggleAutoApply;
window.runAutoApplyNow = runAutoApplyNow;
window.fetchAutoApplyStatus = fetchAutoApplyStatus;
