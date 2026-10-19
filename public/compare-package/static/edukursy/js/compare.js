(function () {
  var KEY = 'edukursy_compare';
  var COOKIE_LIMIT = 3800;
  var body = document.body;
  var compareUrl = body.getAttribute('data-compare-url') || '/compare/';

  var ICON_SWAP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/></svg>';
  var ICON_X = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>';
  var ICON_UP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m18 15-6-6-6 6"/></svg>';
  var ICON_LEFT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>';
  var ICON_RIGHT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>';

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(v) ? v : [];
    } catch (e) {
      return [];
    }
  }
  function syncCookie(list) {
    var ids = [];
    var len = 0;
    for (var i = 0; i < list.length; i++) {
      var part = encodeURIComponent(list[i].id);
      if (len + part.length + 3 > COOKIE_LIMIT) break;
      ids.push(list[i].id);
      len += part.length + 3;
    }
    var value = encodeURIComponent(ids.join(','));
    document.cookie = KEY + '=' + value + ';path=/;max-age=' + (value ? 2592000 : 0) + ';SameSite=Lax';
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
      if (Array.isArray(fromServer)) localStorage.setItem(KEY, JSON.stringify(fromServer));
    } catch (e) {}
  }

  var toastEl, toastTimer;
  function toast(text) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'cmp-toast';
      toastEl.setAttribute('role', 'status');
      toastEl.setAttribute('aria-live', 'polite');
      body.appendChild(toastEl);
    }
    toastEl.textContent = text;
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
      var nav = e.target.closest('[data-tray-scroll]');
      if (nav) {
        var listEl = tray.querySelector('.cmp-tray__list');
        listEl.scrollBy({ left: Number(nav.getAttribute('data-tray-scroll')) * listEl.clientWidth * 0.8, behavior: 'smooth' });
        return;
      }
      if (e.target.closest('[data-compare-collapse]')) {
        collapsed = !collapsed;
        render();
      }
    });
  }

  function updateTrayArrows() {
    if (!tray) return;
    var listEl = tray.querySelector('.cmp-tray__list');
    if (!listEl) return;
    var max = listEl.scrollWidth - listEl.clientWidth;
    tray.classList.toggle('can-left', listEl.scrollLeft > 4);
    tray.classList.toggle('can-right', listEl.scrollLeft < max - 4);
  }

  function renderTray(list, scrollToEnd) {
    if (hideTray) return;
    if (!tray) buildTray();
    var n = list.length;
    body.classList.toggle('has-cmp-tray', n > 0);
    tray.hidden = n === 0;
    tray.classList.toggle('is-collapsed', collapsed);
    if (!n) return;

    var prevList = tray.querySelector('.cmp-tray__list');
    var prevScroll = prevList ? prevList.scrollLeft : 0;

    var chips = '';
    for (var i = 0; i < n; i++) {
      var c = list[i];
      chips += '<li class="cmp-tray__chip"><span class="cmp-tray__chip-text"><span class="cmp-tray__chip-name">' + esc(c.name) + '</span><span class="cmp-tray__chip-school">' + esc(c.school) + '</span></span><button type="button" class="cmp-tray__remove" data-compare-remove="' + esc(c.id) + '" aria-label="Убрать из сравнения: ' + esc(c.name) + '">' + ICON_X + '</button></li>';
    }
    if (n < 2) chips += '<li class="cmp-tray__chip cmp-tray__chip--empty" aria-hidden="true">+ ещё курс</li>';

    var ready = n >= 2;
    tray.innerHTML =
      '<div class="cmp-tray__inner">' +
        '<button type="button" class="cmp-tray__head" data-compare-collapse aria-expanded="' + String(!collapsed) + '">' +
          '<span class="cmp-tray__icon">' + ICON_SWAP + '</span>' +
          '<span class="cmp-tray__title">Сравнение <span class="cmp-tray__count">' + n + ' ' + plural(n) + '</span></span>' +
          '<span class="cmp-tray__chevron">' + ICON_UP + '</span>' +
        '</button>' +
        '<div class="cmp-tray__rail">' +
          '<button type="button" class="cmp-tray__nav cmp-tray__nav--prev" data-tray-scroll="-1" aria-label="Прокрутить влево">' + ICON_LEFT + '</button>' +
          '<ul class="cmp-tray__list">' + chips + '</ul>' +
          '<button type="button" class="cmp-tray__nav cmp-tray__nav--next" data-tray-scroll="1" aria-label="Прокрутить вправо">' + ICON_RIGHT + '</button>' +
        '</div>' +
        '<div class="cmp-tray__actions">' +
          '<button type="button" class="cmp-tray__clear" data-compare-clear>Очистить</button>' +
          (ready
            ? '<a href="' + esc(urlFor(list)) + '" class="btn btn--primary cmp-tray__go">Сравнить ' + n + ' ' + plural(n) + '</a>'
            : '<span class="btn cmp-tray__go cmp-tray__go--disabled" aria-disabled="true">Добавьте ещё 1 курс</span>') +
        '</div>' +
      '</div>';

    var listEl = tray.querySelector('.cmp-tray__list');
    listEl.scrollLeft = scrollToEnd ? listEl.scrollWidth : prevScroll;
    listEl.addEventListener('scroll', updateTrayArrows, { passive: true });
    updateTrayArrows();
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
      badge.textContent = n > 99 ? '99+' : n;
      badge.hidden = n === 0;
      badge.setAttribute('aria-label', 'выбрано: ' + n);
    }
  }

  function render(scrollToEnd) {
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
    renderTray(list, scrollToEnd === true);
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
    list.push({
      id: id,
      name: btn.getAttribute('data-compare-name') || id,
      school: btn.getAttribute('data-compare-school') || ''
    });
    collapsed = false;
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
    } catch (err) {}
    syncCookie(list);
    render(true);
    if (list.length === 1) toast('Курс добавлен. Выберите ещё хотя бы один для сравнения.');
  });

  /* Страница сравнения: прокрутка широкой таблицы стрелками */
  var scrollBox = document.querySelector('[data-cmp-scroll]');
  if (scrollBox) {
    var prev = document.querySelector('[data-cmp-scroll-btn="-1"]');
    var next = document.querySelector('[data-cmp-scroll-btn="1"]');
    var pos = document.querySelector('[data-cmp-scroll-pos]');
    var cols = scrollBox.querySelectorAll('thead .cmp-col');
    var update = function () {
      var max = scrollBox.scrollWidth - scrollBox.clientWidth;
      var nav = scrollBox.parentNode.querySelector('.cmp-nav');
      if (nav) nav.hidden = max <= 4;
      if (prev) prev.disabled = scrollBox.scrollLeft <= 4;
      if (next) next.disabled = scrollBox.scrollLeft >= max - 4;
      if (pos && cols.length) {
        var box = scrollBox.getBoundingClientRect();
        var corner = scrollBox.querySelector('.cmp-corner');
        var stickyRight = corner ? corner.getBoundingClientRect().right : box.left;
        var first = 0, last = 0;
        for (var i = 0; i < cols.length; i++) {
          var r = cols[i].getBoundingClientRect();
          var visible = r.left >= stickyRight - 2 && r.right <= box.right + 2;
          if (visible) {
            if (!first) first = i + 1;
            last = i + 1;
          }
        }
        pos.textContent = first ? first + (last > first ? '–' + last : '') + ' из ' + cols.length : '';
      }
    };
    var step = function (dir) {
      var colW = cols.length ? cols[0].getBoundingClientRect().width : 240;
      scrollBox.scrollBy({ left: dir * colW, behavior: 'smooth' });
    };
    if (prev) prev.addEventListener('click', function () { step(-1); });
    if (next) next.addEventListener('click', function () { step(1); });
    scrollBox.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  syncCookie(read());

  window.addEventListener('storage', function (e) {
    if (e.key === KEY) render();
  });
  window.addEventListener('resize', updateTrayArrows);

  render();
})();
