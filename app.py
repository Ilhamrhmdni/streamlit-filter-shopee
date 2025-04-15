import streamlit as st
import pandas as pd
import io

# === CUSTOM CSS STYLE ===
st.markdown("""
    <style>
        @keyframes neonGlow {
            0% { box-shadow: 0 0 5px rgba(0, 255, 204, 0.2); }
            50% { box-shadow: 0 0 15px rgba(0, 255, 204, 0.6); }
            100% { box-shadow: 0 0 5px rgba(0, 255, 204, 0.2); }
        }

        @keyframes colorChange {
            0% { border-color: #00ffcc; }
            33% { border-color: #B026FF; }
            66% { border-color: #FF073A; }
            100% { border-color: #39FF14; }
        }

        body {
            background-color: #111111;
            color: #e0ffe0;
        }
        .reportview-container .main .block-container {
            background-color: #111111;
            color: #e0ffe0;
        }
        .sidebar .sidebar-content {
            background-color: #1a1a1a;
        }
        .section-title {
            font-size: 1.4em;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #00ffcc;
            text-shadow: 0 0 3px #00ffcc;
        }
        .stat-box {
            background-color: #333333;
            padding: 1em;
            border-radius: 10px;
            margin-bottom: 1em;
            border: 3px solid #00ffcc;
            color: #e0ffe0;
            animation: neonGlow 3s ease-in-out infinite, colorChange 6s infinite;
        }
        .stat-box ul {
            padding-left: 1.2em;
        }
        .stat-box li {
            margin-bottom: 0.4em;
        }
        .stButton>button {
            background-color: #00ffcc;
            color: black;
            border: none;
            padding: 0.5em 1em;
            border-radius: 4px;
            font-weight: bold;
            box-shadow: 0 0 5px #00ffcc;
            transition: 0.3s ease;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 8px #00ffcc;
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #222;
            color: #e0ffe0;
            border: 1px solid #00ffcc;
            box-shadow: 0 0 3px #00ffcc;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #111111;
            color: #e0ffe0;
            text-align: center;
            padding: 1em;
            font-size: 0.9em;
            font-style: italic;
            border-top: 1px solid #00ffcc;
            box-shadow: 0 0 10px rgba(0, 255, 204, 0.3);
        }
    </style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
st.sidebar.title("🚬 Marlboro Filter")

stok_min = st.sidebar.number_input("Batas minimal stok", min_value=0, value=10)
terjual_min = st.sidebar.number_input("Batas minimal terjual per bulan", min_value=0, value=5)
harga_min = st.sidebar.number_input("Batas minimal harga produk", min_value=0.0, value=10000.0)
komisi_persen_min = st.sidebar.number_input("Batas minimal komisi (%)", min_value=0.0, value=2.0)
komisi_rp_min = st.sidebar.number_input("Batas minimal komisi (Rp)", min_value=0.0, value=200.0)

uploaded_files = st.file_uploader("Masukan File Format (.txt)", type=["txt"], accept_multiple_files=True)

# === UTILITY FUNCTIONS ===
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

# === PROSES DATA ===
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
show_feedback = st.checkbox("💬 Kritik & Saran", value=False)
if show_feedback:
    feedback = st.text_area("Tulis kritik atau saran kamu di sini:")
    if st.button("Kirim"):
        st.success("🎉 Terima kasih atas masukannya!")

# === FOOTER ===
st.markdown("""
    <div class="footer">
        &copy; 2025 - Dibuat oleh Wong Sukses
    </div>
""", unsafe_allow_html=True)
