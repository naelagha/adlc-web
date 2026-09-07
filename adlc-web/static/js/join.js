/* Join flow.
   The whole form is in the page; this turns it into steps, keeps the
   order summary in sync, and validates before advancing.

   Deliberately NOT here: any card field, and any network request. The
   payment step hands off to the gateway's hosted checkout, so card data
   never touches the club's own pages (and this prototype cannot collect
   it even by accident). Without JS the form degrades to one long page
   with every step visible, which still reads correctly.
*/
(function () {
  var form = document.querySelector('[data-join]');
  if (!form) return;

  var steps = [].slice.call(form.querySelectorAll('.step'));
  var progress = [].slice.call(form.querySelectorAll('.progress li'));
  var counter = form.querySelector('.step-count');
  var errBox = form.querySelector('.form-error');
  var i18n = JSON.parse(form.dataset.i18n || '{}');
  var vatRate = 0.05;
  var at = 0;

  /* ---------- money ---------- */
  function money(v) {
    if (v === null || v === undefined || isNaN(v)) return i18n.dash || 'AED —';
    return 'AED ' + v.toLocaleString(document.documentElement.lang === 'ar' ? 'ar-AE' : 'en-AE',
      { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  }

  function billing() {
    var r = form.querySelector('input[name="billing"]:checked');
    return r ? r.value : 'annual';
  }
  function selectedTier() {
    var r = form.querySelector('input[name="tier"]:checked');
    if (!r) return null;
    // a tier holds one price per billing period; reading the wrong one would
    // bill an annual figure monthly, so the period is part of the lookup
    var raw = billing() === 'monthly' ? r.dataset.priceMonthly : r.dataset.priceAnnual;
    return { id: r.value, name: r.dataset.name, price: raw === '' || raw == null ? null : Number(raw) };
  }

  function syncSummary() {
    var tier = selectedTier(), bill = billing();
    var net = tier && tier.price !== null ? tier.price : null;
    var vat = net === null ? null : Math.round(net * vatRate * 100) / 100;
    var tot = net === null ? null : net + vat;
    form.querySelectorAll('[data-sum]').forEach(function (el) {
      switch (el.dataset.sum) {
        case 'tier':    el.textContent = tier ? tier.name : '—'; break;
        case 'billing': el.textContent = i18n[bill] || bill; break;
        case 'net':     el.textContent = money(net); break;
        case 'vat':     el.textContent = money(vat); break;
        case 'total':   el.textContent = money(tot); break;
      }
    });
    form.querySelectorAll('[data-paylabel]').forEach(function (el) {
      el.textContent = (i18n.gateway || 'Continue to secure payment');
    });
  }

  /* ---------- validation ---------- */
  function validate(step) {
    var bad = [];
    step.querySelectorAll('[required]').forEach(function (f) {
      var wrap = f.closest('.field') || f.closest('.consent');
      var ok = f.type === 'checkbox' ? f.checked : String(f.value).trim() !== '';
      if (f.type === 'email' && ok) ok = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f.value.trim());
      if (wrap) wrap.classList.toggle('invalid', !ok);
      if (!ok) bad.push(f);
    });
    if (bad.length) {
      errBox.hidden = false;
      errBox.textContent = (i18n.fixErrors || 'Please complete the highlighted fields.');
      bad[0].focus();
      return false;
    }
    errBox.hidden = true;
    return true;
  }

  /* ---------- navigation ---------- */
  function show(n, initial) {
    at = n;
    steps.forEach(function (s, idx) { s.hidden = idx !== n; });
    progress.forEach(function (li, idx) {
      li.dataset.state = idx < n ? 'done' : idx === n ? 'now' : 'todo';
    });
    if (counter) counter.textContent =
      (i18n.stepWord || 'Step') + ' ' + (n + 1) + ' ' + (i18n.of || 'of') + ' ' + steps.length +
      ' \u00b7 ' + steps[n].dataset.label;
    errBox.hidden = true;
    if (initial) return;            // never move the page on first paint
    var lg = steps[n].querySelector('legend');
    lg.setAttribute('tabindex', '-1');
    lg.focus({ preventScroll: true }); // focus() alone scrolls; we choose where to go
    var top = form.getBoundingClientRect().top + window.scrollY - 16;
    window.scrollTo({ top: Math.max(top, 0), behavior: 'smooth' });
  }

  form.addEventListener('click', function (e) {
    var next = e.target.closest('[data-next]'), back = e.target.closest('[data-back]');
    if (next) { e.preventDefault(); if (validate(steps[at])) show(Math.min(at + 1, steps.length - 1)); }
    if (back) { e.preventDefault(); show(Math.max(at - 1, 0)); }
  });
  form.addEventListener('change', function (e) {
    if (e.target.name === 'tier' || e.target.name === 'billing') syncSummary();
    var wrap = e.target.closest('.field') || e.target.closest('.consent');
    if (wrap) wrap.classList.remove('invalid');
  });
  form.addEventListener('submit', function (e) { e.preventDefault(); });

  /* preselect a tier from ?tier=gold, so membership.html can link straight in */
  var want = new URLSearchParams(location.search).get('tier');
  if (want) {
    var r = form.querySelector('input[name="tier"][value="' + CSS.escape(want) + '"]');
    if (r) r.checked = true;
  }

  syncSummary();
  show(0, true);
})();
