/* Generic faceted filtering for any server-rendered list.
   Used by the timetable (day, type) and by events (kind).

   Markup contract:
     [data-filterable]              the container
       [data-facet="day"][data-value="sun"]   a filter button
       [data-item][data-day="sun"]            an item, one attribute per facet
       [data-group]                           optional wrapper, hidden when empty
       [data-empty]                            shown when nothing matches

   The items are rendered by the server and this only hides them, so every
   list still reads correctly with JavaScript off.
*/
(function () {
  document.querySelectorAll('[data-filterable]').forEach(function (root) {
    var buttons = [].slice.call(root.querySelectorAll('[data-facet]'));
    if (!buttons.length) return;

    var facets = {};
    buttons.forEach(function (b) { facets[b.dataset.facet] = 'all'; });

    var items = [].slice.call(root.querySelectorAll('[data-item]'));
    var groups = [].slice.call(root.querySelectorAll('[data-group]'));
    var empty = root.querySelector('[data-empty]');

    function apply() {
      var shown = 0;
      items.forEach(function (el) {
        var ok = Object.keys(facets).every(function (f) {
          return facets[f] === 'all' || el.dataset[f] === facets[f];
        });
        el.hidden = !ok;
        if (ok) shown++;
      });
      groups.forEach(function (g) {
        g.hidden = !g.querySelector('[data-item]:not([hidden])');
      });
      if (empty) empty.hidden = shown !== 0;
    }

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var f = btn.dataset.facet;
        facets[f] = btn.dataset.value;
        buttons.forEach(function (b) {
          if (b.dataset.facet === f) b.setAttribute('aria-pressed', String(b === btn));
        });
        apply();
      });
    });

    apply();
  });
})();
