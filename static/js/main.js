// OnePass — minimal client helpers
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 5s
  document.querySelectorAll('.alert.fade').forEach(a => {
    setTimeout(() => a.classList.remove('show'), 5000);
  });

  // Default date input to today
  document.querySelectorAll('input[type="date"]').forEach(i => {
    if (!i.value) {
      const d = new Date();
      i.min = d.toISOString().split('T')[0];
    }
  });
});
