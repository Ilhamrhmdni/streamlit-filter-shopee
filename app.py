import streamlit as st
import pandas as pd
import io

# === SET PAGE CONFIG ===
st.set_page_config(page_title="Filter Produk Shopee", layout="wide")

# === CSS UNTUK SEMUA OPSI ===
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        .reportview-container .main .block-container {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        .sidebar .sidebar-content {
            background-color: #2a2a2a;
        }
        .section-title {
            font-size: 1.4em;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #99ddff;
        }
        .stat-box {
            background-color: #333;
            padding: 1em;
            border-radius: 10px;
            margin-bottom: 1em;
            border: 1px solid #99ddff;
            color: #e0e0e0;
        }
        .stat-box ul { padding-left: 1.2em; }
        .stat-box li { margin-bottom: 0.4em; }
        .stButton>button {
            background-color: #99ddff;
            color: black;
            border: none;
            padding: 0.5em 1em;
            border-radius: 4px;
            font-weight: bold;
        }
        .stButton>button:hover {
            transform: scale(1.05);
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #2e2e2e;
            color: #e0e0e0;
            border: 1px solid #99ddff;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #1e1e1e;
            color: #ccc;
            text-align: center;
            padding: 1em;
            font-size: 0.9em;
            font-style: italic;
            border-top: 1px solid #99ddff;
        }
    </style>
""", unsafe_allow_html=True)

# === PILIH OPSI ===
option = st.sidebar.selectbox("🎯 Pilih Mode Aplikasi", [
    "Filter Produk Extension Xyra", 
    "Filter Produk Shoptik"
])

# === FUNGSI UMUM ===
def read_and_validate_file(uploaded_file, delimiter='\t'):
    try:
        content = uploaded_file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(content), delimiter=delimiter, on_bad_lines='skip')
        df['source_file'] = uploaded_file.name
        return df
    except Exception as e:
        st.error(f"Gagal membaca {uploaded_file.name}: {e}")
        return None


# === FUNGSI PREPROCESSING SHOPTIK ===
def preprocess_shoptik(df):
    required_cols = ['productLink', 'Peringkat', 'Penjualan (30 Hari)', 'Harga', 'Stok', 'trendPercentage']
    for col in required_cols:
        if col not in df.columns:
            st.warning(f"Kolom '{col}' tidak ditemukan dalam file.")
            df[col] = None

    # Bersihkan data
    df['trendPercentage'] = pd.to_numeric(df['trendPercentage'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
    df['Harga'] = pd.to_numeric(df['Harga'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    df['Penjualan (30 Hari)'] = pd.to_numeric(df['Penjualan (30 Hari)'], errors='coerce').fillna(0)
    df['Stok'] = pd.to_numeric(df['Stok'], errors='coerce').fillna(0)
    df['Peringkat'] = pd.to_numeric(
        df['Peringkat'].astype(str).str.replace(',', '.').str.extract(r'(\d+\.?\d*)', expand=False),
        errors='coerce'
    ).fillna(0)
    df['isAd'] = df['isAd'].astype(str).str.contains('True|1|Ya|Yes', case=False, na=False)

    return df


# === FUNGSI APPLY FILTER SHOPTIK ===
def apply_shoptik_filters(df, trend_percentage_min, harga_min_shoptik, penjualan_30_hari_min, stok_min_shoptik, rating_min):
    filtered_df = df[
        (df['trendPercentage'] >= trend_percentage_min) &
        (df['Harga'] >= harga_min_shoptik) &
        (df['Penjualan (30 Hari)'] >= penjualan_30_hari_min) &
        (df['Stok'] >= stok_min_shoptik) &
        (df['Peringkat'] >= rating_min)
    ]
    
    if is_ad:
        filtered_df = filtered_df[filtered_df['isAd']]
    
    return filtered_df


# === OPSI 1: FILTER PRODUK EXTENSION XYRA ===
if option == "Filter Produk Extension Xyra":
    st.title("🛒 Filter Produk Extension Xyra")
    st.markdown("Gunakan filter di sidebar untuk menyaring produk sesuai kriteria.")

    # Input filter
    st.sidebar.title("🚬 Filter Black")
    stok_min = st.sidebar.number_input("Batas minimal stok", min_value=0, value=10)
    terjual_min = st.sidebar.number_input("Batas minimal terjual per bulan", min_value=0, value=100)
    harga_min = st.sidebar.number_input("Batas minimal harga produk", min_value=0.0, value=0.0)
    komisi_persen_min = st.sidebar.number_input("Batas minimal komisi (%)", min_value=0.0, value=0.0)
    komisi_rp_min = st.sidebar.number_input("Batas minimal komisi (Rp)", min_value=0.0, value=500.0)
    jumlah_live_min = st.sidebar.number_input("Batas minimal jumlah live", min_value=0, value=1)

    # Upload hanya file .txt
    uploaded_files = st.file_uploader("Masukkan File di Sini", type=["txt"], accept_multiple_files=True)

    def preprocess_data(df):
        df['Harga'] = pd.to_numeric(df['Harga'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'].astype(str), errors='coerce').fillna(0)
        df['Terjual(Bulanan)'] = pd.to_numeric(df['Terjual(Bulanan)'].astype(str), errors='coerce').fillna(0)
        df['Komisi(%)'] = pd.to_numeric(df['Komisi(%)'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
        df['Komisi(Rp)'] = pd.to_numeric(df['Komisi(Rp)'].astype(str), errors='coerce').fillna(0)
        df['Jumlah Live'] = pd.to_numeric(df['Jumlah Live'].astype(str), errors='coerce').fillna(0)
        return df

    def apply_filters(df):
        return df[
            (df['Stock'] >= stok_min) &
            (df['Terjual(Bulanan)'] >= terjual_min) &
            (df['Harga'] >= harga_min) &
            (df['Komisi(%)'] >= komisi_persen_min) &
            (df['Komisi(Rp)'] >= komisi_rp_min) &
            (df['Jumlah Live'] >= jumlah_live_min)
        ]

    if uploaded_files:
        if st.button("🚀 Proses Data"):
            with st.spinner("⏳ Memproses data..."):
                combined_df = pd.DataFrame()

                for file in uploaded_files:
                    df = read_and_validate_file(file, delimiter='\t')
                    if df is not None:
                        combined_df = pd.concat([combined_df, df], ignore_index=True)

                if not combined_df.empty:
                    total_links = len(combined_df)
                    combined_df.drop_duplicates(subset=['Link Produk'], inplace=True)
                    deleted_dupes = total_links - len(combined_df)

                    combined_df = preprocess_data(combined_df)
                    filtered_df = apply_filters(combined_df)
                    removed_df = combined_df[~combined_df.index.isin(filtered_df.index)]

                    avg_live = filtered_df['Jumlah Live'].mean().round(1)

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
                            <li>Rata-rata jumlah live: <strong>{avg_live}</strong></li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

                    st.subheader("✅ Final Produk")
                    st.dataframe(filtered_df)
                    st.download_button("⬇️ Download Data Produk", filtered_df.to_csv(index=False).encode('utf-8'), file_name="data_produk.csv", mime='text/csv')

                    st.subheader("🗑️ Produk Sampah")
                    st.dataframe(removed_df)
                    st.download_button("⬇️ Download Sampah", removed_df.to_csv(index=False).encode('utf-8'), file_name="sampah.csv", mime='text/csv')

                else:
                    st.warning("Tidak ada data valid yang bisa diproses.")
    else:
        st.info("📁 Silakan upload file terlebih dahulu.")


# === OPSI 2: FILTER PRODUK SHOPTIK ===
elif option == "Filter Produk Shoptik":
    st.title("📱 Filter Produk Shoptik")
    st.markdown("Gunakan filter di bawah ini untuk menganalisis produk dari Shoptik.")

    # Sidebar filter tambahan
    st.sidebar.title("⚙️ Filter Shoptik")
    trend_percentage_min = st.sidebar.number_input("Tren minimum (%)", min_value=0.0, value=50.0)
    harga_min_shoptik = st.sidebar.number_input("Harga minimum", min_value=0.0, value=0.0)
    penjualan_30_hari_min = st.sidebar.number_input("Penjualan minimum (30 Hari)", min_value=0, value=100)
    stok_min_shoptik = st.sidebar.number_input("Minimal stok", min_value=0, value=10)
    rating_min = st.sidebar.slider("Rating minimum", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
    is_ad = st.sidebar.checkbox("Tampilkan hanya produk beriklan", value=False)

    # Upload hanya file .csv
    uploaded_files = st.file_uploader("Masukkan File", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("🔎 Analisis Data"):
            with st.spinner("⏳ Menganalisis data Shoptik..."):
                combined_df = pd.DataFrame()

                for file in uploaded_files:
                    df = read_and_validate_file(file, delimiter=',')  # Untuk .csv gunakan koma
                    if df is not None:
                        combined_df = pd.concat([combined_df, df], ignore_index=True)

                if not combined_df.empty:
                    total_products = len(combined_df)

                    # 🚫 Hapus duplikat berdasarkan productLink
                    combined_df.drop_duplicates(subset=['productLink'], keep='first', inplace=True)
                    deleted_dupes = total_products - len(combined_df)

                    combined_df = preprocess_shoptik(combined_df)
                    filtered_df = apply_shoptik_filters(
                        combined_df,
                        trend_percentage_min,
                        harga_min_shoptik,
                        penjualan_30_hari_min,
                        stok_min_shoptik,
                        rating_min
                    )
                    removed_df = combined_df[~combined_df.index.isin(filtered_df.index)]

                    # Validasi rata-rata
                    avg_rating = filtered_df['Peringkat'].mean().round(1) if 'Peringkat' in filtered_df.columns and not filtered_df.empty else "Tidak tersedia"
                    avg_trend = filtered_df['trendPercentage'].mean().round(1) if 'trendPercentage' in filtered_df.columns and not filtered_df.empty else "Tidak tersedia"

                    st.success("✅ Analisis selesai!")

                    st.markdown(f"""
                    <div class="stat-box">
                        <div class="section-title">📊 Statistik Shoptik</div>
                        <ul>
                            <li>Total produk diproses: <strong>{total_products}</strong></li>
                            <li>Produk unik setelah hapus duplikat: <strong>{len(combined_df)}</strong></li>
                            <li>Produk lolos filter: <strong>{len(filtered_df)}</strong></li>
                            <li>Produk tidak lolos filter: <strong>{len(removed_df)}</strong></li>
                            <li>Duplikat berdasarkan link: <strong>{deleted_dupes}</strong></li>
                            <li>Rata-rata rating: <strong>{avg_rating}</strong></li>
                            <li>Rata-rata tren (%): <strong>{avg_trend}%</strong></li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

                    st.subheader("✅ Produk Lolos Filter")
                    st.dataframe(filtered_df)
                    st.download_button("⬇️ Download Data Shoptik", filtered_df.to_csv(index=False).encode('utf-8'), file_name="data_shoptik.csv", mime='text/csv')

                    st.subheader("🗑️ Produk Dihapus (Duplikat)")
                    st.dataframe(removed_df)
                    st.download_button("⬇️ Download Sampah", removed_df.to_csv(index=False).encode('utf-8'), file_name="sampah_shoptik.csv", mime='text/csv')

                else:
                    st.warning("Tidak ada data valid untuk dianalisis.")
    else:
        st.info("📁 Silakan upload file")


# === FOOTER ===
st.markdown("""
    <div class="footer">
        &copy; 2025 - Dibuat oleh Wong Sukses
    </div>
""", unsafe_allow_html=True)
