/* 全站唯一的交互逻辑：从 data.json 渲染表格 + 筛选 + 排序 */
(function () {
  var t = document.getElementById('t');
  if (!t) return;
  var cols = [].map.call(t.querySelectorAll('thead th'), function (th) {
    return { k: th.dataset.k, label: th.textContent.trim(), sortable: th.classList.contains('s') };
  });
  var tbody = t.querySelector('tbody');
  var state = { sort: null, dir: 1, data: [] };
  var fbar = document.querySelector('.fbar');
  var cnt = document.querySelector('.cnt');

  fetch('assets/data.json').then(function (r) { return r.json(); }).then(function (data) {
    state.data = data;
    buildFilters(data);
    wire();
    render();
  });

  function buildFilters(data) {
    [].forEach.call(document.querySelectorAll('select[id^="f-"]'), function (sel) {
      var key = sel.id.slice(2);
      if (key === 'trad') return;
      var vals = [], seen = {};
      data.forEach(function (d) {
        if (d[key] && !seen[d[key]]) { seen[d[key]] = 1; vals.push(d[key]); }
      });
      vals.sort(function (a, b) { return a.localeCompare(b, 'zh'); });
      vals.forEach(function (v) {
        var o = document.createElement('option');
        o.value = v; o.textContent = v; sel.appendChild(o);
      });
    });
    var tr = document.getElementById('f-trad');
    if (tr) {
      var seen = {};
      data.forEach(function (d) { seen[d.trad] = 1; });
      Object.keys(seen).sort().forEach(function (v) {
        var o = document.createElement('option'); o.value = v; o.textContent = v; tr.appendChild(o);
      });
    }
  }

  function wire() {
    if (fbar) {
      [].forEach.call(fbar.querySelectorAll('input,select'), function (el) {
        el.addEventListener('input', render);
        el.addEventListener('change', render);
      });
    }
    [].forEach.call(t.querySelectorAll('th.s'), function (th) {
      th.addEventListener('click', function () {
        var k = th.dataset.k;
        if (state.sort === k) { state.dir = -state.dir; }
        else { state.sort = k; state.dir = 1; }
        render();
      });
    });
  }

  function render() {
    var q = (document.getElementById('q') || {}).value || '';
    q = q.trim().toLowerCase();
    var rows = state.data.filter(function (d) {
      if (q && (d.name + d.school + d.trad).toLowerCase().indexOf(q) < 0) return false;
      var ok = true;
      [].forEach.call(document.querySelectorAll('select[id^="f-"]'), function (sel) {
        if (sel.value && d[sel.id.slice(2)] !== sel.value) ok = false;
      });
      return ok;
    });
    if (state.sort) {
      var k = state.sort, dir = state.dir;
      rows.sort(function (a, b) {
        var x = a[k], y = b[k];
        if (typeof x === 'number' && typeof y === 'number') return (x - y) * dir;
        return String(x).localeCompare(String(y), 'zh') * dir;
      });
    }
    tbody.innerHTML = rows.map(function (d) {
      return '<tr>' + cols.map(function (c) {
        if (c.k === 'name') return '<td><a href="people/' + d.slug + '.html">' + d.name + '</a></td>';
        var v = d[c.k];
        if (c.k === 'A' || c.k === 'B' || c.k === 'N') return '<td class="n">' + v + '</td>';
        return '<td>' + v + '</td>';
      }).join('') + '</tr>';
    }).join('');
    if (cnt) cnt.textContent = rows.length + ' / ' + state.data.length + ' 人';
  }
})();
