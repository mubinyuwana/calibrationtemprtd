# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- KONSTANTA & FUNGSI INTI ---
# Konstanta RTD berdasarkan standar IEC 60751
A = 3.9083e-3
B = -5.775e-7

def hitung_resistansi_standar(T, R0):
    """Menghitung resistansi standar RTD pada suhu T."""
    return R0 * (1 + A * T + B * T**2)

def style_kondisi(val):
    """Memberi warna pada sel 'Kondisi' di tabel."""
    color = 'limegreen' if val == "Layak" else 'crimson'
    return f'color: {color}; font-weight: bold;'

# --- PENGATURAN HALAMAN STREAMLIT ---
st.set_page_config(page_title="Form Kalibrasi RTD", layout="wide", initial_sidebar_state="expanded")
st.title("GENERATOR FORM KALIBRASI RTD 🌡️")
st.write("Aplikasi untuk membuat, mengisi, dan memproses form kalibrasi RTD tipe Pt100 dan Pt1000.")

# --- SIDEBAR UNTUK INPUT UTAMA ---
with st.sidebar:
    st.header("⚙️ Parameter Awal")
    tipe_rtd = st.selectbox('Pilih Tipe RTD:', ('Pt100', 'Pt1000'), key='tipe_rtd')
    temp_min = st.number_input('Suhu Minimum (°C):', value=0.0, format="%.2f", key='temp_min')
    temp_max = st.number_input('Suhu Maksimum (°C):', value=100.0, format="%.2f", key='temp_max')

    # Tombol untuk membuat form kalibrasi
    if st.button('Buat Form Kalibrasi', use_container_width=True, type="primary"):
        st.session_state.form_dibuat = True
        st.session_state.hasil_diproses = False  # Reset hasil jika form dibuat ulang
        R0 = 100 if st.session_state.tipe_rtd == 'Pt100' else 1000
        step = (st.session_state.temp_max - st.session_state.temp_min) / 4
        
        persen = [0, 25, 50, 75, 100]
        suhu_up = [round(st.session_state.temp_min + step * i, 2) for i in range(5)]
        st.session_state.suhu_points = {
            'persen': persen,
            'up': suhu_up,
            'down': list(reversed(suhu_up)),
            'std_up': [round(hitung_resistansi_standar(t, R0), 3) for t in suhu_up],
            'std_down': [round(hitung_resistansi_standar(t, R0), 3) for t in list(reversed(suhu_up))]
        }

# --- FORM PENGISIAN DATA KALIBRASI ---
if 'form_dibuat' in st.session_state and st.session_state.form_dibuat:
    with st.form("kalibrasi_form"):
        st.subheader("📝 Input Data Resistansi Terukur (Ω)")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Bawah ke Atas (0% → 100%)**")
            for i, (persen, suhu) in enumerate(zip(st.session_state.suhu_points['persen'], st.session_state.suhu_points['up'])):
                st.number_input(f"{persen}% ({suhu}°C)", key=f"ukur_up_{i}", value=None, format="%.3f", placeholder="Masukkan resistansi...")
        
        with col2:
            st.markdown("**Atas ke Bawah (100% → 0%)**")
            for i, (persen, suhu) in enumerate(zip(reversed(st.session_state.suhu_points['persen']), st.session_state.suhu_points['down'])):
                st.number_input(f"{persen}% ({suhu}°C)", key=f"ukur_down_{i}", value=None, format="%.3f", placeholder="Masukkan resistansi...")

        submitted = st.form_submit_button("✅ Proses & Hitung Hasil Kalibrasi", use_container_width=True)

        if submitted:
            st.session_state.hasil_diproses = True
            data_up, data_down = [], []
            R0 = 100 if st.session_state.tipe_rtd == 'Pt100' else 1000

            for i in range(5):
                r_ukur_up = st.session_state[f'ukur_up_{i}']
                if r_ukur_up is not None:
                    r_std_up = st.session_state.suhu_points['std_up'][i]
                    error_up = abs((r_ukur_up - r_std_up) / r_std_up) * 100 if r_std_up != 0 else 0
                    data_up.append({'Presentasi (%)': st.session_state.suhu_points['persen'][i], 'Suhu (°C)': st.session_state.suhu_points['up'][i], 'Resistansi Standar (Ω)': r_std_up, 'Resistansi Terukur (Ω)': r_ukur_up, 'Error (%)': error_up, 'Kondisi': "Layak" if error_up < 2 else "Tidak Layak"})

            for i in range(5):
                r_ukur_down = st.session_state[f'ukur_down_{i}']
                if r_ukur_down is not None:
                    r_std_down = st.session_state.suhu_points['std_down'][i]
                    error_down = abs((r_ukur_down - r_std_down) / r_std_down) * 100 if r_std_down != 0 else 0
                    data_down.append({'Presentasi (%)': list(reversed(st.session_state.suhu_points['persen']))[i], 'Suhu (°C)': st.session_state.suhu_points['down'][i], 'Resistansi Standar (Ω)': r_std_down, 'Resistansi Terukur (Ω)': r_ukur_down, 'Error (%)': error_down, 'Kondisi': "Layak" if error_down < 2 else "Tidak Layak"})
            
            st.session_state.df_up = pd.DataFrame(data_up)
            st.session_state.df_down = pd.DataFrame(data_down)

# --- TAMPILAN HASIL KALIBRASI ---
if 'hasil_diproses' in st.session_state and st.session_state.hasil_diproses:
    st.divider()
    st.subheader("📊 Hasil Akhir Kalibrasi")

    if not st.session_state.df_up.empty:
        st.markdown("#### Hasil: Bawah ke Atas")
        col_tabel1, col_grafik1 = st.columns([1.5, 1])
        with col_tabel1:
            st.dataframe(st.session_state.df_up.style.applymap(style_kondisi, subset=['Kondisi']).format({'Error (%)': "{:.2f}%", 'Resistansi Standar (Ω)': "{:.3f}", 'Resistansi Terukur (Ω)': "{:.3f}"}))
        with col_grafik1:
            if st.checkbox("Tampilkan Grafik Bawah → Atas", value=True):
                fig, ax = plt.subplots(); ax.plot(st.session_state.df_up['Suhu (°C)'], st.session_state.df_up['Resistansi Standar (Ω)'], 'o-', label='Standar'); ax.plot(st.session_state.df_up['Suhu (°C)'], st.session_state.df_up['Resistansi Terukur (Ω)'], 'x-', label='Terukur'); ax.set_title('Grafik Kalibrasi: Bawah ke Atas'); ax.set_xlabel("Suhu (°C)"); ax.set_ylabel("Resistansi (Ω)"); ax.grid(True); ax.legend(); plt.tight_layout(); st.pyplot(fig)
    
    if not st.session_state.df_down.empty:
        st.markdown("#### Hasil: Atas ke Bawah")
        col_tabel2, col_grafik2 = st.columns([1.5, 1])
        with col_tabel2:
            st.dataframe(st.session_state.df_down.style.applymap(style_kondisi, subset=['Kondisi']).format({'Error (%)': "{:.2f}%", 'Resistansi Standar (Ω)': "{:.3f}", 'Resistansi Terukur (Ω)': "{:.3f}"}))
        with col_grafik2:
            if st.checkbox("Tampilkan Grafik Atas → Bawah", value=True):
                fig, ax = plt.subplots(); ax.plot(st.session_state.df_down['Suhu (°C)'], st.session_state.df_down['Resistansi Standar (Ω)'], 'o-', label='Standar'); ax.plot(st.session_state.df_down['Suhu (°C)'], st.session_state.df_down['Resistansi Terukur (Ω)'], 'x-', label='Terukur'); ax.set_title('Grafik Kalibrasi: Atas ke Bawah'); ax.set_xlabel("Suhu (°C)"); ax.set_ylabel("Resistansi (Ω)"); ax.grid(True); ax.legend(); plt.tight_layout(); st.pyplot(fig)

elif 'form_dibuat' not in st.session_state:
    st.info("👈 Silakan atur parameter di sidebar kiri dan klik 'Buat Form Kalibrasi' untuk memulai.")
