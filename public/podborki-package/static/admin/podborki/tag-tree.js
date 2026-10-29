/* Виджет «Подборки» в карточке курса: дерево с чекбоксами, чипы выбранных, поиск. */
(function () {
  function ready(fn) { if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function () {
  document.querySelectorAll('[data-tag-tree]').forEach(function (tree) {
  /* Карточка курса: дерево подборок */
  {
    var selected = tree.querySelector('[data-tt-selected]');
    var checks = function () { return Array.prototype.slice.call(tree.querySelectorAll('[data-tt-check]')); };
    function pathOf(input) {
      var names = [];
      var li = input.closest('[data-tt-item]');
      while (li) {
        var n = li.querySelector(':scope > .tt-row .tt-name');
        names.unshift(n.getAttribute('data-short') || n.textContent);
        li = li.parentNode.closest('[data-tt-item]');
      }
      return names.join(' › ');
    }
    function refresh() {
      checks().forEach(function (c) { c.indeterminate = false; });
      checks().forEach(function (c) {
        if (!c.checked) return;
        var li = c.closest('[data-tt-item]').parentNode.closest('[data-tt-item]');
        while (li) {
          var pc = li.querySelector(':scope > .tt-row [data-tt-check]');
          if (!pc.checked) pc.indeterminate = true;
          li = li.parentNode.closest('[data-tt-item]');
        }
      });
      var on = checks().filter(function (c) { return c.checked; });
      selected.innerHTML = on.length ? on.map(function (c) {
        return '<span class="tt-chip">' + pathOf(c) + '<button type="button" aria-label="Убрать" data-tt-remove="' + c.value + '">×</button></span>';
      }).join('') : '<span class="tt-empty">Подборки не выбраны — курс не попадёт ни в одну подборку</span>';
    }
    tree.addEventListener('change', refresh);
    tree.addEventListener('click', function (e) {
      var tg = e.target.closest('[data-tt-toggle]');
      if (tg) {
        var li = tg.closest('[data-tt-item]');
        var open = !li.classList.contains('is-open');
        li.classList.toggle('is-open', open);
        tg.setAttribute('aria-expanded', String(open));
      }
      var rm = e.target.closest('[data-tt-remove]');
      if (rm) {
        var c = tree.querySelector('[data-tt-check][value="' + rm.getAttribute('data-tt-remove') + '"]');
        if (c) { c.checked = false; refresh(); }
      }
      if (e.target.closest('[data-tt-expand]') || e.target.closest('[data-tt-collapse]')) {
        var ex = !!e.target.closest('[data-tt-expand]');
        tree.querySelectorAll('[data-tt-item]').forEach(function (li2) {
          if (li2.querySelector('.tt-list')) {
            li2.classList.toggle('is-open', ex);
            var t = li2.querySelector(':scope > .tt-row [data-tt-toggle]');
            if (t) t.setAttribute('aria-expanded', String(ex));
          }
        });
      }
    });
    var search = tree.querySelector('[data-tt-search]');
    search.addEventListener('input', function () {
      var q = search.value.trim().toLowerCase().replace(/ё/g, 'е');
      var items = Array.prototype.slice.call(tree.querySelectorAll('[data-tt-item]'));
      items.forEach(function (li) {
        var name = li.querySelector(':scope > .tt-row .tt-name');
        if (!name.dataset.orig) name.dataset.orig = name.textContent;
        name.textContent = name.dataset.orig;
        li.classList.remove('is-filtered-out');
      });
      if (!q) return;
      items.reverse().forEach(function (li) {
        var name = li.querySelector(':scope > .tt-row .tt-name');
        var txt = name.dataset.orig;
        var i = txt.toLowerCase().replace(/ё/g, 'е').indexOf(q);
        var childVisible = li.querySelector('.tt-list > .tt-item:not(.is-filtered-out)');
        if (i > -1) name.innerHTML = txt.slice(0, i) + '<mark>' + txt.slice(i, i + q.length) + '</mark>' + txt.slice(i + q.length);
        if (i === -1 && !childVisible) li.classList.add('is-filtered-out');
        else if (li.querySelector('.tt-list')) {
          li.classList.add('is-open');
          var t = li.querySelector(':scope > .tt-row [data-tt-toggle]');
          if (t) t.setAttribute('aria-expanded', 'true');
        }
      });
    });
    refresh();
  }
  });
  });
})();
