import streamlit as st
import pandas as pd
import io
import csv

st.set_page_config(page_title="Iso-iso Westo", layout="wide")

# === CSS untuk tema gelap tetap ===
st.markdown("""
    <style>
        /* ... (tetap sama seperti kode sebelumnya) ... */
    </style>
""", unsafe_allow_html=True)

# === INPUT FILTER DI SIDEBAR ===
st.sidebar.title("🚬 Marlboro Filter Black")
use_filters = st.sidebar.checkbox("Gunakan Filter", value=True)

stok_min = st.sidebar.number_input("Batas minimal stok", min_value=0, value=50, help="Stok minimum yang diperbolehkan sebelum produk dianggap habis")
terjual_min = st.sidebar.number_input("Batas minimal terjual per bulan", min_value=0, value=30, help="Jumlah terjual minimum per bulan untuk produk populer")
harga_min = st.sidebar.number_input("Batas minimal harga produk", min_value=0.0, value=10000.0, help="Harga minimum produk yang ingin ditampilkan")
komisi_persen_min = st.sidebar.number_input("Batas minimal komisi (%)", min_value=0.0, value=2.0, help="Persentase komisi minimum yang menguntungkan")
komisi_rp_min = st.sidebar.number_input("Batas minimal komisi (Rp)", min_value=0.0, value=0.0, help="Nominal komisi minimum dalam rupiah")

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
        
        # Pastikan semua kolom penting ada
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
    # Harga dan Stok: isi dengan NaN lalu ganti dengan rata-rata jika memungkinkan
    df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce')
    
    # Terjual Bulanan: isi dengan median jika kosong
    df['Terjual(Bulanan)'] = pd.to_numeric(df['Terjual(Bulanan)'], errors='coerce').fillna(
        df['Terjual(Bulanan)'].median() if not df['Terjual(Bulanan)'].isnull().all() else 0
    )
    
    # Terjual Semua: isi dengan median jika kosong
    df['Terjual(Semua)'] = pd.to_numeric(df['Terjual(Semua)'], errors='coerce').fillna(
        df['Terjual(Semua)'].median() if not df['Terjual(Semua)'].isnull().all() else 0
    )
    
    # Stock: isi dengan median jika kosong
    df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(
        df['Stock'].median() if not df['Stock'].isnull().all() else 0
    )
    
    # Komisi: tetap isi 0 jika tidak ditemukan
    df['Komisi(%)'] = pd.to_numeric(df['Komisi(%)'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
    
    # Komisi(Rp): Bersihkan format mata uang
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
                
            # Menghitung trend dengan pembatasan dua desimal
            filtered_df['Trend'] = (
                filtered_df['Terjual(Bulanan)'] / 
                filtered_df['Terjual(Semua)'].replace(0, 1) * 100
            ).round(2).fillna(0)

            # Menentukan status
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

            st.markdown(f"""
            <div class="stat-box">
                <div class="section-title">📊 Statistik</div>
                <ul>
                    <li>Total produk diproses: <strong>{total_links}</strong></li>
                    <li>Produk unik setelah hapus duplikat: <strong>{len(combined_df)}</strong></li>
                    <li>Produk lolos filter: <strong>{len(filtered_df)}</strong></li>
                    <li>Produk tidak lolos filter: <strong>{len(combined_df) - len(filtered_df)}</strong></li>
                    <li>Duplikat yang dihapus: <strong>{deleted_dupes}</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("✅ Final Produk")
            st.dataframe(filtered_df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download Data Produk (CSV)", 
                                 filtered_df.to_csv(index=False).encode('utf-8'), 
                                 file_name="data_produk.csv", 
                                 mime='text/csv')
            with col2:
                st.download_button("⬇️ Download Data Produk (Excel)",
                                 filtered_df.to_excel(index=False).encode('utf-8'),
                                 file_name="data_produk.xlsx",
                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            st.subheader("🗑️ Produk Dihapus")
            st.dataframe(combined_df[~combined_df.index.isin(filtered_df.index)])
            st.download_button("⬇️ Download sampah", 
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
    <div class="footer">
        &copy; 2025 - Dibuat oleh Wong Sukses
    </div>
""", unsafe_allow_html=True)
