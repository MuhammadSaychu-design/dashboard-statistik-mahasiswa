import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

DATA = Path(__file__).parent / "data" / "latihan1.csv"
LABEL = {
    "Age": "Usia",
    "Study_Hours": "Jam belajar",
    "Sleep_Hours": "Jam tidur",
    "Attendance": "Kehadiran (%)",
    "Exam_Score": "Nilai ujian",
    "Monthly_Spending": "Pengeluaran bulanan",
    "Screen_Hours": "Jam layar",
    "Satisfaction": "Kepuasan (1-10)",
}
GCOL = alt.Scale(domain=["F", "M"], range=["#0c8f8f", "#d9772b"])
UP, DOWN, FLAT = "#2f5da8", "#b8442b", "#6b7385"


@st.cache_data
def read_csv(src):
    return pd.read_csv(src)


# --- BACA DATA AWAL SECARA GLOBAL ---

# =========================================================================
# 2. TAMPILAN HALAMAN PERTAMA (Halaman Pembuka/Filter)
# =========================================================================
# --- BACA DATA AWAL SECARA GLOBAL (Rapat ke kiri tanpa spasi) ---
if "halaman" not in st.session_state:
    st.session_state.halaman = "pembuka"
upload = None
orig_df = read_csv(upload) if upload else read_csv(DATA)
src_id = f"{upload.name}:{upload.size}" if upload else "bawaan"

if st.session_state.get("src_id") != src_id:
    st.session_state.src_id = src_id
    st.session_state.base = orig_df.copy()
    st.session_state.ed_ver = 0

num_cols = [c for c in orig_df.select_dtypes("number").columns if "id" not in c.lower()]
has_g = "Gender" in orig_df.columns

# # 2. TAMPILAN HALAMAN PERTAMA (Halaman Pembuka/Filter)
if st.session_state.halaman == "pembuka":
    st.title("Selamat Datang di Aplikasi Dashboard")
    st.subheader("Silakan atur filter data Anda terlebih dahulu:")

    upload = st.file_uploader("Ganti data (CSV)", type="csv")
    orig_df = read_csv(upload) if upload else read_csv(DATA)
    if st.session_state.get("src_id") != (f"{upload.name}:{upload.size}" if upload else "bawaan"):
        st.session_state.src_id = f"{upload.name}:{upload.size}" if upload else "bawaan"
        st.session_state.base = orig_df.copy()
        st.session_state.ed_ver = 0
    num_cols = [c for c in orig_df.select_dtypes("number").columns if "id" not in c.lower()]
    has_g = "Gender" in orig_df.columns


    # Wadah data yang akan difilter (Gunakan 4 spasi masuk ke kanan)
    d = orig_df.copy()

    # Menampilkan filter langsung di halaman utama pembuka
    if has_g:
        pick = st.multiselect(
            "Jenis kelamin",
            ["F", "M"],
            default=["F", "M"],
            format_func=lambda g: {"F": "Perempuan (F)", "M": "Laki-laki (M)"}[g],
        )
        d = d[d["Gender"].isin(pick)]

    if "Age" in orig_df.columns and orig_df["Age"].nunique() > 1:
        lo, hi = int(np.floor(orig_df["Age"].min())), int(np.ceil(orig_df["Age"].max()))
        a1, a2 = st.slider("Rentang usia", lo, hi, (lo, hi))
        d = d[(d["Age"] >= a1) & (d["Age"] <= a2)]

    # Simpan hasil filter ke session_state agar bisa terbaca di halaman kedua
    st.session_state.data_terfilter = d

    st.write(f"👉 **{len(d)} dari {len(orig_df)} baris data siap digunakan.**")
    st.write("---")

    # Tombol masuk
    if st.button("Masuk ke Dashboard Website →", type="primary"):
        st.session_state.halaman = "dashboard"
        st.rerun()

# =========================================================================
# 3. TAMPILAN HALAMAN KEDUA (Isi Web Utama)
# =========================================================================
elif st.session_state.halaman == "dashboard":
    # Tombol Kembali jika ingin mengubah filter lagi
    if st.button("⬅ Kembali ke Pengaturan Filter"):
        st.session_state.halaman = "pembuka"
        st.rerun()

    # 1. Ambil data hasil filter halaman pembuka (Beri 4 spasi di awal)
    if "data_terfilter" in st.session_state:
        d = st.session_state.data_terfilter
    else:
        d = orig_df.copy()

    # 2. Hitung kolom angka berdasarkan data terfilter 'd' (Wajib di sini agar tidak KeyError)
    num_cols = [c for c in d.select_dtypes("number").columns if "id" not in c.lower()]
    has_g = "Gender" in d.columns

    # 3. Pindahkan Judul Utama ke luar expander agar langsung kelihatan
    st.title("Kebiasaan mahasiswa dan nilai ujian")

    # --- KODE EDITOR DATA DIKEMBALIKAN KE SINI (Hanya muncul di halaman dashboard) ---
    with st.expander("Ubah data (klik sel untuk mengedit)"):
        base = st.session_state.base
        locked = [c for c in base.columns if "id" in c.lower()]
        df = st.data_editor(
            base,
            key=f"ed_{st.session_state.ed_ver}",
            num_rows="fixed",
            width="stretch",
            height=300,
            disabled=locked,
        )

    def L(c):
        return LABEL.get(c, c.replace("_", " "))


    def fm(v, d=2):
        """Format angka gaya Indonesia (koma desimal)."""
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "-"
        return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    LAB_HTML = r"""<!doctype html>
    <html lang="id" data-theme="__THEME__"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>Ubah data, lihat korelasinya berubah</title>
    <style>
    :root{--bg:#eef1f6;--card:#fff;--ink:#172033;--mut:#5b6577;--line:#d5dbe4;--pos:#2f5da8;--f:#0c8f8f;--m:#d9772b;--neg:#b8442b;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
    @media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1522;--card:#172033;--ink:#e6eaf2;--mut:#9aa5b8;--line:#2b374d;--pos:#6f9bea;--f:#3cc0b8;--m:#f0a15a;--neg:#e5836b}}
    :root[data-theme="dark"]{--bg:#0f1522;--card:#172033;--ink:#e6eaf2;--mut:#9aa5b8;--line:#2b374d;--pos:#6f9bea;--f:#3cc0b8;--m:#f0a15a;--neg:#e5836b}
    *{box-sizing:border-box}html{scroll-padding-top:env(safe-area-inset-top,0px)}
    body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,"Segoe UI",sans-serif;font-variant-numeric:tabular-nums}
    main{max-width:1180px;margin:0 auto;padding:16px}
    h1{font-size:1.35rem;margin:0 0 12px}
    .bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin-bottom:14px}
    .bar.dirty{border-color:var(--m)}
    .bar .msg{flex:1 1 240px;color:var(--mut);font-size:.9rem}
    .badge{border-radius:99px;padding:3px 12px;font-size:.84rem;font-weight:600;white-space:nowrap}
    .badge.w{background:color-mix(in srgb,var(--m) 22%,transparent);color:var(--m)}
    .badge.o{background:color-mix(in srgb,var(--f) 20%,transparent);color:var(--f)}
    button{font:inherit;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:6px;padding:6px 14px;cursor:pointer}
    button:hover:not(:disabled){border-color:var(--ink)}button:disabled{opacity:.4;cursor:default}
    button.pri{background:var(--pos);border-color:var(--pos);color:#fff;font-weight:600}
    .grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(280px,1fr);gap:14px;align-items:start}
    @media(max-width:820px){.grid{grid-template-columns:minmax(0,1fr)}}
    .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:14px}
    .card h2{margin:0 0 8px;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
    svg{width:100%;height:auto;display:block;touch-action:none;user-select:none}
    .g{stroke:var(--line)}.ax{fill:var(--mut);font-size:11px}.al{fill:var(--mut);font-size:12px;font-weight:600}
    .mn{stroke:var(--ink);stroke-width:1.4;stroke-dasharray:5 4;opacity:.8}.gd{stroke:var(--ink);stroke-dasharray:2 3;opacity:.7}
    .lb{fill:var(--ink);font-size:11.5px;font-weight:600}.reg{stroke:var(--ink);stroke-width:3;stroke-linecap:round}
    .bp{fill:var(--f);fill-opacity:.14}.bn{fill:var(--m);fill-opacity:.18}
    .pt{fill:var(--pos);stroke:#fff;stroke-width:1.5;cursor:grab}.pt:hover{stroke-width:3}
    .pt.a,.pt:focus-visible{stroke:var(--ink);stroke-width:3;outline:none;cursor:grabbing}
    .pn{fill:var(--ink);font-size:11px;pointer-events:none}.pr{fill:none;stroke:var(--ink);stroke-width:2.5}
    .lg{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:.84rem;color:var(--mut);margin-top:6px}
    .lg i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
    .hint{color:var(--mut);font-size:.86rem;margin:8px 0 0}
    .rb{font-size:2.8rem;font-weight:600;line-height:1.1}
    .gauge{position:relative;height:10px;border-radius:6px;margin-top:10px;background:linear-gradient(90deg,var(--neg),var(--line) 50%,var(--f))}
    .gauge span{position:absolute;top:-4px;width:4px;height:18px;background:var(--ink);border-radius:2px;transform:translateX(-2px)}
    .gl{display:flex;justify-content:space-between;color:var(--mut);font-size:.75rem;margin:6px 0 8px}
    dl{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;margin:12px 0 0}dl div{border-top:1px solid var(--line);padding-top:5px}
    dt{color:var(--mut);font-size:.78rem}dd{margin:0;font-weight:600}
    .pd{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}.pd input{width:100%;accent-color:var(--pos)}
    .names{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}.names label{font-size:.82rem;color:var(--mut);display:grid;gap:2px;flex:1 1 110px}
    input[type=text],input[type=number]{font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:4px 7px;width:100%}
    .tw{max-height:300px;overflow:auto;border:1px solid var(--line);border-radius:6px}
    table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{padding:4px 8px;text-align:left;border-bottom:1px solid var(--line)}
    th{position:sticky;top:0;background:var(--card);color:var(--mut);font-weight:600}td:first-child{color:var(--mut);width:34px}
    td button{padding:1px 8px;border-color:transparent;color:var(--mut)}
    .w2{color:var(--m)}
    </style></head>
    <body><main>
    <div class="bar" id="bar" role="status">
    <span class="badge o" id="badge"></span><span class="msg" id="msg"></span>
    <button class="pri" id="save">Unduh CSV</button><button id="undo">Kembalikan data awal</button>
    </div>
    <div class="grid">
    <div>
        <div class="card">
        <svg id="svg" viewBox="0 0 640 440" role="group" aria-label="Diagram sebar, titik bisa diseret"></svg>
        <div class="lg"><span><i style="background:var(--pos);border-radius:50%"></i>Satu titik = satu baris data</span>
            <span><i style="background:var(--f);opacity:.6"></i>Kotak searah (+)</span><span><i style="background:var(--m);opacity:.7"></i>Kotak berlawanan (−)</span></div>
        <label class="hint" style="display:block"><input type="checkbox" id="bx" checked> Tampilkan kotak searah/berlawanan</label>
        <p class="hint">Seret titik di grafik, atau fokuskan titik lalu pakai tombol panah (Shift = langkah besar). Angka di tabel ikut berubah, dan sebaliknya.</p>
        </div>
    </div>
    <div>
        <div class="card"><h2>Korelasi (r)</h2>
        <div class="rb" id="rb">–</div><div class="gauge"><span id="gm"></span></div>
        <div class="gl"><span>−1</span><span>0</span><span>+1</span></div>
        <p id="rt" style="margin:6px 0 0"></p><dl id="st"></dl>
        <div class="pd"><label><span id="pl"></span><input type="range" id="px" aria-label="Nilai X untuk perkiraan"></label><p id="po" style="margin:6px 0 0"></p></div>
        </div>
        <div class="card"><h2>Tabel data (ketik untuk mengubah)</h2>
        <div class="names"><label>Nama X<input type="text" id="xn"></label><label>Nama Y<input type="text" id="yn"></label></div>
        <div class="tw"><table><thead><tr><th>No</th><th id="hx"></th><th id="hy"></th><th></th></tr></thead><tbody id="tb"></tbody></table></div>
        <button id="add" style="margin-top:8px">+ Tambah baris</button>
        </div>
    </div>
    </div>
    </main>
    <script>
    (function(){
    var $=function(i){return document.getElementById(i)},KEY='korelasi-interaktif-v1';
    var CFG=__CFG__,DEF={xn:CFG.xn,yn:CFG.yn,pts:CFG.pts};
    function clone(o){return JSON.parse(JSON.stringify(o))}
    function load(){return clone(DEF)}
    var saved=load(),pts=clone(saved.pts),xn=saved.xn||'X',yn=saved.yn||'Y',drag=null,x0=null,AX,AY,dX=0,dY=0,timer=null;
    var W=640,H=440,M={l:58,r:20,t:30,b:48},PW=W-M.l-M.r,PH=H-M.t-M.b,svg=$('svg');
    function fm(v,d){if(d===undefined)d=2;return(v==null||!isFinite(v))?'–':v.toLocaleString('id-ID',{minimumFractionDigits:d,maximumFractionDigits:d})}
    function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
    function cl(v,a,b){return Math.min(b,Math.max(a,v))}function r2(v){return Math.round(v*100)/100}
    function nice(lo,hi){if(hi-lo===0){lo-=1;hi+=1}var raw=(hi-lo)/6,mag=Math.pow(10,Math.floor(Math.log10(raw))),nr=raw/mag,step=(nr<1.5?1:nr<3?2:nr<7?5:10)*mag,a=Math.floor(lo/step+1e-9)*step,b=Math.ceil(hi/step-1e-9)*step,t=[];for(var v=a;v<=b+step/2;v+=step)t.push(Math.round(v/step)*step);return{lo:a,hi:b,ticks:t,step:step}}
    function span(k){var v=pts.map(function(p){return p[k]}),lo=Math.min.apply(null,v),hi=Math.max.apply(null,v),pad=(hi-lo)*.1||1;return nice(lo>=0?0:lo-pad,hi+pad)}
    function dec(s){return s>=1?0:Math.min(4,Math.ceil(-Math.log10(s)))}
    function sx(x){return M.l+(x-AX.lo)/(AX.hi-AX.lo)*PW}function sy(y){return M.t+PH-(y-AY.lo)/(AY.hi-AY.lo)*PH}
    function calc(){var n=pts.length,mx=0,my=0,i;for(i=0;i<n;i++){mx+=pts[i].x;my+=pts[i].y}mx/=n;my/=n;var sxx=0,syy=0,sxy=0;for(i=0;i<n;i++){var a=pts[i].x-mx,b=pts[i].y-my;sxx+=a*a;syy+=b*b;sxy+=a*b}var b1=sxx>0?sxy/sxx:NaN;return{n:n,mx:mx,my:my,b:b1,a:my-b1*mx,r:(sxx>0&&syy>0)?sxy/Math.sqrt(sxx*syy):NaN,cov:n>1?sxy/(n-1):NaN}}
    function chart(S){
    var h='<defs><clipPath id="cp"><rect x="'+M.l+'" y="'+M.t+'" width="'+PW+'" height="'+PH+'"/></clipPath></defs>',i;
    AX.ticks.forEach(function(t){var x=sx(t);h+='<line class="g" x1="'+x+'" x2="'+x+'" y1="'+M.t+'" y2="'+(M.t+PH)+'"/><text class="ax" x="'+x+'" y="'+(M.t+PH+16)+'" text-anchor="middle">'+fm(t,dX)+'</text>'});
    AY.ticks.forEach(function(t){var y=sy(t);h+='<line class="g" x1="'+M.l+'" x2="'+(M.l+PW)+'" y1="'+y+'" y2="'+y+'"/><text class="ax" x="'+(M.l-8)+'" y="'+(y+4)+'" text-anchor="end">'+fm(t,dY)+'</text>'});
    h+='<text class="al" x="'+(M.l+PW/2)+'" y="'+(H-8)+'" text-anchor="middle">'+esc(xn)+' (X)</text><text class="al" transform="translate(14 '+(M.t+PH/2)+') rotate(-90)" text-anchor="middle">'+esc(yn)+' (Y)</text><g clip-path="url(#cp)">';
    if($('bx').checked)for(i=0;i<S.n;i++){var p=pts[i],xa=sx(Math.min(p.x,S.mx)),xb=sx(Math.max(p.x,S.mx)),ya=sy(Math.max(p.y,S.my)),yb=sy(Math.min(p.y,S.my));h+='<rect class="'+((p.x-S.mx)*(p.y-S.my)>=0?'bp':'bn')+'" x="'+xa+'" y="'+ya+'" width="'+(xb-xa)+'" height="'+(yb-ya)+'"/>'}
    h+='<line class="mn" x1="'+sx(S.mx)+'" x2="'+sx(S.mx)+'" y1="'+M.t+'" y2="'+(M.t+PH)+'"/><line class="mn" x1="'+M.l+'" x2="'+(M.l+PW)+'" y1="'+sy(S.my)+'" y2="'+sy(S.my)+'"/>';
    if(isFinite(S.b))h+='<line class="reg" x1="'+sx(AX.lo)+'" y1="'+sy(S.a+S.b*AX.lo)+'" x2="'+sx(AX.hi)+'" y2="'+sy(S.a+S.b*AX.hi)+'"/>';
    h+='</g><text class="lb" x="'+cl(sx(S.mx),M.l+24,M.l+PW-24)+'" y="'+(M.t-8)+'" text-anchor="middle">X̄ = '+fm(S.mx,1)+'</text><text class="lb" x="'+(M.l+PW-4)+'" y="'+(sy(S.my)-6)+'" text-anchor="end">Ȳ = '+fm(S.my,1)+'</text>';
    if(isFinite(S.b)){h+='<text class="lb" x="'+(M.l+8)+'" y="'+(M.t+16)+'" style="font-weight:400">ŷ = '+fm(S.a)+(S.b>=0?' + ':' − ')+fm(Math.abs(S.b))+'·X</text>';var y0=S.a+S.b*x0;if(y0>=AY.lo&&y0<=AY.hi)h+='<line class="gd" x1="'+M.l+'" x2="'+sx(x0)+'" y1="'+sy(y0)+'" y2="'+sy(y0)+'"/><line class="gd" x1="'+sx(x0)+'" x2="'+sx(x0)+'" y1="'+sy(y0)+'" y2="'+(M.t+PH)+'"/><circle class="pr" cx="'+sx(x0)+'" cy="'+sy(y0)+'" r="7"/>'}
    for(i=0;i<S.n;i++){var q=pts[i];h+='<circle class="pt'+(drag===i?' a':'')+'" data-i="'+i+'" cx="'+sx(q.x)+'" cy="'+sy(q.y)+'" r="'+(drag===i?8:6.5)+'" tabindex="0" role="button" aria-label="Titik '+(i+1)+': X '+fm(q.x)+', Y '+fm(q.y)+'. Tombol panah mengubah nilai."><title>Titik '+(i+1)+': X = '+fm(q.x)+', Y = '+fm(q.y)+'</title></circle><text class="pn" x="'+(sx(q.x)+9)+'" y="'+(sy(q.y)-8)+'">'+(i+1)+'</text>'}
    svg.innerHTML=h}
    function strength(a){return a>=.8?'sangat kuat':a>=.6?'kuat':a>=.4?'sedang':a>=.2?'lemah':'sangat lemah'}
    function panel(S){var r=S.r;$('rb').textContent=fm(r);$('gm').style.left=(isFinite(r)?(r+1)/2*100:50)+'%';
    $('rt').textContent=!isFinite(r)?'Belum bisa dihitung: semua nilai X atau semua nilai Y sama.':Math.abs(r)<.2?'Hampir tidak ada hubungan garis lurus antara X dan Y.':'Hubungan '+strength(Math.abs(r))+' dan '+(r>0?'naik: X yang lebih besar cenderung bersama Y yang lebih besar.':'turun: X yang lebih besar cenderung bersama Y yang lebih kecil.')+' Sekitar '+Math.round(r*r*100)+'% variasi Y ikut dijelaskan X.';
    $('st').innerHTML=[['Jumlah data (n)',S.n],['r²',fm(r*r)],['Rata-rata X',fm(S.mx)],['Rata-rata Y',fm(S.my)],['Kemiringan (b)',fm(S.b)],['Intersep (a)',fm(S.a)]].map(function(a){return'<div><dt>'+a[0]+'</dt><dd>'+a[1]+'</dd></div>'}).join('');
    var px=$('px');px.min=AX.lo;px.max=AX.hi;px.step=(AX.hi-AX.lo)/200;px.value=x0;
    $('pl').innerHTML='Perkiraan '+esc(yn.toLowerCase())+' untuk X = <b>'+fm(x0,dX)+'</b>';var y0=S.a+S.b*x0;
    $('po').innerHTML=isFinite(y0)?esc(yn)+' diperkirakan <b>'+fm(y0,1)+'</b>.':'';
    var d=Math.abs(pts.length-saved.pts.length);pts.forEach(function(p,i){var s=saved.pts[i];if(s&&(s.x!==p.x||s.y!==p.y))d++});
    if(xn!==saved.xn||yn!==saved.yn)d=d||1;
    var b=$('badge');$('bar').classList.toggle('dirty',d>0);b.className='badge '+(d>0?'w':'o');b.textContent=d>0?'● Data diubah':'● Sama dengan data awal';
    $('msg').textContent=d>0?d+' baris berbeda dari data awal. Hitungan memakai data terbaru; unduh CSV untuk menyimpannya.':'Ubah angka di tabel atau seret titik di grafik; r, garis, dan kotak ikut berubah.';
    $('undo').disabled=d===0}
    function render(){if(drag===null){AX=span('x');AY=span('y');dX=dec(AX.step);dY=dec(AY.step)}
    var S=calc();if(x0===null||!isFinite(x0))x0=r2(S.mx);chart(S);panel(S)}
    function table(){$('hx').textContent=xn;$('hy').textContent=yn;
    $('tb').innerHTML=pts.map(function(p,i){return'<tr><td>'+(i+1)+'</td><td><input type="number" step="any" data-i="'+i+'" data-k="x" value="'+p.x+'" aria-label="X baris '+(i+1)+'"></td><td><input type="number" step="any" data-i="'+i+'" data-k="y" value="'+p.y+'" aria-label="Y baris '+(i+1)+'"></td><td><button data-del="'+i+'" aria-label="Hapus baris '+(i+1)+'"'+(pts.length<=2?' disabled':'')+'>×</button></td></tr>'}).join('')}
    function syncRow(i){['x','y'].forEach(function(k){var e=$('tb').querySelector('[data-i="'+i+'"][data-k="'+k+'"]');if(e&&e!==document.activeElement)e.value=pts[i][k]})}
    function toData(e){var rc=svg.getBoundingClientRect(),px=(e.clientX-rc.left)*W/rc.width,py=(e.clientY-rc.top)*H/rc.height;return{x:r2(cl(AX.lo+(px-M.l)/PW*(AX.hi-AX.lo),AX.lo,AX.hi)),y:r2(cl(AY.lo+(M.t+PH-py)/PH*(AY.hi-AY.lo),AY.lo,AY.hi))}}
    svg.addEventListener('pointerdown',function(e){var c=e.target.closest('[data-i]');if(!c)return;drag=+c.getAttribute('data-i');if(svg.setPointerCapture)svg.setPointerCapture(e.pointerId);e.preventDefault();render()});
    svg.addEventListener('pointermove',function(e){if(drag===null)return;var p=toData(e);pts[drag].x=p.x;pts[drag].y=p.y;syncRow(drag);render()});
    function end(){if(drag!==null){drag=null;render()}}svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
    svg.addEventListener('keydown',function(e){var c=e.target.closest('[data-i]');if(!c)return;var i=+c.getAttribute('data-i'),k=e.shiftKey?10:1,sxs=(AX.hi-AX.lo)/100*k,sys=(AY.hi-AY.lo)/100*k,p=pts[i];
    if(e.key==='ArrowLeft')p.x=r2(cl(p.x-sxs,AX.lo,AX.hi));else if(e.key==='ArrowRight')p.x=r2(cl(p.x+sxs,AX.lo,AX.hi));else if(e.key==='ArrowUp')p.y=r2(cl(p.y+sys,AY.lo,AY.hi));else if(e.key==='ArrowDown')p.y=r2(cl(p.y-sys,AY.lo,AY.hi));else return;
    e.preventDefault();syncRow(i);render();var el=svg.querySelector('[data-i="'+i+'"]');if(el)el.focus({preventScroll:true})});
    $('tb').addEventListener('input',function(e){var t=e.target;if(!t.dataset||!t.dataset.k)return;var v=parseFloat(t.value);if(!isFinite(v))return;pts[+t.dataset.i][t.dataset.k]=v;render()});
    $('tb').addEventListener('click',function(e){var t=e.target.closest('[data-del]');if(!t||pts.length<=2)return;pts.splice(+t.getAttribute('data-del'),1);table();render()});
    $('add').addEventListener('click',function(){var S=calc();pts.push({x:r2(S.mx),y:r2(S.my)});table();render()});
    $('px').addEventListener('input',function(e){x0=parseFloat(e.target.value);render()});$('bx').addEventListener('change',render);
    $('xn').value=xn;$('yn').value=yn;
    $('xn').addEventListener('input',function(e){xn=e.target.value||'X';$('hx').textContent=xn;render()});$('yn').addEventListener('input',function(e){yn=e.target.value||'Y';$('hy').textContent=yn;render()});
    $('save').addEventListener('click',function(){var q=function(t){return '"'+String(t).replace(/"/g,'""')+'"'},rows=['No,'+q(xn)+','+q(yn)];pts.forEach(function(p,i){rows.push((i+1)+','+p.x+','+p.y)});var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([rows.join('\n')],{type:'text/csv;charset=utf-8'}));a.download='data_diedit.csv';document.body.appendChild(a);a.click();document.body.removeChild(a)});
    $('undo').addEventListener('click',function(){pts=clone(saved.pts);xn=saved.xn;yn=saved.yn;$('xn').value=xn;$('yn').value=yn;table();render()});
    table();render();
    })();
    </script></body></html>
    """

    def lab(pair, xv, yv, height=900):
        """Tabel + grafik yang saling terhubung (ketik angka atau seret titik), seluruhnya berjalan di browser."""
        try:
            theme = st.context.theme.type or "light"
        except Exception:
            theme = "light"
        cfg = {
            "xn": L(xv),
            "yn": L(yv),
            "pts": [{"x": float(x), "y": float(y)} for x, y in zip(pair[xv], pair[yv])],
        }
        html = (
            LAB_HTML.replace(
                "__CFG__", json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/")
            )
            .replace("__THEME__", theme)
            .replace(
                'id="bx" checked', 'id="bx"' + (" checked" if len(pair) <= 30 else "")
            )
        )
        if hasattr(st, "iframe"):
            st.iframe(html, height=height)
        else:
            import streamlit.components.v1 as components

            components.html(html, height=height, scrolling=True)

    st.title("Kebiasaan mahasiswa dan nilai ujian")
    st.caption(
        "Statistik deskriptif, hubungan dua variabel dengan prediksi, dan keputusan yang dapat diambil."
    )

    with st.expander("Ubah data (klik sel untuk mengedit)"):
        base = st.session_state.base
        cfg_cols = (
            {
                "Gender": st.column_config.SelectboxColumn(
                    "Gender", options=["F", "M"], required=True
                )
            }
            if "Gender" in base
            else {}
        )
        locked = [c for c in base.columns if "id" in c.lower()]

        # Menampilkan tabel editor data dengan spasi menjorok yang benar

        n_diff = int(
            (~((df == orig_df) | (df.isna() & orig_df.isna()))).to_numpy().sum()
        )
        b1, b2 = st.columns(2)
        if b1.button("Kembalikan data awal", disabled=n_diff == 0):
            st.session_state.base = orig_df.copy()
            st.session_state.ed_ver += 1
            st.rerun()

        b2.download_button(
            "Unduh data hasil edit (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            "data_diedit.csv",
            "text/csv",
        )
        st.caption(
            f"{n_diff} sel berbeda dari data awal. Perubahan (lewat tabel ini atau dengan menyeret titik) berlaku untuk "
            "seluruh dashboard selama sesi ini dan hilang bila halaman dimuat ulang. Unduh CSV untuk menyimpannya."
        )

    if len(d) < 5 or len(num_cols) < 2:
        st.warning(
            "Data terlalu sedikit atau kurang kolom numerik. Ubah filter atau data."
        )
        st.stop()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Ringkasan",
            "Distribusi",
            "Dua variabel + prediksi",
            "Korelasi dan perbandingan",
            "Keputusan",
        ]
    )

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
        tbl = pd.DataFrame(
            {
                "Mean": x.mean(),
                "Median": x.median(),
                "Modus": x.mode().iloc[0],
                "Simp. baku": x.std(),
                "Varians": x.var(),
                "Min": x.min(),
                "Q1": x.quantile(0.25),
                "Q3": x.quantile(0.75),
                "Maks": x.max(),
                "Rentang": x.max() - x.min(),
                "IQR": x.quantile(0.75) - x.quantile(0.25),
                "CV (%)": x.std() / x.mean() * 100,
                "Skewness": x.skew(),
                "Kurtosis": x.kurt(),
            }
        )
        tbl.index = [L(i) for i in tbl.index]
        st.subheader("Ringkasan statistik per variabel")
        st.dataframe(tbl.style.format("{:.2f}"), width="stretch")
        st.caption(
            "Simpangan baku dan varians memakai rumus sampel (n - 1). Skewness mendekati 0 berarti simetris; "
            "kurtosis negatif berarti lebih datar dari kurva normal."
        )

    # ------------------------------------------------------------------ 2. distribusi
    with tab2:
        v = st.selectbox(
            "Variabel",
            num_cols,
            index=num_cols.index("Exam_Score") if "Exam_Score" in num_cols else 0,
            format_func=L,
            key="distvar",
        )
        bins = st.slider("Jumlah kelompok (bin)", 4, 20, 10)
        color = (
            alt.Color("Gender:N", scale=GCOL, title="Gender")
            if has_g
            else alt.value("#3b4a6b")
        )
        hist = (
            alt.Chart(d)
            .mark_bar(clip=True)
            .encode(
                alt.X(f"{v}:Q", bin=alt.Bin(maxbins=bins), title=L(v)),
                alt.Y("count()", title="Jumlah"),
                color=color,
            )
        )
        rule = (
            alt.Chart(pd.DataFrame({"m": [d[v].mean()]}))
            .mark_rule(color="black", strokeWidth=2, clip=True)
            .encode(x="m:Q")
        )
        st.altair_chart(
            (hist + rule).properties(height=300).interactive(), width="stretch"
        )
        st.caption(
            "Grafik bisa digerakkan: seret untuk menggeser, scroll untuk zoom, klik dua kali untuk mengembalikan."
        )
        box = (
            alt.Chart(d)
            .mark_boxplot(extent=1.5)
            .encode(
                alt.X(f"{v}:Q", title=L(v)),
                **({"y": alt.Y("Gender:N"), "color": color} if has_g else {}),
            )
            .properties(height=140)
        )
        st.altair_chart(box, width="stretch")
        sk = d[v].skew()
        bentuk = (
            "cukup simetris"
            if abs(sk) < 0.5
            else ("condong ke kanan" if sk > 0 else "condong ke kiri")
        )
        st.write(
            f"**{L(v)}**: mean {fm(d[v].mean())} (garis hitam), median {fm(d[v].median())}, simpangan baku "
            f"{fm(d[v].std())}. Distribusinya {bentuk} (skewness {fm(sk)})."
        )

    # ------------------------------------------------------------------ 3. dua variabel + prediksi
    with tab3:
        st.subheader("Statistik khusus dua variabel dengan prediksi")
        c1, c2 = st.columns(2)
        xv = c1.selectbox(
            "Variabel X (penjelas)",
            num_cols,
            index=num_cols.index("Study_Hours") if "Study_Hours" in num_cols else 0,
            format_func=L,
        )
        yv = c2.selectbox(
            "Variabel Y (yang diprediksi)",
            num_cols,
            index=num_cols.index("Exam_Score") if "Exam_Score" in num_cols else 1,
            format_func=L,
        )
        if xv == yv:
            st.warning("Pilih dua variabel yang berbeda.")
        else:
            sub = d[[xv, yv] + (["Gender"] if has_g else [])].dropna()
            n = len(sub)
            X, Y = sub[xv].to_numpy(float), sub[yv].to_numpy(float)
            res = stats.linregress(X, Y)
            r, r2, b, a, p = (
                res.rvalue,
                res.rvalue**2,
                res.slope,
                res.intercept,
                res.pvalue,
            )
            resid = Y - (a + b * X)
            s_e = np.sqrt((resid**2).sum() / (n - 2))
            tcrit = stats.t.ppf(0.975, n - 2)
            sxx = ((X - X.mean()) ** 2).sum()
            rho = stats.spearmanr(X, Y).statistic

            # vonis arah
            if p >= 0.05 or np.isnan(r):
                arrow, word, col = (
                    "→",
                    "Tidak ada pola naik atau turun yang jelas",
                    FLAT,
                )
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
                f"(r = {fm(r)}, p {'< 0,001' if p < .001 else '= ' + fm(p, 3)}).</div></div>",
                unsafe_allow_html=True,
            )

            m = st.columns(6)
            m[0].metric("Pearson r", fm(r))
            m[1].metric("r² (daya jelas)", f"{r2 * 100:.0f}%")
            m[2].metric("Kemiringan (b)", fm(b))
            m[3].metric("Intersep (a)", fm(a))
            m[4].metric("Spearman ρ", fm(rho))
            m[5].metric("n", n)

            with st.expander(
                "Statistik deskriptif kedua variabel dan detail regresi", expanded=True
            ):
                two = (
                    pd.DataFrame({xv: sub[xv], yv: sub[yv]})
                    .agg(["mean", "median", "std", "min", "max", "skew"])
                    .T
                )
                two.columns = [
                    "Mean",
                    "Median",
                    "Simp. baku",
                    "Min",
                    "Maks",
                    "Skewness",
                ]
                two.index = [f"{L(xv)} (X)", f"{L(yv)} (Y)"]
                st.dataframe(two.style.format("{:.2f}"), width="stretch")
                ci = (b - tcrit * res.stderr, b + tcrit * res.stderr)
                st.markdown(
                    f"- Persamaan: **ŷ = {fm(a)} {'+' if b >= 0 else '-'} {fm(abs(b))}·X**\n"
                    f"- Kovarians: {fm(np.cov(X, Y)[0, 1])}\n"
                    f"- Selang kepercayaan 95% untuk kemiringan: [{fm(ci[0])}; {fm(ci[1])}]\n"
                    f"- Galat baku residual (s): {fm(s_e)} satuan Y"
                )

            st.markdown("#### Seret titik atau ketik angka, garis regresi ikut berubah")
            st.caption(
                f"Otomatis memakai {L(xv)} (X) dan {L(yv)} (Y) yang dipilih di atas, dengan data sesuai filter. "
                "Perubahan di grafik ini untuk mencoba-coba dan tidak mengubah angka di bagian lain halaman; "
                'untuk mengubah data seluruh dashboard, pakai bagian "Ubah data" di atas.'
            )
            lab(sub[[xv, yv]], xv, yv)

            # grafik dengan pita prediksi (hanya zoom/geser tampilan)
            with st.expander(
                "Grafik dengan pita prediksi (hanya bisa di-zoom, titiknya tidak bisa digeser)"
            ):
                gx = np.linspace(X.min(), X.max(), 60)
                gy = a + b * gx
                h = 1 / n + (gx - X.mean()) ** 2 / sxx
                grid = pd.DataFrame(
                    {
                        "x": gx,
                        "y": gy,
                        "pl": gy - tcrit * s_e * np.sqrt(1 + h),
                        "ph": gy + tcrit * s_e * np.sqrt(1 + h),
                        "cl": gy - tcrit * s_e * np.sqrt(h),
                        "ch": gy + tcrit * s_e * np.sqrt(h),
                    }
                )
                band_p = (
                    alt.Chart(grid)
                    .mark_area(opacity=0.12, color=col, clip=True)
                    .encode(x="x:Q", y="pl:Q", y2="ph:Q")
                )
                band_c = (
                    alt.Chart(grid)
                    .mark_area(opacity=0.25, color=col, clip=True)
                    .encode(x="x:Q", y="cl:Q", y2="ch:Q")
                )
                line = (
                    alt.Chart(grid)
                    .mark_line(color=col, strokeWidth=3, clip=True)
                    .encode(
                        x=alt.X("x:Q", title=L(xv)),
                        y=alt.Y("y:Q", title=L(yv), scale=alt.Scale(zero=False)),
                    )
                )
                pc = (
                    alt.Color("Gender:N", scale=GCOL) if has_g else alt.value("#3b4a6b")
                )
                pts = (
                    alt.Chart(sub)
                    .mark_circle(size=60, opacity=0.75, clip=True)
                    .encode(
                        x=alt.X(f"{xv}:Q", scale=alt.Scale(zero=False)),
                        y=alt.Y(f"{yv}:Q", scale=alt.Scale(zero=False)),
                        color=pc,
                        tooltip=[xv, yv] + (["Gender"] if has_g else []),
                    )
                )
                st.altair_chart(
                    (band_p + band_c + line + pts).properties(height=380).interactive(),
                    width="stretch",
                )
                st.caption(
                    "Seret untuk menggeser, scroll untuk zoom, klik dua kali untuk reset. Garis = regresi. Pita pekat = selang kepercayaan 95% rata-rata Y. Pita tipis = selang prediksi 95% untuk satu mahasiswa baru."
                )

            # prediksi
            st.markdown("#### Prediksi")
            step = (
                0.1
                if np.issubdtype(sub[xv].dtype, np.floating)
                and (sub[xv] % 1 != 0).any()
                else 1.0
            )
            x0 = st.number_input(
                f"Masukkan nilai {L(xv).lower()} (X)",
                value=float(round(X.mean() / step) * step),
                step=float(step),
            )
            yh = a + b * x0
            hh = 1 / n + (x0 - X.mean()) ** 2 / sxx
            pi_ = tcrit * s_e * np.sqrt(1 + hh)
            ci_ = tcrit * s_e * np.sqrt(hh)
            k = st.columns(3)
            k[0].metric(f"Prediksi {L(yv).lower()}", fm(yh, 1))
            k[1].metric(
                "Selang prediksi 95% (1 orang)",
                f"{fm(yh - pi_, 1)} – {fm(yh + pi_, 1)}",
            )
            k[2].metric(
                "Selang kepercayaan 95% (rata-rata)",
                f"{fm(yh - ci_, 1)} – {fm(yh + ci_, 1)}",
            )
            if x0 < X.min() or x0 > X.max():
                st.warning(
                    f"X = {fm(x0)} di luar rentang data ({fm(X.min())} sampai {fm(X.max())}). Ini ekstrapolasi, hasilnya kurang andal."
                )
            st.caption(
                "Prediksi berasal dari garis regresi; bukan kepastian, dan menunjukkan keterkaitan, bukan sebab-akibat."
            )
            tbl_x = np.linspace(X.min(), X.max(), 6)
            st.dataframe(
                pd.DataFrame(
                    {
                        L(xv): tbl_x,
                        f"Prediksi {L(yv)}": a + b * tbl_x,
                        "Batas bawah 95%": a
                        + b * tbl_x
                        - tcrit
                        * s_e
                        * np.sqrt(1 + 1 / n + (tbl_x - X.mean()) ** 2 / sxx),
                        "Batas atas 95%": a
                        + b * tbl_x
                        + tcrit
                        * s_e
                        * np.sqrt(1 + 1 / n + (tbl_x - X.mean()) ** 2 / sxx),
                    }
                ).style.format("{:.1f}"),
                width="stretch",
                hide_index=True,
            )

            # diagnosis sisaan
            with st.expander(
                "Periksa kecocokan model (sisaan) dan pola per jenis kelamin"
            ):
                rd = pd.DataFrame({"Nilai prediksi": a + b * X, "Sisaan": resid})
                rp = (
                    alt.Chart(rd)
                    .mark_circle(size=50, opacity=0.7, color="#3b4a6b", clip=True)
                    .encode(x="Nilai prediksi:Q", y="Sisaan:Q")
                )
                st.altair_chart(
                    (
                        rp
                        + alt.Chart(pd.DataFrame({"z": [0]}))
                        .mark_rule(color="black", clip=True)
                        .encode(y="z:Q")
                    )
                    .properties(height=240)
                    .interactive(),
                    width="stretch",
                )
                st.write(
                    f"RMSE = {fm(np.sqrt((resid ** 2).mean()))}. Sisaan yang menyebar acak di sekitar 0 menandakan garis lurus cukup cocok."
                )
                if has_g:
                    rows = []
                    for g, part in sub.groupby("Gender"):
                        if len(part) >= 5:
                            rg = stats.linregress(part[xv], part[yv])
                            rows.append(
                                {
                                    "Gender": g,
                                    "n": len(part),
                                    "r": rg.rvalue,
                                    "Kemiringan": rg.slope,
                                    "Intersep": rg.intercept,
                                }
                            )
                    if rows:
                        st.dataframe(
                            pd.DataFrame(rows).style.format(
                                {
                                    "r": "{:.2f}",
                                    "Kemiringan": "{:.2f}",
                                    "Intersep": "{:.2f}",
                                }
                            ),
                            hide_index=True,
                        )
                        st.caption(
                            "Jika arah pola sama di kedua kelompok, hubungannya tidak sekadar akibat perbedaan jenis kelamin."
                        )
        # --- TAMBAHAN UNTUK POIN 4: MULTIPLE LINEAR REGRESSION ---
    st.markdown("---")
    st.subheader("4. Multiple Linear Regression (Regresi Berganda)")
    st.write("Memprediksi Nilai Ujian berdasarkan Jam Belajar, Jam Tidur, dan Kehadiran secara bersamaan.")
    
    target_cols = ["Study_Hours", "Sleep_Hours", "Attendance"]
    if all(col in d.columns for col in target_cols) and "Exam_Score" in d.columns:
        X_multi = d[target_cols].dropna()
        Y_multi = d.loc[X_multi.index, "Exam_Score"].to_numpy()
        X_mat = np.column_stack((np.ones(len(X_multi)), X_multi.to_numpy()))
        
        try:
            beta = np.linalg.inv(X_mat.T @ X_mat) @ X_mat.T @ Y_multi
            st.write(f"**Persamaan Regresi Berganda yang didapat:**")
            st.code(f"ŷ = {fm(beta[0])} + ({fm(beta[1])} * Jam Belajar) + ({fm(beta[2])} * Jam Tidur) + ({fm(beta[3])} * Kehadiran)")
            st.caption("Nilai kemiringan (koefisien) positif menunjukkan bahwa variabel tersebut berkontribusi meningkatkan perkiraan nilai ujian secara simultan.")
        except np.linalg.LinAlgError:
            st.warning("Data tidak cukup bervariasi untuk menghitung regresi berganda.")
    else:
        st.info("Kolom bawaan (Study_Hours, Sleep_Hours, Attendance, Exam_Score) tidak ditemukan untuk analisis regresi berganda.")

    # ------------------------------------------------------------------ 4. korelasi & perbandingan
    with tab4:
        cm = d[num_cols].corr()
        long = cm.stack().reset_index()
        long.columns = ["a", "b", "r"]
        long["a"], long["b"] = long["a"].map(L), long["b"].map(L)
        base = alt.Chart(long).encode(
            x=alt.X("b:N", title=None), y=alt.Y("a:N", title=None)
        )
        heat = base.mark_rect().encode(
            color=alt.Color(
                "r:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 1]), title="r"
            )
        )
        txt = base.mark_text(fontSize=11).encode(
            text=alt.Text("r:Q", format=".2f"),
            color=alt.condition(
                "abs(datum.r) > 0.55", alt.value("white"), alt.value("black")
            ),
        )
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
        need = {
            "Exam_Score",
            "Attendance",
            "Sleep_Hours",
            "Screen_Hours",
            "Study_Hours",
            "Gender",
            "Age",
        }
        if not need <= set(df.columns):
            st.info(
                "Keputusan otomatis hanya tersedia untuk kolom bawaan Latihan 1 (Exam_Score, Attendance, Sleep_Hours, "
                "Screen_Hours, Study_Hours, Gender, Age)."
            )
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
                (
                    "Pasang peringatan dini berbasis kehadiran",
                    f"Mahasiswa dengan kehadiran ≤ 80% ({n1} orang) rata-rata bernilai {fm(m1, 1)}, sedangkan yang hadir di atas 90% ({n2} orang) {fm(m2, 1)}. "
                    f"Kehadiran paling mudah dipantau, sehingga cocok menjadi pemicu pendampingan.",
                ),
                (
                    "Dampingi kelompok berisiko nilai < 60",
                    f"Ada {len(low)} mahasiswa dengan nilai di bawah 60. Rata-rata mereka belajar {fm(low['Study_Hours'].mean(), 1)} jam, tidur {fm(low['Sleep_Hours'].mean(), 1)} jam, "
                    f"hadir {fm(low['Attendance'].mean(), 0)}%, dan {fm(low['Screen_Hours'].mean(), 1)} jam di depan layar.",
                ),
                (
                    "Fokuskan program pada kelompok dengan nilai terendah",
                    f"Rata-rata nilai per jenis kelamin: "
                    + ", ".join(f"{k} = {fm(v, 1)}" for k, v in g["Exam_Score"].items())
                    + f". Jam belajar: "
                    + ", ".join(
                        f"{k} = {fm(v, 1)}" for k, v in g["Study_Hours"].items()
                    )
                    + ".",
                ),
                (
                    "Dorong tidur cukup dan batasi waktu layar",
                    f"Tidur < 6 jam ({n3} orang): nilai {fm(m3, 1)}; tidur ≥ 7 jam ({n4} orang): {fm(m4, 1)}. "
                    f"Layar > 8 jam ({n5} orang): {fm(m5, 1)}; layar ≤ 4 jam ({n6} orang): {fm(m6, 1)}.",
                ),
                (
                    "Perhatikan angkatan yang lebih tua",
                    f"Rata-rata nilai turun dari {fm(ages.iloc[0], 1)} (usia {ages.index[0]}) menjadi {fm(ages.iloc[-1], 1)} (usia {ages.index[-1]}). "
                    f"Periksa dulu apakah penyebabnya beban di luar kuliah.",
                ),
                (
                    "Pakai kepuasan dan pengeluaran sebagai sinyal, bukan target",
                    f"Keduanya sangat terkait dengan nilai (r kepuasan = {fm(df['Satisfaction'].corr(df['Exam_Score']))}, r pengeluaran = "
                    f"{fm(df['Monthly_Spending'].corr(df['Exam_Score']))}), tetapi mengubah keduanya belum tentu mengubah nilai.",
                ),
            ]
            for i, (t, body) in enumerate(items, 1):
                st.markdown(f"**{i}. {t}**  \n{body}")
            st.warning(
                "**Batas kesimpulan.** Hampir semua variabel berkorelasi sangat kuat (|r| sering di atas 0,9), pola yang jarang pada data nyata, "
                "jadi data ini kemungkinan data latihan. Ini data pengamatan satu waktu (n = 100): menunjukkan keterkaitan, bukan sebab-akibat, "
                "dan efek tiap kebiasaan tidak bisa dipisahkan. Sebelum kebijakan besar, lakukan uji lanjutan (uji beda rata-rata, regresi berganda)."
            )
    # Tambahan CSS untuk memenuhi syarat tugas nomor 1a
    st.markdown(
        """
    <style>
        /* Mengubah warna latar belakang tombol upload */
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
        }
        /* Mengubah font kartu metrik angka */
        [data-testid="stMetricValue"] {
            font-size: 40px;
            color: #00c8f8;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
