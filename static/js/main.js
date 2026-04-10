/* ═══════════════════════════════════════════
   Biblioteca Digital v2 — JavaScript
   ═══════════════════════════════════════════ */

// ── Scroll Reveal ────────────────────────────────────
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.scroll-reveal').forEach(el => {
  revealObserver.observe(el);
});

// ── Sidebar Toggle (móvil) ───────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.toggle('open');
}

// Cerrar sidebar al hacer clic fuera
document.addEventListener('click', (e) => {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.sidebar-toggle');
  if (sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove('open');
    }
  }
});

// ── Auto-dismiss de alertas ──────────────────────────
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(alert => {
    alert.style.transition = 'opacity .4s ease, transform .4s ease';
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-8px)';
    setTimeout(() => alert.remove(), 400);
  });
}, 4000);

// ── Confirmación en formularios de eliminar ──────────
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', (e) => {
    if (!confirm(form.dataset.confirm)) e.preventDefault();
  });
});

// ── Ripple effect en botones ──────────────────────────
document.querySelectorAll('.btn').forEach(btn => {
  btn.addEventListener('click', function(e) {
    const ripple = document.createElement('span');
    const rect   = btn.getBoundingClientRect();
    const size   = Math.max(rect.width, rect.height);
    ripple.style.cssText = `
      position:absolute; border-radius:50%; background:rgba(255,255,255,0.3);
      width:${size}px; height:${size}px; pointer-events:none;
      left:${e.clientX - rect.left - size/2}px;
      top:${e.clientY - rect.top - size/2}px;
      transform:scale(0); animation:ripple .5s ease-out forwards;
    `;
    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 500);
  });
});

// Inject ripple keyframe
const style = document.createElement('style');
style.textContent = `@keyframes ripple { to { transform:scale(2.5); opacity:0; } }`;
document.head.appendChild(style);
