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


@st.cache_data
def read_csv(src):
    return pd.read_csv(src)


# ------------------------------------------------------------------ data & filter
st.sidebar.header("Data dan filter")
upload = st.sidebar.file_uploader("Ganti data (CSV)", type="csv")
df = read_csv(upload) if upload else read_csv(DATA)
num_cols = [c for c in df.select_dtypes("number").columns if "id" not in c.lower()]
has_g = "Gender" in df.columns
d = df.copy()
if has_g:
    pick = st.sidebar.multiselect("Jenis kelamin", ["F", "M"], default=["F", "M"],
                                  format_func=lambda g: {"F": "Perempuan (F)", "M": "Laki-laki (M)"}[g])
    d = d[d["Gender"].isin(pick)]
if "Age" in df.columns and df["Age"].nunique() > 1:
    lo, hi = int(df["Age"].min()), int(df["Age"].max())
    a1, a2 = st.sidebar.slider("Rentang usia", lo, hi, (lo, hi))
    d = d[(d["Age"] >= a1) & (d["Age"] <= a2)]
st.sidebar.caption(f"{len(d)} dari {len(df)} baris dipakai.")

st.title("Kebiasaan mahasiswa dan nilai ujian")
st.caption("Statistik deskriptif, hubungan dua variabel dengan prediksi, dan keputusan yang dapat diambil.")
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
    hist = alt.Chart(d).mark_bar().encode(
        alt.X(f"{v}:Q", bin=alt.Bin(maxbins=bins), title=L(v)), alt.Y("count()", title="Jumlah"), color=color)
    rule = alt.Chart(pd.DataFrame({"m": [d[v].mean()]})).mark_rule(color="black", strokeWidth=2).encode(x="m:Q")
    st.altair_chart((hist + rule).properties(height=300), width="stretch")
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
        band_p = alt.Chart(grid).mark_area(opacity=.12, color=col).encode(x="x:Q", y="pl:Q", y2="ph:Q")
        band_c = alt.Chart(grid).mark_area(opacity=.25, color=col).encode(x="x:Q", y="cl:Q", y2="ch:Q")
        line = alt.Chart(grid).mark_line(color=col, strokeWidth=3).encode(x=alt.X("x:Q", title=L(xv)), y=alt.Y("y:Q", title=L(yv), scale=alt.Scale(zero=False)))
        pc = alt.Color("Gender:N", scale=GCOL) if has_g else alt.value("#3b4a6b")
        pts = alt.Chart(sub).mark_circle(size=60, opacity=.75).encode(
            x=alt.X(f"{xv}:Q", scale=alt.Scale(zero=False)), y=alt.Y(f"{yv}:Q", scale=alt.Scale(zero=False)), color=pc,
            tooltip=[xv, yv] + (["Gender"] if has_g else []))
        st.altair_chart((band_p + band_c + line + pts).properties(height=380), width="stretch")
        st.caption("Garis = regresi. Pita pekat = selang kepercayaan 95% rata-rata Y. Pita tipis = selang prediksi 95% untuk satu mahasiswa baru.")

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
            rp = alt.Chart(rd).mark_circle(size=50, opacity=.7, color="#3b4a6b").encode(x="Nilai prediksi:Q", y="Sisaan:Q")
            st.altair_chart((rp + alt.Chart(pd.DataFrame({"z": [0]})).mark_rule(color="black").encode(y="z:Q")).properties(height=240), width="stretch")
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
