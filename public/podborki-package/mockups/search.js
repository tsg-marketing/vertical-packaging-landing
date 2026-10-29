(function () {
  var roots = document.querySelectorAll('[data-suggest]');
  if (!roots.length) return;

  var RECENT_KEY = 'edukursy_recent_search';
  var EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,.`";
  var RU = 'йцукенгшщзхъфывапролджэячсмитьбюё';

  function norm(s) {
    return String(s || '').toLowerCase().replace(/ё/g, 'е').replace(/\s+/g, ' ').trim();
  }
  function swapLayout(s) {
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var ch = s[i].toLowerCase();
      var a = EN.indexOf(ch);
      var b = RU.indexOf(ch);
      out += a > -1 ? RU[a] : b > -1 ? EN[b] : ch;
    }
    return out;
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function highlight(text, q) {
    var t = String(text || '');
    var nt = norm(t);
    var words = norm(q).split(' ').filter(Boolean).sort(function (a, b) { return b.length - a.length; });
    var marks = [];
    words.forEach(function (w) {
      var from = 0, i;
      while ((i = nt.indexOf(w, from)) > -1) {
        marks.push([i, i + w.length]);
        from = i + w.length;
      }
    });
    if (!marks.length) return esc(t);
    marks.sort(function (a, b) { return a[0] - b[0]; });
    var res = '', pos = 0;
    marks.forEach(function (m) {
      if (m[0] < pos) return;
      res += esc(t.slice(pos, m[0])) + '<mark>' + esc(t.slice(m[0], m[1])) + '</mark>';
      pos = m[1];
    });
    return res + esc(t.slice(pos));
  }
  function rub(n) {
    return n == null ? '' : String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0') + '\u00a0₽';
  }
  function plural(n, f) {
    var m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return f[0];
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return f[1];
    return f[2];
  }
  function readRecent() {
    try {
      var v = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
      return Array.isArray(v) ? v.slice(0, 5) : [];
    } catch (e) {
      return [];
    }
  }
  function saveRecent(q) {
    q = String(q || '').trim();
    if (q.length < 2) return;
    var list = readRecent().filter(function (x) { return norm(x) !== norm(q); });
    list.unshift(q);
    try {
      localStorage.setItem(RECENT_KEY, JSON.stringify(list.slice(0, 5)));
    } catch (e) {}
  }

  /* Демо-режим (только макет): data-suggest-demo = id <script type="application/json"> или URL JSON-файла.
     На Django атрибута нет — идёт запрос к data-suggest-url. */
  var demoCache = null;
  function demoSearch(url, q) {
    if (!demoCache) {
      var inline = document.getElementById(url);
      if (inline) demoCache = JSON.parse(inline.textContent);
    }
    var load = demoCache
      ? Promise.resolve(demoCache)
      : fetch(url).then(function (r) { return r.json(); }).then(function (d) { demoCache = d; return d; });
    return load.then(function (d) {
      function run(query) {
        var words = norm(query).split(' ').filter(Boolean);
        function score(name) {
          var n = norm(name);
          for (var i = 0; i < words.length; i++) if (n.indexOf(words[i]) === -1) return -1;
          if (n.indexOf(words[0]) === 0) return 0;
          if ((' ' + n).indexOf(' ' + words[0]) > -1) return 1;
          return 2;
        }
        function pick(list, limit) {
          var hit = [];
          list.forEach(function (x) {
            var s = score(x.name);
            if (s > -1) hit.push({ s: s, x: x });
          });
          hit.sort(function (a, b) { return a.s - b.s || a.x.name.length - b.x.name.length; });
          return { items: hit.slice(0, limit).map(function (h) { return h.x; }), total: hit.length };
        }
        var p = pick(d.professions, 4);
        var c = pick(d.courses, 6);
        return { query: query, professions: p.items, courses: c.items, total_professions: p.total, total_courses: c.total };
      }
      var res = run(q);
      if (!res.professions.length && !res.courses.length) {
        var alt = swapLayout(q);
        if (alt !== q) {
          var res2 = run(alt);
          if (res2.professions.length || res2.courses.length) {
            res2.corrected = alt;
            return res2;
          }
        }
      }
      res.popular = d.popular;
      return res;
    });
  }

  for (var r = 0; r < roots.length; r++) init(roots[r]);

  function init(root) {
    var input = root.querySelector('[data-suggest-input]');
    var panel = root.querySelector('[data-suggest-panel]');
    var clearBtn = root.querySelector('[data-suggest-clear]');
    var form = input.form;
    var endpoint = root.getAttribute('data-suggest-url');
    var demo = root.getAttribute('data-suggest-demo');
    var searchUrl = (form && form.getAttribute('action')) || '/search/';
    var minChars = Number(root.getAttribute('data-suggest-min') || 2);
    var popular = [];
    try {
      popular = JSON.parse(root.getAttribute('data-suggest-popular') || '[]');
    } catch (e) {}

    var timer = null;
    var controller = null;
    var active = -1;
    var lastQuery = null;
    var cache = {};

    function options() {
      return panel.querySelectorAll('[role="option"]');
    }
    function setActive(i) {
      var opts = options();
      if (!opts.length) return;
      if (i < 0) i = opts.length - 1;
      if (i >= opts.length) i = 0;
      for (var k = 0; k < opts.length; k++) opts[k].classList.toggle('is-active', k === i);
      active = i;
      input.setAttribute('aria-activedescendant', opts[i].id);
      opts[i].scrollIntoView({ block: 'nearest' });
    }
    function open() {
      panel.hidden = false;
      root.classList.add('is-open');
      input.setAttribute('aria-expanded', 'true');
    }
    function close() {
      panel.hidden = true;
      root.classList.remove('is-open');
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
      active = -1;
    }
    function allUrl(q) {
      return searchUrl + '?q=' + encodeURIComponent(q);
    }
    var uid = 0;
    function optId() {
      uid += 1;
      return input.id + '-opt-' + uid;
    }

    function chip(text, kind) {
      return '<li><a href="' + esc(allUrl(text)) + '" class="suggest__chip" role="option" id="' + optId() + '" data-fill="' + esc(text) + '">' +
        (kind === 'recent'
          ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/></svg>'
          : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/></svg>') +
        esc(text) + '</a></li>';
    }

    function renderStart() {
      var recent = readRecent();
      var html = '';
      if (recent.length) {
        html += '<div class="suggest__group"><div class="suggest__head"><span>Вы искали</span><button type="button" class="suggest__link" data-suggest-forget>Очистить</button></div><ul class="suggest__chips">' +
          recent.map(function (x) { return chip(x, 'recent'); }).join('') + '</ul></div>';
      }
      if (popular.length) {
        html += '<div class="suggest__group"><div class="suggest__head"><span>Часто ищут</span></div><ul class="suggest__chips">' +
          popular.map(function (x) { return chip(x, 'popular'); }).join('') + '</ul></div>';
      }
      if (!html) return close();
      panel.innerHTML = html;
      active = -1;
      open();
    }

    function renderLoading() {
      if (panel.hidden || !panel.querySelector('.suggest__group--results')) {
        panel.innerHTML = '<div class="suggest__state"><span class="suggest__spinner" aria-hidden="true"></span>Ищем…</div>';
        open();
      }
      root.classList.add('is-loading');
    }

    function renderResults(q, data) {
      root.classList.remove('is-loading');
      var shownQ = data.corrected || q;
      var html = '';
      if (data.corrected) {
        html += '<p class="suggest__fix">Показаны результаты по запросу «<strong>' + esc(data.corrected) + '</strong>»</p>';
      }
      if (data.professions && data.professions.length) {
        html += '<div class="suggest__group suggest__group--results"><div class="suggest__head"><span>Профессии</span>' +
          (data.total_professions > data.professions.length ? '<span class="suggest__total">' + data.total_professions + '</span>' : '') +
          '</div><ul class="suggest__list">';
        data.professions.forEach(function (p) {
          html += '<li><a href="' + esc(p.url) + '" class="suggest__item" role="option" id="' + optId() + '">' +
            (p.image ? '<img src="' + esc(p.image) + '" alt="" class="suggest__thumb suggest__thumb--round" width="40" height="40" loading="lazy">' : '<span class="suggest__thumb suggest__thumb--round suggest__thumb--empty" aria-hidden="true">' + esc(p.name.charAt(0)) + '</span>') +
            '<span class="suggest__text"><span class="suggest__name">' + highlight(p.name, shownQ) + '</span>' +
            '<span class="suggest__meta">' + p.courses_count + ' ' + plural(p.courses_count, ['курс', 'курса', 'курсов']) + (p.min_price_month ? ' · от ' + rub(p.min_price_month) + '/мес' : '') + '</span></span>' +
            '<span class="suggest__tag">Профессия</span></a></li>';
        });
        html += '</ul></div>';
      }
      if (data.courses && data.courses.length) {
        html += '<div class="suggest__group suggest__group--results"><div class="suggest__head"><span>Курсы</span>' +
          (data.total_courses > data.courses.length ? '<span class="suggest__total">' + data.total_courses + '</span>' : '') +
          '</div><ul class="suggest__list">';
        data.courses.forEach(function (c) {
          html += '<li><a href="' + esc(c.url) + '" class="suggest__item" role="option" id="' + optId() + '">' +
            (c.school_logo ? '<img src="' + esc(c.school_logo) + '" alt="" class="suggest__thumb" width="40" height="40" loading="lazy">' : '<span class="suggest__thumb suggest__thumb--empty" aria-hidden="true">' + esc((c.school || '?').charAt(0)) + '</span>') +
            '<span class="suggest__text"><span class="suggest__name">' + highlight(c.name, shownQ) + '</span>' +
            '<span class="suggest__meta">' + esc(c.school) + (c.duration ? ' · ' + esc(c.duration) : '') + '</span></span>' +
            '<span class="suggest__price">' + (c.price_month ? rub(c.price_month) + '<small>/мес</small>' : rub(c.price)) + '</span></a></li>';
        });
        html += '</ul></div>';
      }
      if (!html || (!data.professions.length && !data.courses.length)) {
        html = '<div class="suggest__empty"><p class="suggest__empty-title">По запросу «' + esc(q) + '» ничего не нашли</p><p>Проверьте написание или попробуйте другое слово.</p>' +
          ((data.popular || popular).length ? '<ul class="suggest__chips">' + (data.popular || popular).map(function (x) { return chip(x, 'popular'); }).join('') + '</ul>' : '') + '</div>';
      } else {
        var total = (data.total_professions || 0) + (data.total_courses || 0);
        html += '<a href="' + esc(allUrl(shownQ)) + '" class="suggest__all" role="option" id="' + optId() + '">Все результаты по запросу «' + esc(shownQ) + '»' + (total ? ' <span>' + total + '</span>' : '') +
          '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg></a>';
      }
      panel.innerHTML = html;
      active = -1;
      input.removeAttribute('aria-activedescendant');
      open();
      var live = root.querySelector('[data-suggest-live]');
      if (live) {
        var n = (data.professions || []).length + (data.courses || []).length;
        live.textContent = n ? 'Найдено подсказок: ' + n : 'Ничего не найдено';
      }
    }

    function fetchData(q) {
      var key = norm(q);
      if (cache[key]) return Promise.resolve(cache[key]);
      var p;
      if (demo) {
        p = demoSearch(demo, q);
      } else {
        if (controller) controller.abort();
        controller = 'AbortController' in window ? new AbortController() : null;
        p = fetch(endpoint + (endpoint.indexOf('?') > -1 ? '&' : '?') + 'q=' + encodeURIComponent(q), {
          headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
          signal: controller ? controller.signal : undefined
        }).then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        });
      }
      return p.then(function (d) {
        cache[key] = d;
        return d;
      });
    }

    function onInput() {
      var q = input.value.trim();
      root.classList.toggle('has-value', input.value.length > 0);
      clearTimeout(timer);
      if (q.length < minChars) {
        lastQuery = null;
        root.classList.remove('is-loading');
        if (q.length === 0) renderStart();
        else {
          panel.innerHTML = '<div class="suggest__state">Введите ещё ' + (minChars - q.length) + ' ' + plural(minChars - q.length, ['букву', 'буквы', 'букв']) + '</div>';
          open();
        }
        return;
      }
      if (norm(q) === lastQuery) return;
      renderLoading();
      timer = setTimeout(function () {
        lastQuery = norm(q);
        fetchData(q).then(function (d) {
          if (norm(input.value.trim()) !== norm(q)) return;
          renderResults(q, d);
        }).catch(function (err) {
          if (err && err.name === 'AbortError') return;
          root.classList.remove('is-loading');
          panel.innerHTML = '<div class="suggest__state">Не удалось загрузить подсказки. Нажмите «Найти», чтобы увидеть все результаты.</div>';
          open();
        });
      }, demo ? 120 : 220);
    }

    input.addEventListener('input', onInput);
    input.addEventListener('focus', function () {
      if (!input.value.trim()) renderStart();
      else if (panel.innerHTML) open();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (panel.hidden) onInput();
        setActive(active + 1);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActive(active - 1);
      } else if (e.key === 'Escape') {
        if (!panel.hidden) {
          e.preventDefault();
          close();
        } else if (input.value) {
          input.value = '';
          onInput();
        }
      } else if (e.key === 'Enter' && active > -1) {
        var opt = options()[active];
        if (opt) {
          e.preventDefault();
          saveRecent(opt.getAttribute('data-fill') || input.value);
          window.location.href = opt.getAttribute('href');
        }
      }
    });

    panel.addEventListener('mousedown', function (e) {
      if (e.target.closest('a, button')) e.preventDefault();
    });
    panel.addEventListener('click', function (e) {
      if (e.target.closest('[data-suggest-forget]')) {
        try {
          localStorage.removeItem(RECENT_KEY);
        } catch (err) {}
        renderStart();
        input.focus();
        return;
      }
      var a = e.target.closest('a');
      if (a) saveRecent(a.getAttribute('data-fill') || input.value);
    });
    panel.addEventListener('mousemove', function (e) {
      var opt = e.target.closest('[role="option"]');
      if (!opt) return;
      var opts = options();
      for (var i = 0; i < opts.length; i++) if (opts[i] === opt && i !== active) setActive(i);
    });

    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        input.value = '';
        input.focus();
        onInput();
      });
    }
    if (form) {
      form.addEventListener('submit', function (e) {
        var q = input.value.trim();
        if (!q) {
          e.preventDefault();
          input.focus();
          return;
        }
        saveRecent(q);
      });
    }
    document.addEventListener('click', function (e) {
      if (!root.contains(e.target)) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && document.activeElement && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
        e.preventDefault();
        input.focus();
      }
    });

    root.classList.toggle('has-value', input.value.length > 0);
  }
})();
