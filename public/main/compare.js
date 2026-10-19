(function () {
  var KEY = 'edukursy_compare';
  var MAX = 4;
  var body = document.body;
  var compareUrl = body.getAttribute('data-compare-url') || '/compare/';

  var ICON_SWAP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/></svg>';
  var ICON_X = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>';
  var ICON_UP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m18 15-6-6-6 6"/></svg>';

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(v) ? v.slice(0, MAX) : [];
    } catch (e) {
      return [];
    }
  }
  function syncCookie(list) {
    var ids = list.map(function (c) { return c.id; }).join(',');
    document.cookie = KEY + '=' + encodeURIComponent(ids) + ';path=/;max-age=' + (ids ? 2592000 : 0) + ';SameSite=Lax';
  }
  function write(list) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
    } catch (e) {}
    syncCookie(list);
    render();
  }
  function has(list, id) {
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return true;
    return false;
  }
  function esc(s) {
    return String(s || '').replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function plural(n) {
    var m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return 'курс';
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return 'курса';
    return 'курсов';
  }
  function urlFor(list) {
    return compareUrl + (list.length ? '?courses=' + list.map(function (c) { return c.id; }).join(',') : '');
  }

  var state = document.getElementById('compare-state');
  if (state) {
    try {
      var fromServer = JSON.parse(state.textContent);
      if (Array.isArray(fromServer)) localStorage.setItem(KEY, JSON.stringify(fromServer.slice(0, MAX)));
    } catch (e) {}
  }

  var toastEl, toastTimer;
  function toast(text, linkText) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'cmp-toast';
      toastEl.setAttribute('role', 'status');
      toastEl.setAttribute('aria-live', 'polite');
      body.appendChild(toastEl);
    }
    toastEl.innerHTML = esc(text) + (linkText ? ' <a href="' + esc(urlFor(read())) + '">' + esc(linkText) + '</a>' : '');
    toastEl.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('is-visible'); }, 3200);
  }

  var tray = null;
  var collapsed = false;
  var hideTray = body.hasAttribute('data-compare-hide-tray') || !!state;

  function buildTray() {
    tray = document.createElement('aside');
    tray.className = 'cmp-tray';
    tray.setAttribute('aria-label', 'Курсы для сравнения');
    if (document.querySelector('.sticky-cta')) tray.classList.add('cmp-tray--raised');
    body.appendChild(tray);
    tray.addEventListener('click', function (e) {
      var rm = e.target.closest('[data-compare-remove]');
      if (rm) {
        var id = rm.getAttribute('data-compare-remove');
        write(read().filter(function (c) { return c.id !== id; }));
        return;
      }
      if (e.target.closest('[data-compare-clear]')) {
        write([]);
        return;
      }
      if (e.target.closest('[data-compare-collapse]')) {
        collapsed = !collapsed;
        render();
      }
    });
  }

  function renderTray(list) {
    if (hideTray) return;
    if (!tray) buildTray();
    var n = list.length;
    body.classList.toggle('has-cmp-tray', n > 0);
    tray.hidden = n === 0;
    tray.classList.toggle('is-collapsed', collapsed);
    if (!n) return;

    var chips = '';
    for (var i = 0; i < MAX; i++) {
      var c = list[i];
      chips += c
        ? '<li class="cmp-tray__chip"><span class="cmp-tray__chip-text"><span class="cmp-tray__chip-name">' + esc(c.name) + '</span><span class="cmp-tray__chip-school">' + esc(c.school) + '</span></span><button type="button" class="cmp-tray__remove" data-compare-remove="' + esc(c.id) + '" aria-label="Убрать из сравнения: ' + esc(c.name) + '">' + ICON_X + '</button></li>'
        : '<li class="cmp-tray__chip cmp-tray__chip--empty" aria-hidden="true">+ курс</li>';
    }
    var ready = n >= 2;
    tray.innerHTML =
      '<div class="cmp-tray__inner">' +
        '<button type="button" class="cmp-tray__head" data-compare-collapse aria-expanded="' + String(!collapsed) + '">' +
          '<span class="cmp-tray__icon">' + ICON_SWAP + '</span>' +
          '<span class="cmp-tray__title">Сравнение <span class="cmp-tray__count">' + n + ' из ' + MAX + '</span></span>' +
          '<span class="cmp-tray__chevron">' + ICON_UP + '</span>' +
        '</button>' +
        '<ul class="cmp-tray__list">' + chips + '</ul>' +
        '<div class="cmp-tray__actions">' +
          '<button type="button" class="cmp-tray__clear" data-compare-clear>Очистить</button>' +
          (ready
            ? '<a href="' + esc(urlFor(list)) + '" class="btn btn--primary cmp-tray__go">Сравнить ' + n + ' ' + plural(n) + '</a>'
            : '<span class="btn cmp-tray__go cmp-tray__go--disabled" aria-disabled="true">Добавьте ещё 1 курс</span>') +
        '</div>' +
      '</div>';
  }

  function renderNav(n) {
    var links = document.querySelectorAll('.main-nav a[href$="/compare/"], .main-nav a[href$="compare/index.html"]');
    for (var i = 0; i < links.length; i++) {
      var badge = links[i].querySelector('.nav-count');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'nav-count';
        links[i].appendChild(badge);
      }
      badge.textContent = n;
      badge.hidden = n === 0;
      badge.setAttribute('aria-label', 'выбрано: ' + n);
    }
  }

  function render() {
    var list = read();
    var btns = document.querySelectorAll('[data-compare-id]');
    for (var i = 0; i < btns.length; i++) {
      var on = has(list, btns[i].getAttribute('data-compare-id'));
      btns[i].setAttribute('aria-pressed', String(on));
      btns[i].classList.toggle('is-active', on);
    }
    var links = document.querySelectorAll('[data-compare-link]');
    for (var j = 0; j < links.length; j++) {
      links[j].hidden = list.length === 0;
      links[j].setAttribute('href', urlFor(list));
      var cnt = links[j].querySelector('[data-compare-count]');
      if (cnt) cnt.textContent = list.length;
    }
    renderNav(list.length);
    renderTray(list);
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-compare-id]');
    if (!btn) return;
    e.preventDefault();
    var id = btn.getAttribute('data-compare-id');
    var list = read();
    if (has(list, id)) {
      write(list.filter(function (c) { return c.id !== id; }));
      return;
    }
    if (list.length >= MAX) {
      toast('Можно сравнить не больше ' + MAX + ' курсов. Уберите один из списка.', 'Открыть сравнение');
      return;
    }
    list.push({
      id: id,
      name: btn.getAttribute('data-compare-name') || id,
      school: btn.getAttribute('data-compare-school') || ''
    });
    collapsed = false;
    write(list);
    if (list.length === 1) toast('Курс добавлен. Выберите ещё хотя бы один для сравнения.');
  });

  syncCookie(read());

  window.addEventListener('storage', function (e) {
    if (e.key === KEY) render();
  });

  render();
})();
