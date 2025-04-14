import streamlit as st
import pandas as pd
import io

# === CUSTOM CSS STYLE ===
st.markdown("""
    <style>
        /* Animasi glow pelan-pelan */
        @keyframes neonGlow {
            0% {
                box-shadow: 0 0 5px rgba(0, 255, 204, 0.2);
            }
            50% {
                box-shadow: 0 0 15px rgba(0, 255, 204, 0.6);
            }
            100% {
                box-shadow: 0 0 5px rgba(0, 255, 204, 0.2);
            }
        }

        /* Animasi perubahan warna frame */
        @keyframes colorChange {
            0% {
                border-color: #00ffcc;  /* Biru */
            }
            33% {
                border-color: #800080;  /* Ungu */
            }
            66% {
                border-color: #ff0000;  /* Merah */
            }
            100% {
                border-color: #00ffcc;  /* Kembali ke Biru */
            }
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
            background-color: #333333;  /* Warna abu-abu tua */
            padding: 1em;
            border-radius: 10px;
            margin-bottom: 1em;
            border: 3px solid #00ffcc;  /* Warna awal biru */
            color: #e0ffe0;
            animation: neonGlow 3s ease-in-out infinite, colorChange 6s infinite;  /* Menambahkan animasi perubahan warna */
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

        /* Footer untuk copyright */
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
st.sidebar.title("🚬 Marlboro Filter Black")

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

            # === STATISTIK RINCI ===
            produk_duplikat = combined_df[combined_df.duplicated(subset=['Link Produk'], keep=False)]
            produk_stok_kurang = combined_df[combined_df['Stock'] < stok_min]
            produk_harga_kurang = combined_df[combined_df['Harga'] < harga_min]
            produk_terjual_kurang = combined_df[combined_df['Terjual(Bulanan)'] < terjual_min]
            produk_komisi_kurang = combined_df[combined_df['Komisi(Rp)'] < komisi_rp_min]

            # Menampilkan statistik rinci
            st.markdown(f"""
            <div class="stat-box">
                <div class="section-title">📊 Statistik Rinci</div>
                <table style="width:100%; color:#e0ffe0;">
                    <tr>
                        <td><strong>Total produk diproses</strong></td>
                        <td><strong>{total_links}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Produk duplikat yang dihapus</strong></td>
                        <td><strong>{len(produk_duplikat)}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Produk dengan stok kurang dari batas</strong></td>
                        <td><strong>{len(produk_stok_kurang)}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Produk dengan harga kurang dari batas</strong></td>
                        <td><strong>{len(produk_harga_kurang)}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Produk dengan terjual bulanan kurang dari batas</strong></td>
                        <td><strong>{len(produk_terjual_kurang)}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Produk dengan komisi kurang dari batas</strong></td>
                        <td><strong>{len(produk_komisi_kurang)}</strong></td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("🗑️ Produk yang Tidak Lolos Filter")
            produk_tidak_lolos = pd.concat([produk_duplikat, produk_stok_kurang, produk_harga_kurang, produk_terjual_kurang, produk_komisi_kurang]).drop_duplicates()
            st.dataframe(produk_tidak_lolos)

            # --- Download produk yang tidak lolos filter ---
            st.download_button("⬇️ Download Produk Tidak Lolos Filter", produk_tidak_lolos.to_csv(index=False).encode('utf-8'), file_name="produk_tidak_lolos.csv", mime='text/csv')
        else:
            st.warning("Tidak ada data valid yang bisa diproses.")

# Footer layout
st.markdown("""
    <div class="footer">
        &copy; 2025 - Dibuat oleh Banyak Orang
    </div>
""", unsafe_allow_html=True)
