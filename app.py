import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Shopee Filter", layout="wide")

# === PILIHAN MODE TEMA ===
theme_mode = st.sidebar.selectbox("🎨 Pilih Gaya Visual", ["Neon", "Soft Dark"])

# === CSS untuk mode Neon dan Soft Dark ===
neon_css = """
    <style>
        html, body, .reportview-container, .main, .block-container {
            background-color: #0d0d0d !important;
            color: #e0ffe0 !important;
        }
        .sidebar-content {
            background-color: #1a1a1a !important;
            color: #e0ffe0 !important;
        }
        .section-title {
            color: #00ffcc;
            text-shadow: 0 0 3px #00ffcc;
        }
        .stat-box {
            background-color: #222;
            border: 3px solid #00ffcc;
            box-shadow: 0 0 10px #00ffcc;
        }
        .stButton>button {
            background-color: #00ffcc;
            color: black;
            box-shadow: 0 0 8px #00ffcc;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            background-color: #1affd5;
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #222 !important;
            color: #e0ffe0 !important;
            border: 1px solid #00ffcc;
        }
        .footer {
            background-color: #111;
            color: #00ffcc;
            border-top: 1px solid #00ffcc;
            text-align: center;
            padding: 1em;
            font-size: 0.9em;
        }
    </style>
"""

soft_dark_css = """
    <style>
        html, body, .reportview-container, .main, .block-container {
            background-color: #1e1e1e !important;
            color: #e0e0e0 !important;
        }
        .sidebar-content {
            background-color: #2a2a2a !important;
            color: #e0e0e0 !important;
        }
        .section-title {
            color: #99ddff;
        }
        .stat-box {
            background-color: #333;
            border: 1px solid #99ddff;
        }
        .stButton>button {
            background-color: #99ddff;
            color: black;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            background-color: #bce6ff;
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #2e2e2e !important;
            color: #e0e0e0 !important;
            border: 1px solid #99ddff;
        }
        .footer {
            background-color: #1e1e1e;
            color: #ccc;
            border-top: 1px solid #99ddff;
            text-align: center;
            padding: 1em;
            font-size: 0.9em;
        }
    </style>
"""

# === APPLY THEME ===
st.markdown(neon_css if theme_mode == "Neon" else soft_dark_css, unsafe_allow_html=True)

# === SIDEBAR FILTER ===
st.sidebar.title("🚬 Marlboro Filter Black")
stok_min = st.sidebar.number_input("Batas minimal stok", min_value=0, value=10)
terjual_min = st.sidebar.number_input("Batas minimal terjual per bulan", min_value=0, value=5)
harga_min = st.sidebar.number_input("Batas minimal harga produk", min_value=0.0, value=10000.0)
komisi_persen_min = st.sidebar.number_input("Batas minimal komisi (%)", min_value=0.0, value=2.0)
komisi_rp_min = st.sidebar.number_input("Batas minimal komisi (Rp)", min_value=0.0, value=200.0)

uploaded_files = st.file_uploader("Masukan File Format (.txt)", type=["txt"], accept_multiple_files=True)

# === FUNCTION UNTUK PROSES DATA ===
def read_and_validate_file(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(content), delimiter='\t', on_bad_lines='skip')
        df['source_file'] = uploaded_file.name
        if 'Link Produk' not in df.columns:
            df['Link Produk'] = 'Link tidak tersedia'
        for col in ['Harga', 'Stock', 'Terjual(Bulanan)', 'Komisi(%)', 'Komisi(Rp)']:
            if col not in df.columns:
                st.warning(f"Kolom '{col}' tidak ditemukan di {uploaded_file.name}, akan diisi 0.")
                df[col] = 0
        return df
    except Exception as e:
        st.error(f"Gagal membaca {uploaded_file.name}: {e}")
        return None

def preprocess_data(df):
    df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
    df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
    df['Terjual(Bulanan)'] = pd.to_numeric(df['Terjual(Bulanan)'], errors='coerce').fillna(0)
    df['Komisi(%)'] = pd.to_numeric(df['Komisi(%)'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
    df['Komisi(Rp)'] = pd.to_numeric(df['Komisi(Rp)'], errors='coerce').fillna(0)
    return df

def apply_filters(df):
    return df[
        (df['Stock'] >= stok_min) &
        (df['Terjual(Bulanan)'] >= terjual_min) &
        (df['Harga'] >= harga_min) &
        (df['Komisi(%)'] >= komisi_persen_min) &
        (df['Komisi(Rp)'] >= komisi_rp_min)
    ]

# === MAIN ===
if uploaded_files and st.button("🚀 Proses Data"):
    with st.spinner("⏳ Memproses data..."):
        combined_df = pd.DataFrame()

        for file in uploaded_files:
            df = read_and_validate_file(file)
            if df is not None:
                combined_df = pd.concat([combined_df, df], ignore_index=True)

        if not combined_df.empty:
            total_links = len(combined_df)
            combined_df.drop_duplicates(subset=['Link Produk'], inplace=True)
            deleted_dupes = total_links - len(combined_df)

            combined_df = preprocess_data(combined_df)
            filtered_df = apply_filters(combined_df)
            removed_df = combined_df[~combined_df.index.isin(filtered_df.index)]

            st.success("✅ Data berhasil diproses!")

            st.markdown(f"""
            <div class="stat-box">
                <div class="section-title">📊 Statistik</div>
                <ul>
                    <li>Total produk diproses: <strong>{total_links}</strong></li>
                    <li>Produk unik setelah hapus duplikat: <strong>{len(combined_df)}</strong></li>
                    <li>Produk lolos filter: <strong>{len(filtered_df)}</strong></li>
                    <li>Produk tidak lolos filter: <strong>{len(removed_df)}</strong></li>
                    <li>Duplikat yang dihapus: <strong>{deleted_dupes}</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("✅ Final Produk")
            st.dataframe(filtered_df)
            st.download_button("⬇️ Download Data Produk", filtered_df.to_csv(index=False).encode('utf-8'), file_name="data_produk.csv", mime='text/csv')

            st.subheader("🗑️ Produk Dihapus")
            st.dataframe(removed_df)
            st.download_button("⬇️ Download sampah", removed_df.to_csv(index=False).encode('utf-8'), file_name="sampah.csv", mime='text/csv')
        else:
            st.warning("Tidak ada data valid yang bisa diproses.")

# === FEEDBACK SECTION ===
if st.checkbox("💬 Kritik & Saran", value=False):
    feedback = st.text_area("Tulis kritik atau saran kamu di sini:")
    if st.button("Kirim"):
        st.success("🎉 Terima kasih atas masukannya!")

# === FOOTER ===
st.markdown("""
    <div class="footer">
        &copy; 2025 - Dibuat oleh Wong Sukses
    </div>
""", unsafe_allow_html=True)
