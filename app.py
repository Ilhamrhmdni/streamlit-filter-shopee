import streamlit as st
import pandas as pd
import io
import csv
import plotly.express as px

st.set_page_config(page_title="Iso-iso Westo", layout="wide")

# === CSS untuk tema gelap dan tampilan modern ===
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
        }
        .section-title {
            font-size: 1.5em;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #99ddff;
            border-left: 4px solid #99ddff;
            padding-left: 10px;
        }
        .stat-card {
            background: linear-gradient(145deg, #2a2a2a, #333);
            padding: 1em;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.2s;
            min-width: 200px;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card h3 {
            font-size: 1.1em;
            margin-bottom: 0.5em;
        }
        .stat-card p {
            font-size: 1.8em;
            margin: 0;
        }
        .stButton>button {
            background-color: #99ddff;
            color: black;
            border: none;
            padding: 0.5em 1em;
            border-radius: 4px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .stButton>button:hover {
            transform: scale(1.05);
        }
        .fade-in {
            animation: fadeIn 1s ease-in;
        }
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
    </style>
""", unsafe_allow_html=True)

# === INPUT FILTER DI SIDEBAR ===
st.sidebar.title("🚬 Marlboro Filter Black")
use_filters = st.sidebar.checkbox("Gunakan Filter", value=True)

stok_min = st.sidebar.number_input("Batas minimal stok", min_value=0, value=50)
terjual_min = st.sidebar.number_input("Batas minimal terjual per bulan", min_value=0, value=30)
harga_min = st.sidebar.number_input("Batas minimal harga produk", min_value=0.0, value=10000.0)
komisi_persen_min = st.sidebar.number_input("Batas minimal komisi (%)", min_value=0.0, value=2.0)
komisi_rp_min = st.sidebar.number_input("Batas minimal komisi (Rp)", min_value=0.0, value=0.0)

uploaded_files = st.file_uploader("Masukan File Format (.txt)", type=["txt"], accept_multiple_files=True)

# === FUNGSI PEMBACAAN DAN FILTER ===
def detect_delimiter(content):
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(content[:1024])
    return dialect.delimiter

def read_and_validate_file(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        delimiter = detect_delimiter(content)
        df = pd.read_csv(io.StringIO(content), delimiter=delimiter, on_bad_lines='skip')
        df['source_file'] = uploaded_file.name
        
        required_cols = ['Harga', 'Stock', 'Terjual(Bulanan)', 'Komisi(%)', 'Komisi(Rp)', 'Terjual(Semua)']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
                st.warning(f"Kolom '{col}' tidak ditemukan di {uploaded_file.name}, akan diisi 0.")
        
        if 'Link Produk' not in df.columns:
            df['Link Produk'] = 'Link tidak tersedia'
            
        return df
    except Exception as e:
        st.error(f"Gagal membaca {uploaded_file.name}: {e}")
        return None

def preprocess_data(df):
    df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce')
    df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
    df['Terjual(Bulanan)'] = pd.to_numeric(df['Terjual(Bulanan)'], errors='coerce').fillna(
        df['Terjual(Bulanan)'].median() if not df['Terjual(Bulanan)'].isnull().all() else 0
    )
    df['Terjual(Semua)'] = pd.to_numeric(df['Terjual(Semua)'], errors='coerce').fillna(
        df['Terjual(Semua)'].median() if not df['Terjual(Semua)'].isnull().all() else 0
    )
    df['Komisi(%)'] = pd.to_numeric(df['Komisi(%)'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
    df['Komisi(Rp)'] = pd.to_numeric(
        df['Komisi(Rp)'].astype(str).str.replace(r'[^\d.]', '', regex=True),
        errors='coerce'
    ).fillna(0)
    
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
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            df = read_and_validate_file(file)
            if df is not None:
                combined_df = pd.concat([combined_df, df], ignore_index=True)
            progress_bar.progress((i+1)/len(uploaded_files))
        
        if not combined_df.empty:
            total_links = len(combined_df)
            combined_df.drop_duplicates(subset=['Link Produk'], inplace=True)
            deleted_dupes = total_links - len(combined_df)

            combined_df = preprocess_data(combined_df)
            
            if use_filters:
                filtered_df = apply_filters(combined_df)
            else:
                filtered_df = combined_df.copy()
                st.info("Filter dinonaktifkan")
                
            # Hitung trend
            filtered_df['Trend'] = (
                filtered_df['Terjual(Bulanan)'] / 
                filtered_df['Terjual(Semua)'].replace(0, 1) * 100
            ).round(2).fillna(0)

            # Status produk
            def get_status(row):
                if row['Trend'] >= 10:
                    return 'Trending🔥'
                elif row['Trend'] >= 2:
                    return 'Stabil 👍'
                elif row['Trend'] < 2 and row['Trend'] > 0:
                    return 'Menurun ❌'
                else:
                    return 'NEW PRODUK '

            filtered_df['Status'] = filtered_df.apply(get_status, axis=1)

            st.success("✅ Data berhasil diproses!")

            # === DASHBOARD STATISTIK ===
            st.markdown('<div class="section-title fade-in">📊 Dashboard Analisis</div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <h3>📦 Total Produk</h3>
                    <p>{total_links}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <h3>🔥 Trending</h3>
                    <p>{len(filtered_df[filtered_df['Status'] == 'Trending🔥'])}</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="stat-card">
                    <h3>🗑️ Sampah</h3>
                    <p>{len(combined_df) - len(filtered_df)}</p>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="stat-card">
                    <h3>🗑️ Duplikat</h3>
                    <p>{deleted_dupes}</p>
                </div>
                """, unsafe_allow_html=True)

            # Grafik distribusi harga
            st.markdown('<div class="section-title fade-in">📈 Visualisasi Data</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                fig_harga = px.histogram(filtered_df, x='Harga', title='Distribusi Harga Produk')
                st.plotly_chart(fig_harga, use_container_width=True)
            
            with col2:
                fig_komisi = px.box(filtered_df, y='Komisi(Rp)', title='Distribusi Komisi (Rp)')
                st.plotly_chart(fig_komisi, use_container_width=True)

            # === TABS UNTUK DATA ===
            st.markdown('<div class="section-title fade-in">📂 Data Produk</div>', unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["✅ Produk Lolos Filter", "🗑️ Produk Tidak Lolos"])

            with tab1:
                st.dataframe(filtered_df)
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("⬇️ Download CSV", 
                                     filtered_df.to_csv(index=False).encode('utf-8'), 
                                     file_name="data_produk.csv", 
                                     mime='text/csv')
                with col2:
                    st.download_button("⬇️ Download Excel",
                                     filtered_df.to_excel(index=False).encode('utf-8'),
                                     file_name="data_produk.xlsx",
                                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with tab2:
                removed_df = combined_df[~combined_df.index.isin(filtered_df.index)]
                st.dataframe(removed_df)
                st.download_button("⬇️ Download Sampah", 
                                 removed_df.to_csv(index=False).encode('utf-8'), 
                                 file_name="sampah.csv", 
                                 mime='text/csv')

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
    <div style="text-align: center; padding: 2em; font-size: 0.9em; color: #888;">
        &copy; 2025 - Dibuat oleh Wong Sukses
    </div>
""", unsafe_allow_html=True)
