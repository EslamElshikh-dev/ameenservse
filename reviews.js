/* Native RTL scroll-snap: all review text remains in the server-rendered HTML. */
(() => {
  'use strict';

  document.querySelectorAll('[data-review-carousel]').forEach((root) => {
    const track = root.querySelector('.review-track');
    const cards = Array.from(track.querySelectorAll('.review-card'));
    const controls = root.querySelector('.review-controls');
    const previous = root.querySelector('.review-prev');
    const next = root.querySelector('.review-next');
    const playback = root.querySelector('.review-playback');
    const counter = root.querySelector('.review-counter');
    const dots = root.querySelector('.review-dots');
    const announcement = root.querySelector('.review-announcement');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const numbers = new Intl.NumberFormat('ar-SA');
    let index = 0;
    let visible = 1;
    let maximum = 0;
    let direction = 1;
    let timer = 0;
    let frame = 0;
    let inView = false;
    let hovered = false;
    let focused = false;
    let touching = false;
    let paused = false;

    root.classList.add('is-ready');

    const stop = () => { window.clearTimeout(timer); timer = 0; };
    const label = () => `${numbers.format(index + 1)}–${numbers.format(Math.min(index + visible, cards.length))} من ${numbers.format(cards.length)}`;
    const paint = () => {
      previous.disabled = index === 0;
      next.disabled = index === maximum;
      counter.textContent = label();
      Array.from(dots.children).forEach((dot, position) => {
        dot.setAttribute('aria-current', String(position === index));
      });
      playback.textContent = paused || reducedMotion.matches ? 'تشغيل الحركة' : 'إيقاف الحركة';
      playback.setAttribute('aria-pressed', String(paused || reducedMotion.matches));
      playback.disabled = reducedMotion.matches;
      if (reducedMotion.matches) playback.textContent = 'الحركة متوقفة حسب تفضيلك';
    };
    const schedule = () => {
      stop();
      if (!maximum || !inView || document.hidden || hovered || focused || touching || paused || reducedMotion.matches) return;
      timer = window.setTimeout(() => {
        if (index >= maximum) direction = -1;
        if (index <= 0) direction = 1;
        go(index + direction, false);
      }, 6500);
    };
    const go = (position, manual = true, instant = false) => {
      index = Math.max(0, Math.min(maximum, position));
      const bounds = track.getBoundingClientRect();
      const card = cards[index].getBoundingClientRect();
      const styles = window.getComputedStyle(track);
      const rtl = styles.direction === 'rtl';
      const delta = rtl
        ? card.right - (bounds.right - parseFloat(styles.paddingRight || '0'))
        : card.left - (bounds.left + parseFloat(styles.paddingLeft || '0'));
      track.scrollTo({ left: track.scrollLeft + delta, behavior: instant || reducedMotion.matches ? 'instant' : 'smooth' });
      paint();
      if (manual) announcement.textContent = `التقييمات ${label()}`;
      schedule();
    };
    const layout = () => {
      const columnValue = Number(window.getComputedStyle(root).getPropertyValue('--review-columns'));
      visible = Math.max(1, Math.min(cards.length, columnValue || 1));
      maximum = Math.max(0, cards.length - visible);
      controls.hidden = maximum === 0;
      if (dots.children.length !== maximum + 1) {
        dots.replaceChildren();
        for (let position = 0; position <= maximum; position += 1) {
          const dot = document.createElement('button');
          dot.type = 'button';
          dot.className = 'review-dot';
          dot.setAttribute('aria-label', `عرض التقييمات بدءًا من ${numbers.format(position + 1)}`);
          dot.setAttribute('aria-controls', track.id);
          dot.addEventListener('click', () => go(position));
          dots.append(dot);
        }
      }
      go(index, false, true);
    };

    previous.addEventListener('click', () => go(index - 1));
    next.addEventListener('click', () => go(index + 1));
    playback.addEventListener('click', () => { paused = !paused; paint(); schedule(); });
    track.addEventListener('keydown', (event) => {
      if (event.target !== track) return;
      const rtl = window.getComputedStyle(track).direction === 'rtl';
      const actions = { ArrowLeft: index + (rtl ? 1 : -1), ArrowRight: index + (rtl ? -1 : 1), Home: 0, End: maximum };
      if (!(event.key in actions)) return;
      event.preventDefault();
      go(actions[event.key]);
    });
    track.addEventListener('scroll', () => {
      if (frame) return;
      frame = window.requestAnimationFrame(() => {
        frame = 0;
        const bounds = track.getBoundingClientRect();
        const styles = window.getComputedStyle(track);
        const rtl = styles.direction === 'rtl';
        const edge = rtl ? bounds.right - parseFloat(styles.paddingRight || '0') : bounds.left + parseFloat(styles.paddingLeft || '0');
        let closest = 0;
        let distance = Infinity;
        cards.forEach((card, position) => {
          const rect = card.getBoundingClientRect();
          const difference = Math.abs((rtl ? rect.right : rect.left) - edge);
          if (difference < distance) { distance = difference; closest = position; }
        });
        index = Math.min(maximum, closest);
        paint();
        schedule();
      });
    }, { passive: true });
    root.addEventListener('mouseenter', () => { hovered = true; stop(); });
    root.addEventListener('mouseleave', () => { hovered = false; schedule(); });
    root.addEventListener('focusin', () => { focused = true; stop(); });
    root.addEventListener('focusout', (event) => {
      focused = !!event.relatedTarget && root.contains(event.relatedTarget);
      schedule();
    });
    track.addEventListener('pointerdown', () => { touching = true; stop(); }, { passive: true });
    const release = () => { touching = false; schedule(); };
    window.addEventListener('pointerup', release, { passive: true });
    window.addEventListener('pointercancel', release, { passive: true });
    document.addEventListener('visibilitychange', schedule);
    reducedMotion.addEventListener('change', () => { paint(); schedule(); });
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([entry]) => { inView = entry.isIntersecting && entry.intersectionRatio >= 0.25; schedule(); }, { threshold: 0.25 }).observe(root);
    }
    if ('ResizeObserver' in window) new ResizeObserver(layout).observe(track);
    else window.addEventListener('resize', layout, { passive: true });
    layout();
  });
})();
