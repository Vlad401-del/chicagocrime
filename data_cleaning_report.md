# Laporan Data Cleaning & Transformation: Chicago Crime Dataset

Dokumen ini merangkum proses pembersihan data (*data cleaning*) dan transformasi data (*data transformation*) dari dataset mentah Chicago Crime sebelum dimasukkan ke dalam pangkalan data MySQL dan digunakan untuk analisis Machine Learning.

---

## 1. Perbedaan Jumlah Record (Raw vs Cleaned)

Proses pembersihan berhasil mempertahankan mayoritas integritas data sembari membuang anomali dan duplikasi.

- **Total Record Mentah (Raw)**: 1.273.286 baris
- **Total Record Bersih (Cleaned)**: 1.273.124 baris
- **Selisih Data**: **162 baris**

Selisih 162 baris ini merupakan data **duplikat** berdasarkan nomor kasus (`Case Number`). Karena satu nomor kasus harus merujuk pada satu insiden unik, duplikat tersebut dihapus (dengan mempertahankan entri data pertama yang ditemukan).

---

## 2. Proses Data Cleaning

Proses pembersihan dilakukan menggunakan pustaka `pandas` di Python (melalui `scripts/cleaning.py`) dengan urutan pengerjaan sebagai berikut:

### A. Filter Relevansi Tahun
Data disaring (*filter*) secara eksplisit untuk hanya mencakup insiden yang terjadi dalam rentang tahun **2021 hingga 2026**, agar analisis tetap fokus pada tren kejahatan era modern/terbaru.

### B. Penghapusan Kolom Redundan
Menghapus kolom `Location`. Alasannya, kolom ini hanyalah teks gabungan dari kolom `Latitude` dan `Longitude`. Menghapus kolom ini menghemat penggunaan memori dan memangkas ukuran *file*.

### C. Penanganan Data Kosong (Missing Values Imputation)
Tidak semua data dibuang saat ada sel yang kosong. Proses imputasi yang dilakukan meliputi:
1. **Location Description**: Mengisi **6.432** baris data kosong dengan teks `'UNKNOWN'`.
2. **Koordinat (X/Y, Latitude, Longitude)**: Mengisi **17.016** baris data koordinat yang hilang dengan nilai `0` atau `0.0` sebagai representasi default ketika lokasi absolut tidak tercatat.
3. **Ward & Community Area**: Mengisi data distrik/wilayah spesifik yang kosong dengan angka `0`.

### D. Standardisasi Tipe Data
1. Mengubah format kolom target `Arrest` (Penangkapan) dan `Domestic` (Kekerasan Rumah Tangga) dari format Boolean (True/False) menjadi format biner integer (**1** dan **0**) agar lebih mudah dikelola oleh MySQL dan Algoritma Machine Learning.
2. Memastikan tipe data bernomor dibaca secara presisi sebagai `int` atau `float`.
3. Menghilangkan `.0` di ujung kode teks pada kolom `IUCR` dan `FBI Code`.

### E. Standardisasi Format Teks
Memastikan konsistensi format penulisan (*case formatting*) untuk mempermudah pencarian dan pengelompokan. Seluruh kolom berbasis teks seperti `Block`, `Primary Type`, `Description`, dan `Location Description` diubah menjadi **HURUF KAPITAL (UPPERCASE)** serta menghilangkan spasi berlebih (*trailing spaces*).

---

## 3. Proses Transformasi Data (Data Transformation)

Setelah dibersihkan, data tidak langsung ditumpuk ke dalam tabel tunggal di database. Data mengalami proses transformasi model **Star Schema** (melalui `scripts/import_mysql.py`) untuk memisahkan antara tabel metrik (*Fact*) dan tabel detail (*Dimension*).

### A. Pembuatan Tabel Dimensi (Dimension Tables)
Data dipecah berdasarkan entitas logis untuk menghilangkan redundansi di database relasional:

1. **`dim_time` (Dimensi Waktu)**:
   - Diekstrak dari kolom `Date`.
   - Dilakukan transformasi penambahan fitur turunan seperti: Ekstraksi *Hour* (jam), *Month* (bulan), *Year* (tahun), *Day of Week* (nama hari).
   - Penambahan kategori seperti **Shift** (Pagi, Siang, Sore, Malam) dan penanda **is_weekend** (Apakah insiden terjadi di akhir pekan).

2. **`dim_crime_type` (Dimensi Kejahatan)**:
   - Mendaftar semua kombinasi unik dari kode `IUCR`, `Primary Type`, `Description`, dan `FBI Code`.
   - Menambahkan kolom fitur klasifikasi turunan `is_violent` (skala 1/0) dan `severity_level` (High/Medium) dengan mendeteksi jenis kejahatan berisiko tinggi (misal: HOMICIDE, ASSAULT, ROBBERY).

3. **`dim_location` (Dimensi Lokasi)**:
   - Mengelompokkan kombinasi lokasi unik berdasarkan `Block`, `Location Description`, `Ward`, `Beat`, hingga titik Koordinat. Memisahkan data geografis dari kejadian aslinya.

4. **`dim_district` (Dimensi Distrik Kepolisian)**:
   - Membuat ID unik untuk setiap kode `District`.

### B. Pembuatan Tabel Fakta (Fact Table)
Transformasi terakhir adalah membuat tabel utama bernama **`fact_incident`**:
- Proses ini menggunakan fungsi *Merge/Join* pandas yang mencocokkan baris-baris pada CSV yang sudah bersih dengan *ID/Foreign Key* dari masing-masing tabel dimensi di atas.
- Tabel ini hanya menyimpan metrik dasar seperti `is_domestic`, `arrest_made` serta sekumpulan kunci (*Foreign Key*) menuju tabel dimensi. Proses ini sukses memetakan jutaan baris data secara lebih ringkas dan terstruktur (kurang lebih terhubung secara relasional tipe *1-to-many*).
