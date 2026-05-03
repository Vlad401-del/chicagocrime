# ============================================================
# FILE: cleaning.py
# FUNGSI: Membersihkan raw dataset Chicago Crime
#         → Filter 2021–2026, handle missing values, standardisasi
#         → Simpan hasil ke data/cleaned/
# ============================================================

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ----------------------------------------------------------
# KONFIGURASI PATH
# ----------------------------------------------------------
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_PATH    = os.path.join(BASE_DIR, 'data', 'raw', 'Crimes_-_2001_to_Present_20260501.csv')
CLEANED_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
OUTPUT_PATH = os.path.join(CLEANED_DIR, 'crimes_2021_2026.csv')

# Pastikan folder output ada
os.makedirs(CLEANED_DIR, exist_ok=True)

# ----------------------------------------------------------
# 1. LOAD RAW DATA
# ----------------------------------------------------------
print("=" * 60)
print("📂 TAHAP 1: Memuat raw dataset...")
print("=" * 60)
df = pd.read_csv(RAW_PATH, low_memory=False)
print(f"   Total record awal: {len(df):,}")
print(f"   Jumlah kolom     : {df.shape[1]}")
print(f"   Kolom: {list(df.columns)}")

# ----------------------------------------------------------
# 2. FILTER TAHUN 2021–2026
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("📅 TAHAP 2: Filter data tahun 2021–2026...")
print("=" * 60)

# Konversi kolom Date ke datetime
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
df['Year'] = df['Date'].dt.year

# Filter rentang tahun
df = df[df['Year'].between(2021, 2026)].copy()
print(f"   Record setelah filter 2021–2026: {len(df):,}")

# Tampilkan distribusi per tahun
print("\n   Distribusi per tahun:")
year_counts = df['Year'].value_counts().sort_index()
for year, count in year_counts.items():
    print(f"   {int(year)}: {count:,} record")

# ----------------------------------------------------------
# 3. HAPUS KOLOM YANG TIDAK DIPERLUKAN
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("🗑️  TAHAP 3: Menghapus kolom tidak diperlukan...")
print("=" * 60)

# Kolom 'Location' adalah gabungan (lat, lon) yang redundan
drop_cols = ['Location']
existing_drop = [c for c in drop_cols if c in df.columns]
if existing_drop:
    df.drop(columns=existing_drop, inplace=True)
    print(f"   Kolom dihapus: {existing_drop}")
else:
    print("   Tidak ada kolom yang perlu dihapus.")

# ----------------------------------------------------------
# 4. HANDLE MISSING VALUES
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("🔍 TAHAP 4: Menangani missing values...")
print("=" * 60)

# Tampilkan jumlah null per kolom (yang ada null-nya saja)
null_counts = df.isnull().sum()
null_cols = null_counts[null_counts > 0]
if len(null_cols) > 0:
    print("\n   Missing values sebelum cleaning:")
    for col, count in null_cols.items():
        pct = count / len(df) * 100
        print(f"   - {col}: {count:,} ({pct:.2f}%)")
else:
    print("   Tidak ada missing values.")

# 4a. Hapus record yang tidak punya Date (kritis)
before = len(df)
df.dropna(subset=['Date'], inplace=True)
dropped = before - len(df)
if dropped > 0:
    print(f"\n   ❌ Dihapus {dropped:,} record tanpa Date")

# 4b. Hapus record tanpa Case Number (kritis untuk identitas)
before = len(df)
df.dropna(subset=['Case Number'], inplace=True)
dropped = before - len(df)
if dropped > 0:
    print(f"   ❌ Dihapus {dropped:,} record tanpa Case Number")

# 4c. Hapus record tanpa IUCR dan District (kritis untuk relasi tabel)
before = len(df)
df.dropna(subset=['IUCR', 'District'], inplace=True)
dropped = before - len(df)
if dropped > 0:
    print(f"   ❌ Dihapus {dropped:,} record tanpa IUCR/District")

# 4d. Isi missing values kolom non-kritis dengan nilai default
fill_defaults = {
    'Block': 'UNKNOWN',
    'Primary Type': 'UNKNOWN',
    'Description': 'UNKNOWN',
    'Location Description': 'UNKNOWN',
    'FBI Code': 'UNKNOWN',
    'Ward': 0,
    'Community Area': 0,
    'Beat': 0,
    'X Coordinate': 0,
    'Y Coordinate': 0,
    'Latitude': 0.0,
    'Longitude': 0.0,
}
for col, default in fill_defaults.items():
    if col in df.columns:
        filled = df[col].isnull().sum()
        if filled > 0:
            df[col].fillna(default, inplace=True)
            print(f"   ✅ {col}: {filled:,} null → diisi '{default}'")

print(f"\n   Record setelah handling missing: {len(df):,}")

# ----------------------------------------------------------
# 5. STANDARDISASI TIPE DATA
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("🔧 TAHAP 5: Standardisasi tipe data...")
print("=" * 60)

# Konversi Arrest & Domestic dari string ke boolean/int
df['Arrest'] = df['Arrest'].map(
    {True: 1, False: 0, 'true': 1, 'false': 1, 'True': 1, 'False': 0}
).fillna(0).astype(int)

df['Domestic'] = df['Domestic'].map(
    {True: 1, False: 0, 'true': 1, 'false': 0, 'True': 1, 'False': 0}
).fillna(0).astype(int)

# Konversi kolom numerik
int_cols = ['ID', 'Beat', 'District', 'Ward', 'Community Area', 'Year']
for col in int_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

float_cols = ['X Coordinate', 'Y Coordinate', 'Latitude', 'Longitude']
for col in float_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

# Pastikan IUCR dan FBI Code tetap string
df['IUCR'] = df['IUCR'].astype(str).str.strip()
df['FBI Code'] = df['FBI Code'].astype(str).str.strip()
df['Case Number'] = df['Case Number'].astype(str).str.strip()

print("   ✅ Arrest & Domestic → integer (0/1)")
print("   ✅ Kolom numerik → int/float")
print("   ✅ IUCR, FBI Code, Case Number → string (stripped)")

# ----------------------------------------------------------
# 6. STANDARDISASI TEKS
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("📝 TAHAP 6: Standardisasi teks...")
print("=" * 60)

text_cols = ['Block', 'Primary Type', 'Description', 'Location Description']
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()

print("   ✅ Kolom teks → uppercase & stripped")

# ----------------------------------------------------------
# 7. HAPUS DUPLIKAT
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("♻️  TAHAP 7: Menghapus duplikat...")
print("=" * 60)

before = len(df)
df.drop_duplicates(subset=['Case Number'], keep='first', inplace=True)
dropped = before - len(df)
print(f"   Duplikat dihapus (berdasarkan Case Number): {dropped:,}")
print(f"   Record unik tersisa: {len(df):,}")

# ----------------------------------------------------------
# 8. RESET INDEX
# ----------------------------------------------------------
df.reset_index(drop=True, inplace=True)

# ----------------------------------------------------------
# 9. KONVERSI Updated On KE DATETIME
# ----------------------------------------------------------
if 'Updated On' in df.columns:
    df['Updated On'] = pd.to_datetime(df['Updated On'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')

# ----------------------------------------------------------
# 10. SIMPAN HASIL CLEANING
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("💾 TAHAP 8: Menyimpan hasil cleaning...")
print("=" * 60)

df.to_csv(OUTPUT_PATH, index=False)
file_size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
print(f"   📄 File: {OUTPUT_PATH}")
print(f"   📊 Total record bersih: {len(df):,}")
print(f"   📦 Ukuran file: {file_size_mb:.1f} MB")

# ----------------------------------------------------------
# RINGKASAN AKHIR
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("🎉 DATA CLEANING SELESAI!")
print("=" * 60)
print(f"\n   Ringkasan:")
print(f"   - Rentang tahun : {int(df['Year'].min())} – {int(df['Year'].max())}")
print(f"   - Total record  : {len(df):,}")
print(f"   - Total kolom   : {df.shape[1]}")
print(f"   - Output file   : {OUTPUT_PATH}")
print(f"\n   Distribusi Arrest:")
print(f"   - Tidak ditangkap (0): {(df['Arrest']==0).sum():,} ({(df['Arrest']==0).mean()*100:.1f}%)")
print(f"   - Ditangkap       (1): {(df['Arrest']==1).sum():,} ({(df['Arrest']==1).mean()*100:.1f}%)")
print(f"\n   Kolom final: {list(df.columns)}")
