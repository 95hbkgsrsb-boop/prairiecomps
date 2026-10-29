(function () {
  const q = document.getElementById('q');
  const make = document.getElementById('make');
  const province = document.getElementById('province');
  const cards = Array.from(document.querySelectorAll('[data-model-card]'));
  const empty = document.getElementById('empty-state');
  if (!cards.length) return;

  function apply() {
    const term = (q && q.value || '').trim().toLowerCase();
    const mk = (make && make.value || '').toLowerCase();
    const pv = (province && province.value || '').toLowerCase();
    let shown = 0;
    cards.forEach(card => {
      const hay = (card.getAttribute('data-search') || '').toLowerCase();
      const okTerm = !term || hay.includes(term);
      const okMake = !mk || (card.getAttribute('data-make') || '').toLowerCase() === mk;
      const okProv = !pv || (card.getAttribute('data-provinces') || '').toLowerCase().includes(pv);
      const ok = okTerm && okMake && okProv;
      card.classList.toggle('hidden', !ok);
      if (ok) shown += 1;
    });
    if (empty) empty.classList.toggle('hidden', shown > 0);
  }
  [q, make, province].forEach(el => {
    if (!el) return;
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
})();
