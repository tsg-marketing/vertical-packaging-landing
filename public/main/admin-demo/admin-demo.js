(function () {
  function show(id) {
    var tabs = document.querySelectorAll('[data-tab]');
    var screens = document.querySelectorAll('[data-screen]');
    for (var i = 0; i < tabs.length; i++) tabs[i].classList.toggle('is-active', tabs[i].getAttribute('data-tab') === id);
    for (var j = 0; j < screens.length; j++) screens[j].classList.toggle('is-active', screens[j].getAttribute('data-screen') === id);
    window.scrollTo(0, 0);
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tab], [data-tab-link]');
    if (!t) return;
    e.preventDefault();
    var id = t.getAttribute('data-tab') || t.getAttribute('data-tab-link');
    history.replaceState(null, '', '#' + id);
    show(id);
  });
  if (location.hash && document.querySelector('[data-screen="' + location.hash.slice(1) + '"]')) show(location.hash.slice(1));

  /* Список: свернуть/развернуть ветку */
  var table = document.querySelector('[data-sortable-tree]');
  if (table) {
    var rows = function () { return Array.prototype.slice.call(table.querySelectorAll('tbody tr')); };
    table.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-tree-toggle]');
      if (btn) {
        var row = btn.closest('tr');
        var open = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!open));
        var path = row.getAttribute('data-path') + '/';
        rows().forEach(function (r) {
          if (r.getAttribute('data-path').indexOf(path) === 0) {
            if (open) r.classList.add('is-hidden-tree');
            else {
              var parentHidden = false;
              var p = r.getAttribute('data-path');
              rows().forEach(function (x) {
                var xp = x.getAttribute('data-path');
                var t = x.querySelector('[data-tree-toggle]');
                if (t && t.getAttribute('aria-expanded') === 'false' && p.indexOf(xp + '/') === 0 && xp + '/' !== path) parentHidden = true;
              });
              if (!parentHidden) r.classList.remove('is-hidden-tree');
            }
          }
        });
        return;
      }
      var mv = e.target.closest('.adm-move');
      if (mv) moveRow(mv.closest('tr'), mv.title === 'Выше' ? -1 : 1);
    });

    function block(row) {
      var path = row.getAttribute('data-path') + '/';
      var list = [row];
      var r = row.nextElementSibling;
      while (r && r.getAttribute('data-path').indexOf(path) === 0) { list.push(r); r = r.nextElementSibling; }
      return list;
    }
    function siblings(row) {
      var lvl = row.getAttribute('data-level');
      var parent = row.getAttribute('data-path').split('/').slice(0, -1).join('/');
      return rows().filter(function (r) {
        return r.getAttribute('data-level') === lvl && r.getAttribute('data-path').split('/').slice(0, -1).join('/') === parent;
      });
    }
    function moveRow(row, dir) {
      var sib = siblings(row);
      var i = sib.indexOf(row);
      var target = sib[i + dir];
      if (!target) return;
      var mine = block(row);
      var tbody = row.parentNode;
      if (dir < 0) mine.forEach(function (r) { tbody.insertBefore(r, target); });
      else {
        var after = block(target);
        var ref = after[after.length - 1].nextElementSibling;
        mine.forEach(function (r) { tbody.insertBefore(r, ref); });
      }
      flash();
    }
    function flash() {
      var msg = document.querySelector('#list .adm-msg--ok');
      if (msg) { msg.style.transition = 'none'; msg.style.background = '#bfeebf'; setTimeout(function () { msg.style.transition = 'background 1s'; msg.style.background = ''; }, 60); }
    }

    var dragRow = null;
    table.addEventListener('dragstart', function (e) {
      dragRow = e.target.closest('tr');
      if (!dragRow) return;
      dragRow.classList.add('is-dragging');
      e.dataTransfer.effectAllowed = 'move';
      try { e.dataTransfer.setData('text/plain', dragRow.getAttribute('data-path')); } catch (err) {}
    });
    table.addEventListener('dragover', function (e) {
      var over = e.target.closest('tr');
      if (!dragRow || !over || over === dragRow) return;
      if (siblings(dragRow).indexOf(over) === -1) return;
      e.preventDefault();
      rows().forEach(function (r) { r.classList.remove('is-drop-before', 'is-drop-after'); });
      var rect = over.getBoundingClientRect();
      over.classList.add(e.clientY < rect.top + rect.height / 2 ? 'is-drop-before' : 'is-drop-after');
    });
    table.addEventListener('drop', function (e) {
      var over = e.target.closest('tr');
      if (!dragRow || !over) return;
      e.preventDefault();
      var before = over.classList.contains('is-drop-before');
      var mine = block(dragRow);
      var tbody = over.parentNode;
      if (before) mine.forEach(function (r) { tbody.insertBefore(r, over); });
      else {
        var b = block(over);
        var ref = b[b.length - 1].nextElementSibling;
        mine.forEach(function (r) { tbody.insertBefore(r, ref); });
      }
      flash();
    });
    table.addEventListener('dragend', function () {
      rows().forEach(function (r) { r.classList.remove('is-dragging', 'is-drop-before', 'is-drop-after'); });
      dragRow = null;
    });
  }

  /* Карточка курса: дерево подборок */
  var tree = document.querySelector('[data-tag-tree]');
  if (tree) {
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
})();
