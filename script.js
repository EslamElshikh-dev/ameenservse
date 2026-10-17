(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#main-nav');
  const closeMenu = () => {
    toggle?.setAttribute('aria-expanded', 'false');
    toggle?.setAttribute('aria-label', 'فتح القائمة');
    nav?.classList.remove('is-open');
  };
  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'إغلاق القائمة' : 'فتح القائمة');
    nav?.classList.toggle('is-open', open);
  });
  nav?.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') {
      closeMenu();
      toggle.focus();
    }
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.header-inner')) closeMenu();
  });
  window.matchMedia('(min-width: 921px)').addEventListener?.('change', closeMenu);
  const filters = [...document.querySelectorAll('[data-filter]')];
  const cards = [...document.querySelectorAll('.service-catalog [data-category]')];
  const filterStatus = document.querySelector('.filter-status');
  filters.forEach(filter => filter.addEventListener('click', () => {
    const type = filter.dataset.filter;
    let count = 0;
    cards.forEach(card => {
      card.hidden = type !== 'all' && card.dataset.category !== type;
      if (!card.hidden) count++;
    });
    filters.forEach(item => item.setAttribute('aria-pressed', String(item === filter)));
    if (filterStatus) filterStatus.textContent = `عرض ${count} خدمة`;
  }));
  const fields = ['request-service', 'request-area', 'request-details'].map(id => document.getElementById(id));
  const requestLink = document.getElementById('request-link');
  if (requestLink && fields.every(Boolean)) {
    const [service, area, details] = fields;
    const updateRequest = () => {
      const message = [`مرحبًا أمين سرور، أرغب في طلب خدمة ${service.value}.`, area.value.trim() ? `الحي في الرياض: ${area.value.trim()}` : '', details.value.trim() ? `تفاصيل الطلب: ${details.value.trim()}` : ''].filter(Boolean).join('\n');
      requestLink.href = `https://wa.me/966545350293?text=${encodeURIComponent(message)}`;
    };
    fields.forEach(field => field.addEventListener('input', updateRequest));
    updateRequest();
  }
  const year = document.getElementById('current-year');
  if (year) year.textContent = String(new Date().getFullYear());
  // This public event measures a click, never a completed call or a qualified lead.
  document.querySelectorAll('a[href^="tel:"],a[href^="https://wa.me/"]').forEach(link => link.addEventListener('click', () => {
    const detail = {channel: link.href.startsWith('tel:') ? 'phone' : 'whatsapp', page: location.pathname};
    window.dispatchEvent(new CustomEvent('ameen:contact-click', {detail}));
  }));
})();
