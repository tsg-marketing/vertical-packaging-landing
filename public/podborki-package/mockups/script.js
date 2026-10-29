(function () {
  var burger = document.querySelector('.burger');
  var nav = document.getElementById('main-nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = burger.getAttribute('aria-expanded') === 'true';
      burger.setAttribute('aria-expanded', String(!open));
      burger.setAttribute('aria-label', open ? 'Открыть меню' : 'Закрыть меню');
      nav.classList.toggle('is-open', !open);
    });
  }

  var range = document.getElementById('pk-budget');
  var out = document.getElementById('pk-budget-out');
  if (range && out) {
    var fmt = function () {
      out.textContent = Number(range.value).toLocaleString('ru-RU').replace(/\u00A0/g, ' ') + ' ₽';
    };
    range.addEventListener('input', fmt);
    fmt();
  }

  var sidebar = document.getElementById('filters');
  var openBtn = document.querySelector('.filters-open');
  var closeBtn = document.querySelector('.filters-close');
  if (sidebar && openBtn) {
    var setFilters = function (open) {
      sidebar.classList.toggle('is-open', open);
      document.body.classList.toggle('filters-locked', open);
      openBtn.setAttribute('aria-expanded', String(open));
      if (open) {
        var first = sidebar.querySelector('input, button, a');
        if (first) first.focus();
      } else {
        openBtn.focus();
      }
    };
    openBtn.setAttribute('aria-controls', 'filters');
    openBtn.setAttribute('aria-expanded', 'false');
    openBtn.addEventListener('click', function (e) {
      e.preventDefault();
      setFilters(true);
    });
    if (closeBtn) {
      closeBtn.addEventListener('click', function (e) {
        e.preventDefault();
        setFilters(false);
      });
    }
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && sidebar.classList.contains('is-open')) setFilters(false);
    });
  }

  var sortSelect = document.getElementById('sort');
  if (sortSelect && sortSelect.form) {
    sortSelect.addEventListener('change', function () {
      sortSelect.form.submit();
    });
  }

  var buttons = document.querySelectorAll('.faq-item__btn');
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].addEventListener('click', function () {
      var expanded = this.getAttribute('aria-expanded') === 'true';
      var panel = document.getElementById(this.getAttribute('aria-controls'));
      this.setAttribute('aria-expanded', String(!expanded));
      if (panel) panel.hidden = expanded;
    });
  }
})();