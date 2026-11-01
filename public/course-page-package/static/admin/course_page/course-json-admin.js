/* Поля extract_json / editorial_json: проверка на лету, форматирование, шаблон. */
(function () {
  function ready(fn) { if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  function strip(text) { return text.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim(); }
  function lineOf(text, pos) { return text.slice(0, pos).split('\n').length; }
  ready(function () {
    document.querySelectorAll('[data-cp-json]').forEach(function (box) {
      var ta = box.querySelector('textarea');
      var st = box.querySelector('[data-cp-status]');
      function check() {
        var raw = ta.value;
        box.classList.remove('is-ok', 'is-err');
        if (!raw.trim()) { st.textContent = 'Пусто — блоки из этого JSON не выводятся'; return null; }
        try {
          var data = JSON.parse(strip(raw));
          if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('Нужен объект { ... }');
          var keys = Object.keys(data);
          var filled = keys.filter(function (k) {
            var v = data[k];
            if (v === null || v === '') return false;
            if (Array.isArray(v)) return v.length > 0;
            if (typeof v === 'object') return Object.keys(v).some(function (x) { return v[x] !== null && v[x] !== ''; });
            return true;
          });
          var status = data.extraction_status || data.draft_status;
          st.textContent = 'JSON корректный · ключей: ' + keys.length + ', заполнено: ' + filled.length + (status ? ' · статус: ' + status : '');
          box.classList.add(status === 'failed' ? 'is-err' : 'is-ok');
          return data;
        } catch (e) {
          var m = /position (\d+)/.exec(e.message);
          st.textContent = 'Ошибка: ' + e.message + (m ? ' (строка ' + lineOf(strip(raw), +m[1]) + ')' : '');
          box.classList.add('is-err');
          return null;
        }
      }
      ta.addEventListener('input', check);
      box.querySelector('[data-cp-format]').addEventListener('click', function () {
        var d = check();
        if (d) { ta.value = JSON.stringify(d, null, 2); check(); }
      });
      box.querySelector('[data-cp-clear]').addEventListener('click', function () {
        if (!ta.value.trim() || confirm('Очистить поле? Блоки из этого JSON пропадут со страницы после сохранения.')) { ta.value = ''; check(); }
      });
      box.querySelector('[data-cp-template]').addEventListener('click', function () {
        if (ta.value.trim() && !confirm('Заменить текущее содержимое пустым шаблоном?')) return;
        ta.value = box.querySelector('[data-cp-template-json]').innerHTML.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
        check();
      });
      check();
    });
  });
})();
