# Panduan Tugas Kecerdasan Bisnis Analitik
## Dataset: Chicago Crime (2018–2023)

---

## Daftar Isi

1. [Gambaran Umum Dataset](#1-gambaran-umum-dataset)
2. [Download & Persiapan Data](#2-download--persiapan-data)
3. [Struktur Database MySQL (5 Modul)](#3-struktur-database-mysql-5-modul)
4. [Script Import Data ke MySQL (Python)](#4-script-import-data-ke-mysql-python)
5. [Algoritma Klasifikasi: Random Forest](#5-algoritma-klasifikasi-random-forest)
6. [Tampilan Web (Flask + Bootstrap)](#6-tampilan-web-flask--bootstrap)
7. [Checklist Pemenuhan Kriteria Tugas](#7-checklist-pemenuhan-kriteria-tugas)

---

## 1. Gambaran Umum Dataset

| Atribut | Detail |
|---|---|
| **Nama** | Chicago Crime Dataset |
| **Sumber** | [Kaggle](https://www.kaggle.com/datasets/chicago/chicago-crime) / [Chicago Data Portal](https://data.cityofchicago.org/) |
| **Total Record Asli** | 7+ juta (2001–sekarang) |
| **Record Setelah Filter** | ±80.000–150.000 (filter 2018–2023) |
| **Rentang Waktu** | 2001–sekarang → **digunakan 2018–2023 (5 tahun)** |
| **Target Klasifikasi** | `Arrest` → apakah berujung penangkapan? (True/False) |
| **Lisensi** | Public Domain (Open Government Data) |

### Kolom Utama dalam Dataset Mentah

| Kolom | Tipe | Keterangan |
|---|---|---|
| `ID` | INT | ID unik setiap insiden |
| `Case Number` | VARCHAR | Nomor kasus kepolisian |
| `Date` | DATETIME | Tanggal dan waktu kejadian |
| `Block` | VARCHAR | Nama blok jalan |
| `IUCR` | VARCHAR | Kode klasifikasi kejahatan Illinois |
| `Primary Type` | VARCHAR | Jenis kejahatan utama (THEFT, BATTERY, dll) |
| `Description` | VARCHAR | Deskripsi detail kejahatan |
| `Location Description` | VARCHAR | Lokasi fisik kejadian |
| `Arrest` | BOOLEAN | **Target prediksi** — apakah terjadi penangkapan |
| `Domestic` | BOOLEAN | Apakah kejadian domestik |
| `Beat` | INT | Kode area patroli polisi |
| `District` | INT | Nomor distrik kepolisian |
| `Ward` | INT | Nomor ward kota Chicago |
| `Community Area` | INT | Nomor area komunitas |
| `FBI Code` | VARCHAR | Kode kejahatan FBI |
| `X Coordinate` | FLOAT | Koordinat X (proyeksi State Plane) |
| `Y Coordinate` | FLOAT | Koordinat Y |
| `Latitude` | FLOAT | Koordinat lintang |
| `Longitude` | FLOAT | Koordinat bujur |
| `Year` | INT | Tahun kejadian |

---

## 2. Download & Persiapan Data

### Opsi A — Download via Kaggle CLI (Direkomendasikan)

```bash
# Install Kaggle CLI
pip install kaggle

# Letakkan kaggle.json di ~/.kaggle/kaggle.json
# (download dari: https://www.kaggle.com/settings -> API -> Create New Token)

# Download dataset
kaggle datasets download -d chicago/chicago-crime
unzip chicago-crime.zip -d data/
```

### Opsi B — Download Manual

1. Buka [https://www.kaggle.com/datasets/chicago/chicago-crime](https://www.kaggle.com/datasets/chicago/chicago-crime)
2. Klik **Download** → simpan sebagai `crimes.csv`
3. Letakkan di folder `data/`

### Filter Data ke 5 Tahun (2018–2023)

```python
import pandas as pd

df = pd.read_csv('data/crimes.csv', low_memory=False)
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y %I:%M:%S %p')
df['Year'] = df['Date'].dt.year

# Filter 5 tahun
df_filtered = df[df['Year'].between(2018, 2023)].copy()
df_filtered.to_csv('data/crimes_2018_2023.csv', index=False)

print(f"Total record: {len(df_filtered):,}")
# Output: ~80.000–150.000 record
```

---

## 3. Struktur Database MySQL (5 Modul)

### Diagram Relasi

```
dim_crime_type ──────────┐
                         │
dim_location ────────────┼──── fact_incident ────── fact_arrest_prediction
                         │           │
dim_district ────────────┘           │
                                     │
                              dim_time (via date_id)
```

### DDL: Buat Database & Semua Tabel

```sql
-- ============================================================
-- BUAT DATABASE
-- ============================================================
CREATE DATABASE IF NOT EXISTS chicago_crime_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE chicago_crime_db;

-- ============================================================
-- MODUL 1: dim_time — Dimensi Waktu
-- Berisi data temporal setiap insiden (hari, bulan, tahun, shift)
-- ============================================================
CREATE TABLE dim_time (
    time_id         INT PRIMARY KEY AUTO_INCREMENT,
    full_date       DATE NOT NULL,
    year            SMALLINT NOT NULL,
    quarter         TINYINT NOT NULL,          -- 1–4
    month           TINYINT NOT NULL,          -- 1–12
    month_name      VARCHAR(15) NOT NULL,
    day             TINYINT NOT NULL,
    day_of_week     TINYINT NOT NULL,          -- 1=Minggu, 7=Sabtu
    day_name        VARCHAR(15) NOT NULL,
    hour            TINYINT NOT NULL,          -- 0–23
    shift           ENUM('Morning','Afternoon','Evening','Night') NOT NULL,
    is_weekend      TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE KEY uq_datetime (full_date, hour)
);

-- ============================================================
-- MODUL 2: dim_crime_type — Dimensi Jenis Kejahatan
-- Berisi klasifikasi jenis kejahatan berdasarkan IUCR & FBI Code
-- ============================================================
CREATE TABLE dim_crime_type (
    crime_type_id   INT PRIMARY KEY AUTO_INCREMENT,
    iucr_code       VARCHAR(10) NOT NULL,
    primary_type    VARCHAR(100) NOT NULL,
    description     VARCHAR(255),
    fbi_code        VARCHAR(10),
    is_violent      TINYINT(1) DEFAULT 0,      -- 1 = kejahatan kekerasan
    severity_level  ENUM('Low','Medium','High','Critical') DEFAULT 'Medium',
    UNIQUE KEY uq_iucr (iucr_code)
);

-- ============================================================
-- MODUL 3: dim_location — Dimensi Lokasi Kejadian
-- Berisi data geografis dan deskripsi tempat kejadian
-- ============================================================
CREATE TABLE dim_location (
    location_id         INT PRIMARY KEY AUTO_INCREMENT,
    block               VARCHAR(100),
    location_desc       VARCHAR(100),           -- STREET, RESIDENCE, ALLEY, dll
    community_area_no   TINYINT UNSIGNED,
    ward                TINYINT UNSIGNED,
    beat                SMALLINT UNSIGNED,
    latitude            DECIMAL(10, 7),
    longitude           DECIMAL(10, 7),
    x_coordinate        INT,
    y_coordinate        INT
);

-- ============================================================
-- MODUL 4: dim_district — Dimensi Distrik Kepolisian
-- Berisi informasi organisasi wilayah kepolisian Chicago
-- ============================================================
CREATE TABLE dim_district (
    district_id         INT PRIMARY KEY AUTO_INCREMENT,
    district_no         TINYINT UNSIGNED NOT NULL UNIQUE,
    district_name       VARCHAR(100),
    commander           VARCHAR(100),           -- bisa diisi manual
    total_beats         INT DEFAULT 0,
    area_sq_miles       DECIMAL(6,2),
    UNIQUE KEY uq_district (district_no)
);

-- ============================================================
-- MODUL 5: fact_incident — Fakta Utama Insiden Kejahatan
-- Tabel pusat yang menghubungkan semua dimensi
-- ============================================================
CREATE TABLE fact_incident (
    incident_id         INT PRIMARY KEY AUTO_INCREMENT,
    case_number         VARCHAR(20) UNIQUE NOT NULL,
    time_id             INT NOT NULL,
    crime_type_id       INT NOT NULL,
    location_id         INT NOT NULL,
    district_id         INT NOT NULL,
    is_domestic         TINYINT(1) DEFAULT 0,
    arrest_made         TINYINT(1) DEFAULT 0,   -- TARGET KLASIFIKASI
    updated_on          DATETIME,
    FOREIGN KEY (time_id)       REFERENCES dim_time(time_id),
    FOREIGN KEY (crime_type_id) REFERENCES dim_crime_type(crime_type_id),
    FOREIGN KEY (location_id)   REFERENCES dim_location(location_id),
    FOREIGN KEY (district_id)   REFERENCES dim_district(district_id),
    INDEX idx_year      (time_id),
    INDEX idx_crime     (crime_type_id),
    INDEX idx_district  (district_id),
    INDEX idx_arrest    (arrest_made)
);

-- ============================================================
-- MODUL TAMBAHAN: fact_arrest_prediction — Output Model Python
-- Menyimpan hasil prediksi algoritma Random Forest
-- ============================================================
CREATE TABLE fact_arrest_prediction (
    prediction_id       INT PRIMARY KEY AUTO_INCREMENT,
    incident_id         INT NOT NULL,
    model_name          VARCHAR(50) DEFAULT 'Random Forest',
    model_version       VARCHAR(20) DEFAULT 'v1.0',
    predicted_arrest    TINYINT(1) NOT NULL,    -- 0=tidak, 1=ya
    probability_arrest  DECIMAL(6,4) NOT NULL,  -- contoh: 0.8231
    actual_arrest       TINYINT(1),
    is_correct          TINYINT(1),
    predicted_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES fact_incident(incident_id)
);
```

---

## 4. Script Import Data ke MySQL (Python)

### Instalasi Dependencies

```bash
pip install pandas sqlalchemy pymysql scikit-learn tqdm
```

### Script Lengkap: `import_to_mysql.py`

```python
# ============================================================
# FILE: import_to_mysql.py
# FUNGSI: Load CSV Chicago Crime → transform → import ke MySQL
# ============================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# ----------------------------------------------------------
# KONFIGURASI — sesuaikan dengan environment kamu
# ----------------------------------------------------------
DB_USER     = 'root'
DB_PASSWORD = 'password'
DB_HOST     = 'localhost'
DB_PORT     = '3306'
DB_NAME     = 'chicago_crime_db'
CSV_PATH    = 'data/crimes_2018_2023.csv'
CHUNK_SIZE  = 5000

engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    echo=False
)

# ----------------------------------------------------------
# 1. LOAD CSV
# ----------------------------------------------------------
print("📂 Loading CSV...")
df = pd.read_csv(CSV_PATH, low_memory=False)
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
df.dropna(subset=['Date', 'District', 'IUCR'], inplace=True)
df.reset_index(drop=True, inplace=True)
print(f"   ✅ {len(df):,} record siap diproses")

# ----------------------------------------------------------
# 2. POPULATE dim_time
# ----------------------------------------------------------
print("\n⏱️  Mengisi dim_time...")

shift_map = {
    **{h: 'Night'     for h in list(range(0,6))},
    **{h: 'Morning'   for h in list(range(6,12))},
    **{h: 'Afternoon' for h in list(range(12,18))},
    **{h: 'Evening'   for h in list(range(18,24))},
}
day_names  = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
month_names = ['','January','February','March','April','May','June',
               'July','August','September','October','November','December']

times = df[['Date']].drop_duplicates().copy()
times['full_date']   = times['Date'].dt.date
times['year']        = times['Date'].dt.year
times['quarter']     = times['Date'].dt.quarter
times['month']       = times['Date'].dt.month
times['month_name']  = times['month'].map(lambda m: month_names[m])
times['day']         = times['Date'].dt.day
times['day_of_week'] = times['Date'].dt.dayofweek + 1  # 1=Mon, 7=Sun
times['day_name']    = (times['Date'].dt.dayofweek).map(lambda d: day_names[d])
times['hour']        = times['Date'].dt.hour
times['shift']       = times['hour'].map(shift_map)
times['is_weekend']  = times['day_of_week'].isin([6,7]).astype(int)
times.drop(columns=['Date'], inplace=True)
times.drop_duplicates(subset=['full_date','hour'], inplace=True)

times.to_sql('dim_time', engine, if_exists='append', index=False, method='multi', chunksize=CHUNK_SIZE)
print(f"   ✅ {len(times):,} record dim_time berhasil diimport")

# ----------------------------------------------------------
# 3. POPULATE dim_crime_type
# ----------------------------------------------------------
print("\n🔍 Mengisi dim_crime_type...")

violent_types = ['HOMICIDE','ROBBERY','BATTERY','ASSAULT','CRIMINAL SEXUAL ASSAULT',
                 'KIDNAPPING','ARSON','HUMAN TRAFFICKING']

crime_types = df[['IUCR','Primary Type','Description','FBI Code']].drop_duplicates('IUCR').copy()
crime_types.columns = ['iucr_code','primary_type','description','fbi_code']
crime_types['is_violent']    = crime_types['primary_type'].isin(violent_types).astype(int)
crime_types['severity_level'] = crime_types['is_violent'].map({1:'High', 0:'Medium'})
crime_types.fillna('UNKNOWN', inplace=True)

crime_types.to_sql('dim_crime_type', engine, if_exists='append', index=False, chunksize=CHUNK_SIZE)
print(f"   ✅ {len(crime_types):,} jenis kejahatan berhasil diimport")

# ----------------------------------------------------------
# 4. POPULATE dim_location
# ----------------------------------------------------------
print("\n📍 Mengisi dim_location...")

loc_cols = ['Block','Location Description','Community Area','Ward','Beat',
            'Latitude','Longitude','X Coordinate','Y Coordinate']
locations = df[loc_cols].drop_duplicates().copy()
locations.columns = ['block','location_desc','community_area_no','ward','beat',
                     'latitude','longitude','x_coordinate','y_coordinate']
locations.fillna({'block':'UNKNOWN','location_desc':'UNKNOWN'}, inplace=True)

locations.to_sql('dim_location', engine, if_exists='append', index=False, chunksize=CHUNK_SIZE)
print(f"   ✅ {len(locations):,} lokasi berhasil diimport")

# ----------------------------------------------------------
# 5. POPULATE dim_district
# ----------------------------------------------------------
print("\n🏛️  Mengisi dim_district...")

districts = df[['District']].drop_duplicates().dropna().copy()
districts.columns = ['district_no']
districts['district_no']  = districts['district_no'].astype(int)
districts['district_name'] = districts['district_no'].map(lambda d: f'District {d}')

districts.to_sql('dim_district', engine, if_exists='append', index=False)
print(f"   ✅ {len(districts):,} distrik berhasil diimport")

# ----------------------------------------------------------
# 6. POPULATE fact_incident (dengan JOIN id dari tabel dimensi)
# ----------------------------------------------------------
print("\n📋 Mengisi fact_incident...")

# Ambil mapping id dari DB
time_map     = pd.read_sql("SELECT time_id, full_date, hour FROM dim_time", engine)
crime_map    = pd.read_sql("SELECT crime_type_id, iucr_code FROM dim_crime_type", engine)
district_map = pd.read_sql("SELECT district_id, district_no FROM dim_district", engine)
location_map = pd.read_sql("SELECT location_id, block, location_desc FROM dim_location", engine)

# Merge ke df utama
df['full_date'] = df['Date'].dt.date.astype(str)
df['hour']      = df['Date'].dt.hour

time_map['full_date'] = time_map['full_date'].astype(str)
df = df.merge(time_map, on=['full_date','hour'], how='left')
df = df.merge(crime_map.rename(columns={'iucr_code':'IUCR'}), on='IUCR', how='left')
df['District'] = df['District'].astype('Int64')
district_map['district_no'] = district_map['district_no'].astype('Int64')
df = df.merge(district_map.rename(columns={'district_no':'District'}), on='District', how='left')
df = df.merge(
    location_map,
    left_on=['Block','Location Description'],
    right_on=['block','location_desc'],
    how='left'
)

fact = df[['Case Number','time_id','crime_type_id','location_id','district_id',
           'Domestic','Arrest','Updated On']].copy()
fact.columns = ['case_number','time_id','crime_type_id','location_id','district_id',
                'is_domestic','arrest_made','updated_on']
fact['is_domestic']  = fact['is_domestic'].map({True:1, False:0, 'true':1, 'false':0}).fillna(0).astype(int)
fact['arrest_made']  = fact['arrest_made'].map({True:1, False:0, 'true':1, 'false':0}).fillna(0).astype(int)
fact.dropna(subset=['time_id','crime_type_id','district_id'], inplace=True)

fact.to_sql('fact_incident', engine, if_exists='append', index=False,
            method='multi', chunksize=CHUNK_SIZE)
print(f"   ✅ {len(fact):,} insiden berhasil diimport ke fact_incident")

print("\n🎉 Import selesai! Semua data berhasil masuk ke MySQL.")
```

---

## 5. Algoritma Klasifikasi: Random Forest

**Target:** Memprediksi apakah suatu insiden kejahatan akan berujung pada penangkapan (`arrest_made = 1`).

### Script Lengkap: `predict_arrest.py`

```python
# ============================================================
# FILE: predict_arrest.py
# ALGORITMA: Random Forest Classifier
# TARGET: Prediksi apakah insiden berujung penangkapan (biner)
# ============================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, accuracy_score)
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# ----------------------------------------------------------
# 1. LOAD DATA DARI MYSQL
# ----------------------------------------------------------
engine = create_engine('mysql+pymysql://root:password@localhost/chicago_crime_db')

query = """
    SELECT
        ct.primary_type,
        ct.fbi_code,
        ct.is_violent,
        ct.severity_level,
        l.location_desc,
        l.community_area_no,
        l.beat,
        d.district_no,
        t.year,
        t.month,
        t.day_of_week,
        t.hour,
        t.shift,
        t.is_weekend,
        t.quarter,
        fi.is_domestic,
        fi.arrest_made           AS target
    FROM fact_incident fi
    JOIN dim_time       t  ON fi.time_id       = t.time_id
    JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
    JOIN dim_location   l  ON fi.location_id   = l.location_id
    JOIN dim_district   d  ON fi.district_id   = d.district_id
"""
print("📥 Loading data dari MySQL...")
df = pd.read_sql(query, engine)
print(f"   Total: {len(df):,} record")

# ----------------------------------------------------------
# 2. FEATURE ENGINEERING & PREPROCESSING
# ----------------------------------------------------------
# Encode kolom kategorikal
cat_cols = ['primary_type','fbi_code','severity_level','location_desc','shift']
le = LabelEncoder()
for col in cat_cols:
    df[col] = le.fit_transform(df[col].astype(str))

df.fillna(0, inplace=True)

feature_cols = [
    'primary_type', 'fbi_code', 'is_violent', 'severity_level',
    'location_desc', 'community_area_no', 'beat', 'district_no',
    'year', 'month', 'day_of_week', 'hour', 'shift',
    'is_weekend', 'quarter', 'is_domestic'
]

X = df[feature_cols]
y = df['target']

print(f"\n📊 Distribusi target:")
print(f"   Tidak ditangkap (0): {(y==0).sum():,} ({(y==0).mean()*100:.1f}%)")
print(f"   Ditangkap       (1): {(y==1).sum():,} ({(y==1).mean()*100:.1f}%)")

# ----------------------------------------------------------
# 3. SPLIT DATA (80% train, 20% test)
# ----------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\n✂️  Data split: {len(X_train):,} train | {len(X_test):,} test")

# ----------------------------------------------------------
# 4. TRAINING MODEL
# ----------------------------------------------------------
print("\n🌲 Melatih Random Forest...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    min_samples_split=10,
    min_samples_leaf=5,
    class_weight='balanced',  # menangani imbalanced data
    random_state=42,
    n_jobs=-1                 # gunakan semua CPU core
)
model.fit(X_train, y_train)
print("   ✅ Training selesai!")

# ----------------------------------------------------------
# 5. EVALUASI MODEL
# ----------------------------------------------------------
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("\n" + "="*50)
print("📈 HASIL EVALUASI MODEL")
print("="*50)
print(f"Accuracy  : {accuracy_score(y_test, y_pred):.4f}")
print(f"ROC-AUC   : {roc_auc_score(y_test, y_prob):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Tidak Ditangkap','Ditangkap']))

# Cross Validation
cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
print(f"\n5-Fold Cross Val AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Pred: Tidak','Pred: Ya'],
            yticklabels=['Aktual: Tidak','Aktual: Ya'])
plt.title('Confusion Matrix — Prediksi Penangkapan')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150)
print("\n   📊 Confusion matrix disimpan: confusion_matrix.png")

# Feature Importance
feat_imp = pd.Series(model.feature_importances_, index=feature_cols)
feat_imp.sort_values(ascending=False).head(10).plot(kind='barh', figsize=(8,5))
plt.title('Top 10 Feature Importance')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=150)
print("   📊 Feature importance disimpan: feature_importance.png")

# ----------------------------------------------------------
# 6. SIMPAN HASIL PREDIKSI KE MYSQL
# ----------------------------------------------------------
print("\n💾 Menyimpan hasil prediksi ke MySQL...")

# Ambil incident_id dari test set
incident_ids = pd.read_sql(
    f"SELECT incident_id FROM fact_incident LIMIT {len(X_test)}",
    engine
)['incident_id'].values[:len(X_test)]

results_df = pd.DataFrame({
    'incident_id'      : incident_ids,
    'model_name'       : 'Random Forest',
    'model_version'    : 'v1.0',
    'predicted_arrest' : y_pred,
    'probability_arrest': y_prob,
    'actual_arrest'    : y_test.values,
    'is_correct'       : (y_pred == y_test.values).astype(int)
})
results_df.to_sql('fact_arrest_prediction', engine, if_exists='append', index=False)
print(f"   ✅ {len(results_df):,} hasil prediksi tersimpan di fact_arrest_prediction")

# ----------------------------------------------------------
# 7. SIMPAN MODEL
# ----------------------------------------------------------
joblib.dump(model, 'random_forest_arrest.pkl')
print("\n🎯 Model disimpan: random_forest_arrest.pkl")
print("\n✅ Semua proses selesai!")
```

---

## 6. Tampilan Web (Flask + Bootstrap)

### Struktur Folder Proyek

```
chicago_crime_web/
├── app.py                  ← Flask main app
├── static/
│   └── charts/             ← Grafik Chart.js
├── templates/
│   ├── base.html           ← Layout utama + Bootstrap
│   ├── dashboard.html      ← Halaman dashboard utama
│   ├── incidents.html      ← Daftar insiden (Modul 5)
│   └── prediction.html     ← Hasil prediksi (Modul arrest)
└── requirements.txt
```

### `app.py` — Backend Flask

```python
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import pandas as pd

app = Flask(__name__)
engine = create_engine('mysql+pymysql://root:password@localhost/chicago_crime_db')

@app.route('/')
def dashboard():
    with engine.connect() as conn:
        # Total insiden per tahun
        yearly = pd.read_sql("""
            SELECT t.year, COUNT(*) AS total,
                   SUM(fi.arrest_made) AS total_arrested
            FROM fact_incident fi
            JOIN dim_time t ON fi.time_id = t.time_id
            GROUP BY t.year ORDER BY t.year
        """, conn)

        # Top 5 jenis kejahatan
        top_crimes = pd.read_sql("""
            SELECT ct.primary_type, COUNT(*) AS total
            FROM fact_incident fi
            JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
            GROUP BY ct.primary_type
            ORDER BY total DESC LIMIT 5
        """, conn)

        # Akurasi model
        accuracy = pd.read_sql("""
            SELECT ROUND(AVG(is_correct)*100, 2) AS accuracy
            FROM fact_arrest_prediction
        """, conn).iloc[0,0]

    return render_template('dashboard.html',
        yearly=yearly.to_dict('records'),
        top_crimes=top_crimes.to_dict('records'),
        accuracy=accuracy
    )

@app.route('/incidents')
def incidents():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    with engine.connect() as conn:
        data = pd.read_sql(f"""
            SELECT fi.case_number, ct.primary_type, l.location_desc,
                   d.district_no, t.full_date, t.hour, fi.arrest_made
            FROM fact_incident fi
            JOIN dim_time       t  ON fi.time_id       = t.time_id
            JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
            JOIN dim_location   l  ON fi.location_id   = l.location_id
            JOIN dim_district   d  ON fi.district_id   = d.district_id
            ORDER BY t.full_date DESC
            LIMIT {per_page} OFFSET {offset}
        """, conn)

    return render_template('incidents.html', incidents=data.to_dict('records'), page=page)

@app.route('/predictions')
def predictions():
    with engine.connect() as conn:
        data = pd.read_sql("""
            SELECT fi.case_number, ct.primary_type,
                   p.predicted_arrest, p.probability_arrest,
                   p.actual_arrest, p.is_correct, p.predicted_at
            FROM fact_arrest_prediction p
            JOIN fact_incident   fi ON p.incident_id   = fi.incident_id
            JOIN dim_crime_type  ct ON fi.crime_type_id = ct.crime_type_id
            ORDER BY p.predicted_at DESC LIMIT 200
        """, conn)
    return render_template('prediction.html', predictions=data.to_dict('records'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Menjalankan Aplikasi

```bash
pip install flask sqlalchemy pymysql pandas

cd chicago_crime_web
python app.py

# Buka browser: http://localhost:5000
```

---

## 7. Checklist Pemenuhan Kriteria Tugas

| No | Kriteria Tugas | Status | Bukti |
|---|---|---|---|
| 1 | Minimal 10.000 data/record | ✅ | ~80.000–150.000 record (filter 2018–2023) |
| 2 | Historis transaksi minimal 5 tahun | ✅ | Data 2018, 2019, 2020, 2021, 2022, 2023 |
| 3 | Minimal 5 modul | ✅ | `dim_time`, `dim_crime_type`, `dim_location`, `dim_district`, `fact_incident` |
| 4 | Import ke database MySQL | ✅ | Script `import_to_mysql.py` dengan SQLAlchemy |
| 5 | Ditampilkan melalui web | ✅ | Aplikasi Flask + Bootstrap di `app.py` |
| 6 | Klasifikasi/Prediksi dengan Python | ✅ | Random Forest Classifier (`predict_arrest.py`) |
| 7 | Dataset publik | ✅ | Kaggle / Chicago Data Portal (open data) |

---

## Urutan Pengerjaan yang Disarankan

```
1. Download dataset dari Kaggle
       ↓
2. Jalankan filter 2018–2023 (bagian 2)
       ↓
3. Buat database & semua tabel di MySQL (bagian 3)
       ↓
4. Jalankan import_to_mysql.py (bagian 4)
       ↓
5. Jalankan predict_arrest.py (bagian 5)
       ↓
6. Jalankan Flask web app (bagian 6)
       ↓
7. Screenshot & dokumentasi untuk laporan
```

---

*Dokumen ini dibuat untuk keperluan tugas mata kuliah Kecerdasan Bisnis Analitik.*
