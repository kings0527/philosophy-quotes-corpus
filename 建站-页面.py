# -*- coding: utf-8 -*-
"""
建站 · 生成 GitHub Pages 静态站点到 docs/

分层（解耦）：
  1. 数据层  统计总表.csv + 元数据.csv + 坐标表.csv  →  docs/assets/data.json
  2. 样式层  一份 style.css，全站复用
  3. 逻辑层  一份 app.js，所有页面共用（筛选/排序/搜索）
  4. 页面层  扉页 / 介绍 / 大纲 / 资料 / 人物索引 / 坐标表 / 分析 / 77 个人物页

运行： python 建站-坐标数据.py && python 建站-页面.py
"""
import csv
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")

SHORT = {"海亚姆（奥马尔·海亚姆）": "海亚姆"}
NAV = [("index.html", "扉页"), ("about.html", "介绍"), ("outline.html", "大纲"),
       ("corpus.html", "资料"), ("people.html", "人物索引"),
       ("coordinates.html", "坐标表"), ("analysis.html", "分析")]


def slug(name):
    return SHORT.get(name, name)


# ────────────────────────────── 数据层 ──────────────────────────────
def load_data():
    def rd(fn):
        with io.open(os.path.join(ROOT, fn), encoding="utf-8-sig") as fp:
            return list(csv.DictReader(fp))
    cor = {r["人物"]: r for r in rd("统计总表.csv")}
    meta = {r["人物"]: r for r in rd("元数据.csv")}
    coord = rd("坐标表.csv")
    data = []
    for c in coord:
        n = c["人物"]
        a = cor[n]
        m = meta.get(n, {})
        data.append({
            "name": n, "slug": slug(n), "file": a["文件"].replace("/", os.sep),
            "trad": c["传统"], "school": c["派别"],
            "axis1a": c["①界线"], "axis1b": c["①关系"], "axis2": c["②不动层"],
            "axis3a": c["③先验"], "axis3b": c["③秩序来源"],
            "axis4a": c["④互动"], "axis4b": c["④可改变"], "axis4c": c["④干预"],
            "genre": m.get("文体", ""), "rel": m.get("可靠度", ""),
            "concern": m.get("核心关切", ""),
            "A": int(a["A对自我"]), "B": int(a["B对外界"]), "N": int(a["合计"]),
            "share": round(float(a["A占比"]) * 100),
        })
    return data


# ────────────────────────────── Markdown ──────────────────────────────
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md2html(md):
    if md.startswith("---"):
        parts = md.split("---", 2)
        if len(parts) >= 3:
            md = parts[2]
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s == "---":
            out.append("<hr>")
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            lv = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv))
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            head = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<div class='tw'><table><thead><tr>" +
                       "".join("<th>%s</th>" % inline(c) for c in head) + "</tr></thead><tbody>" +
                       "".join("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>" for r in body) +
                       "</tbody></table></div>")
            continue
        if s.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(inline(lines[i].strip().lstrip(">").strip()))
                i += 1
            out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>")
            continue
        if re.match(r"^\d+\.\s", s):
            buf = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                buf.append(inline(re.sub(r"^\d+\.\s", "", lines[i].strip())))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % x for x in buf) + "</ol>")
            continue
        if re.match(r"^[-*]\s", s):
            buf = []
            while i < len(lines) and re.match(r"^[-*]\s", lines[i].strip()):
                buf.append(inline(re.sub(r"^[-*]\s", "", lines[i].strip())))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % x for x in buf) + "</ul>")
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|\||>\s|\d+\.\s|[-*]\s|---$)", lines[i].strip()):
            buf.append(inline(lines[i].strip()))
            i += 1
        if buf:
            out.append("<p>" + " ".join(buf) + "</p>")
    return "\n".join(out)


def fm_field(text, key):
    m = re.search(r"^%s:\s*(.*)$" % re.escape(key), text, re.M)
    return m.group(1).strip() if m else ""


# ────────────────────────────── 样式 ──────────────────────────────
CSS = """:root{--bg:#FBFAF7;--fg:#1F1E1B;--mut:#6B6862;--dim:#93908A;--line:rgba(0,0,0,.10);
--card:#fff;--soft:#F3F1EA;--accent:#8A4B2A;--accent2:#E8DFD2;--blue:#2C5C8F;--amber:#8A6414;}
@media (prefers-color-scheme:dark){:root{--bg:#171614;--fg:#EDEAE3;--mut:#A5A199;--dim:#7A766F;
--line:rgba(255,255,255,.12);--card:#201F1C;--soft:#26241F;--accent:#D89C74;--accent2:#3A342B;
--blue:#7FB0E0;--amber:#D8B45E;}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
font-family:"Noto Serif SC","Songti SC",Georgia,"Times New Roman",serif;
font-size:16px;line-height:1.85;}
header.top{border-bottom:.5px solid var(--line);background:var(--bg);position:sticky;top:0;z-index:9}
.wrap{max-width:920px;margin:0 auto;padding:0 20px}
.top .wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding-top:12px;padding-bottom:12px}
.brand{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
font-size:15px;font-weight:500;color:var(--fg);text-decoration:none;letter-spacing:.05em;white-space:nowrap}
.brand span{color:var(--accent)}
nav.site{display:flex;gap:2px;flex-wrap:wrap;margin-left:auto}
nav.site a{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
font-size:13px;color:var(--mut);text-decoration:none;padding:5px 11px;border-radius:7px}
nav.site a:hover{background:var(--soft);color:var(--fg)}
nav.site a.on{background:var(--accent2);color:var(--accent)}
main{padding:44px 0 90px}
h1{font-size:27px;font-weight:500;line-height:1.45;margin:0 0 8px;letter-spacing:.01em}
h2{font-size:20px;font-weight:500;margin:46px 0 14px;padding-bottom:8px;border-bottom:.5px solid var(--line)}
h3{font-size:16px;font-weight:500;margin:30px 0 10px}
h4{font-size:15px;font-weight:500;margin:22px 0 8px;color:var(--mut)}
p{margin:0 0 15px}
a{color:var(--blue)}
hr{border:0;border-top:.5px solid var(--line);margin:38px 0}
blockquote{margin:0 0 16px;padding:12px 18px;background:var(--soft);border-left:2px solid var(--accent);
border-radius:0 8px 8px 0;color:var(--fg)}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;background:var(--soft);
padding:1px 5px;border-radius:4px}
.lead{font-size:17px;color:var(--mut);margin:0 0 30px;line-height:1.9}
.crumb{font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;font-size:13px;color:var(--dim);
margin:0 0 18px}
.crumb a{color:var(--dim);text-decoration:none}
.crumb a:hover{color:var(--accent)}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));margin:26px 0}
.card{display:block;text-decoration:none;color:inherit;background:var(--card);border:.5px solid var(--line);
border-radius:12px;padding:16px 18px}
.card:hover{border-color:var(--accent)}
.card h3{margin:0 0 5px;font-size:15px}
.card p{margin:0;font-size:13px;color:var(--mut);line-height:1.7;
font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif}
.stats{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));margin:28px 0}
.stat{background:var(--soft);border-radius:10px;padding:13px 15px}
.stat b{display:block;font-size:23px;font-weight:500;line-height:1.3}
.stat i{font-style:normal;font-size:12px;color:var(--mut);
font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif}
.tw{overflow-x:auto;margin:0 0 22px;border:.5px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:9px 13px;text-align:left;border-bottom:.5px solid var(--line);vertical-align:top}
th{font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;font-size:12.5px;font-weight:500;
color:var(--mut);background:var(--soft);white-space:nowrap;position:sticky;top:45px}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--soft)}
th.s{cursor:pointer;user-select:none}
th.s:hover{color:var(--accent)}
td.n{font-family:ui-monospace,Menlo,monospace;font-size:13px;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 26px}
.chip{font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;font-size:12.5px;padding:3px 10px;
border-radius:20px;background:var(--soft);color:var(--mut);border:.5px solid var(--line)}
.chip b{font-weight:500;color:var(--fg)}
.fbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 18px;
font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;font-size:13px}
.fbar select,.fbar input{font-family:inherit;font-size:13px;padding:6px 10px;border-radius:8px;
border:.5px solid var(--line);background:var(--card);color:var(--fg)}
.fbar input{min-width:150px}
.fbar .cnt{color:var(--dim);margin-left:auto}
.pager{display:flex;justify-content:space-between;gap:14px;margin:52px 0 0;padding-top:20px;
border-top:.5px solid var(--line);font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;font-size:13.5px}
.pager a{color:var(--blue);text-decoration:none;max-width:46%}
.pager .r{text-align:right;margin-left:auto}
footer{border-top:.5px solid var(--line);padding:24px 0 40px;color:var(--dim);font-size:12.5px;
font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif}
footer a{color:var(--dim)}
ol,ul{padding-left:1.5em;margin:0 0 16px}
li{margin:0 0 6px}
@media(max-width:640px){h1{font-size:22px}main{padding:28px 0 60px}th{position:static}}
@media print{header.top,footer,nav.site{display:none}}
"""

JS = """/* 全站唯一的交互逻辑：从 data.json 渲染表格 + 筛选 + 排序 */
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
"""


# ────────────────────────────── 页面外壳 ──────────────────────────────
def shell(title, body, cur="", depth=0):
    p = "../" * depth
    navs = "".join(
        '<a href="%s%s"%s>%s</a>' % (p, h, ' class="on"' if h == cur else "", t) for h, t in NAV)
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · 哲学统计</title>
<link rel="stylesheet" href="%sassets/style.css"></head><body>
<header class="top"><div class="wrap">
<a class="brand" href="%sindex.html">哲学<span>统计</span></a>
<nav class="site">%s</nav></div></header>
<main><div class="wrap">%s</div></main>
<footer><div class="wrap">哲学统计 · 77 位哲学家 / 4505 条带出处语句 ｜
<a href="%soutline.html">大纲</a> · <a href="%scoordinates.html">坐标表</a> ·
<a href="%sanalysis.html">分析</a></div></footer>
<script src="%sassets/app.js"></script></body></html>""" % (
        esc(title), p, p, navs, body, p, p, p, p)


def write(path, html):
    full = os.path.join(DOCS, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with io.open(full, "w", encoding="utf-8") as fp:
        fp.write(html)


# ────────────────────────────── 主流程 ──────────────────────────────
def main():
    data = load_data()
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    pub = [{k: v for k, v in d.items() if k != "file"} for d in data]
    with io.open(os.path.join(DOCS, "assets/data.json"), "w", encoding="utf-8") as fp:
        json.dump(pub, fp, ensure_ascii=False, separators=(",", ":"))
    with io.open(os.path.join(DOCS, "assets/style.css"), "w", encoding="utf-8") as fp:
        fp.write(CSS)
    with io.open(os.path.join(DOCS, "assets/app.js"), "w", encoding="utf-8") as fp:
        fp.write(JS)
    with io.open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fp:
        fp.write("")

    A = sum(d["A"] for d in data)
    B = sum(d["B"] for d in data)
    idx = {d["slug"]: i for i, d in enumerate(data)}
    bytrad = {}
    for d in data:
        bytrad.setdefault(d["trad"], []).append(d)
    tradline = " · ".join("%s %d" % (t, len(v)) for t, v in bytrad.items())

    # ── 扉页 ──
    write("index.html", shell("扉页", """
<h1>哲学统计</h1>
<p class="lead">把 77 位哲学家、思想家的 4505 条带出处语句，聚合到十二条互相独立的轴上，
<br>再收敛为四个必须表态的问题。</p>
<div class="stats">
<div class="stat"><b>77</b><i>思想家</i></div>
<div class="stat"><b>4,505</b><i>带出处语句</i></div>
<div class="stat"><b>12</b><i>坐标轴</i></div>
<div class="stat"><b>4</b><i>根本问题</i></div>
</div>
<div class="grid">
<a class="card" href="about.html"><h3>介绍</h3><p>项目目的、方法与真伪原则、轴系设计、数据口径</p></a>
<a class="card" href="outline.html"><h3>大纲</h3><p>全书结构导览：四问 → 十二轴 → 77 人</p></a>
<a class="card" href="corpus.html"><h3>资料</h3><p>77 位思想家的语录库，按传统／文体／可靠度筛选</p></a>
<a class="card" href="people.html"><h3>人物索引</h3><p>一人一页，含坐标取值与语录全文</p></a>
<a class="card" href="coordinates.html"><h3>坐标表</h3><p>77 人 × 四问取值的可筛选总表</p></a>
<a class="card" href="analysis.html"><h3>分析</h3><p>升维聚合：十二轴逐轴论证与统合归总</p></a>
</div>
<h2>四个问题</h2>
<p>十二轴收敛为四个必须表态的问题——不回答本身就是一种回答（取默认值）。</p>
<div class="tw"><table>
<thead><tr><th>问题</th><th>由哪些轴构成</th></tr></thead>
<tbody>
<tr><td><strong>① 我在哪里结束？</strong></td><td>界线 · 关系</td></tr>
<tr><td><strong>② 哪一层不动？</strong></td><td>时间 · 纵深</td></tr>
<tr><td><strong>③ 秩序和知识从哪里来？</strong></td><td>信道 · 更新 · 涌现</td></tr>
<tr><td><strong>④ 我能改变什么？</strong></td><td>模态 · 互动 · 尺度 · 干预</td></tr>
</tbody></table></div>
<h2>覆盖</h2>
<p>%s</p>
<p style="color:var(--mut);font-size:14px">A 类「对自我的认知」%d 条 ／ B 类「对外界的认知」%d 条</p>
""" % (tradline, A, B), "index.html"))

    # ── 介绍 ──
    readme = io.open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    write("about.html", shell("介绍",
        '<h1>介绍</h1><p class="lead">项目目的、方法与真伪原则、轴系设计、数据口径。</p>'
        + md2html(readme), "about.html"))

    # ── 大纲 ──
    write("outline.html", shell("大纲", """
<h1>大纲</h1>
<p class="lead">全书结构：从四个问题出发，展开为十二条轴，落到 77 个人。</p>

<h2>第一层 · 四个问题</h2>
<div class="tw"><table><thead><tr><th>#</th><th>问题</th><th>构成轴</th><th>取值</th></tr></thead><tbody>
<tr><td>①</td><td>我在哪里结束，世界在哪里开始？</td><td>界线 · 关系</td>
<td>未分／二分／统一 ｜ 关系／实体</td></tr>
<tr><td>②</td><td>哪一层不动？</td><td>时间 · 纵深</td><td>20 个受控值（道·自然／天·理／心·灵魂…）</td></tr>
<tr><td>③</td><td>秩序和知识从哪里来？</td><td>信道 · 更新 · 涌现</td>
<td>先验：厚／薄／零 ｜ 秩序来源：设计／涌现／兼有</td></tr>
<tr><td>④</td><td>我能改变什么？</td><td>模态 · 互动 · 尺度 · 干预</td>
<td>互动：伙伴／对手／共在／独在 ｜ 可改变：我／心／制度／条件／关系／无 ｜ 干预：法／心／理·天／自然</td></tr>
</tbody></table></div>

<h2>第二层 · 十二条轴（四组）</h2>
<div class="grid">
<a class="card" href="analysis.html#a1-界线轴自我在哪里结束世界从哪里开始"><h3>A 本体轴</h3>
<p>A1 界线　A2 关系　A3 时间<br>世界以什么方式存在</p></a>
<a class="card" href="analysis.html#b1-纵深轴自我分为几层杠杆在哪一层"><h3>B 结构轴</h3>
<p>B1 纵深　B2 信道　B3 边界<br>认知如何组织</p></a>
<a class="card" href="analysis.html#c1-模态轴事件是被决定的还是条件依赖的"><h3>C 动力轴</h3>
<p>C1 模态　C2 更新　C3 涌现<br>认知如何运转</p></a>
<a class="card" href="analysis.html#d1-互动轴他人是对手还是伙伴"><h3>D 实践轴</h3>
<p>D1 互动　D2 尺度　D3 干预<br>如何行动</p></a>
</div>

<h2>第三层 · 人与资料</h2>
<div class="grid">
<a class="card" href="coordinates.html"><h3>哲学坐标表</h3><p>77 人 × 四问取值，可筛选、可排序</p></a>
<a class="card" href="people.html"><h3>人物索引</h3><p>一人一页，含坐标取值与语录全文</p></a>
<a class="card" href="corpus.html"><h3>资料总览</h3><p>按传统／文体／可靠度筛选语料库</p></a>
</div>

<h2>第四层 · 分析产出</h2>
<div class="grid">
<a class="card" href="analysis.html"><h3>升维聚合哲学</h3><p>十二轴逐轴论证 + 统合归总（正文）</p></a>
<a class="card" href="analysis-data.html"><h3>数据可用性说明</h3><p>量化的边界：删失、方差归属、自然实验</p></a>
</div>

<h2>阅读路径建议</h2>
<ol>
<li><strong>想快速抓住全貌</strong>：扉页 → 坐标表（按「不动层」排序）→ 分析 §归总</li>
<li><strong>想读哲学</strong>：分析（十二轴全文）→ 遇到感兴趣的人再点进人物页</li>
<li><strong>想查资料</strong>：资料 → 人物索引 → 单人页（带出处的完整语录）</li>
<li><strong>想核数据</strong>：介绍 §方法与真伪原则 → 数据可用性说明</li>
</ol>
""", "outline.html"))

    # ── 资料 ──
    write("corpus.html", shell("资料", """
<h1>资料</h1>
<p class="lead">77 位思想家的语录库总览。每一行可进入单人页，查看带《文献》出处的完整条目。</p>
<div class="fbar">
<input id="q" placeholder="搜索人名或派别…">
<select id="f-trad"><option value="">全部传统</option></select>
<select id="f-genre"><option value="">全部文体</option></select>
<select id="f-rel"><option value="">全部可靠度</option></select>
<span class="cnt"></span>
</div>
<div class="tw"><table id="t">
<thead><tr><th class="s" data-k="name">人物</th><th class="s" data-k="trad">传统</th>
<th class="s" data-k="school">派别</th><th class="s" data-k="genre">文体</th>
<th class="s" data-k="rel">可靠度</th><th class="s" data-k="A">A 自我</th>
<th class="s" data-k="B">B 外界</th><th class="s" data-k="N">合计</th></tr></thead>
<tbody></tbody></table></div>
""", "corpus.html"))

    # ── 人物索引 ──
    write("people.html", shell("人物索引", """
<h1>人物索引</h1>
<p class="lead">按坐标取值检索。点人名进入单人页。</p>
<div class="fbar">
<input id="q" placeholder="搜索人名或派别…">
<select id="f-trad"><option value="">全部传统</option></select>
<select id="f-axis2"><option value="">全部「不动层」</option></select>
<select id="f-axis3a"><option value="">全部先验</option></select>
<select id="f-axis1a"><option value="">全部界线</option></select>
<span class="cnt"></span>
</div>
<div class="tw"><table id="t">
<thead><tr><th class="s" data-k="name">人物</th><th class="s" data-k="trad">传统</th>
<th class="s" data-k="axis1a">①界线</th><th class="s" data-k="axis1b">①关系</th>
<th class="s" data-k="axis2">②不动层</th><th class="s" data-k="axis3a">③先验</th>
<th class="s" data-k="axis3b">③秩序</th><th class="s" data-k="axis4b">④可改变</th>
<th class="s" data-k="axis4c">④干预</th></tr></thead>
<tbody></tbody></table></div>
""", "people.html"))

    # ── 坐标表 ──
    write("coordinates.html", shell("坐标表", """
<h1>哲学坐标表</h1>
<p class="lead">把 77 位思想家投影到四个问题上。每个问题给出离散取值——同一列里的人，
在这个问题上回答了同一句话。</p>
<div class="fbar">
<input id="q" placeholder="搜索人名或派别…">
<select id="f-trad"><option value="">全部传统</option></select>
<select id="f-axis2"><option value="">全部「不动层」</option></select>
<select id="f-axis4c"><option value="">全部干预</option></select>
<span class="cnt"></span>
</div>
<div class="tw"><table id="t">
<thead><tr><th class="s" data-k="name">人物</th>
<th class="s" data-k="axis1a">①界线</th><th class="s" data-k="axis1b">①关系</th>
<th class="s" data-k="axis2">②不动层</th>
<th class="s" data-k="axis3a">③先验</th><th class="s" data-k="axis3b">③秩序来源</th>
<th class="s" data-k="axis4a">④互动</th><th class="s" data-k="axis4b">④可改变</th>
<th class="s" data-k="axis4c">④干预</th></tr></thead>
<tbody></tbody></table></div>

<h2>怎么读这张表</h2>
<ol>
<li><strong>只看第 5 列（②不动层）</strong>：这一列是全表的枢纽——你选哪一层作为不变的支点，
决定了其余各列。按它排序，77 人会自然分成 20 组。</li>
<li><strong>横向读一行</strong>：得到一个人的完整立场。比如「未分 · 关系 · 道·自然 · 零 · 涌现 ·
独在 · 我 · 自然」——这是庄子。</li>
<li><strong>纵向读一列</strong>：得到一个问题上的全部选项。第 4 列告诉我们「第一原理」只有 20 种
可能答案。</li>
<li><strong>找表中最像的两行</strong>：往往就是被并称的那两位。老子与庄子八列全同；
孔子与韩非只在「②不动层」与「④可改变」上分道。</li>
</ol>

<h2>四问取值分布</h2>
<div class="tw"><table><thead><tr><th>问题</th><th>取值分布</th></tr></thead><tbody>
<tr><td>① 界线</td><td>未分 34 ｜ 二分 32 ｜ 统一 11</td></tr>
<tr><td>① 关系</td><td>关系 51 ｜ 实体 26</td></tr>
<tr><td>② 不动层</td><td>自然律·逻各斯 8 ｜ 道·自然 8 ｜ 天·理 7 ｜ 心·灵魂 6 ｜ 法·制度 6 ｜
自由·存在 6 ｜ 神·梵·绝对 5 ｜ 逻辑·语言 4 ｜ 经验·习惯 4 ｜ 物质·实践 4 ｜ 缘起·空 3 ｜
形式·先验 3 ｜ 存在·理念 2 ｜ 目的·中道 2 ｜ 意志·生命 2 ｜ 关系·他者 2 ｜ 无常·当下 2 ｜
我思·主体 1 ｜ 辩证·历史 1 ｜ 爱 1</td></tr>
<tr><td>③ 先验</td><td>厚 38 ｜ 薄 26 ｜ 零 13</td></tr>
<tr><td>③ 秩序来源</td><td>涌现 52 ｜ 设计 22 ｜ 兼有 3</td></tr>
<tr><td>④ 互动</td><td>共在 38 ｜ 独在 24 ｜ 伙伴 10 ｜ 对手 5</td></tr>
<tr><td>④ 可改变</td><td>我 31 ｜ 心 20 ｜ 制度 14 ｜ 无 8 ｜ 条件 2 ｜ 关系 2</td></tr>
<tr><td>④ 干预</td><td>自然 27 ｜ 心 25 ｜ 理·天 15 ｜ 法 10</td></tr>
</tbody></table></div>
""", "coordinates.html"))

    # ── 分析 ──
    phil = io.open(os.path.join(ROOT, "升维聚合哲学.md"), encoding="utf-8").read()
    write("analysis.html", shell("分析",
        '<h1>升维聚合哲学</h1>'
        '<p class="lead">十二条轴上的自我与外界——逐轴论证、统合归总。</p>'
        '<div class="chips"><span class="chip">修订 <b>v2</b></span>'
        '<span class="chip">四组 <b>十二条轴</b></span>'
        '<span class="chip">收敛为 <b>四个问题</b></span></div>'
        + md2html(phil), "analysis.html"))

    rep = io.open(os.path.join(ROOT, "升维分析报告.md"), encoding="utf-8").read()
    write("analysis-data.html", shell("数据可用性说明",
        '<h1>数据可用性说明</h1>'
        '<p class="lead">这份语料库能支撑什么结论、不能支撑什么结论——量化的边界。</p>'
        + md2html(rep), "analysis.html"))

    # ── 人物页 ──
    for d in data:
        raw = io.open(os.path.join(ROOT, d["file"]), encoding="utf-8").read()
        k = idx[d["slug"]]
        prev = data[k - 1] if k > 0 else None
        nxt = data[k + 1] if k < len(data) - 1 else None
        pager = '<div class="pager">%s%s</div>' % (
            '<a href="%s.html">← %s</a>' % (prev["slug"], prev["name"]) if prev else "<span></span>",
            '<a class="r" href="%s.html">%s →</a>' % (nxt["slug"], nxt["name"]) if nxt else "<span></span>")
        chips = ('<div class="chips">'
                 '<span class="chip">① 界线 <b>%s</b></span>'
                 '<span class="chip">① 关系 <b>%s</b></span>'
                 '<span class="chip">② 不动层 <b>%s</b></span>'
                 '<span class="chip">③ 先验 <b>%s</b></span>'
                 '<span class="chip">③ 秩序 <b>%s</b></span>'
                 '<span class="chip">④ 互动 <b>%s</b></span>'
                 '<span class="chip">④ 可改变 <b>%s</b></span>'
                 '<span class="chip">④ 干预 <b>%s</b></span>'
                 '<span class="chip">A %d ／ B %d</span></div>') % (
            d["axis1a"], d["axis1b"], d["axis2"], d["axis3a"], d["axis3b"],
            d["axis4a"], d["axis4b"], d["axis4c"], d["A"], d["B"])
        body = ('<p class="crumb"><a href="people.html">人物索引</a> › '
                '<a href="coordinates.html">%s · %s</a></p>%s%s%s') % (
            d["trad"], d["school"], chips, md2html(raw), pager)
        write("people/%s.html" % d["slug"], shell(d["name"], body, "", depth=1))

    print("已生成站点：%d 页（含 %d 个人物页）" % (8 + len(data), len(data)))
    print("输出目录：", DOCS)


if __name__ == "__main__":
    main()
