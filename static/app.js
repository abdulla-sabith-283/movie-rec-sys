const API = '';
let currentUser = null;
let currentPage = 1;
let currentFilters = {};
let currentMood = null;
let ratingMovieId = null;
let selectedStar = 0;
let searchTimer = null;

// ── AUTH ──────────────────────────────────────────────────────────────────────
function getToken() { return localStorage.getItem('token'); }
function setToken(t) { localStorage.setItem('token', t); }
function clearToken() { localStorage.removeItem('token'); }

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

async function loadCurrentUser() {
  if (!getToken()) return;
  const { ok, data } = await apiFetch('/api/auth/me');
  if (ok) {
    currentUser = data;
    document.getElementById('auth-buttons').style.display = 'none';
    document.getElementById('user-menu').style.display = 'flex';
    document.getElementById('user-name-display').textContent = data.name;
    if (data.is_admin) document.getElementById('admin-link').style.display = 'inline';
  } else {
    clearToken();
  }
}

async function doLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const err = document.getElementById('login-error');
  err.style.display = 'none';
  const { ok, data } = await apiFetch('/api/auth/login', {
    method: 'POST', body: JSON.stringify({ email, password })
  });
  if (ok) {
    setToken(data.token);
    currentUser = data.user;
    document.getElementById('auth-buttons').style.display = 'none';
    document.getElementById('user-menu').style.display = 'flex';
    document.getElementById('user-name-display').textContent = data.user.name;
    if (data.user.is_admin) document.getElementById('admin-link').style.display = 'inline';
    closeModals();
    showToast('Welcome back, ' + data.user.name + '!', 'success');
    loadMovies();
  } else {
    err.textContent = data.error || 'Login failed';
    err.style.display = 'block';
  }
}

async function doRegister(e) {
  e.preventDefault();
  const name = document.getElementById('reg-name').value;
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  const err = document.getElementById('reg-error');
  err.style.display = 'none';
  const { ok, data } = await apiFetch('/api/auth/register', {
    method: 'POST', body: JSON.stringify({ name, email, password })
  });
  if (ok) {
    setToken(data.token);
    currentUser = data.user;
    document.getElementById('auth-buttons').style.display = 'none';
    document.getElementById('user-menu').style.display = 'flex';
    document.getElementById('user-name-display').textContent = data.user.name;
    closeModals();
    showToast('Account created! Welcome, ' + data.user.name + '!', 'success');
    loadMovies();
  } else {
    err.textContent = data.error || 'Registration failed';
    err.style.display = 'block';
  }
}

function logout() {
  clearToken();
  currentUser = null;
  document.getElementById('auth-buttons').style.display = 'flex';
  document.getElementById('user-menu').style.display = 'none';
  document.getElementById('admin-link').style.display = 'none';
  showPage('home');
  showToast('Logged out successfully');
}

function requireAuth(page) {
  if (!currentUser) { showModal('login-modal'); return; }
  showPage(page);
}

// ── MODALS ────────────────────────────────────────────────────────────────────
function showModal(id) {
  document.getElementById('modal-backdrop').classList.add('visible');
  document.getElementById(id).classList.add('visible');
}
function closeModals() {
  document.getElementById('modal-backdrop').classList.remove('visible');
  document.querySelectorAll('.modal').forEach(m => m.classList.remove('visible'));
}
function switchModal(id) {
  document.querySelectorAll('.modal').forEach(m => m.classList.remove('visible'));
  document.getElementById(id).classList.add('visible');
}

// ── PAGES ─────────────────────────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById('page-' + name);
  if (page) page.classList.add('active');
  window.scrollTo(0, 0);

  if (name === 'home') loadMovies();
  if (name === 'recommendations') loadRecommendations(null);
  if (name === 'watchlist') loadWatchlist();
  if (name === 'history') loadHistory();
  if (name === 'admin') loadAdmin();
}

// ── TOAST ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = '') {
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 2500);
}

// ── MOVIES ────────────────────────────────────────────────────────────────────
async function loadGenres() {
  const { ok, data } = await apiFetch('/api/movies/genres');
  if (!ok) return;
  const sel = document.getElementById('filter-genre');
  data.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g; opt.textContent = g;
    sel.appendChild(opt);
  });
}

async function loadMovies(page = 1) {
  currentPage = page;
  const grid = document.getElementById('movies-grid');
  grid.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';

  const params = new URLSearchParams({ page, per_page: 12 });
  if (currentFilters.genre) params.set('genre', currentFilters.genre);
  if (currentFilters.language) params.set('language', currentFilters.language);
  if (currentFilters.year) params.set('year', currentFilters.year);
  if (currentFilters.sort) params.set('sort', currentFilters.sort);
  if (currentFilters.search) params.set('search', currentFilters.search);
  if (currentMood) params.set('mood', currentMood);

  const { ok, data } = await apiFetch('/api/movies/?' + params);
  if (!ok) { grid.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px">Failed to load movies</p>'; return; }

  if (data.movies.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🎬</div><h3>No movies found</h3><p>Try adjusting your filters</p></div>';
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  grid.innerHTML = '';
  data.movies.forEach(m => grid.appendChild(createMovieCard(m)));
  renderPagination(data.page, data.pages, loadMovies);
}

function createMovieCard(m, showRemove = false) {
  const card = document.createElement('div');
  card.className = 'movie-card';
  const posterHTML = m.poster_url
    ? `<img class="movie-poster" src="${m.poster_url}" alt="${escHtml(m.title)}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" loading="lazy"><div class="movie-poster-placeholder" style="display:none">🎬</div>`
    : `<div class="movie-poster-placeholder">🎬</div>`;

  const stars = m.tmdb_rating ? '★ ' + m.tmdb_rating.toFixed(1) : '';
  const watchlistBtn = currentUser
    ? m.in_watchlist
      ? `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();removeWatchlist(${m.id},this)">✓ Saved</button>`
      : `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();addWatchlist(${m.id},this)">+ Save</button>`
    : '';
  const rateBtn = currentUser
    ? `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openRateModal(${m.id},'${escHtml(m.title)}')">★ Rate</button>`
    : '';
  const removeBtn = showRemove
    ? `<button class="btn btn-danger btn-sm" onclick="event.stopPropagation();removeWatchlist(${m.id},null,true)">Remove</button>`
    : '';

  card.innerHTML = `
    ${posterHTML}
    <div class="movie-info">
      <div class="movie-title">${escHtml(m.title)}</div>
      <div class="movie-meta">${m.release_year || ''} ${m.language ? '· ' + m.language.toUpperCase() : ''}</div>
      ${stars ? `<div class="movie-rating">${stars}</div>` : ''}
      <div class="movie-genre">${escHtml(m.genre || '')}</div>
    </div>
    ${(watchlistBtn || rateBtn || removeBtn) ? `<div class="movie-card-actions">${watchlistBtn}${rateBtn}${removeBtn}</div>` : ''}
  `;
  card.addEventListener('click', () => showMovieDetail(m.id));
  return card;
}

function renderPagination(current, total, loadFn) {
  const pag = document.getElementById('pagination');
  if (!pag || total <= 1) { if (pag) pag.innerHTML = ''; return; }
  let html = '';
  if (current > 1) html += `<button class="page-btn" onclick="${loadFn.name}(${current - 1})">‹</button>`;
  for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) {
    html += `<button class="page-btn ${i === current ? 'active' : ''}" onclick="${loadFn.name}(${i})">${i}</button>`;
  }
  if (current < total) html += `<button class="page-btn" onclick="${loadFn.name}(${current + 1})">›</button>`;
  pag.innerHTML = html;
}

function applyFilters() {
  currentFilters.genre = document.getElementById('filter-genre').value;
  currentFilters.language = document.getElementById('filter-language').value;
  currentFilters.year = document.getElementById('filter-year').value;
  currentFilters.sort = document.getElementById('filter-sort').value;
  loadMovies(1);
}

function clearFilters() {
  currentFilters = {};
  currentMood = null;
  document.getElementById('filter-genre').value = '';
  document.getElementById('filter-language').value = '';
  document.getElementById('filter-year').value = '';
  document.getElementById('filter-sort').value = 'rating';
  document.getElementById('search-input').value = '';
  document.querySelectorAll('.mood-chip').forEach(c => c.classList.remove('active'));
  loadMovies(1);
}

function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(doSearch, 400);
}

function doSearch() {
  currentFilters.search = document.getElementById('search-input').value;
  loadMovies(1);
}

function setupMoodChips() {
  const moods = ['Happy', 'Thriller', 'Romantic', 'Sad', 'Action', 'Family', 'Horror', 'Comedy'];
  ['mood-chips', 'rec-mood-chips'].forEach((id, idx) => {
    const container = document.getElementById(id);
    if (!container) return;
    moods.forEach(mood => {
      const chip = document.createElement('button');
      chip.className = 'mood-chip';
      chip.textContent = mood;
      chip.onclick = () => {
        const isRec = id === 'rec-mood-chips';
        if (isRec) {
          document.querySelectorAll('#rec-mood-chips .mood-chip').forEach(c => c.classList.remove('active'));
          chip.classList.add('active');
          loadRecommendations(mood);
        } else {
          if (currentMood === mood) {
            currentMood = null;
            chip.classList.remove('active');
          } else {
            currentMood = mood;
            document.querySelectorAll('#mood-chips .mood-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
          }
          loadMovies(1);
        }
      };
      container.appendChild(chip);
    });
  });
}

function setupYearFilter() {
  const sel = document.getElementById('filter-year');
  const currentYear = new Date().getFullYear();
  for (let y = currentYear; y >= 1980; y--) {
    const opt = document.createElement('option');
    opt.value = y; opt.textContent = y;
    sel.appendChild(opt);
  }
}

// ── MOVIE DETAIL ──────────────────────────────────────────────────────────────
async function showMovieDetail(movieId) {
  showPage('movie-detail');
  const content = document.getElementById('movie-detail-content');
  content.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';

  const { ok, data } = await apiFetch(`/api/movies/${movieId}`);
  if (!ok) { content.innerHTML = '<p style="text-align:center;padding:40px;color:var(--text-muted)">Movie not found</p>'; return; }

  const poster = data.poster_url
    ? `<img class="movie-detail-poster" src="${data.poster_url}" alt="${escHtml(data.title)}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
    : '';
  const posterFallback = `<div class="movie-detail-poster-placeholder" ${data.poster_url ? '' : ''}>🎬</div>`;

  const platforms = data.streaming_platforms
    ? data.streaming_platforms.split(',').map(p => `<span class="streaming-badge">${p.trim()}</span>`).join('')
    : '';

  const watchlistBtnId = 'detail-wl-btn-' + movieId;
  const watchlistBtn = currentUser
    ? data.in_watchlist
      ? `<button id="${watchlistBtnId}" class="btn btn-ghost" onclick="removeWatchlist(${movieId}, document.getElementById('${watchlistBtnId}'))">✓ In Watchlist</button>`
      : `<button id="${watchlistBtnId}" class="btn btn-ghost" onclick="addWatchlist(${movieId}, document.getElementById('${watchlistBtnId}'))">+ Watchlist</button>`
    : `<button class="btn btn-ghost" onclick="showModal('login-modal')">+ Watchlist</button>`;

  const watchedBtn = currentUser
    ? data.in_history
      ? `<button class="btn btn-ghost" disabled>✓ Watched</button>`
      : `<button class="btn btn-ghost" onclick="markWatched(${movieId}, this)">Mark Watched</button>`
    : '';

  const rateBtn = currentUser
    ? `<button class="btn btn-primary" onclick="openRateModal(${movieId},'${escHtml(data.title)}')">★ Rate Movie</button>`
    : `<button class="btn btn-primary" onclick="showModal('login-modal')">★ Rate Movie</button>`;

  const reviews = data.reviews || [];
  const reviewsHTML = reviews.length
    ? reviews.map(r => `
        <div class="review-card">
          <div class="review-header">
            <span class="review-author">${escHtml(r.user_name)}</span>
            <span class="review-stars">${'★'.repeat(r.score)}${'☆'.repeat(5 - r.score)}</span>
            <span class="review-date">${new Date(r.created_at).toLocaleDateString()}</span>
          </div>
          ${r.review ? `<div class="review-text">${escHtml(r.review)}</div>` : ''}
        </div>`).join('')
    : '<p style="color:var(--text-muted)">No reviews yet. Be the first!</p>';

  const similar = data.similar_movies || [];
  const similarHTML = similar.length
    ? similar.map(m => `
        <div class="similar-card" onclick="showMovieDetail(${m.id})">
          ${m.poster_url ? `<img src="${m.poster_url}" alt="${escHtml(m.title)}" onerror="this.src=''">` : '<div style="aspect-ratio:2/3;background:var(--bg-card2);display:flex;align-items:center;justify-content:center;font-size:2rem">🎬</div>'}
          <div class="similar-card-title">${escHtml(m.title)}</div>
        </div>`).join('')
    : '<p style="color:var(--text-muted)">No similar movies found</p>';

  content.innerHTML = `
    <div class="movie-detail-hero">
      ${data.poster_url ? `<div class="movie-detail-bg" style="background-image:url('${data.poster_url}')"></div>` : ''}
      <div class="movie-detail-inner">
        ${poster}${posterFallback}
        <div class="movie-detail-info">
          <h1>${escHtml(data.title)}</h1>
          <div class="movie-detail-meta">
            ${data.release_year ? `<span class="badge">${data.release_year}</span>` : ''}
            ${data.language ? `<span class="badge">${data.language.toUpperCase()}</span>` : ''}
            ${data.tmdb_rating ? `<span class="badge badge-primary">★ ${data.tmdb_rating}</span>` : ''}
            ${data.avg_user_rating ? `<span class="badge">User: ${data.avg_user_rating}/5</span>` : ''}
          </div>
          <div class="movie-detail-meta">
            ${data.genre ? data.genre.split(',').map(g => `<span class="badge">${g.trim()}</span>`).join('') : ''}
          </div>
          ${data.synopsis ? `<p class="movie-detail-synopsis">${escHtml(data.synopsis)}</p>` : ''}
          ${data.director ? `<p class="movie-detail-cast"><strong>Director:</strong> ${escHtml(data.director)}</p>` : ''}
          ${data.cast ? `<p class="movie-detail-cast"><strong>Cast:</strong> ${escHtml(data.cast)}</p>` : ''}
          ${platforms ? `<div class="streaming-badges"><strong style="font-size:.85rem;color:var(--text-muted)">Watch on:</strong>${platforms}</div>` : ''}
          <div class="movie-detail-actions" style="margin-top:24px">
            ${watchlistBtn}${watchedBtn}${rateBtn}
            <button class="btn btn-ghost" onclick="history.back()">← Back</button>
          </div>
        </div>
      </div>
    </div>
    <div class="movie-detail-body">
      <div class="section-title">Reviews</div>
      <div class="reviews-list">${reviewsHTML}</div>
      <div class="section-title">Similar Movies</div>
      <div class="similar-scroll">${similarHTML}</div>
    </div>
  `;
}

// ── WATCHLIST ─────────────────────────────────────────────────────────────────
async function addWatchlist(movieId, btn) {
  if (!currentUser) { showModal('login-modal'); return; }
  const { ok, data } = await apiFetch('/api/watchlist/add', {
    method: 'POST', body: JSON.stringify({ movie_id: movieId })
  });
  if (ok) {
    showToast('Added to watchlist', 'success');
    if (btn) { btn.textContent = '✓ Saved'; btn.onclick = () => removeWatchlist(movieId, btn); }
  } else showToast(data.error || 'Failed', 'error');
}

async function removeWatchlist(movieId, btn, reload = false) {
  if (!currentUser) return;
  const { ok } = await apiFetch(`/api/watchlist/remove/${movieId}`, { method: 'DELETE' });
  if (ok) {
    showToast('Removed from watchlist');
    if (reload) loadWatchlist();
    else if (btn) { btn.textContent = '+ Save'; btn.onclick = () => addWatchlist(movieId, btn); }
  } else showToast('Failed to remove', 'error');
}

async function loadWatchlist() {
  const grid = document.getElementById('watchlist-grid');
  grid.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';
  const { ok, data } = await apiFetch('/api/watchlist/');
  if (!ok) { grid.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px">Failed to load</p>'; return; }
  if (data.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><h3>Your watchlist is empty</h3><p>Browse movies and save ones you want to watch</p></div>';
    return;
  }
  grid.innerHTML = '';
  data.forEach(e => {
    const card = createMovieCard({ ...e.movie, in_watchlist: true }, true);
    grid.appendChild(card);
  });
}

// ── HISTORY ───────────────────────────────────────────────────────────────────
async function loadHistory() {
  const grid = document.getElementById('history-grid');
  grid.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';
  const { ok, data } = await apiFetch('/api/history/');
  if (!ok) { grid.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px">Failed to load</p>'; return; }
  if (data.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🎞️</div><h3>No watch history</h3><p>Start browsing and watching movies</p></div>';
    return;
  }
  grid.innerHTML = '';
  data.forEach(e => {
    const card = createMovieCard(e.movie);
    grid.appendChild(card);
  });
}

async function markWatched(movieId, btn) {
  if (!currentUser) return;
  const { ok } = await apiFetch('/api/history/mark-watched', {
    method: 'POST', body: JSON.stringify({ movie_id: movieId })
  });
  if (ok) {
    showToast('Marked as watched', 'success');
    if (btn) { btn.textContent = '✓ Watched'; btn.disabled = true; }
  }
}

// ── RECOMMENDATIONS ───────────────────────────────────────────────────────────
const ALGO_META = {
  hybrid:        { icon: '🔀', label: 'Hybrid ML',           desc: 'Collaborative filtering + content-based (TF-IDF cosine similarity)', card: 'hybrid' },
  collaborative: { icon: '👥', label: 'Collaborative Filtering', desc: 'User-item matrix — finding people with similar taste', card: 'collaborative' },
  content:       { icon: '🎯', label: 'Content-Based Filtering', desc: 'TF-IDF cosine similarity on genre, cast & synopsis', card: 'content' },
  mood:          { icon: '😊', label: 'Mood-Based',          desc: 'Genre mapping from your selected mood', card: 'mood' },
  popular:       { icon: '📈', label: 'Trending',             desc: 'Top-rated movies — rate more films for personalised picks', card: null },
};

async function loadRecommendations(mood) {
  const grid = document.getElementById('rec-grid');
  grid.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';
  const params = mood ? '?mood=' + encodeURIComponent(mood) : '';
  const { ok, data } = await apiFetch('/api/recommendations/' + params);
  if (!ok) { grid.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px">Failed to load</p>'; return; }

  // Update algorithm display
  const algoType = data.algorithm_type || 'popular';
  const meta = ALGO_META[algoType] || ALGO_META.popular;
  const bar = document.getElementById('rec-algo-bar');
  const iconEl = document.getElementById('rec-algo-icon');
  const nameEl = document.getElementById('rec-algo-label');
  const descEl = document.getElementById('rec-algo-desc');
  if (bar) {
    bar.style.display = 'block';
    iconEl.textContent = meta.icon;
    nameEl.textContent = meta.label;
    descEl.textContent = meta.desc;
  }

  // Highlight active ML card
  document.querySelectorAll('.ml-card').forEach(c => c.classList.remove('active'));
  if (meta.card) {
    const activeCard = document.getElementById('ml-card-' + meta.card);
    if (activeCard) activeCard.classList.add('active');
  }

  grid.innerHTML = '';
  if (!data.recommendations || data.recommendations.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🤖</div><h3>No recommendations yet</h3><p>Browse and rate a few movies to unlock personalised ML picks</p></div>';
    return;
  }
  data.recommendations.forEach(m => grid.appendChild(createMovieCard(m)));
}

// ── RATINGS ───────────────────────────────────────────────────────────────────
function openRateModal(movieId, title) {
  if (!currentUser) { showModal('login-modal'); return; }
  ratingMovieId = movieId;
  selectedStar = 0;
  document.getElementById('rating-movie-title').textContent = title;
  document.getElementById('rating-review').value = '';
  document.getElementById('rating-error').style.display = 'none';
  document.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
  showModal('rating-modal');
}

function setStarRating(val) {
  selectedStar = val;
  document.querySelectorAll('.star').forEach(s => {
    s.classList.toggle('active', parseInt(s.dataset.v) <= val);
  });
}

async function submitRating() {
  if (!selectedStar) {
    document.getElementById('rating-error').textContent = 'Please select a star rating';
    document.getElementById('rating-error').style.display = 'block';
    return;
  }
  const review = document.getElementById('rating-review').value;
  const err = document.getElementById('rating-error');
  const { ok, data } = await apiFetch('/api/ratings/submit', {
    method: 'POST', body: JSON.stringify({ movie_id: ratingMovieId, score: selectedStar, review })
  });
  if (ok) {
    closeModals();
    showToast('Rating submitted!', 'success');
  } else {
    err.textContent = data.error || 'Failed to submit rating';
    err.style.display = 'block';
  }
}

// ── ADMIN ─────────────────────────────────────────────────────────────────────
async function loadAdmin() {
  if (!currentUser || !currentUser.is_admin) { showPage('home'); return; }
  adminTab('stats');
}

async function adminTab(tab) {
  document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', ['stats','reviews','users'][i] === tab));
  document.getElementById('admin-stats').style.display = tab === 'stats' ? 'block' : 'none';
  document.getElementById('admin-reviews').style.display = tab === 'reviews' ? 'block' : 'none';
  document.getElementById('admin-users').style.display = tab === 'users' ? 'block' : 'none';

  if (tab === 'stats') {
    const { ok, data } = await apiFetch('/api/admin/stats');
    if (!ok) return;
    document.getElementById('stats-cards').innerHTML = [
      ['Total Users', data.total_users, '👤'],
      ['Total Movies', data.total_movies, '🎬'],
      ['Total Ratings', data.total_ratings, '⭐'],
      ['Avg Rating', data.avg_rating, '📊'],
      ['Flagged Reviews', data.flagged_reviews, '🚩'],
    ].map(([label, val, icon]) => `
      <div class="stat-card">
        <div style="font-size:2rem;margin-bottom:8px">${icon}</div>
        <div class="stat-value">${val}</div>
        <div class="stat-label">${label}</div>
      </div>`).join('');
  }

  if (tab === 'reviews') {
    const { ok, data } = await apiFetch('/api/admin/reviews');
    if (!ok) return;
    document.getElementById('reviews-table').innerHTML = `
      <div style="overflow-x:auto">
      <table>
        <thead><tr><th>User</th><th>Movie</th><th>Score</th><th>Review</th><th>Flagged</th><th>Action</th></tr></thead>
        <tbody>${data.map(r => `
          <tr class="${r.is_flagged ? 'flagged-row' : ''}">
            <td>${escHtml(r.user_name)}</td>
            <td>${escHtml(r.movie_title)}</td>
            <td>${'★'.repeat(r.score)}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(r.review || '')}</td>
            <td>${r.is_flagged ? '🚩' : '—'}</td>
            <td><button class="btn btn-ghost btn-sm" onclick="flagReview(${r.id})">${r.is_flagged ? 'Unflag' : 'Flag'}</button></td>
          </tr>`).join('')}</tbody>
      </table>
      </div>`;
  }

  if (tab === 'users') {
    const { ok, data } = await apiFetch('/api/admin/users');
    if (!ok) return;
    document.getElementById('users-table').innerHTML = `
      <div style="overflow-x:auto">
      <table>
        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead>
        <tbody>${data.map(u => `
          <tr>
            <td>${escHtml(u.name)}</td>
            <td>${escHtml(u.email)}</td>
            <td>${u.is_admin ? '<span class="badge badge-primary">Admin</span>' : 'User'}</td>
            <td>${new Date(u.created_at).toLocaleDateString()}</td>
          </tr>`).join('')}</tbody>
      </table>
      </div>`;
  }
}

async function flagReview(id) {
  const { ok } = await apiFetch(`/api/admin/reviews/${id}/flag`, { method: 'POST' });
  if (ok) { showToast('Review flag toggled'); adminTab('reviews'); }
}

// ── UTILS ─────────────────────────────────────────────────────────────────────
function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── INIT ──────────────────────────────────────────────────────────────────────
async function init() {
  await loadCurrentUser();
  setupMoodChips();
  setupYearFilter();
  await loadGenres();
  loadMovies();
}

init();
