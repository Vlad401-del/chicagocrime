# Implementation Plan - Chicago Crime Streamlit Dashboard

Rencana ini bertujuan untuk membangun dashboard interaktif menggunakan Streamlit untuk memvisualisasikan data kejahatan Chicago (2021-2026) yang telah tersimpan di MySQL.

## User Review Required

> [!IMPORTANT]
> Dashboard ini akan membutuhkan koneksi langsung ke MySQL Laragon Anda. Pastikan MySQL dalam keadaan menyala saat menjalankan Streamlit.

## Proposed Changes

### Dashboard Component

#### [NEW] [app.py](file:///d:/laragon/www/chicagocrime/dashboard/app.py)
Aplikasi utama Streamlit yang akan berisi:
- **Sidebar Filters**: Filter berdasarkan Tahun, Jenis Kejahatan (Primary Type), dan Distrik.
- **Key Metrics**: Total Kejahatan, Arrest Rate (%), Domestic Incident (%), dan Tren vs Bulan Lalu.
- **Visualisasi**:
    - **Trend Over Time**: Grafik garis insiden bulanan.
    - **Top Crime Categories**: Grafik batang jenis kejahatan terbanyak.
    - **Heatmap/Map**: Peta lokasi kejahatan (menggunakan Latitude/Longitude).
    - **Arrest Analysis**: Perbandingan jumlah penangkapan vs tidak.
- **Data Table**: Tampilan 100 data terbaru dengan fitur pencarian.

### Dependencies

#### [MODIFY] [requirements.txt](file:///d:/laragon/www/chicagocrime/requirements.txt)
Menambahkan:
- `streamlit`
- `plotly` (untuk grafik interaktif yang lebih premium)

## Verification Plan

### Automated Tests
- Menjalankan `streamlit run dashboard/app.py` dan memverifikasi koneksi database berhasil.
- Mencoba setiap filter di sidebar untuk memastikan data terupdate secara dinamis.

### Manual Verification
- Memastikan angka di dashboard sinkron dengan hasil query SQL manual.
- Memastikan peta menampilkan titik-titik koordinat dengan benar.
