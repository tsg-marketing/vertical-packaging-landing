(function () {
  var drops = document.querySelectorAll('[data-nav-drop]');
  if (!drops.length) return;

  var desktop = window.matchMedia('(min-width: 1024px) and (hover: hover)');

  function isDesktop() {
    return desktop.matches;
  }

  for (var d = 0; d < drops.length; d++) init(drops[d]);

  function init(drop) {
    var btn = drop.querySelector('[data-nav-drop-btn]');
    var menu = drop.querySelector('[data-nav-drop-menu]');
    var items = drop.querySelectorAll('[data-tnav-item]');
    var closeTimer = null;
    var hoverTimer = null;

    function setActiveItem(item) {
      for (var i = 0; i < items.length; i++) {
        var on = items[i] === item;
        items[i].classList.toggle('is-hover', on);
        var t = items[i].querySelector('.tnav__toggle');
        if (t) t.setAttribute('aria-expanded', String(on && items[i].classList.contains('has-children')));
      }
    }

    function firstActive() {
      var cur = drop.querySelector('.tnav__item1.is-current.has-children') || drop.querySelector('.tnav__item1.has-children');
      return cur;
    }

    function open() {
      clearTimeout(closeTimer);
      if (drop.classList.contains('is-open')) return;
      closeOthers(drop);
      drop.classList.add('is-open');
      btn.setAttribute('aria-expanded', 'true');
      if (isDesktop() && !drop.querySelector('.tnav__item1.is-hover')) setActiveItem(firstActive());
    }

    function close() {
      drop.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
      if (!isDesktop()) setActiveItem(null);
    }

    drop._close = close;

    btn.addEventListener('click', function (e) {
      if (isDesktop()) return;
      e.preventDefault();
      if (drop.classList.contains('is-open')) close();
      else open();
    });

    drop.addEventListener('mouseenter', function () {
      if (isDesktop()) open();
    });
    drop.addEventListener('mouseleave', function () {
      if (!isDesktop()) return;
      clearTimeout(closeTimer);
      closeTimer = setTimeout(close, 180);
    });

    for (var i = 0; i < items.length; i++) {
      (function (item) {
        item.addEventListener('mouseenter', function () {
          if (!isDesktop()) return;
          clearTimeout(hoverTimer);
          if (!item.classList.contains('has-children')) return;
          hoverTimer = setTimeout(function () { setActiveItem(item); }, 90);
        });
        var toggle = item.querySelector('.tnav__toggle');
        if (toggle) {
          toggle.addEventListener('click', function (e) {
            e.preventDefault();
            var opened = item.classList.contains('is-hover');
            setActiveItem(opened ? null : item);
          });
        }
        var sub2 = item.querySelectorAll('.tnav__item2.has-children > .tnav__link2');
        for (var k = 0; k < sub2.length; k++) {
          sub2[k].addEventListener('focus', function () {
            if (isDesktop()) setActiveItem(item);
          });
        }
      })(items[i]);
    }

    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || ((e.key === 'Enter' || e.key === ' ') && !drop.classList.contains('is-open') && !isDesktop())) {
        e.preventDefault();
        open();
        var first = menu.querySelector('.tnav__link1');
        if (first) first.focus();
      }
    });

    menu.addEventListener('focusin', function (e) {
      var item = e.target.closest('[data-tnav-item]');
      if (item && isDesktop() && item.classList.contains('has-children')) setActiveItem(item);
      open();
    });

    menu.addEventListener('keydown', function (e) {
      var links = Array.prototype.slice.call(menu.querySelectorAll('.tnav__link1'));
      var idx = links.indexOf(document.activeElement);
      if (e.key === 'Escape') {
        e.preventDefault();
        close();
        btn.focus();
      } else if (idx > -1 && e.key === 'ArrowDown') {
        e.preventDefault();
        links[(idx + 1) % links.length].focus();
      } else if (idx > -1 && e.key === 'ArrowUp') {
        e.preventDefault();
        links[(idx - 1 + links.length) % links.length].focus();
      } else if (idx > -1 && e.key === 'ArrowRight') {
        var panel = links[idx].parentNode.querySelector('.tnav__panel a');
        if (panel) {
          e.preventDefault();
          setActiveItem(links[idx].parentNode);
          panel.focus();
        }
      } else if (e.key === 'ArrowLeft' && idx === -1) {
        var it = document.activeElement.closest('[data-tnav-item]');
        if (it) {
          e.preventDefault();
          it.querySelector('.tnav__link1').focus();
        }
      }
    });

    drop.addEventListener('focusout', function (e) {
      if (!drop.contains(e.relatedTarget)) close();
    });
  }

  function closeOthers(except) {
    for (var i = 0; i < drops.length; i++) if (drops[i] !== except && drops[i]._close) drops[i]._close();
  }

  document.addEventListener('click', function (e) {
    for (var i = 0; i < drops.length; i++) {
      if (!drops[i].contains(e.target) && drops[i]._close) drops[i]._close();
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeOthers(null);
  });
})();
