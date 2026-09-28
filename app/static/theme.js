(function () {
  const KEY = 'cp-theme';
  const root = document.documentElement;

  function apply(mode) {
    if (mode === 'light' || mode === 'dark') {
      root.setAttribute('data-theme', mode);
    } else {
      root.removeAttribute('data-theme');
    }
  }

  const saved = (() => { try { return localStorage.getItem(KEY); } catch (_) { return null; } })();
  apply(saved || 'auto');

  function labelFor(mode) {
    if (mode === 'light') return '☀️ Clair';
    if (mode === 'dark') return '🌙 Sombre';
    return '🖥️ Auto';
  }

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    let current = saved || 'auto';
    btn.textContent = labelFor(current);
    btn.addEventListener('click', () => {
      current = current === 'auto' ? 'light' : current === 'light' ? 'dark' : 'auto';
      try { localStorage.setItem(KEY, current); } catch (_) {}
      apply(current);
      btn.textContent = labelFor(current);
    });
  });
})();
