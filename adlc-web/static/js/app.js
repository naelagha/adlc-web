/* Member app prototype.
   Booking is a checkbox, and a confirmation takes over the screen rather than
   flashing a toast — the booking is the moment the member came for.
   State is in memory only: no network, no storage. In a real build toggle()
   calls the booking engine and the sheet renders from its response. */
(function () {
  var root = document.querySelector('[data-app]');
  if (!root) return;
  var i18n = {};
  try { i18n = JSON.parse(root.dataset.i18n || '{}'); } catch (e) {}
  var rtl = document.documentElement.lang === 'ar';

  function n(v) {
    return rtl ? String(v).replace(/[0-9]/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'[+d]; }) : String(v);
  }

  /* ---- confirmation sheet ---- */
  var sheet = document.querySelector('[data-sheet]');
  function openSheet(row) {
    if (!sheet) return;
    var set = function (k, v) {
      var el = sheet.querySelector('[data-sh="' + k + '"]');
      if (el) el.textContent = v;
    };
    set('when', row.dataset.when || '');
    set('what', row.dataset.name || '');
    set('who', row.dataset.who || '');
    set('countdown', row.dataset.countdown || '');
    sheet.hidden = false;
    document.body.style.overflow = 'hidden';
    var c = sheet.querySelector('.sh-close');
    if (c) c.focus();
  }
  function closeSheet() {
    if (!sheet) return;
    sheet.hidden = true;
    document.body.style.overflow = '';
  }
  if (sheet) {
    sheet.addEventListener('click', function (e) {
      if (e.target.closest('[data-sheet-close]')) closeSheet();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !sheet.hidden) closeSheet();
    });
  }

  /* ---- booking checkboxes ---- */
  root.querySelectorAll('.check').forEach(function (box) {
    var row = box.closest('.app-cls');
    var spots = row && row.querySelector('.spots');
    var free = Number(box.dataset.free || 0);
    box.addEventListener('click', function () {
      var s = box.dataset.state;
      var next = s === 'free' ? 'booked' : s === 'booked' ? 'free'
               : s === 'wait' ? 'waiting' : 'wait';
      box.dataset.state = next;
      box.setAttribute('aria-pressed', String(next === 'booked' || next === 'waiting'));
      box.textContent = next === 'booked' ? '✓' : next === 'waiting' ? '·' : '';
      box.setAttribute('aria-label',
        (next === 'booked' ? i18n.booked : next === 'waiting' ? i18n.waiting
         : next === 'wait' ? i18n.wait : i18n.book) + ' — ' + (row.dataset.name || ''));
      if (spots && spots.dataset.template) {
        var left = free - (next === 'booked' ? 1 : 0);
        spots.textContent = spots.dataset.template.replace('{n}', n(left));
      }
      if (next === 'booked') openSheet(row);
    });
  });
})();
