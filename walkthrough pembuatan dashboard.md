# Laporan Penyelesaian: Dashboard Streamlit Chicago Crime

Dashboard analitik interaktif untuk dataset Chicago Crime (2021-2026) telah berhasil dibangun dan dapat diakses.

## Fitur Utama yang Diimplementasikan

1. **Integrasi Database Otomatis**: 
   Aplikasi secara langsung terkoneksi ke `chicago_crime_db` di MySQL menggunakan SQLAlchemy, sehingga data yang ditampilkan selalu aktual. Dilengkapi sistem *caching* (`@st.cache_data`) agar dashboard tidak lambat meski memproses jutaan baris.

2. **Panel Filter Dinamis**:
   Pengguna dapat menyaring seluruh visualisasi berdasarkan:
   - **Tahun Kejadian** (2021 hingga 2026)
   - **Distrik Kepolisian** (District 1 - 31)
   - **Kategori Kejahatan Utama** (Misal: THEFT, BATTERY, HOMICIDE, dll)

3. **Key Performance Indicators (KPI)**:
   - **Total Kejahatan**: Menampilkan jumlah insiden sesuai filter.
   - **Arrest Rate**: Persentase insiden yang berujung pada penangkapan polisi.
   - **Kasus Domestik**: Persentase insiden yang tergolong kekerasan dalam rumah tangga/domestik.

4. **Visualisasi Interaktif (Plotly)**:
   - **Tren Bulanan (Line Chart)**: Melihat pergerakan jumlah kriminalitas dari waktu ke waktu secara fluktuatif.
   - **Top 10 Kejahatan (Bar Chart)**: Menemukan kategori kejahatan apa yang paling dominan di area/tahun tertentu.
   - **Peta Lokasi (Mapbox Scatter)**: Menampilkan titik koordinat persis setiap kejadian. *(Dibatasi 2000 data teratas agar peramban tetap ringan)*.

5. **Tabel Data Rinci**:
   Menampilkan daftar 100 insiden terbaru lengkap dengan nomor kasus, tanggal, blok lokasi, dan status penangkapan untuk keperluan audit silang.

## Status Aplikasi

> [!TIP]
> Aplikasi saat ini sedang berjalan di latar belakang! Anda dapat langsung membukanya dengan mengklik tautan berikut di peramban web Anda:
> **http://localhost:8501**
