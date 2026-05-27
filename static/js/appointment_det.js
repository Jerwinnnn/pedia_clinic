let _pendingForm = null;

function toggle(id, headEl) {
  const body = document.getElementById('body-' + id);
  const isOpen = body.classList.contains('is-open');
  document.querySelectorAll('.action-body').forEach(el => el.classList.remove('is-open'));
  document.querySelectorAll('.action-head').forEach(el => el.classList.remove('is-open'));
  if (!isOpen) {
    body.classList.add('is-open');
    headEl.classList.add('is-open');
    body.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function showConfirm(formId, type, title, msg) {
  _pendingForm = document.getElementById(formId);

  const icons = {
    green: '✓',
    blue:  '⟳',
    red:   '✕'
  };

  const icon = document.getElementById('confirmIcon');
  icon.className = 'confirm-icon ' + type;
  icon.textContent = icons[type];

  document.getElementById('confirmTitle').textContent = title;
  document.getElementById('confirmMsg').innerHTML = msg;

  const btn = document.getElementById('confirmOkBtn');
  btn.className = 'confirm-ok ' + type;
  btn.textContent = title;

  document.getElementById('confirmModal').classList.add('open');
}

function closeConfirm() {
  document.getElementById('confirmModal').classList.remove('open');
  _pendingForm = null;
}

function submitConfirmed() {
  if (_pendingForm) {
    _pendingForm.submit();
  }
  closeConfirm();
}

// Close on backdrop click
document.getElementById('confirmModal').addEventListener('click', function(e) {
  if (e.target === this) closeConfirm();
});

// Close on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeConfirm();
});

// ── Read toasts from data attributes on page load ──
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.toast-data').forEach(function(el) {
    showToast(el.dataset.type, el.dataset.msg);
    el.remove();
  });
});

// ── Toast system ──
function showToast(type, message) {
  const titles = { success: 'Success', error: 'Error', warning: 'Warning' };
  const icons = {
    success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M20 6L9 17l-5-5"/></svg>`,
    error:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>`,
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${icons[type] || icons.success}</div>
    <div class="toast-body">
      <div class="toast-title">${titles[type] || 'Notice'}</div>
      <div class="toast-msg">${message}</div>
    </div>
    <button class="toast-close" onclick="dismissToast(this.parentElement)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
    </button>
    <div class="toast-progress"></div>
  `;

  document.getElementById('toastContainer').appendChild(toast);

  // Auto dismiss after 4 seconds
  setTimeout(() => dismissToast(toast), 4000);
}

function dismissToast(toast) {
  if (!toast || toast.classList.contains('hiding')) return;
  toast.classList.add('hiding');
  setTimeout(() => toast.remove(), 300);
}