// Confirmation dialogs for forms marked with data-confirm.
// (Inline onsubmit handlers are blocked by the CSP: script-src 'self'.)
document.addEventListener('submit', (e) => {
  const form = e.target.closest('form[data-confirm]');
  if (form && !window.confirm(form.dataset.confirm)) {
    e.preventDefault();
  }
});
