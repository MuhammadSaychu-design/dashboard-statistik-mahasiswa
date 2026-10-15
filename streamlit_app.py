"""Dashboard statistik deskriptif Latihan 1 versi Streamlit.

Jalankan:  streamlit run streamlit_app.py
Data bawaan: data/latihan1.csv (bisa diganti lewat unggah CSV di sidebar).
"""
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

DATA = Path(__file__).parent / "data" / "latihan1.csv"
LABEL = {
    "Age": "Usia", "Study_Hours": "Jam belajar", "Sleep_Hours": "Jam tidur",
    "Attendance": "Kehadiran (%)", "Exam_Score": "Nilai ujian",
    "Monthly_Spending": "Pengeluaran bulanan", "Screen_Hours": "Jam layar",
    "Satisfaction": "Kepuasan (1-10)",
}
GCOL = alt.Scale(domain=["F", "M"], range=["#0c8f8f", "#d9772b"])
UP, DOWN, FLAT = "#2f5da8", "#b8442b", "#6b7385"

st.set_page_config(page_title="Statistik deskriptif - Latihan 1", layout="wide")


def L(c):
    return LABEL.get(c, c.replace("_", " "))


def fm(v, d=2):
    """Format angka gaya Indonesia (koma desimal)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


DRAG_HTML = r"""<div class="app">
<div class="bar" id="bar" role="status">
  <span class="badge ok" id="badge"></span>
  <span class="msg" id="msg"></span>
  <button type="button" id="reset">Kembalikan titik ke data awal</button>
</div>

<div class="wrap">
  <div>
    <svg id="svg" viewBox="0 0 640 460" role="group" aria-label="Diagram sebar yang bisa digeser"></svg>
    <div class="legend">
      <span><i class="dot"></i>Satu titik = satu mahasiswa</span>
      <span><i class="dash"></i>Rata-rata X dan Y</span>
      <span><i style="background:var(--f);opacity:.55"></i>Kotak searah (+)</span>
      <span><i style="background:var(--m);opacity:.65"></i>Kotak berlawanan (−)</span>
    </div>
    <label class="hint" style="display:block"><input type="checkbox" id="boxes"> Tampilkan kotak searah/berlawanan untuk tiap titik</label>
    <p class="hint">Seret titik di grafik, atau fokuskan titik lalu pakai tombol panah (Shift = langkah besar), untuk mengubah nilainya.</p>
  </div>

  <div>
    <div class="panel">
      <h4>Korelasi (r)</h4>
      <div class="rbig" id="rBig">–</div>
      <div class="gauge"><span id="gMark"></span></div>
      <div class="gl"><span>−1</span><span>0</span><span>+1</span></div>
      <p class="read" id="rText"></p>
      <dl id="stats"></dl>
      <div class="pred-box">
        <label><span id="predLbl"></span>
          <input type="range" id="predX" aria-label="Nilai X untuk perkiraan"></label>
        <p class="read" id="predOut"></p>
      </div>
    </div>
  </div>
</div>

</div>
"""

DRAG_CSS = r"""
.app{--ink:#172033;--muted:#5b6577;--line:#d5dbe4;--pos:#2f5da8;--f:#0c8f8f;--m:#d9772b;--neg:#b8442b;--soft:rgba(127,127,127,.07)}
.app.dark{--ink:#e6eaf2;--muted:#9aa5b8;--line:#2b374d;--pos:#6f9bea;--f:#3cc0b8;--m:#f0a15a;--neg:#e5836b}
.app,.app *{box-sizing:border-box}
.app{margin:0;padding:2px;font:inherit;font-size:14px;line-height:1.45;color:var(--ink);background:transparent;font-variant-numeric:tabular-nums}
.bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;border:1px solid var(--line);border-radius:8px;padding:9px 12px;margin-bottom:12px;background:var(--soft)}
.bar.dirty{border-color:var(--m)}
.badge{border-radius:99px;padding:2px 12px;font-size:.82rem;white-space:nowrap}
.badge.warn{background:color-mix(in srgb,var(--m) 22%,transparent);color:var(--m)}
.badge.ok{background:color-mix(in srgb,var(--f) 20%,transparent);color:var(--f)}
.bar span.msg{flex:1 1 220px;color:var(--muted);font-size:.9rem}
button{font:inherit;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:6px;padding:4px 12px;cursor:pointer}
button:hover{border-color:var(--ink)}
button:disabled{opacity:.4;cursor:default}
.wrap{display:grid;grid-template-columns:minmax(0,1.9fr) minmax(250px,1fr);gap:16px;align-items:start}
@media(max-width:760px){.wrap{grid-template-columns:minmax(0,1fr)}}
svg{width:100%;height:auto;display:block;touch-action:none;user-select:none}
.grid{stroke:var(--line);stroke-width:1}
.axis{stroke:var(--muted);stroke-width:1}
.ax{fill:var(--muted);font-size:11px}
.axl{fill:var(--muted);font-size:12px;font-weight:600}
.mean{stroke:var(--ink);stroke-width:1.4;stroke-dasharray:5 4;opacity:.8}
.guide{stroke:var(--ink);stroke-width:1.2;stroke-dasharray:2 3;opacity:.7}
.lbl{fill:var(--ink);font-size:11.5px;font-weight:600}
.eq{fill:var(--ink);font-size:12px}
.reg{stroke:var(--ink);stroke-width:3;stroke-linecap:round}
.bpos{fill:var(--f);fill-opacity:.13}
.bneg{fill:var(--m);fill-opacity:.17}
.pt{fill:var(--pos);stroke:#fff;stroke-width:1.5;cursor:grab}
.pt:hover{stroke-width:3}
.pt:focus-visible,.pt.active{stroke:var(--ink);stroke-width:3;outline:none;cursor:grabbing}
.pn{fill:var(--ink);font-size:11px;pointer-events:none}
.pred{fill:none;stroke:var(--ink);stroke-width:2.5}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:.84rem;color:var(--muted);margin:6px 0 0}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.legend i.dash{width:18px;height:0;border-top:2px dashed var(--ink);border-radius:0}
.legend i.dot{border-radius:50%;background:var(--pos)}
.hint{color:var(--muted);font-size:.86rem;margin:8px 0 0}
.panel{border:1px solid var(--line);border-radius:8px;padding:14px 16px;background:var(--soft)}
.panel h4{margin:0 0 6px;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.rbig{font-size:2.8rem;font-weight:600;line-height:1.1}
.gauge{position:relative;height:10px;border-radius:6px;margin-top:10px;background:linear-gradient(90deg,var(--neg),var(--line) 50%,var(--f))}
.gauge span{position:absolute;top:-4px;width:4px;height:18px;background:var(--ink);border-radius:2px;transform:translateX(-2px)}
.gl{display:flex;justify-content:space-between;color:var(--muted);font-size:.75rem;margin:6px 0 8px}
.read{margin:6px 0 0;font-size:.92rem}
dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 14px;margin:12px 0 0}
dl div{border-top:1px solid var(--line);padding-top:5px}
dt{color:var(--muted);font-size:.78rem}
dd{margin:0;font-weight:600}
.pred-box{margin-top:14px;border-top:1px solid var(--line);padding-top:10px}
.pred-box label{display:grid;gap:6px;font-size:.9rem}
.pred-box input{width:100%;accent-color:var(--pos)}
.warn-t{color:var(--m)}
"""

DRAG_JS = r"""export default function (component) {
  var app = component.parentElement.querySelector('.app');
  if (!app) return;
  if (!app.__w) app.__w = create(app);
  app.__w.update(component.data, component.setTriggerValue);
}

function create(app) {
  function $(id) { return app.querySelector('#' + id); }
  var W = 640, H = 460, M = { l: 58, r: 20, t: 30, b: 50 };
  var PW = W - M.l - M.r, PH = H - M.t - M.b;
  var svg = $('svg');
  var send = function () {};
  var XL = '', YL = '', curKey = null;
  var rows = [], orig = [], pts = [], n = 0;
  var AX, AY, dX = 0, dY = 0, x0 = 0, showBoxes = true;
  var drag = null, timer = null;

  function fm(v, d) {
    if (d === undefined) d = 2;
    if (v === null || v === undefined || !isFinite(v)) return '–';
    return v.toLocaleString('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function r2(v) { return Math.round(v * 100) / 100; }
  function dec(step) { return step >= 1 ? 0 : Math.min(4, Math.ceil(-Math.log10(step))); }

  function niceAxis(lo, hi) {
    if (hi - lo === 0) { lo -= 1; hi += 1; }
    var raw = (hi - lo) / 6, mag = Math.pow(10, Math.floor(Math.log10(raw))), nr = raw / mag;
    var step = (nr < 1.5 ? 1 : nr < 3 ? 2 : nr < 7 ? 5 : 10) * mag;
    var a = Math.floor(lo / step + 1e-9) * step, b = Math.ceil(hi / step - 1e-9) * step;
    var t = [];
    for (var v = a; v <= b + step / 2; v += step) t.push(Math.round(v / step) * step);
    return { lo: a, hi: b, ticks: t, step: step };
  }
  function rangeOf(key) {
    var lo = Infinity, hi = -Infinity;
    [rows, orig].forEach(function (arr) {
      arr.forEach(function (p) { if (p[key] < lo) lo = p[key]; if (p[key] > hi) hi = p[key]; });
    });
    var pad = (hi - lo) * 0.08 || 1;
    return niceAxis(lo - pad, hi + pad);
  }
  function setDomain() {
    AX = rangeOf('x'); AY = rangeOf('y');
    dX = dec(AX.step); dY = dec(AY.step);
    var px = $('predX');
    px.min = AX.lo; px.max = AX.hi; px.step = (AX.hi - AX.lo) / 200;
  }
  function outside() {
    var out = false;
    rows.forEach(function (p) { if (p.x < AX.lo || p.x > AX.hi || p.y < AY.lo || p.y > AY.hi) out = true; });
    return out;
  }

  function sx(x) { return M.l + (x - AX.lo) / (AX.hi - AX.lo) * PW; }
  function sy(y) { return M.t + PH - (y - AY.lo) / (AY.hi - AY.lo) * PH; }

  function calc() {
    var mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += pts[i].x; my += pts[i].y; }
    mx /= n; my /= n;
    var sxx = 0, syy = 0, sxy = 0;
    for (i = 0; i < n; i++) {
      var dx = pts[i].x - mx, dy = pts[i].y - my;
      sxx += dx * dx; syy += dy * dy; sxy += dx * dy;
    }
    var b = sxx > 0 ? sxy / sxx : NaN;
    var r = (sxx > 0 && syy > 0) ? sxy / Math.sqrt(sxx * syy) : NaN;
    return { mx: mx, my: my, b: b, a: my - b * mx, r: r, cov: n > 1 ? sxy / (n - 1) : NaN };
  }

  function render() {
    var S = calc(), h = '', i;
    h += '<defs><clipPath id="cp"><rect x="' + M.l + '" y="' + M.t + '" width="' + PW + '" height="' + PH + '"/></clipPath></defs>';
    AX.ticks.forEach(function (t) {
      var x = sx(t);
      h += '<line class="grid" x1="' + x + '" x2="' + x + '" y1="' + M.t + '" y2="' + (M.t + PH) + '"/>' +
           '<text class="ax" x="' + x + '" y="' + (M.t + PH + 16) + '" text-anchor="middle">' + fm(t, dX) + '</text>';
    });
    AY.ticks.forEach(function (t) {
      var y = sy(t);
      h += '<line class="grid" x1="' + M.l + '" x2="' + (M.l + PW) + '" y1="' + y + '" y2="' + y + '"/>' +
           '<text class="ax" x="' + (M.l - 8) + '" y="' + (y + 4) + '" text-anchor="end">' + fm(t, dY) + '</text>';
    });
    h += '<line class="axis" x1="' + M.l + '" x2="' + (M.l + PW) + '" y1="' + (M.t + PH) + '" y2="' + (M.t + PH) + '"/>' +
         '<line class="axis" x1="' + M.l + '" x2="' + M.l + '" y1="' + M.t + '" y2="' + (M.t + PH) + '"/>';
    h += '<text class="axl" x="' + (M.l + PW / 2) + '" y="' + (H - 8) + '" text-anchor="middle">' + esc(XL) + ' (X)</text>';
    h += '<text class="axl" transform="translate(14 ' + (M.t + PH / 2) + ') rotate(-90)" text-anchor="middle">' + esc(YL) + ' (Y)</text>';

    h += '<g clip-path="url(#cp)">';
    if (showBoxes) {
      for (i = 0; i < n; i++) {
        var p = pts[i], same = (p.x - S.mx) * (p.y - S.my) >= 0;
        var xa = sx(Math.min(p.x, S.mx)), xb = sx(Math.max(p.x, S.mx));
        var ya = sy(Math.max(p.y, S.my)), yb = sy(Math.min(p.y, S.my));
        h += '<rect class="' + (same ? 'bpos' : 'bneg') + '" x="' + xa + '" y="' + ya + '" width="' + (xb - xa) + '" height="' + (yb - ya) + '"/>';
      }
    }
    h += '<line class="mean" x1="' + sx(S.mx) + '" x2="' + sx(S.mx) + '" y1="' + M.t + '" y2="' + (M.t + PH) + '"/>';
    h += '<line class="mean" x1="' + M.l + '" x2="' + (M.l + PW) + '" y1="' + sy(S.my) + '" y2="' + sy(S.my) + '"/>';
    if (isFinite(S.b)) {
      h += '<line class="reg" x1="' + sx(AX.lo) + '" y1="' + sy(S.a + S.b * AX.lo) + '" x2="' + sx(AX.hi) + '" y2="' + sy(S.a + S.b * AX.hi) + '"/>';
    }
    h += '</g>';
    h += '<text class="lbl" x="' + clamp(sx(S.mx), M.l + 24, M.l + PW - 24) + '" y="' + (M.t - 8) + '" text-anchor="middle">X̄ = ' + fm(S.mx, 1) + '</text>';
    h += '<text class="lbl" x="' + (M.l + PW - 4) + '" y="' + (sy(S.my) - 6) + '" text-anchor="end">Ȳ = ' + fm(S.my, 1) + '</text>';
    if (isFinite(S.b)) {
      h += '<text class="eq" x="' + (M.l + 8) + '" y="' + (M.t + 16) + '">ŷ = ' + fm(S.a) + (S.b >= 0 ? ' + ' : ' − ') + fm(Math.abs(S.b)) + '·X</text>';
      var y0 = S.a + S.b * x0;
      if (y0 >= AY.lo && y0 <= AY.hi) {
        h += '<line class="guide" x1="' + M.l + '" x2="' + sx(x0) + '" y1="' + sy(y0) + '" y2="' + sy(y0) + '"/>' +
             '<line class="guide" x1="' + sx(x0) + '" x2="' + sx(x0) + '" y1="' + sy(y0) + '" y2="' + (M.t + PH) + '"/>' +
             '<circle class="pred" cx="' + sx(x0) + '" cy="' + sy(y0) + '" r="7"/>';
      }
    }
    for (i = 0; i < n; i++) {
      var q = pts[i];
      h += '<circle class="pt' + (drag === i ? ' active' : '') + '" data-i="' + i + '" cx="' + sx(q.x) + '" cy="' + sy(q.y) + '" r="' + (drag === i ? 8 : (n > 30 ? 5 : 6.5)) + '"' +
           ' tabindex="0" role="button" aria-label="Titik ' + q.id + ': X ' + fm(q.x) + ', Y ' + fm(q.y) + '. Tombol panah mengubah nilai.">' +
           '<title>Titik ' + q.id + (q.g ? ' (' + q.g + ')' : '') + ': X = ' + fm(q.x) + ', Y = ' + fm(q.y) + '</title></circle>';
      if (n <= 30) h += '<text class="pn" x="' + (sx(q.x) + 9) + '" y="' + (sy(q.y) - 8) + '">' + q.id + '</text>';
    }
    svg.innerHTML = h;
    panel(S);
  }

  function strength(a) { return a >= .8 ? 'sangat kuat' : a >= .6 ? 'kuat' : a >= .4 ? 'sedang' : a >= .2 ? 'lemah' : 'sangat lemah'; }

  function changedFromOrig() {
    var k = 0;
    for (var i = 0; i < n; i++) if (pts[i].x !== orig[i].x || pts[i].y !== orig[i].y) k++;
    return k;
  }

  function panel(S) {
    var r = S.r;
    $('rBig').textContent = fm(r);
    $('gMark').style.left = (isFinite(r) ? (r + 1) / 2 * 100 : 50) + '%';
    var t;
    if (!isFinite(r)) t = 'Belum bisa dihitung: semua nilai X atau semua nilai Y sama.';
    else if (Math.abs(r) < .2) t = 'Hampir tidak ada hubungan garis lurus antara X dan Y.';
    else t = 'Hubungan ' + strength(Math.abs(r)) + ' dan ' + (r > 0 ? 'naik' : 'turun') + ': ' +
             (r > 0 ? 'X yang lebih besar cenderung bersama Y yang lebih besar.' : 'X yang lebih besar cenderung bersama Y yang lebih kecil.') +
             ' Sekitar ' + Math.round(r * r * 100) + '% variasi Y ikut dijelaskan X.';
    $('rText').textContent = t;
    var items = [['Jumlah titik (n)', String(n)], ['r²', fm(r * r)], ['Rata-rata X', fm(S.mx)], ['Rata-rata Y', fm(S.my)],
                 ['Kemiringan (b)', fm(S.b)], ['Intersep (a)', fm(S.a)], ['Kovarians', fm(S.cov)]];
    $('stats').innerHTML = items.map(function (it) { return '<div><dt>' + it[0] + '</dt><dd>' + it[1] + '</dd></div>'; }).join('');
    $('predLbl').innerHTML = 'Perkiraan ' + esc(YL.toLowerCase()) + ' untuk X = <b>' + fm(x0, dX) + '</b>';
    var y0 = S.a + S.b * x0, out = '';
    if (isFinite(y0)) {
      out = esc(YL) + ' diperkirakan <b>' + fm(y0, 1) + '</b>.';
      if (x0 < AX.lo || x0 > AX.hi) out += ' <span class="warn-t">X di luar rentang grafik, ini ekstrapolasi.</span>';
    }
    $('predOut').innerHTML = out;

    var k = changedFromOrig();
    $('bar').classList.toggle('dirty', k > 0);
    var badge = $('badge');
    badge.className = 'badge ' + (k > 0 ? 'warn' : 'ok');
    badge.textContent = k > 0 ? '● Data diubah' : '● Sama dengan data awal';
    $('msg').textContent = k > 0
      ? k + ' titik berbeda dari data awal. Perubahan ini ikut mengubah seluruh dashboard.'
      : 'Seret titik, atau pakai tombol panah, untuk mengubah data. Seluruh dashboard ikut dihitung ulang.';
    $('reset').disabled = k === 0;
  }

  function diff() {
    var out = [];
    for (var i = 0; i < n; i++) {
      if (pts[i].x !== rows[i].x || pts[i].y !== rows[i].y) out.push({ i: pts[i].i, x: pts[i].x, y: pts[i].y });
    }
    return out;
  }
  function sendNow() {
    if (timer) { clearTimeout(timer); timer = null; }
    var d = diff();
    if (d.length) send('moved', { points: d, t: Date.now() });
  }

  function toData(e) {
    var rc = svg.getBoundingClientRect();
    var px = (e.clientX - rc.left) * W / rc.width, py = (e.clientY - rc.top) * H / rc.height;
    return {
      x: r2(clamp(AX.lo + (px - M.l) / PW * (AX.hi - AX.lo), AX.lo, AX.hi)),
      y: r2(clamp(AY.lo + (M.t + PH - py) / PH * (AY.hi - AY.lo), AY.lo, AY.hi))
    };
  }

  svg.addEventListener('pointerdown', function (e) {
    var c = e.target.closest ? e.target.closest('[data-i]') : null;
    if (!c) return;
    drag = +c.getAttribute('data-i');
    if (svg.setPointerCapture) svg.setPointerCapture(e.pointerId);
    e.preventDefault();
    render();
  });
  svg.addEventListener('pointermove', function (e) {
    if (drag === null) return;
    var p = toData(e);
    pts[drag].x = p.x; pts[drag].y = p.y;
    render();
  });
  function endDrag() { if (drag !== null) { drag = null; render(); sendNow(); } }
  svg.addEventListener('pointerup', endDrag);
  svg.addEventListener('pointercancel', endDrag);

  svg.addEventListener('keydown', function (e) {
    var c = e.target.closest ? e.target.closest('[data-i]') : null;
    if (!c) return;
    var i = +c.getAttribute('data-i'), big = e.shiftKey ? 10 : 1;
    var sxs = (AX.hi - AX.lo) / 100 * big, sys = (AY.hi - AY.lo) / 100 * big;
    var p = pts[i];
    if (e.key === 'ArrowLeft') p.x = r2(clamp(p.x - sxs, AX.lo, AX.hi));
    else if (e.key === 'ArrowRight') p.x = r2(clamp(p.x + sxs, AX.lo, AX.hi));
    else if (e.key === 'ArrowUp') p.y = r2(clamp(p.y + sys, AY.lo, AY.hi));
    else if (e.key === 'ArrowDown') p.y = r2(clamp(p.y - sys, AY.lo, AY.hi));
    else return;
    e.preventDefault();
    render();
    var el = svg.querySelector('[data-i="' + i + '"]');
    if (el && el.focus) el.focus({ preventScroll: true });
    if (timer) clearTimeout(timer);
    timer = setTimeout(sendNow, 450);
  });

  $('predX').addEventListener('input', function (e) { x0 = parseFloat(e.target.value); render(); });
  $('boxes').addEventListener('change', function (e) { showBoxes = e.target.checked; render(); });
  $('reset').addEventListener('click', function () {
    pts = pts.map(function (p, k) { return { i: p.i, id: p.id, g: p.g, x: orig[k].x, y: orig[k].y }; });
    render();
    sendNow();
  });

  return {
    update: function (cfg, sendFn) {
      if (!cfg || !cfg.rows || !cfg.rows.length) return;
      send = sendFn || send;
      app.classList.toggle('dark', cfg.theme === 'dark');
      XL = cfg.xl; YL = cfg.yl;
      rows = cfg.rows.map(function (r) { return { i: r.i, id: r.id, g: r.g, x: r.x, y: r.y }; });
      orig = cfg.orig.map(function (r) { return { x: r.x, y: r.y }; });
      n = rows.length;
      if (cfg.key !== curKey) {
        curKey = cfg.key;
        setDomain();
        x0 = r2((AX.lo + AX.hi) / 2);
        showBoxes = n <= 30;
        $('boxes').checked = showBoxes;
        pts = rows.map(function (r) { return { i: r.i, id: r.id, g: r.g, x: r.x, y: r.y }; });
      } else if (drag === null && !timer) {
        if (outside()) setDomain();
        pts = rows.map(function (r) { return { i: r.i, id: r.id, g: r.g, x: r.x, y: r.y }; });
      }
      $('predX').value = x0;
      render();
    }
  };
}
"""

DRAG_COMP = st.components.v2.component("drag_scatter", html=DRAG_HTML, css=DRAG_CSS, js=DRAG_JS)


def drag_scatter(sub, orig_df, xv, yv):
    """Diagram sebar dengan titik yang bisa diseret. Hasil seretan dikirim balik ke Python lewat trigger 'moved'."""
    try:
        theme = st.context.theme.type or "light"
    except Exception:
        theme = "light"
    o = orig_df.reindex(sub.index)[[xv, yv]].fillna(sub[[xv, yv]])
    g = sub["Gender"].tolist() if "Gender" in sub else [""] * len(sub)
    cfg = {
        "key": f"{xv}|{yv}|{len(sub)}", "theme": theme, "xl": L(xv), "yl": L(yv),
        "rows": [{"i": int(i), "id": int(i) + 1, "x": float(x), "y": float(y), "g": gg}
                 for i, x, y, gg in zip(sub.index, sub[xv], sub[yv], g)],
        "orig": [{"x": float(x), "y": float(y)} for x, y in zip(o[xv], o[yv])],
    }
    return DRAG_COMP(data=cfg, key=f"drag_{xv}_{yv}", on_moved_change=lambda: None)


def apply_moves(df, moved, xv, yv):
    """Terapkan hasil seretan ke data utama (idempoten), lalu jalankan ulang agar seluruh dashboard ikut berubah."""
    if not moved:
        return
    new, changed = df.copy(), False
    for p in moved.get("points", []):
        i = p.get("i")
        if i not in new.index:
            continue
        for col, val in ((xv, p["x"]), (yv, p["y"])):
            if not pd.api.types.is_float_dtype(new[col]):
                new[col] = new[col].astype(float)
            if not np.isclose(new.at[i, col], val):
                new.at[i, col] = val
                changed = True
    if changed:
        st.session_state.base = new
        st.session_state.ed_ver += 1
        st.rerun()


@st.cache_data
def read_csv(src):
    return pd.read_csv(src)


# ------------------------------------------------------------------ data & filter
st.sidebar.header("Data dan filter")
upload = st.sidebar.file_uploader("Ganti data (CSV)", type="csv")
orig_df = read_csv(upload) if upload else read_csv(DATA)
src_id = f"{upload.name}:{upload.size}" if upload else "bawaan"
if st.session_state.get("src_id") != src_id:  # sumber data berganti -> mulai dari data awal
    st.session_state.src_id = src_id
    st.session_state.base = orig_df.copy()
    st.session_state.ed_ver = 0

st.title("Kebiasaan mahasiswa dan nilai ujian")
st.caption("Statistik deskriptif, hubungan dua variabel dengan prediksi, dan keputusan yang dapat diambil.")

with st.expander("Ubah data (klik sel untuk mengedit)"):
    base = st.session_state.base
    cfg_cols = {"Gender": st.column_config.SelectboxColumn("Gender", options=["F", "M"], required=True)} if "Gender" in base else {}
    locked = [c for c in base.columns if "id" in c.lower()]
    df = st.data_editor(base, key=f"ed_{st.session_state.ed_ver}", num_rows="fixed", width="stretch",
                        height=300, disabled=locked, column_config=cfg_cols)
    n_diff = int((~((df == orig_df) | (df.isna() & orig_df.isna()))).to_numpy().sum())
    b1, b2 = st.columns(2)
    if b1.button("Kembalikan data awal", disabled=n_diff == 0):
        st.session_state.base = orig_df.copy()
        st.session_state.ed_ver += 1
        st.rerun()
    b2.download_button("Unduh data hasil edit (CSV)", df.to_csv(index=False).encode("utf-8"),
                       "data_diedit.csv", "text/csv")
    st.caption(f"{n_diff} sel berbeda dari data awal. Perubahan (lewat tabel ini atau dengan menyeret titik) berlaku untuk "
               "seluruh dashboard selama sesi ini dan hilang bila halaman dimuat ulang. Unduh CSV untuk menyimpannya.")

num_cols = [c for c in df.select_dtypes("number").columns if "id" not in c.lower()]
has_g = "Gender" in df.columns
d = df.copy()
if has_g:
    pick = st.sidebar.multiselect("Jenis kelamin", ["F", "M"], default=["F", "M"],
                                  format_func=lambda g: {"F": "Perempuan (F)", "M": "Laki-laki (M)"}[g])
    d = d[d["Gender"].isin(pick)]
if "Age" in df.columns and df["Age"].nunique() > 1:
    lo, hi = int(np.floor(df["Age"].min())), int(np.ceil(df["Age"].max()))
    a1, a2 = st.sidebar.slider("Rentang usia", lo, hi, (lo, hi))
    d = d[(d["Age"] >= a1) & (d["Age"] <= a2)]
st.sidebar.caption(f"{len(d)} dari {len(df)} baris dipakai.")

if len(d) < 5 or len(num_cols) < 2:
    st.warning("Data terlalu sedikit atau kurang kolom numerik. Ubah filter atau data.")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Ringkasan", "Distribusi", "Dua variabel + prediksi", "Korelasi dan perbandingan", "Keputusan"])

# ------------------------------------------------------------------ 1. ringkasan
with tab1:
    if "Exam_Score" in d:
        s = d["Exam_Score"]
        c = st.columns(5)
        c[0].metric("Mahasiswa", len(d))
        c[1].metric("Rata-rata nilai", fm(s.mean(), 1))
        c[2].metric("Median nilai", fm(s.median(), 1))
        c[3].metric("Nilai >= 75", f"{(s >= 75).mean() * 100:.0f}%")
        c[4].metric("Nilai < 60", f"{(s < 60).mean() * 100:.0f}%")
    x = d[num_cols]
    tbl = pd.DataFrame({
        "Mean": x.mean(), "Median": x.median(), "Modus": x.mode().iloc[0], "Simp. baku": x.std(),
        "Varians": x.var(), "Min": x.min(), "Q1": x.quantile(.25), "Q3": x.quantile(.75),
        "Maks": x.max(), "Rentang": x.max() - x.min(), "IQR": x.quantile(.75) - x.quantile(.25),
        "CV (%)": x.std() / x.mean() * 100, "Skewness": x.skew(), "Kurtosis": x.kurt(),
    })
    tbl.index = [L(i) for i in tbl.index]
    st.subheader("Ringkasan statistik per variabel")
    st.dataframe(tbl.style.format("{:.2f}"), width="stretch")
    st.caption("Simpangan baku dan varians memakai rumus sampel (n - 1). Skewness mendekati 0 berarti simetris; "
               "kurtosis negatif berarti lebih datar dari kurva normal.")

# ------------------------------------------------------------------ 2. distribusi
with tab2:
    v = st.selectbox("Variabel", num_cols, index=num_cols.index("Exam_Score") if "Exam_Score" in num_cols else 0,
                     format_func=L, key="distvar")
    bins = st.slider("Jumlah kelompok (bin)", 4, 20, 10)
    color = alt.Color("Gender:N", scale=GCOL, title="Gender") if has_g else alt.value("#3b4a6b")
    hist = alt.Chart(d).mark_bar(clip=True).encode(
        alt.X(f"{v}:Q", bin=alt.Bin(maxbins=bins), title=L(v)), alt.Y("count()", title="Jumlah"), color=color)
    rule = alt.Chart(pd.DataFrame({"m": [d[v].mean()]})).mark_rule(color="black", strokeWidth=2, clip=True).encode(x="m:Q")
    st.altair_chart((hist + rule).properties(height=300).interactive(), width="stretch")
    st.caption("Grafik bisa digerakkan: seret untuk menggeser, scroll untuk zoom, klik dua kali untuk mengembalikan.")
    box = alt.Chart(d).mark_boxplot(extent=1.5).encode(
        alt.X(f"{v}:Q", title=L(v)), **({"y": alt.Y("Gender:N"), "color": color} if has_g else {})).properties(height=140)
    st.altair_chart(box, width="stretch")
    sk = d[v].skew()
    bentuk = "cukup simetris" if abs(sk) < .5 else ("condong ke kanan" if sk > 0 else "condong ke kiri")
    st.write(f"**{L(v)}**: mean {fm(d[v].mean())} (garis hitam), median {fm(d[v].median())}, simpangan baku "
             f"{fm(d[v].std())}. Distribusinya {bentuk} (skewness {fm(sk)}).")

# ------------------------------------------------------------------ 3. dua variabel + prediksi
with tab3:
    st.subheader("Statistik khusus dua variabel dengan prediksi")
    c1, c2 = st.columns(2)
    xv = c1.selectbox("Variabel X (penjelas)", num_cols, index=num_cols.index("Study_Hours") if "Study_Hours" in num_cols else 0, format_func=L)
    yv = c2.selectbox("Variabel Y (yang diprediksi)", num_cols, index=num_cols.index("Exam_Score") if "Exam_Score" in num_cols else 1, format_func=L)
    if xv == yv:
        st.warning("Pilih dua variabel yang berbeda.")
    else:
        sub = d[[xv, yv] + (["Gender"] if has_g else [])].dropna()
        n = len(sub)
        X, Y = sub[xv].to_numpy(float), sub[yv].to_numpy(float)
        res = stats.linregress(X, Y)
        r, r2, b, a, p = res.rvalue, res.rvalue ** 2, res.slope, res.intercept, res.pvalue
        resid = Y - (a + b * X)
        s_e = np.sqrt((resid ** 2).sum() / (n - 2))
        tcrit = stats.t.ppf(.975, n - 2)
        sxx = ((X - X.mean()) ** 2).sum()
        rho = stats.spearmanr(X, Y).statistic

        # vonis arah
        if p >= .05 or np.isnan(r):
            arrow, word, col = "→", "Tidak ada pola naik atau turun yang jelas", FLAT
        elif r > 0:
            arrow, word, col = "↗", "Pola naik (positif)", UP
        else:
            arrow, word, col = "↘", "Pola turun (negatif)", DOWN
        st.markdown(
            f"<div style='border:1px solid #d5dbe4;border-radius:8px;padding:12px 18px;display:flex;gap:16px;align-items:center'>"
            f"<div style='font-size:2.4rem;color:#fff;background:{col};border-radius:50%;width:64px;height:64px;"
            f"display:flex;align-items:center;justify-content:center'>{arrow}</div>"
            f"<div><b style='font-size:1.2rem'>{word}</b><br>Setiap kenaikan 1 satuan {L(xv).lower()}, "
            f"{L(yv).lower()} rata-rata {'naik' if b > 0 else 'turun'} {fm(abs(b))} satuan "
            f"(r = {fm(r)}, p {'< 0,001' if p < .001 else '= ' + fm(p, 3)}).</div></div>", unsafe_allow_html=True)

        m = st.columns(6)
        m[0].metric("Pearson r", fm(r)); m[1].metric("r² (daya jelas)", f"{r2 * 100:.0f}%")
        m[2].metric("Kemiringan (b)", fm(b)); m[3].metric("Intersep (a)", fm(a))
        m[4].metric("Spearman ρ", fm(rho)); m[5].metric("n", n)

        with st.expander("Statistik deskriptif kedua variabel dan detail regresi", expanded=True):
            two = pd.DataFrame({xv: sub[xv], yv: sub[yv]}).agg(["mean", "median", "std", "min", "max", "skew"]).T
            two.columns = ["Mean", "Median", "Simp. baku", "Min", "Maks", "Skewness"]
            two.index = [f"{L(xv)} (X)", f"{L(yv)} (Y)"]
            st.dataframe(two.style.format("{:.2f}"), width="stretch")
            ci = (b - tcrit * res.stderr, b + tcrit * res.stderr)
            st.markdown(
                f"- Persamaan: **ŷ = {fm(a)} {'+' if b >= 0 else '-'} {fm(abs(b))}·X**\n"
                f"- Kovarians: {fm(np.cov(X, Y)[0, 1])}\n"
                f"- Selang kepercayaan 95% untuk kemiringan: [{fm(ci[0])}; {fm(ci[1])}]\n"
                f"- Galat baku residual (s): {fm(s_e)} satuan Y")

        # grafik dengan pita prediksi
        gx = np.linspace(X.min(), X.max(), 60)
        gy = a + b * gx
        h = 1 / n + (gx - X.mean()) ** 2 / sxx
        grid = pd.DataFrame({"x": gx, "y": gy,
                             "pl": gy - tcrit * s_e * np.sqrt(1 + h), "ph": gy + tcrit * s_e * np.sqrt(1 + h),
                             "cl": gy - tcrit * s_e * np.sqrt(h), "ch": gy + tcrit * s_e * np.sqrt(h)})
        band_p = alt.Chart(grid).mark_area(opacity=.12, color=col, clip=True).encode(x="x:Q", y="pl:Q", y2="ph:Q")
        band_c = alt.Chart(grid).mark_area(opacity=.25, color=col, clip=True).encode(x="x:Q", y="cl:Q", y2="ch:Q")
        line = alt.Chart(grid).mark_line(color=col, strokeWidth=3, clip=True).encode(x=alt.X("x:Q", title=L(xv)), y=alt.Y("y:Q", title=L(yv), scale=alt.Scale(zero=False)))
        pc = alt.Color("Gender:N", scale=GCOL) if has_g else alt.value("#3b4a6b")
        pts = alt.Chart(sub).mark_circle(size=60, opacity=.75, clip=True).encode(
            x=alt.X(f"{xv}:Q", scale=alt.Scale(zero=False)), y=alt.Y(f"{yv}:Q", scale=alt.Scale(zero=False)), color=pc,
            tooltip=[xv, yv] + (["Gender"] if has_g else []))
        st.altair_chart((band_p + band_c + line + pts).properties(height=380).interactive(), width="stretch")
        st.caption("Seret untuk menggeser, scroll untuk zoom, klik dua kali untuk reset. Garis = regresi. Pita pekat = selang kepercayaan 95% rata-rata Y. Pita tipis = selang prediksi 95% untuk satu mahasiswa baru.")

        st.markdown("#### Seret titik, lihat korelasinya berubah")
        st.caption("Titik yang digeser langsung mengubah datanya, sehingga tabel, grafik lain, prediksi, dan keputusan ikut dihitung ulang.")
        res = drag_scatter(sub, orig_df, xv, yv)
        apply_moves(df, getattr(res, "moved", None), xv, yv)

        # prediksi
        st.markdown("#### Prediksi")
        step = 0.1 if np.issubdtype(sub[xv].dtype, np.floating) and (sub[xv] % 1 != 0).any() else 1.0
        x0 = st.number_input(f"Masukkan nilai {L(xv).lower()} (X)", value=float(round(X.mean() / step) * step), step=float(step))
        yh = a + b * x0
        hh = 1 / n + (x0 - X.mean()) ** 2 / sxx
        pi_ = tcrit * s_e * np.sqrt(1 + hh)
        ci_ = tcrit * s_e * np.sqrt(hh)
        k = st.columns(3)
        k[0].metric(f"Prediksi {L(yv).lower()}", fm(yh, 1))
        k[1].metric("Selang prediksi 95% (1 orang)", f"{fm(yh - pi_, 1)} – {fm(yh + pi_, 1)}")
        k[2].metric("Selang kepercayaan 95% (rata-rata)", f"{fm(yh - ci_, 1)} – {fm(yh + ci_, 1)}")
        if x0 < X.min() or x0 > X.max():
            st.warning(f"X = {fm(x0)} di luar rentang data ({fm(X.min())} sampai {fm(X.max())}). Ini ekstrapolasi, hasilnya kurang andal.")
        st.caption("Prediksi berasal dari garis regresi; bukan kepastian, dan menunjukkan keterkaitan, bukan sebab-akibat.")
        tbl_x = np.linspace(X.min(), X.max(), 6)
        st.dataframe(pd.DataFrame({L(xv): tbl_x, f"Prediksi {L(yv)}": a + b * tbl_x,
                                   "Batas bawah 95%": a + b * tbl_x - tcrit * s_e * np.sqrt(1 + 1 / n + (tbl_x - X.mean()) ** 2 / sxx),
                                   "Batas atas 95%": a + b * tbl_x + tcrit * s_e * np.sqrt(1 + 1 / n + (tbl_x - X.mean()) ** 2 / sxx)}
                                  ).style.format("{:.1f}"), width="stretch", hide_index=True)

        # diagnosis sisaan
        with st.expander("Periksa kecocokan model (sisaan) dan pola per jenis kelamin"):
            rd = pd.DataFrame({"Nilai prediksi": a + b * X, "Sisaan": resid})
            rp = alt.Chart(rd).mark_circle(size=50, opacity=.7, color="#3b4a6b", clip=True).encode(x="Nilai prediksi:Q", y="Sisaan:Q")
            st.altair_chart((rp + alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color="black", clip=True).encode(y="z:Q")).properties(height=240).interactive(), width="stretch")
            st.write(f"RMSE = {fm(np.sqrt((resid ** 2).mean()))}. Sisaan yang menyebar acak di sekitar 0 menandakan garis lurus cukup cocok.")
            if has_g:
                rows = []
                for g, part in sub.groupby("Gender"):
                    if len(part) >= 5:
                        rg = stats.linregress(part[xv], part[yv])
                        rows.append({"Gender": g, "n": len(part), "r": rg.rvalue, "Kemiringan": rg.slope, "Intersep": rg.intercept})
                if rows:
                    st.dataframe(pd.DataFrame(rows).style.format({"r": "{:.2f}", "Kemiringan": "{:.2f}", "Intersep": "{:.2f}"}), hide_index=True)
                    st.caption("Jika arah pola sama di kedua kelompok, hubungannya tidak sekadar akibat perbedaan jenis kelamin.")

# ------------------------------------------------------------------ 4. korelasi & perbandingan
with tab4:
    cm = d[num_cols].corr()
    long = cm.stack().reset_index()
    long.columns = ["a", "b", "r"]
    long["a"], long["b"] = long["a"].map(L), long["b"].map(L)
    base = alt.Chart(long).encode(x=alt.X("b:N", title=None), y=alt.Y("a:N", title=None))
    heat = base.mark_rect().encode(color=alt.Color("r:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 1]), title="r"))
    txt = base.mark_text(fontSize=11).encode(text=alt.Text("r:Q", format=".2f"),
                                              color=alt.condition("abs(datum.r) > 0.55", alt.value("white"), alt.value("black")))
    st.subheader("Korelasi antar variabel")
    st.altair_chart((heat + txt).properties(height=420), width="stretch")
    if has_g:
        st.subheader("Rata-rata menurut jenis kelamin")
        gm = d.groupby("Gender")[num_cols].mean().T
        gm.index = [L(i) for i in gm.index]
        if {"F", "M"} <= set(gm.columns):
            gm["Selisih M terhadap F (%)"] = (gm["M"] / gm["F"] - 1) * 100
        st.dataframe(gm.style.format("{:.2f}"), width="stretch")

# ------------------------------------------------------------------ 5. keputusan
with tab5:
    st.subheader("Keputusan yang dapat diambil dari data ini")
    need = {"Exam_Score", "Attendance", "Sleep_Hours", "Screen_Hours", "Study_Hours", "Gender", "Age"}
    if not need <= set(df.columns):
        st.info("Keputusan otomatis hanya tersedia untuk kolom bawaan Latihan 1 (Exam_Score, Attendance, Sleep_Hours, "
                "Screen_Hours, Study_Hours, Gender, Age).")
    else:
        st.caption("Dihitung dari seluruh data (tanpa filter sidebar).")

        def grp(mask):
            sub_ = df[mask]
            return len(sub_), sub_["Exam_Score"].mean()

        n1, m1 = grp(df["Attendance"] <= 80)
        n2, m2 = grp(df["Attendance"] > 90)
        low = df[df["Exam_Score"] < 60]
        n3, m3 = grp(df["Sleep_Hours"] < 6)
        n4, m4 = grp(df["Sleep_Hours"] >= 7)
        n5, m5 = grp(df["Screen_Hours"] > 8)
        n6, m6 = grp(df["Screen_Hours"] <= 4)
        g = df.groupby("Gender").mean(numeric_only=True)
        ages = df.groupby("Age")["Exam_Score"].mean()
        items = [
            ("Pasang peringatan dini berbasis kehadiran",
             f"Mahasiswa dengan kehadiran ≤ 80% ({n1} orang) rata-rata bernilai {fm(m1, 1)}, sedangkan yang hadir di atas 90% ({n2} orang) {fm(m2, 1)}. "
             f"Kehadiran paling mudah dipantau, sehingga cocok menjadi pemicu pendampingan."),
            ("Dampingi kelompok berisiko nilai < 60",
             f"Ada {len(low)} mahasiswa dengan nilai di bawah 60. Rata-rata mereka belajar {fm(low['Study_Hours'].mean(), 1)} jam, tidur {fm(low['Sleep_Hours'].mean(), 1)} jam, "
             f"hadir {fm(low['Attendance'].mean(), 0)}%, dan {fm(low['Screen_Hours'].mean(), 1)} jam di depan layar."),
            ("Fokuskan program pada kelompok dengan nilai terendah",
             f"Rata-rata nilai per jenis kelamin: " + ", ".join(f"{k} = {fm(v, 1)}" for k, v in g["Exam_Score"].items()) +
             f". Jam belajar: " + ", ".join(f"{k} = {fm(v, 1)}" for k, v in g["Study_Hours"].items()) + "."),
            ("Dorong tidur cukup dan batasi waktu layar",
             f"Tidur < 6 jam ({n3} orang): nilai {fm(m3, 1)}; tidur ≥ 7 jam ({n4} orang): {fm(m4, 1)}. "
             f"Layar > 8 jam ({n5} orang): {fm(m5, 1)}; layar ≤ 4 jam ({n6} orang): {fm(m6, 1)}."),
            ("Perhatikan angkatan yang lebih tua",
             f"Rata-rata nilai turun dari {fm(ages.iloc[0], 1)} (usia {ages.index[0]}) menjadi {fm(ages.iloc[-1], 1)} (usia {ages.index[-1]}). "
             f"Periksa dulu apakah penyebabnya beban di luar kuliah."),
            ("Pakai kepuasan dan pengeluaran sebagai sinyal, bukan target",
             f"Keduanya sangat terkait dengan nilai (r kepuasan = {fm(df['Satisfaction'].corr(df['Exam_Score']))}, r pengeluaran = "
             f"{fm(df['Monthly_Spending'].corr(df['Exam_Score']))}), tetapi mengubah keduanya belum tentu mengubah nilai."),
        ]
        for i, (t, body) in enumerate(items, 1):
            st.markdown(f"**{i}. {t}**  \n{body}")
        st.warning("**Batas kesimpulan.** Hampir semua variabel berkorelasi sangat kuat (|r| sering di atas 0,9), pola yang jarang pada data nyata, "
                   "jadi data ini kemungkinan data latihan. Ini data pengamatan satu waktu (n = 100): menunjukkan keterkaitan, bukan sebab-akibat, "
                   "dan efek tiap kebiasaan tidak bisa dipisahkan. Sebelum kebijakan besar, lakukan uji lanjutan (uji beda rata-rata, regresi berganda).")
