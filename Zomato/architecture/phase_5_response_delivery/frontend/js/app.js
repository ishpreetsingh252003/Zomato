/* ============================================================
   Zomato AI — Phase 5 Frontend Logic
   Handles form, API calls, card rendering, state management
   ============================================================ */

'use strict';

// ── DOM refs ───────────────────────────────────────────────────
const form          = document.getElementById('pref-form');
const btnRecommend  = document.getElementById('btn-recommend');
const btnSample     = document.getElementById('btn-sample');
const btnRefresh    = document.getElementById('btn-refresh');
const budgetTabs    = document.querySelectorAll('.budget-tab');
const budgetInput   = document.getElementById('budget');
const ratingSlider  = document.getElementById('min-rating');
const ratingDisplay = document.getElementById('rating-display');

const emptyState    = document.getElementById('empty-state');
const skeletons     = document.getElementById('skeletons');
const errorBanner   = document.getElementById('error-banner');
const errorMsg      = document.getElementById('error-message');
const errorDismiss  = document.getElementById('error-dismiss');
const resultsContent= document.getElementById('results-content');
const resultsTitle  = document.getElementById('results-title');
const resultsSummary= document.getElementById('results-summary');
const sourceBadge   = document.getElementById('source-badge');
const cardsGrid     = document.getElementById('cards-grid');

// ── State ──────────────────────────────────────────────────────
let lastPreferences = null;

// ── Budget tab interactions ─────────────────────────────────────
budgetTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    budgetTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    budgetInput.value = tab.dataset.value;
  });
});

// ── Rating slider live update ──────────────────────────────────
ratingSlider.addEventListener('input', () => {
  const val = parseFloat(ratingSlider.value);
  ratingDisplay.textContent = val.toFixed(1);
  // Update gradient fill
  const pct = (val / 5) * 100;
  ratingSlider.style.background =
    `linear-gradient(to right, var(--red) 0%, var(--red) ${pct}%, var(--border) ${pct}%)`;
});

// ── Dismiss error ───────────────────────────────────────────────
errorDismiss.addEventListener('click', () => {
  errorBanner.hidden = true;
});

// ── Gather form values ─────────────────────────────────────────
function getPreferences() {
  const cuisinesRaw = document.getElementById('cuisines').value;
  const optsRaw     = document.getElementById('optional-prefs').value;
  return {
    location:             document.getElementById('location').value.trim(),
    budget:               budgetInput.value,
    cuisines:             cuisinesRaw.split(',').map(s => s.trim()).filter(Boolean),
    min_rating:           parseFloat(ratingSlider.value),
    optional_preferences: optsRaw.split(',').map(s => s.trim()).filter(Boolean),
    top_n:                parseInt(document.getElementById('top-n').value) || 5,
  };
}

// ── UI state machine ────────────────────────────────────────────
function setState(state) {
  emptyState.hidden    = state !== 'empty';
  skeletons.hidden     = state !== 'loading';
  resultsContent.hidden= state !== 'results';
  // Keep error visible across states if already shown
  if (state !== 'error') errorBanner.hidden = true;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorBanner.hidden   = false;
  // Scroll error into view
  errorBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── Stars renderer ──────────────────────────────────────────────
function renderStars(rating) {
  if (rating == null) return '<span style="color:var(--text-muted)">—</span>';
  const full  = Math.floor(rating);
  const half  = (rating - full) >= 0.25 && (rating - full) < 0.75;
  const empty = 5 - full - (half ? 1 : 0);
  let html = '<div class="stars">';
  for (let i = 0; i < full;  i++) html += '<span class="star filled">★</span>';
  if (half)                        html += '<span class="star half">★</span>';
  for (let i = 0; i < empty; i++) html += '<span class="star">★</span>';
  html += '</div>';
  return html;
}

// ── Format cost ────────────────────────────────────────────────
function formatCost(cost) {
  if (cost == null) return '—';
  return `₹${Number(cost).toLocaleString('en-IN')}`;
}

// ── Render a single card ───────────────────────────────────────
function renderCard(rec, delay) {
  const rankClass = rec.rank === 1 ? 'rank-1' : rec.rank === 2 ? 'rank-2' : '';
  const card = document.createElement('article');
  card.className = 'rec-card';
  card.style.animationDelay = `${delay}ms`;
  card.setAttribute('aria-label', `Recommendation ${rec.rank}: ${rec.restaurant_name}`);

  card.innerHTML = `
    <div class="card-rank ${rankClass}">#${rec.rank}</div>
    <h3 class="card-name">${escHtml(rec.restaurant_name)}</h3>
    <p class="card-cuisine">${escHtml(rec.cuisine || '')}</p>

    <div class="card-stats">
      <div class="stat">
        <span class="stat-icon">⭐</span>
        <div>
          ${renderStars(rec.rating)}
          <span class="stat-label">${rec.rating != null ? rec.rating.toFixed(1) : '—'}</span>
        </div>
      </div>
      <div class="stat">
        <span class="stat-icon">💸</span>
        <div>
          <span class="stat-value">${formatCost(rec.cost_for_two)}</span>
          <span class="stat-label"> for 2</span>
        </div>
      </div>
    </div>

    <div class="card-divider"></div>

    <div class="card-explanation-label">
      <span>🤖</span> Why recommended
    </div>
    <p class="card-explanation">${escHtml(rec.explanation || '')}</p>
  `;
  return card;
}

// ── Escape HTML ────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Render full results ────────────────────────────────────────
function renderResults(data) {
  // Summary
  resultsTitle.textContent   = `Top ${data.recommendations.length} Recommendations`;
  resultsSummary.textContent = data.summary || '';

  // Source badge
  const src = data.source || 'live';
  sourceBadge.textContent = src === 'live' ? '● Live AI' : src === 'sample' ? '◆ Sample' : '▲ Ranked';
  sourceBadge.className   = 'source-badge ' + (src === 'live' ? 'live' : src === 'sample' ? 'sample' : 'phase3');

  // Cards
  cardsGrid.innerHTML = '';
  data.recommendations.forEach((rec, i) => {
    cardsGrid.appendChild(renderCard(rec, i * 80));
  });

  setState('results');
}

// ── Fetch from API ─────────────────────────────────────────────
async function fetchRecommendations(prefs) {
  setState('loading');
  btnRecommend.disabled = true;
  btnRecommend.querySelector('.btn-text').textContent = 'Finding restaurants…';

  try {
    const res = await fetch('/api/recommend', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(prefs),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || `Server error ${res.status}`);
    }
    renderResults(data);
  } catch (err) {
    setState('empty');
    showError(err.message || 'Failed to connect to the API.');
  } finally {
    btnRecommend.disabled = false;
    btnRecommend.querySelector('.btn-text').textContent = 'Get Recommendations';
  }
}

// ── Fetch sample data ──────────────────────────────────────────
async function fetchSample() {
  setState('loading');
  btnSample.disabled = true;
  try {
    const res  = await fetch('/api/sample');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Sample fetch failed');
    renderResults(data);
  } catch (err) {
    setState('empty');
    showError(err.message);
  } finally {
    btnSample.disabled = false;
  }
}

// ── Form submit ────────────────────────────────────────────────
form.addEventListener('submit', async e => {
  e.preventDefault();
  const prefs = getPreferences();

  if (!prefs.location) {
    showError('Please enter a location.');
    return;
  }

  lastPreferences = prefs;
  await fetchRecommendations(prefs);
});

// ── Sample button ──────────────────────────────────────────────
btnSample.addEventListener('click', fetchSample);

// ── Refresh button ─────────────────────────────────────────────
btnRefresh.addEventListener('click', async () => {
  const prefs = lastPreferences || getPreferences();
  lastPreferences = prefs;
  await fetchRecommendations(prefs);
});
