// ── API helpers ──────────────────────────────────────────────────────────────

const api = {
  async request(method, url, body = null, isFormData = false) {
    const opts = {
      method,
      credentials: 'include',
      headers: isFormData ? {} : { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);
    const res = await fetch(url, opts);
    let data = {};
    try { data = await res.json(); } catch {}
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  },
  get: (url) => api.request('GET', url),
  post: (url, body) => api.request('POST', url, body),
  patch: (url, body) => api.request('PATCH', url, body),
  delete: (url) => api.request('DELETE', url),
  postForm: (url, formData) => api.request('POST', url, formData, true),
};

// ── Storage helpers ───────────────────────────────────────────────────────────
const store = {
  get: (k) => { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
  set: (k, v) => localStorage.setItem(k, JSON.stringify(v)),
  del: (k) => localStorage.removeItem(k),
};

// ── Show/hide alert ───────────────────────────────────────────────────────────
function showAlert(el, msg, type = 'error') {
  el.className = `alert alert-${type}`;
  el.textContent = msg;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 5000);
}

function hideAlert(el) {
  el.classList.add('hidden');
}

// ── Set loading state on button ───────────────────────────────────────────────
function setLoading(btn, loading, text = 'Loading...') {
  if (loading) {
    btn.dataset.original = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> ${text}`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.original || btn.innerHTML;
    btn.disabled = false;
  }
}

// ── Simple Markdown renderer (no external lib) ────────────────────────────────
function renderMarkdown(text) {
  if (!text) return '';
  return text
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold / italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Code inline
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr>')
    // Unordered lists
    .replace(/^\* (.+)$/gm, '<li>$1</li>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Line breaks (double newline = paragraph)
    .replace(/\n\n/g, '</p><p>')
    // Wrap stray li in ul
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    // Wrap in paragraph
    .replace(/^(?!<[hul]|<hr)(.+)$/gm, '<p>$1</p>')
    // Clean up empty paragraphs
    .replace(/<p><\/p>/g, '');
}

// ── Format currency ───────────────────────────────────────────────────────────
function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(val || 0);
}

// ── Format date ───────────────────────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ── Mask card number ──────────────────────────────────────────────────────────
function maskCard(num) {
  const s = String(num);
  return '**** **** **** ' + s.slice(-4);
}

// ── Load user from API ────────────────────────────────────────────────────────
async function loadCurrentUser() {
  try {
    const data = await api.get('/api/auth/me');
    store.set('user', data.user);
    return data.user;
  } catch {
    return null;
  }
}

// ── Populate sidebar user card ────────────────────────────────────────────────
function populateSidebar(user) {
  if (!user) return;
  const nameEl = document.querySelector('.user-info .name');
  const emailEl = document.querySelector('.user-info .email');
  const avatarEl = document.querySelector('.sidebar-footer .avatar');
  if (nameEl) nameEl.textContent = `${user.fname} ${user.lname}`;
  if (emailEl) emailEl.textContent = user.email;
  if (avatarEl) {
    if (user.profile_img) {
      avatarEl.innerHTML = `<img src="${user.profile_img}" alt="avatar">`;
    } else {
      avatarEl.textContent = (user.fname?.[0] || '') + (user.lname?.[0] || '');
    }
  }
}

// ── Logout ────────────────────────────────────────────────────────────────────
async function logout() {
  try { await api.post('/api/auth/logout'); } catch {}
  store.del('user');
  window.location.href = '/login';
}

// ── Mobile sidebar toggle ─────────────────────────────────────────────────────
function initSidebarToggle() {
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove('open');
      }
    });
  }
}

// ── Set active nav link ───────────────────────────────────────────────────────
function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && path === href) link.classList.add('active');
    else if (href && href !== '/' && path.startsWith(href)) link.classList.add('active');
  });
}

// ── Modal helpers ─────────────────────────────────────────────────────────────
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}
function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('open');
  }
  if (e.target.classList.contains('modal-close')) {
    e.target.closest('.modal-backdrop')?.classList.remove('open');
  }
});

// ── On DOM ready ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  setActiveNav();
  initSidebarToggle();

  // Auto-load user if sidebar exists
  if (document.querySelector('.sidebar')) {
    const cached = store.get('user');
    if (cached) populateSidebar(cached);
    const fresh = await loadCurrentUser();
    if (fresh) populateSidebar(fresh);
  }

  // Logout buttons
  document.querySelectorAll('[data-action="logout"]').forEach(btn => {
    btn.addEventListener('click', logout);
  });
});
