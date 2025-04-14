import streamlit as st
import pandas as pd
import io

# === CUSTOM STYLING ===
st.markdown("""
    <style>
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
            background-color: #222;
            padding: 1em;
            border-radius: 8px;
            margin-bottom: 1em;
            border: 1px solid #00ffcc;
            color: #e0ffe0;
            box-shadow: 0 0 5px #00ffcc;
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
            margin-top: 2em;
            font-size: 0.9em;
            color: gray;
        }
    </style>
""", unsafe_allow_html=True)

# === SIDEBAR INPUT ===
st.sidebar.title("🏍️ Filter Produk Shopee")
stok_min = st.sidebar.number_input("Batas minimal stok", min_value=0, value=10)
terjual_min = st.sidebar.number_input("Batas minimal terjual per bulan", min_value=0, value=5)
harga_min = st.sidebar.number_input("Batas minimal harga produk", min_value=0.0, value=10000.0)
komisi_persen_min = st.sidebar.number_input("Batas minimal komisi (%)", min_value=0.0, value=2.0)
komisi_rp_min = st.sidebar.number_input("Batas minimal komisi (Rp)", min_value=0.0, value=200.0)

uploaded_files = st.file_uploader("📁 Upload file mentahan (.txt)", type=["txt"], accept_multiple_files=True)

# === FUNGSI MODULAR ===

def read_and_validate_file(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(content), delimiter='\t', on_bad_lines='skip')
        df['source_file'] = uploaded_file.name

        if 'Link Produk' not in df.columns:
            df['Link Produk'] = 'Link tidak tersedia'

        required_columns = ['Harga', 'Stock', 'Terjual(Bulanan)', 'Komisi(%)', 'Komisi(Rp)']
        for col in required_columns:
            if col not in df.columns:
                st.warning(f"Kolom '{col}' tidak ada di {uploaded_file.name}, akan diisi default 0.")
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

# === MAIN LOGIC ===

st.markdown("Upload file mentahan (.txt) dan atur kriteria filter untuk memproses produk.")

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

            # === OUTPUT UI ===
            st.success("✅ Data berhasil diproses!")

            st.markdown(f"""
<div class="stat-box">
    <div class="section-title">📊 Statistik</div>
    <ul>
        <li>Total produk diproses: <strong style="color:#00ff00; text-shadow: 0 0 5px #00ff00, 0 0 10px #00ff00;">{total_links}</strong></li>
        <li>Produk unik setelah hapus duplikat: <strong style="color:#00ff00; text-shadow: 0 0 5px #00ff00, 0 0 10px #00ff00;">{len(combined_df)}</strong></li>
        <li>Produk lolos filter: <strong style="color:#00ff00; text-shadow: 0 0 5px #00ff00, 0 0 10px #00ff00;">{len(filtered_df)}</strong></li>
        <li>Produk tidak lolos filter: <strong style="color:#00ff00; text-shadow: 0 0 5px #00ff00, 0 0 10px #00ff00;">{len(removed_df)}</strong></li>
        <li>Duplikat yang dihapus: <strong style="color:#00ff00; text-shadow: 0 0 5px #00ff00, 0 0 10px #00ff00;">{deleted_dupes}</strong></li>
    </ul>
</div>
""", unsafe_allow_html=True)


            st.subheader("✅ Produk Lolos Filter")
            st.dataframe(filtered_df)
            st.download_button("⬇️ Download hasil CSV", filtered_df.to_csv(index=False).encode('utf-8'), file_name="hasil_filter.csv", mime='text/csv')

            st.subheader("🗑️ Produk Dihapus")
            st.dataframe(removed_df)
            st.download_button("⬇️ Download sampah CSV", removed_df.to_csv(index=False).encode('utf-8'), file_name="sampah.csv", mime='text/csv')
        else:
            st.warning("Tidak ada data valid yang bisa diproses.")
