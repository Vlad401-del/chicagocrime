# ============================================================
# FILE: import_mysql.py
# FUNGSI: Load cleaned CSV Chicago Crime → transform → import ke MySQL
# SUMBER: Berdasarkan panduan chicago_crime_KBA_guide.md
# ============================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from tqdm import tqdm
import os
import warnings
warnings.filterwarnings('ignore')

# ----------------------------------------------------------
# KONFIGURASI — Laragon MySQL (root tanpa password)
# ----------------------------------------------------------
DB_USER     = 'root'
DB_PASSWORD = ''
DB_HOST     = '127.0.0.1'
DB_PORT     = '3306'
DB_NAME     = 'chicago_crime_db'
CHUNK_SIZE  = 5000

BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CSV_PATH    = os.path.join(BASE_DIR, 'data', 'cleaned', 'crimes_2021_2026.csv')

engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    echo=False
)

# ----------------------------------------------------------
# 0. TRUNCATE SEMUA TABEL (urutan: fact dulu, lalu dimensi)
# ----------------------------------------------------------
print("=" * 60)
print("PERSIAPAN: Mengosongkan tabel yang ada...")
print("=" * 60)

with engine.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for tbl in ['fact_arrest_prediction', 'fact_incident',
                 'dim_time', 'dim_crime_type', 'dim_location', 'dim_district']:
        conn.execute(text(f"TRUNCATE TABLE {tbl}"))
        print(f"   Tabel {tbl} dikosongkan")
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    conn.commit()

# ----------------------------------------------------------
# 1. LOAD CSV
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("TAHAP 1: Loading cleaned CSV...")
print("=" * 60)
df = pd.read_csv(CSV_PATH, low_memory=False)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df.dropna(subset=['Date', 'District', 'IUCR'], inplace=True)
df.reset_index(drop=True, inplace=True)
print(f"   {len(df):,} record siap diproses")

# ----------------------------------------------------------
# 2. POPULATE dim_time
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("TAHAP 2: Mengisi dim_time...")
print("=" * 60)

shift_map = {
    **{h: 'Night'     for h in range(0, 6)},
    **{h: 'Morning'   for h in range(6, 12)},
    **{h: 'Afternoon' for h in range(12, 18)},
    **{h: 'Evening'   for h in range(18, 24)},
}
day_names  = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
month_names = ['','January','February','March','April','May','June',
               'July','August','September','October','November','December']

times = df[['Date']].copy()
times['full_date']   = times['Date'].dt.date
times['hour']        = times['Date'].dt.hour
times.drop_duplicates(subset=['full_date', 'hour'], inplace=True)

times['year']        = times['Date'].dt.year
times['quarter']     = times['Date'].dt.quarter
times['month']       = times['Date'].dt.month
times['month_name']  = times['month'].map(lambda m: month_names[m])
times['day']         = times['Date'].dt.day
times['day_of_week'] = times['Date'].dt.dayofweek + 1  # 1=Mon, 7=Sun
times['day_name']    = times['Date'].dt.dayofweek.map(lambda d: day_names[d])
times['shift']       = times['hour'].map(shift_map)
times['is_weekend']  = times['day_of_week'].isin([6, 7]).astype(int)
times.drop(columns=['Date'], inplace=True)

# Insert in chunks with progress bar
print(f"   Inserting {len(times):,} records...")
for i in tqdm(range(0, len(times), CHUNK_SIZE), desc="   dim_time"):
    chunk = times.iloc[i:i+CHUNK_SIZE]
    chunk.to_sql('dim_time', engine, if_exists='append', index=False, method='multi')
print(f"   {len(times):,} record dim_time berhasil diimport")

# ----------------------------------------------------------
# 3. POPULATE dim_crime_type
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("TAHAP 3: Mengisi dim_crime_type...")
print("=" * 60)

violent_types = ['HOMICIDE','ROBBERY','BATTERY','ASSAULT','CRIMINAL SEXUAL ASSAULT',
                 'KIDNAPPING','ARSON','HUMAN TRAFFICKING']

crime_types = df[['IUCR','Primary Type','Description','FBI Code']].drop_duplicates('IUCR').copy()
crime_types.columns = ['iucr_code','primary_type','description','fbi_code']
crime_types['is_violent']     = crime_types['primary_type'].isin(violent_types).astype(int)
crime_types['severity_level'] = crime_types['is_violent'].map({1:'High', 0:'Medium'})
crime_types.fillna('UNKNOWN', inplace=True)

crime_types.to_sql('dim_crime_type', engine, if_exists='append', index=False, chunksize=CHUNK_SIZE)
print(f"   {len(crime_types):,} jenis kejahatan berhasil diimport")

# ----------------------------------------------------------
# 4. POPULATE dim_location
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("TAHAP 4: Mengisi dim_location...")
print("=" * 60)

loc_cols = ['Block','Location Description','Community Area','Ward','Beat',
            'Latitude','Longitude','X Coordinate','Y Coordinate']
locations = df[loc_cols].drop_duplicates().copy()
locations.columns = ['block','location_desc','community_area_no','ward','beat',
                     'latitude','longitude','x_coordinate','y_coordinate']
locations.fillna({'block':'UNKNOWN','location_desc':'UNKNOWN'}, inplace=True)
locations.reset_index(drop=True, inplace=True)

print(f"   Inserting {len(locations):,} records...")
for i in tqdm(range(0, len(locations), CHUNK_SIZE), desc="   dim_location"):
    chunk = locations.iloc[i:i+CHUNK_SIZE]
    chunk.to_sql('dim_location', engine, if_exists='append', index=False, method='multi')
print(f"   {len(locations):,} lokasi berhasil diimport")

# ----------------------------------------------------------
# 5. POPULATE dim_district
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("TAHAP 5: Mengisi dim_district...")
print("=" * 60)

# districts = df[['District']].drop_duplicates().dropna().copy()
# districts.columns = ['district_no']
# districts['district_no']   = districts['district_no'].astype(int)
# districts['district_name'] = districts['district_no'].map(lambda d: f'District {d}')

districts = df[['District']].dropna().copy()
districts['District'] = districts['District'].astype(int)
districts = districts.drop_duplicates(subset=['District'])
districts.columns = ['district_no']
districts['district_name'] = districts['district_no'].apply(
    lambda d: f'District {d}'
)

districts.to_sql('dim_district', engine, if_exists='append', index=False)
print(f"   {len(districts):,} distrik berhasil diimport")

# ----------------------------------------------------------
# 6. POPULATE fact_incident (dengan JOIN id dari tabel dimensi)
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("TAHAP 6: Mengisi fact_incident...")
print("=" * 60)

# Ambil mapping id dari DB
print("   Mengambil mapping ID dari database...")
time_map     = pd.read_sql("SELECT time_id, full_date, hour FROM dim_time", engine)
crime_map    = pd.read_sql("SELECT crime_type_id, iucr_code FROM dim_crime_type", engine)
district_map = pd.read_sql("SELECT district_id, district_no FROM dim_district", engine)
# Ambil SEMUA kolom location untuk merge 1-to-1
location_map = pd.read_sql(
    "SELECT location_id, block, location_desc, community_area_no, ward, beat, "
    "latitude, longitude, x_coordinate, y_coordinate FROM dim_location", engine
)

# Siapkan kolom join di df
df['full_date'] = df['Date'].dt.date.astype(str)
df['hour']      = df['Date'].dt.hour

# Merge time
time_map['full_date'] = time_map['full_date'].astype(str)
df = df.merge(time_map, on=['full_date','hour'], how='left')

# Merge crime type
df = df.merge(crime_map.rename(columns={'iucr_code':'IUCR'}), on='IUCR', how='left')

# Merge district
df['District'] = df['District'].astype('Int64')
district_map['district_no'] = district_map['district_no'].astype('Int64')
df = df.merge(district_map.rename(columns={'district_no':'District'}), on='District', how='left')

# Merge location — gunakan SEMUA kolom agar 1-to-1 (tidak terjadi row explosion)
loc_join_left  = ['Block','Location Description','Community Area','Ward','Beat',
                  'Latitude','Longitude','X Coordinate','Y Coordinate']
loc_join_right = ['block','location_desc','community_area_no','ward','beat',
                  'latitude','longitude','x_coordinate','y_coordinate']
df = df.merge(
    location_map,
    left_on=loc_join_left,
    right_on=loc_join_right,
    how='left'
)

print(f"   Record setelah merge: {len(df):,}")

# Siapkan fact table
fact = df[['Case Number','time_id','crime_type_id','location_id','district_id',
           'Domestic','Arrest','Updated On']].copy()
fact.columns = ['case_number','time_id','crime_type_id','location_id','district_id',
                'is_domestic','arrest_made','updated_on']

fact['is_domestic'] = pd.to_numeric(fact['is_domestic'], errors='coerce').fillna(0).astype(int)
fact['arrest_made'] = pd.to_numeric(fact['arrest_made'], errors='coerce').fillna(0).astype(int)
fact['updated_on']  = pd.to_datetime(fact['updated_on'], errors='coerce')

# Hapus record dengan FK null
before = len(fact)
fact.dropna(subset=['time_id','crime_type_id','district_id','location_id'], inplace=True)
dropped = before - len(fact)
if dropped > 0:
    print(f"   (!) {dropped:,} record dihapus karena FK null")

# Deduplikasi berdasarkan case_number (ambil yang pertama)
before = len(fact)
fact.drop_duplicates(subset=['case_number'], keep='first', inplace=True)
deduped = before - len(fact)
if deduped > 0:
    print(f"   (!) {deduped:,} duplikat case_number dihapus")

# Konversi FK ke int
for col in ['time_id','crime_type_id','location_id','district_id']:
    fact[col] = fact[col].astype(int)

fact.reset_index(drop=True, inplace=True)

print(f"   Inserting {len(fact):,} records...")
for i in tqdm(range(0, len(fact), CHUNK_SIZE), desc="   fact_incident"):
    chunk = fact.iloc[i:i+CHUNK_SIZE]
    try:
        chunk.to_sql('fact_incident', engine, if_exists='append', index=False, method='multi')
    except Exception as e:
        # Skip duplicate case numbers individually
        for _, row in chunk.iterrows():
            try:
                row.to_frame().T.to_sql('fact_incident', engine, if_exists='append', index=False)
            except:
                pass

print(f"   {len(fact):,} insiden berhasil diimport ke fact_incident")

# ----------------------------------------------------------
# 7. VERIFIKASI HASIL
# ----------------------------------------------------------
print("\n" + "=" * 60)
print("VERIFIKASI HASIL IMPORT")
print("=" * 60)

with engine.connect() as conn:
    for tbl in ['dim_time','dim_crime_type','dim_location','dim_district',
                'fact_incident','fact_arrest_prediction']:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
        count = result.scalar()
        print(f"   {tbl}: {count:,} record")

print("\n" + "=" * 60)
print("IMPORT SELESAI!")
print("=" * 60)
