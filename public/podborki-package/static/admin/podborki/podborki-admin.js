/* Список подборок: перетаскивание и стрелки ↑↓ внутри одного родителя, сохранение сразу. */
(function () {
  function ready(fn) { if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function () {
    var cfg = document.getElementById('pdb-reorder');
    var table = document.getElementById('result_list');
    if (!cfg || !table) return;
    var tbody = table.tBodies[0];

    var toastEl;
    function toast(text, isError) {
      if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'pdb-toast'; document.body.appendChild(toastEl); }
      toastEl.textContent = text;
      toastEl.classList.toggle('is-error', !!isError);
      toastEl.classList.add('is-visible');
      clearTimeout(toastEl._t);
      toastEl._t = setTimeout(function () { toastEl.classList.remove('is-visible'); }, 2200);
    }
    function info(tr) {
      var h = tr.querySelector('.pdb-drag');
      return h ? { id: h.dataset.id, parent: h.dataset.parent, level: +h.dataset.level } : null;
    }
    function rows() { return Array.prototype.slice.call(tbody.rows); }
    function block(tr) {
      var lvl = info(tr).level, out = [tr], r = tr.nextElementSibling;
      while (r && info(r) && info(r).level > lvl) { out.push(r); r = r.nextElementSibling; }
      return out;
    }
    function siblings(tr) {
      var i = info(tr);
      return rows().filter(function (r) { var x = info(r); return x && x.parent === i.parent && x.level === i.level; });
    }
    function save(tr) {
      var i = info(tr);
      var ids = siblings(tr).map(function (r) { return +info(r).id; });
      fetch(cfg.dataset.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': cfg.dataset.csrf },
        body: JSON.stringify({ parent: i.parent ? +i.parent : null, ids: ids }),
        credentials: 'same-origin'
      }).then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.error || 'Ошибка'); }); })
        .then(function () { toast('Порядок сохранён'); })
        .catch(function (e) { toast(e.message + ' — обновите страницу', true); });
    }
    function moveBlock(tr, target, before) {
      var mine = block(tr);
      if (before) mine.forEach(function (r) { tbody.insertBefore(r, target); });
      else {
        var t = block(target), ref = t[t.length - 1].nextElementSibling;
        mine.forEach(function (r) { tbody.insertBefore(r, ref); });
      }
      rows().forEach(function (r, k) { r.classList.remove('row1', 'row2'); r.classList.add(k % 2 ? 'row2' : 'row1'); });
      save(tr);
    }

    table.addEventListener('click', function (e) {
      var b = e.target.closest('.pdb-move');
      if (!b) return;
      e.preventDefault();
      var tr = b.closest('tr'), sib = siblings(tr), k = sib.indexOf(tr), dir = +b.dataset.dir, target = sib[k + dir];
      if (target) moveBlock(tr, target, dir < 0);
    });

    var drag = null;
    rows().forEach(function (r) { if (info(r)) r.setAttribute('draggable', 'true'); });
    tbody.addEventListener('dragstart', function (e) {
      drag = e.target.closest('tr');
      if (!drag || !info(drag)) { drag = null; return; }
      drag.classList.add('pdb-dragging');
      e.dataTransfer.effectAllowed = 'move';
      try { e.dataTransfer.setData('text/plain', info(drag).id); } catch (err) {}
    });
    tbody.addEventListener('dragover', function (e) {
      var over = e.target.closest('tr');
      if (!drag || !over || over === drag || siblings(drag).indexOf(over) === -1) return;
      e.preventDefault();
      rows().forEach(function (r) { r.classList.remove('pdb-drop-before', 'pdb-drop-after'); });
      var rect = over.getBoundingClientRect();
      over.classList.add(e.clientY < rect.top + rect.height / 2 ? 'pdb-drop-before' : 'pdb-drop-after');
    });
    tbody.addEventListener('drop', function (e) {
      var over = e.target.closest('tr');
      if (!drag || !over || siblings(drag).indexOf(over) === -1) return;
      e.preventDefault();
      moveBlock(drag, over, over.classList.contains('pdb-drop-before'));
    });
    tbody.addEventListener('dragend', function () {
      rows().forEach(function (r) { r.classList.remove('pdb-dragging', 'pdb-drop-before', 'pdb-drop-after'); });
      drag = null;
    });
  });
})();
