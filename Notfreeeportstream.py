import os
import streamlit as st
import pandas as pd
import random
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from supabase import Client as SupabaseClient
else:
    SupabaseClient = Any


#  BACKEND GAME (JANGAN DISENTUH, KAU GANTI DIKIT DAH ERROR NI, PC PANDU DULU)


class NotFreeportGame:
    def __init__(self):
        # Ekonomi dasar
        self.modal = 12_000_000
        self.harga_listrik = 1500
        self.biaya_maintenance_harian = 250_000
        self.kapasitas_harian_gram = 10_000
        self.kapasitas_tersisa_gram = self.kapasitas_harian_gram
        self.hari = 1

        # data_logam: Nama, Efisiensi, Energi kWh per 1000 g, Harga Jual, Harga Beli
        self.data_logam = [
            ["Fe", 0.90, 1.2, 0.15, 0.03],
            ["Al", 0.70, 2.5, 0.25, 0.09],
            ["Cu", 0.85, 2.0, 0.45, 0.12],
            ["Zn", 0.80, 1.5, 0.30, 0.10],
            ["Pb", 0.75, 1.4, 0.20, 0.08],
        ]
        for row in self.data_logam:
            row[0] = row[0].title()

        # Stok bijih (gram)
        self.stok_bijih = [0.0 for _ in self.data_logam]

        # Riwayat laba
        self.riwayat_laba = []

    def get_table_rows(self):
        rows = []
        for i, row in enumerate(self.data_logam):
            nama, ef, energi, harga_jual, harga_beli = row
            stok = self.stok_bijih[i]
            rows.append({
                "No": i + 1,
                "Logam": nama,
                "Harga Jual (Rp/g)": round(harga_jual, 3),
                "Harga Beli (Rp/g)": round(harga_beli, 3),
                "Efisiensi": round(ef, 2),
                "Energi (kWh/1000g)": energi,
                "Stok Bijih (g)": int(stok),
            })
        return rows

    def beli_bijih(self, idx_logam: int, qty_gram: float):
        if idx_logam < 0 or idx_logam >= len(self.data_logam):
            return False, "Logam tidak valid."

        if qty_gram <= 0:
            return False, "Jumlah bijih harus lebih dari 0."

        harga_beli = self.data_logam[idx_logam][4]
        biaya_pembelian = qty_gram * harga_beli

        if biaya_pembelian > self.modal:
            return False, "Modal tidak cukup untuk pembelian tersebut."

        self.stok_bijih[idx_logam] += qty_gram
        self.modal -= biaya_pembelian

        return True, f"Pembelian berhasil. Biaya: Rp {round(biaya_pembelian, 2):,.0f}"

    def proses_bijih(self, idx_logam: int, massa_proses: float):
        if idx_logam < 0 or idx_logam >= len(self.data_logam):
            return False, "Logam tidak valid.", None

        if massa_proses <= 0:
            return False, "Massa harus lebih dari 0.", None

        if massa_proses > self.stok_bijih[idx_logam]:
            return False, "Massa melebihi stok bijih.", None

        if massa_proses > self.kapasitas_tersisa_gram:
            return False, "Massa melebihi kapasitas tersisa hari ini.", None

        nama, efisiensi, energi_per_kg, harga_jual, _ = self.data_logam[idx_logam]

        hasil_logam = massa_proses * efisiensi
        energi_kwh = (massa_proses / 1000.0) * energi_per_kg
        biaya_energi = energi_kwh * self.harga_listrik
        biaya_proses = biaya_energi + self.biaya_maintenance_harian

        self.stok_bijih[idx_logam] -= massa_proses
        self.kapasitas_tersisa_gram -= massa_proses

        pendapatan = hasil_logam * harga_jual
        laba_bersih = pendapatan - biaya_proses
        self.modal += laba_bersih
        self.riwayat_laba.append(laba_bersih)

        hasil = {
            "nama_logam": nama,
            "massa_proses": massa_proses,
            "hasil_logam": hasil_logam,
            "pendapatan": pendapatan,
            "biaya_energi": biaya_energi,
            "biaya_maintenance": self.biaya_maintenance_harian,
            "laba_bersih": laba_bersih,
            "modal_sekarang": self.modal,
        }
        return True, "Proses berhasil.", hasil

    def randomize_harga(self):
        # listrik
        delta_listrik = random.uniform(-0.1, 0.1)
        self.harga_listrik *= (1.0 + delta_listrik)
        if self.harga_listrik < 900:
            self.harga_listrik = 900

        # harga logam
        for j in range(len(self.data_logam)):
            # jual
            delta_jual = random.uniform(-0.15, 0.15)
            self.data_logam[j][3] *= (1 + delta_jual)
            if self.data_logam[j][3] < 0.05:
                self.data_logam[j][3] = 0.05

            # beli
            delta_beli = random.uniform(-0.12, 0.12)
            self.data_logam[j][4] *= (1 + delta_beli)
            if self.data_logam[j][4] < 0.02:
                self.data_logam[j][4] = 0.02

    def boleh_upgrade(self):
        return self.hari % 3 == 0

    def lakukan_upgrade(self, pilihan: int):
        if pilihan == 1:
            if self.modal >= 2_000_000:
                self.kapasitas_harian_gram += 5000
                self.kapasitas_tersisa_gram = min(
                    self.kapasitas_tersisa_gram + 5000, self.kapasitas_harian_gram
                )
                self.modal -= 2_000_000
                return True, f"Kapasitas naik menjadi {int(self.kapasitas_harian_gram)} g/hari."
            else:
                return False, "Modal tidak cukup untuk upgrade kapasitas."

        if pilihan in [2, 3, 4, 5, 6]:
            idx = pilihan - 2
            if self.modal >= 1_500_000:
                self.data_logam[idx][1] += 0.03
                self.modal -= 1_500_000
                return True, f"Efisiensi {self.data_logam[idx][0]} naik menjadi {round(self.data_logam[idx][1], 2)}."
            else:
                return False, "Modal tidak cukup untuk upgrade efisiensi."

        if pilihan == 7:
            return True, "Upgrade dilewati."

        return False, "Pilihan upgrade tidak valid."

    def next_day(self):
        self.hari += 1
        self.randomize_harga()
        self.kapasitas_tersisa_gram = self.kapasitas_harian_gram



#  LEADERBOARD (Pake supabase akunnya Pandu)


def _safe_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)

SUPABASE_TABLE = _safe_secret("SUPABASE_TABLE", "Leaderboard NotFreeport")
SUPABASE_ID_FIELD = _safe_secret("SUPABASE_ID_FIELD", "id")
SUPABASE_NAME_FIELD = _safe_secret("SUPABASE_NAME_FIELD", "Name")
SUPABASE_SCORE_FIELD = _safe_secret("SUPABASE_SCORE_FIELD", "Score")
SUPABASE_URL = _safe_secret("SUPABASE_URL")
SUPABASE_KEY = _safe_secret("SUPABASE_KEY")


def get_supabase_client() -> SupabaseClient | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
    except Exception:
        st.warning("Supabase client belum terpasang, pip install supabase, lalu jalankan ulang.")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        st.error(f"Gagal membuat Supabase client: {exc}")
        return None


def upsert_leaderboard_row(client: SupabaseClient | None, player_id: str, name: str, score: int):
    if client is None:
        return False, "Supabase error astaughfirullah god help me"
    try:
        payload = {
            SUPABASE_ID_FIELD: player_id,
            SUPABASE_NAME_FIELD: name,
            SUPABASE_SCORE_FIELD: score,
        }
        client.table(SUPABASE_TABLE).upsert(payload).execute()
        return True, "Skor tersimpan ke leaderboard."
    except Exception as exc:
        return False, f"Gagal simpan skor: {exc}"


def fetch_leaderboard(client: SupabaseClient | None, limit: int = 10):
    if client is None:
        return []
    try:
        res = (
            client.table(SUPABASE_TABLE)
            .select(f"{SUPABASE_NAME_FIELD},{SUPABASE_SCORE_FIELD}")
            .order(SUPABASE_SCORE_FIELD, desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as exc:
        st.warning(f"Gagal mengambil leaderboard: {exc}")
        return []



#  STREAMLIT UI (Baca documentation di streamlit.io kalo mau nyoba edit)


st.set_page_config(
    page_title="PT NotFreeport",
    page_icon="🪓",
    layout="wide",
)

# Theme (Coba cari tempalte di github banyak kalo mau nyoba template baru)
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Nunito:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"]  {
        background: radial-gradient(circle at top, #1f2937 0, #020617 55%, #000 100%);
        color: #e5e7eb;
        margin: 0;
        padding: 0;
    }
    .block-container {
        max-width: 900px;
        margin: 0 auto;
        padding-top: 0rem;
        padding-bottom: 3rem;
    }
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    h1, h2, h3, h4 {
        font-family: 'Press Start 2P', system-ui, sans-serif;
        letter-spacing: 1px;
    }
    .app-title {
        font-family: 'Press Start 2P', system-ui, sans-serif;
        font-size: 1.3rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 3rem;
        margin-bottom: 0.2rem;
    }
    .app-subtitle {
        text-align: center;
        font-family: 'Nunito', system-ui, sans-serif;
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 1.2rem;
    }
    .stMetric {
        text-align: center !important;
    }
    .stMetric > div {
        width: 100%;
        text-align: center !important;
    }
    .stButton>button {
        font-family: 'Press Start 2P', system-ui, sans-serif;
        font-size: 0.6rem;
        border-radius: 6px;
        background: linear-gradient(135deg, #4c1d95, #7c3aed);
        color: #f9fafb;
        border: 2px solid #a855f7;
        box-shadow: 0 0 0 2px #1f2937, 4px 4px 0 #000;
        text-transform: uppercase;
        padding: 0.35rem 0.9rem;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        border-color: #f97316;
    }
    .app-card {
        background: rgba(15, 23, 42, 0.9);
        border: 2px solid #4b5563;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 0 0 2px #020617, 3px 3px 0 #000;
    }
    .section-title {
        font-family: 'Press Start 2P', system-ui, sans-serif;
        font-size: 0.75rem;
        margin-bottom: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 0 0 2px #020617, 3px 3px 0 #000;
    }
    .status-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(180px, 1fr));
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .status-item {
        background: rgba(31, 41, 55, 0.9);
        border: 2px solid #4b5563;
        border-radius: 10px;
        padding: 0.75rem 0.85rem;
        box-shadow: 0 0 0 2px #020617, 2px 2px 0 #000;
    }
    .status-label {
        font-family: 'Press Start 2P', system-ui, sans-serif;
        font-size: 0.55rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #9ca3af;
        margin-bottom: 0.35rem;
    }
    .status-value {
        font-family: 'Nunito', system-ui, sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #f9fafb;
        line-height: 1.2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


#  SESSION STATE (Part nya supabase)


if "game" not in st.session_state:
    st.session_state.game = NotFreeportGame()
    st.session_state.logs = [
        "Selamat datang di PT NotFreeport! Mulailah membeli dan memproses bijih."
    ]
    st.session_state.selected_beli = 0
    st.session_state.selected_proses = 0
    st.session_state.upgrade_used = False
    st.session_state.player_id = str(uuid.uuid4())
    st.session_state.player_name = ""

game: NotFreeportGame = st.session_state.game

supabase_client = get_supabase_client()


#  HEADER (Silahkan ganti ganti fotonya, pake direct link ya)


st.markdown(
    """
    <div style="text-align:center;">
        <img src="https://files.catbox.moe/4boeab.png" alt="NotFreeport Logo" style="width: 100%; max-width: 840px; image-rendering: pixelated; margin-bottom: 0;">
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="app-title">PT NOTFREEPORT</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Factory Simulator</div>',
    unsafe_allow_html=True,
)

st.markdown("---")


#  STATUS CARD


st.markdown('<div class="section-title">Status Pabrik</div>', unsafe_allow_html=True)
modal_fmt = f"Rp {int(game.modal):,}".replace(",", ".")
listrik_fmt = f"Rp {int(game.harga_listrik):,}/kWh".replace(",", ".")
kapasitas_fmt = f"{int(game.kapasitas_tersisa_gram)}/{int(game.kapasitas_harian_gram)} g"
status_html = f"""
<div class="status-grid">
    <div class="status-item">
        <div class="status-label">Hari</div>
        <div class="status-value">{game.hari}</div>
    </div>
    <div class="status-item">
        <div class="status-label">Modal</div>
        <div class="status-value">{modal_fmt}</div>
    </div>
    <div class="status-item">
        <div class="status-label">Listrik</div>
        <div class="status-value">{listrik_fmt}</div>
    </div>
    <div class="status-item">
        <div class="status-label">Kapasitas</div>
        <div class="status-value">{kapasitas_fmt}</div>
    </div>
</div>
"""
st.markdown(status_html, unsafe_allow_html=True)


#  TABEL LOGAM


st.markdown("")
st.markdown('<div class="section-title">Harga Pasar & Stok Logam</div>', unsafe_allow_html=True)
df_logam = pd.DataFrame(game.get_table_rows())
st.dataframe(
    df_logam.set_index("No"),
    use_container_width=True,
)

st.markdown("---")


#  OPERASIONAL (PEMBELIAN & PROSES)


st.markdown('<div class="section-title">Operasional Harian</div>', unsafe_allow_html=True)

logam_names = [row[0] for row in game.data_logam]

op_cols = st.columns(2)

with op_cols[0]:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("**Pembelian Bijih**")
    idx_beli = st.radio(
        "Pilih logam:",
        options=list(range(len(logam_names))),
        format_func=lambda i: logam_names[i],
        index=st.session_state.selected_beli,
        horizontal=True,
        key="radio_beli",
    )
    st.session_state.selected_beli = idx_beli

    qty_beli = st.number_input(
        "Jumlah dibeli (gram)",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        key="qty_beli",
    )
    if st.button("Beli", key="btn_beli"):
        ok, msg = game.beli_bijih(idx_beli, qty_beli)
        st.session_state.logs.append(msg)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with op_cols[1]:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.markdown("**Produksi / Proses Bijih**")
    idx_proses = st.radio(
        "Pilih logam:",
        options=list(range(len(logam_names))),
        format_func=lambda i: logam_names[i],
        index=st.session_state.selected_proses,
        horizontal=True,
        key="radio_proses",
    )
    st.session_state.selected_proses = idx_proses

    qty_proses = st.number_input(
        "Jumlah diproses (gram)",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        key="qty_proses",
    )
    if st.button("Proses", key="btn_proses"):
        ok, msg, hasil = game.proses_bijih(idx_proses, qty_proses)
        st.session_state.logs.append(msg)
        if ok and hasil is not None:
            laporan = (
                f"[LAPORAN] {hasil['nama_logam']}: "
                f"bijih {hasil['massa_proses']:.0f} g → "
                f"logam {hasil['hasil_logam']:.0f} g, "
                f"pendapatan Rp {hasil['pendapatan']:.0f}, "
                f"biaya energi Rp {hasil['biaya_energi']:.0f}, "
                f"maintenance Rp {hasil['biaya_maintenance']:.0f}, "
                f"laba Rp {hasil['laba_bersih']:.0f}, "
                f"modal sekarang Rp {hasil['modal_sekarang']:.0f}"
            )
            st.session_state.logs.append(laporan)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")


#  NEXT DAY + UPGRADE (CENTERED)


nav_cols = st.columns([1, 1, 1])
with nav_cols[1]:
    if st.button("Lanjut Hari Berikutnya"):
        st.session_state.upgrade_used = False
        game.next_day()
        st.session_state.logs.append(f"Hari berganti: sekarang hari ke-{game.hari}")
        st.rerun()

st.markdown("")

if game.boleh_upgrade():
    st.markdown('<div class="section-title">Upgrade (Setiap 3 Hari)</div>', unsafe_allow_html=True)
    if st.session_state.get("upgrade_used", False):
        st.info("Upgrade hari ini sudah digunakan. Lanjutkan ke hari berikutnya.")
    else:
        upgrade_options = [
            "Kapasitas +5000 g : Rp 2.000.000",
            "Efisiensi Fe +3%  : Rp 1.500.000",
            "Efisiensi Al +3%  : Rp 1.500.000",
            "Efisiensi Cu +3%  : Rp 1.500.000",
            "Efisiensi Zn +3%  : Rp 1.500.000",
            "Efisiensi Pb +3%  : Rp 1.500.000",
            "Lewati upgrade",
        ]
        with st.container(border=True):
            pilihan_str = st.selectbox(
                "Pilih opsi upgrade:",
                options=upgrade_options,
                key="upgrade_choice",
            )
            if st.button("Konfirmasi Upgrade", key="btn_upgrade_confirm"):
                idx_pilihan = upgrade_options.index(pilihan_str) + 1
                ok, msg = game.lakukan_upgrade(idx_pilihan)
                st.session_state.logs.append(msg)
                if ok:
                    st.session_state.upgrade_used = True
                st.rerun()
else:
    st.info("Upgrade hanya tersedia pada hari ke-3, 6, 9, dan seterusnya.")

st.markdown("---")


#  LEADERBOARD


st.markdown('<div class="section-title">Leaderboard</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.write("Isi username lalu kirim skor (diambil dari modal saat ini).")
    username_input = st.text_input(
        "Username",
        value=st.session_state.player_name,
        key="lb_username",
    )
    current_score = int(game.modal)
    st.caption(f"Skor yang akan dikirim: {current_score:,}".replace(",", "."))

    col_submit, col_refresh = st.columns([1, 1])
    with col_submit:
        if st.button("Kirim Skor", key="btn_lb_submit"):
            st.session_state.player_name = username_input.strip()
            if not st.session_state.player_name:
                st.warning("Isi username dulu.")
            else:
                ok, msg = upsert_leaderboard_row(
                    supabase_client,
                    st.session_state.player_id,
                    st.session_state.player_name,
                    current_score,
                )
                (st.success if ok else st.warning)(msg)
    with col_refresh:
        if st.button("Refresh Leaderboard", key="btn_lb_refresh"):
            st.rerun()

    if supabase_client:
        leaderboard_rows = fetch_leaderboard(supabase_client, limit=10)
        if leaderboard_rows:
            df_lb = pd.DataFrame(leaderboard_rows)
            # Only show name and score to the user
            visible_cols = [SUPABASE_NAME_FIELD, SUPABASE_SCORE_FIELD]
            df_show = df_lb[visible_cols] if all(c in df_lb.columns for c in visible_cols) else df_lb
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.info("Leaderboard kosong atau belum ada data.")
    else:
        st.info("Set `SUPABASE_URL` dan `SUPABASE_KEY` di st.secrets untuk mengaktifkan leaderboard.")

st.markdown("---")


#  LOG / LAPORAN


st.markdown('<div class="section-title">Log / Laporan</div>', unsafe_allow_html=True)
with st.container(border=True):
    for entry in reversed(st.session_state.logs[-150:]):
        st.write("•", entry)
