/* Console prototype: the broadcast audience selector recomputes reach.
   Nothing is sent. In a real build this reads from the segment service. */
(function () {
  var form = document.querySelector('[data-broadcast]');
  if (!form) return;
  var i18n = {};
  try { i18n = JSON.parse(form.dataset.i18n || '{}'); } catch (e) {}
  var lang = document.documentElement.lang;

  function n(v) {
    var s = String(v);
    return lang === 'ar' ? s.replace(/[0-9]/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'[+d]; }) : s;
  }

  function sync() {
    var r = form.querySelector('input[name="audience"]:checked');
    if (!r) return;
    var reach = +r.dataset.reach, push = +r.dataset.push, wa = +r.dataset.wa;
    var set = function (k, v) {
      var el = form.querySelector('[data-metric="' + k + '"]');
      if (el) el.textContent = v;
    };
    set('audience', n(reach));
    set('push', n(push));
    set('wa', n(wa));
    set('total', n(push + wa) + ' / ' + n(reach));
    var cmp = form.querySelector('[data-compare]');
    if (cmp) cmp.textContent = (i18n.compare || '').replace('{n}', n(reach));
  }

  form.addEventListener('change', function (e) {
    if (e.target.name === 'audience') sync();
  });
  sync();
})();
