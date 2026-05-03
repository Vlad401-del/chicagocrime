# Dokumentasi Proses Machine Learning: Chicago Crime Arrest Prediction

Dokumen ini merangkum alur kerja (*pipeline*) *machine learning* yang telah dibangun untuk memprediksi apakah suatu insiden kejahatan di Chicago akan berujung pada penangkapan (*Arrest*) menggunakan algoritma **Random Forest Classifier**.

---

## 1. Pemrosesan Data Awal (Preprocessing)
**Skrip:** `scripts/preprocess_ml.py`

Tahap ini bertujuan mengubah data mentah menjadi format numerik yang dapat dipelajari oleh model *machine learning*.
*   **Sumber Data**: Menggunakan `data/cleaned/crimes_2021_2026.csv`.
*   **Sampling Memori**: Mengingat ukuran dataset asli lebih dari 1,2 juta baris, dilakukan pengambilan sampel acak sebanyak **200.000 baris** untuk memastikan efisiensi memori (RAM) saat proses pelatihan.
*   **Pemilihan Fitur (Feature Selection)**: 
    *   **Fitur Waktu**: Mengekstrak `Hour` (jam) dan `Month` (bulan) dari kolom tanggal kejadian.
    *   **Fitur Lokasi & Demografi**: Menggunakan `District`, `Ward`, dan `Community Area`.
    *   **Fitur Kejadian**: Kolom `Domestic` diubah dari nilai True/False ke *integer* 1/0.
*   **Penanganan Kategori (One-Hot Encoding)**:
    *   Hanya mengambil **10 jenis kejahatan teratas** (`Primary Type`). Jenis lainnya dikelompokkan ke dalam kategori `"Other"`.
    *   Dilakukan *one-hot encoding* (`pd.get_dummies()`) pada jenis kejahatan tersebut untuk menjadikannya fitur biner berformat kolom tersendiri.
*   **Pembagian Data (Train-Test Split)**: Data dibagi menjadi **80% data latih** (160.000 data) dan **20% data uji** (40.000 data) dengan proporsi kelas target yang dijaga tetap seimbang (*stratified*).
*   **Penyimpanan Komponen Dasar**: Menyimpan matriks data ke `.npz` dan yang terpenting menyimpan urutan nama kolom hasil encoding ke dalam `models/model_features.pkl` sebagai referensi saat memprediksi data baru.

---

## 2. Pelatihan Model (Model Training)
**Skrip:** `scripts/train_rf.py`

Proses melatih model agar mampu memetakan pola dari fitur ke probabilitas penangkapan.
*   **Algoritma**: `RandomForestClassifier` dari Scikit-Learn.
*   **Parameter Model**:
    *   `n_estimators=50`: Model membangun 50 "pohon keputusan" untuk menghasilkan satu kesimpulan agregat, optimal antara akurasi dan kecepatan komputasi.
    *   `max_depth=20`: Membatasi kedalaman maksimal setiap pohon untuk menghindari *overfitting* (terlalu menghafal data latih).
    *   `class_weight='balanced'`: Penting karena mayoritas kejahatan (sekitar 86%) **tidak** berujung penangkapan. Parameter ini memberikan "bobot/perhatian" lebih pada kasus yang jarang terjadi (penangkapan).
*   **Penyimpanan**: Model latih yang sudah jadi (berukuran beberapa MB) disimpan sebagai `models/rf_model.pkl`.

---

## 3. Evaluasi Kinerja (Model Evaluation)
Evaluasi diuji secara mandiri pada 20% data (*Validation Set*) yang tidak pernah dilihat model saat pelatihan.
*   **Tingkat Akurasi (Accuracy)**: Mendapatkan akurasi keseluruhan sebesar **~85.8%**.
*   **AUC-ROC**: Skor *Area Under the Curve* mencapai **0.7904**, menandakan kapabilitas model yang baik dalam membedakan antara kelas "Akan Ditangkap" dan "Tidak Ditangkap".
*   **Laporan Visual**: Otomatis menghasilkan dua bukti visual performa:
    1.  `models/confusion_matrix.png`: Peta sebaran tebakan benar dan salah dari algoritma.
    2.  `models/roc_curve.png`: Kurva yang menunjukkan perbandingan sensitivitas (*True Positive Rate*) terhadap alarm palsu (*False Positive Rate*).
    3.  `models/classification_report.txt`: Laporan metrik detail mencakup Presisi dan Recall.

---

## 4. Proses Prediksi pada Data Baru (Inference/Prediction)
**Skrip:** `scripts/predict.py` & `dashboard/prediction.py`

Rangkaian alur ketika skrip ini diberikan kasus kejadian baru untuk diramal.
*   Sistem memuat model `rf_model.pkl` dan arsitektur kolom `model_features.pkl`.
*   Data baru diubah (jam, bulan, one-hot encode) agar mengikuti standar data latih.
*   **Penyelarasan Kolom Secara Dinamis**: Menggunakan metode `df.reindex()`. Artinya, meskipun ada jenis kejahatan baru atau ada jenis kejahatan yang tidak disinggung di data masukan, kolom yang dimasukkan ke model akan selalu *pas* urutan dan jumlahnya sesuai saat pelatihan. Kolom dummy yang absen akan otomatis diisi nilai nol (`0`).
*   Mengeluarkan *output* dua lapis:
    *   **Probabilitas (%)**: Seberapa yakin model bahwa tersangka akan tertangkap.
    *   **Label Biner**: 1 (Penangkapan) atau 0 (Tidak ada penangkapan).
