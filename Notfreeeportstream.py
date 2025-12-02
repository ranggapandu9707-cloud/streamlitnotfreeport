import streamlit as st
import pandas as pd
import random

# ============================================================
#  BACKEND GAME (diadaptasi dari versi NiceGUI kamu)
# ============================================================

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

        # Stok bijih (g)
        self.stok_bijih = [0.0 for _ in self.data_logam]

        # History laba
        self.riwayat_laba = []

    def get_table_rows(self):
        rows = []
        for i, row in enumerate(self.data_logam):
            nama, ef, energi, harga_jual, harga_beli = row
            stok = self.stok_bijih[i]
            rows.append({
                'No': i + 1,
                'Logam': nama,
                'Harga Jual (Rp/g)': round(harga_jual, 3),
                'Harga Beli (Rp/g)': round(harga_beli, 3),
                'Efisiensi': round(ef, 2),
                'Energi (kWh/1000g)': energi,
                'Stok Bijih (g)': int(stok),
            })
        return rows

    def beli_bijih(self, idx_logam: int, qty_gram: float):
        if idx_logam < 0 or idx_logam >= len(self.data_logam):
            return False, "Logam tidak valid."

        if qty_gram < 0:
            return False, "Jumlah bijih tidak boleh negatif."

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

        if massa_proses < 0:
            return False, "Massa tidak boleh negatif.", None

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
        delta_listrik = random.uniform(-0.1, 0.1)
        self.harga_listrik *= (1.0 + delta_listrik)
        if self.harga_listrik < 900:
            self.harga_listrik = 900

        for j in range(len(self.data_logam)):
            delta_jual = random.uniform(-0.15, 0.15)
            self.data_logam[j][3] *= (1 + delta_jual)
            if self.data_logam[j][3] < 0.05:
                self.data_logam[j][3] = 0.05

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


# ============================================================
#  STREAMLIT APP
# ============================================================

st.set_page_config(
    page_title="PT NotFreeport",
    page_icon="⚙️",
    layout="wide",
)

# CSS sederhana untuk vibe dark & center-ish
st.markdown(
    """
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background-color: #020617;
        color: #e5e7eb;
    }
    .main > div {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Inisialisasi state
if "game" not in st.session_state:
    st.session_state.game = NotFreeportGame()
    st.session_state.logs = ["Selamat datang di PT NotFreeport! Mulailah membeli dan memproses bijih."]
    st.session_state.selected_beli = 0
    st.session_state.selected_proses = 0

game: NotFreeportGame = st.session_state.game

# ============================================================
#  HEADER
# ============================================================

col_head_left, col_head_right = st.columns([2, 1])

with col_head_left:
    st.image(
        "https://files.catbox.moe/4boeab.png",
        use_column_width=True,
    )
    st.markdown("### PT NotFreeport")
    st.caption("Simulasi Manajemen Pabrik Logam")

with col_head_right:
    st.button("Reset Game", type="secondary")
    if st.session_state.get("reset_clicked", False):
        pass

# Tombol reset beneran
if st.button("🔄 Reset Game (mulai dari awal)"):
    st.session_state.game = NotFreeportGame()
    st.session_state.logs = ["Game di-reset. Selamat datang kembali di PT NotFreeport!"]
    st.experimental_rerun()

# ============================================================
#  STATUS
# ============================================================

st.markdown("---")
st.subheader("Status Pabrik")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Hari", f"{game.hari}")
with c2:
    st.metric("Modal", f"Rp {int(game.modal):,}".replace(",", "."))
with c3:
    st.metric("Harga Listrik", f"Rp {int(game.harga_listrik):,}/kWh".replace(",", "."))
with c4:
    st.metric(
        "Kapasitas Harian",
        f"{int(game.kapasitas_tersisa_gram)}/{int(game.kapasitas_harian_gram)} g",
    )

# ============================================================
#  TABEL LOGAM
# ============================================================

st.markdown("### Harga Pasar & Stok Logam")
df_logam = pd.DataFrame(game.get_table_rows())
st.dataframe(
    df_logam.set_index("No"),
    use_container_width=True,
)

# ============================================================
#  KONTROL PEMBELIAN & PROSES
# ============================================================

st.markdown("---")
st.subheader("Operasional Harian")

col_beli, col_proses = st.columns(2)

logam_names = [row[0] for row in game.data_logam]

with col_beli:
    st.markdown("#### Pembelian Bijih")
    idx_beli = st.radio(
        "Pilih logam untuk dibeli:",
        options=list(range(len(logam_names))),
        format_func=lambda i: logam_names[i],
        index=st.session_state.selected_beli,
        horizontal=True,
    )
    st.session_state.selected_beli = idx_beli

    qty_beli = st.number_input(
        "Jumlah bijih dibeli (gram)",
        min_value=0.0,
        value=1000.0,
        step=100.0,
    )
    if st.button("Beli", key="btn_beli"):
        ok, msg = game.beli_bijih(idx_beli, qty_beli)
        st.session_state.logs.append(msg)
        st.experimental_rerun()

with col_proses:
    st.markdown("#### Produksi / Proses Bijih")
    idx_proses = st.radio(
        "Pilih logam untuk diproses:",
        options=list(range(len(logam_names))),
        format_func=lambda i: logam_names[i],
        index=st.session_state.selected_proses,
        horizontal=True,
    )
    st.session_state.selected_proses = idx_proses

    qty_proses = st.number_input(
        "Jumlah bijih diproses (gram)",
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
        st.experimental_rerun()

# ============================================================
#  NEXT DAY + UPGRADE
# ============================================================

st.markdown("---")
col_day, col_upgrade = st.columns([2, 3])

with col_day:
    if st.button("➡️ Lanjut ke Hari Berikutnya"):
        game.next_day()
        st.session_state.logs.append(f"Hari berganti: sekarang hari ke-{game.hari}")
        st.experimental_rerun()

with col_upgrade:
    if game.boleh_upgrade():
        st.markdown("#### Upgrade Tersedia (Setiap 3 Hari)")
        upgrade_options = [
            "1. Upgrade kapasitas proses (+5000 g) : Rp 2.000.000",
            "2. Upgrade efisiensi Fe (+3%)         : Rp 1.500.000",
            "3. Upgrade efisiensi Al (+3%)         : Rp 1.500.000",
            "4. Upgrade efisiensi Cu (+3%)         : Rp 1.500.000",
            "5. Upgrade efisiensi Zn (+3%)         : Rp 1.500.000",
            "6. Upgrade efisiensi Pb (+3%)         : Rp 1.500.000",
            "7. Lewati upgrade",
        ]
        pilihan_str = st.selectbox(
            "Pilih opsi upgrade:",
            options=upgrade_options,
        )
        if st.button("Konfirmasi Upgrade"):
            idx_pilihan = upgrade_options.index(pilihan_str) + 1
            ok, msg = game.lakukan_upgrade(idx_pilihan)
            st.session_state.logs.append(msg)
            st.experimental_rerun()
    else:
        st.info("Upgrade hanya tersedia pada hari yang kelipatan 3 (3, 6, 9, ...).")

# ============================================================
#  LOG / LAPORAN
# ============================================================

st.markdown("---")
st.subheader("Log / Laporan")

# tampilkan dari paling baru ke paling lama
for entry in reversed(st.session_state.logs[-200:]):
    st.write("•", entry)
