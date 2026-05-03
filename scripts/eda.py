# ============================================================
# FILE: eda.py
# FUNGSI: Exploratory Data Analysis (EDA)
# DATASET: Chicago Crime (2021–2026)
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# ============================================================
# KONFIGURASI DATABASE
# ============================================================

DB_USER = "root"
DB_PASSWORD = ""
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "chicago_crime_db"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("=" * 60)
print("EDA CHICAGO CRIME")
print("=" * 60)

# ============================================================
# 1. TOTAL DATA
# ============================================================

query_total = """
SELECT COUNT(*) AS total
FROM fact_incident
"""

total_df = pd.read_sql(query_total, engine)

print("\nTOTAL DATA:")
print(total_df)

# ============================================================
# 2. CRIME PER YEAR
# ============================================================

query_year = """
SELECT
    t.year,
    COUNT(*) AS total_crime
FROM fact_incident fi
JOIN dim_time t
    ON fi.time_id = t.time_id
GROUP BY t.year
ORDER BY t.year
"""

year_df = pd.read_sql(query_year, engine)

print("\nCRIME PER YEAR:")
print(year_df)

# Chart
plt.figure(figsize=(8,5))
plt.plot(year_df['year'], year_df['total_crime'], marker='o')
plt.title('Crime Per Year')
plt.xlabel('Year')
plt.ylabel('Total Crime')
plt.tight_layout()
plt.savefig('crime_per_year.png')

# ============================================================
# 3. TOP 10 CRIME TYPES
# ============================================================

query_crime = """
SELECT
    ct.primary_type,
    COUNT(*) AS total
FROM fact_incident fi
JOIN dim_crime_type ct
    ON fi.crime_type_id = ct.crime_type_id
GROUP BY ct.primary_type
ORDER BY total DESC
LIMIT 10
"""

crime_df = pd.read_sql(query_crime, engine)

print("\nTOP 10 CRIME TYPES:")
print(crime_df)

# Chart
plt.figure(figsize=(10,6))
plt.barh(crime_df['primary_type'], crime_df['total'])
plt.title('Top 10 Crime Types')
plt.tight_layout()
plt.savefig('top_crime_types.png')

# ============================================================
# 4. ARREST RATE
# ============================================================

query_arrest = """
SELECT
    arrest_made,
    COUNT(*) AS total
FROM fact_incident
GROUP BY arrest_made
"""

arrest_df = pd.read_sql(query_arrest, engine)

print("\nARREST DISTRIBUTION:")
print(arrest_df)

# Chart
plt.figure(figsize=(5,5))
plt.pie(
    arrest_df['total'],
    labels=['No Arrest', 'Arrest'],
    autopct='%1.1f%%'
)
plt.title('Arrest Distribution')
plt.savefig('arrest_distribution.png')

# ============================================================
# 5. CRIME BY DISTRICT
# ============================================================

query_district = """
SELECT
    d.district_no,
    COUNT(*) AS total
FROM fact_incident fi
JOIN dim_district d
    ON fi.district_id = d.district_id
GROUP BY d.district_no
ORDER BY total DESC
LIMIT 10
"""

district_df = pd.read_sql(query_district, engine)

print("\nTOP DISTRICTS:")
print(district_df)

# Chart
plt.figure(figsize=(10,6))
plt.bar(
    district_df['district_no'].astype(str),
    district_df['total']
)
plt.title('Top Districts by Crime')
plt.xlabel('District')
plt.ylabel('Total Crime')
plt.tight_layout()
plt.savefig('top_districts.png')

# ============================================================
# 6. CRIME BY HOUR
# ============================================================

query_hour = """
SELECT
    t.hour,
    COUNT(*) AS total
FROM fact_incident fi
JOIN dim_time t
    ON fi.time_id = t.time_id
GROUP BY t.hour
ORDER BY t.hour
"""

hour_df = pd.read_sql(query_hour, engine)

print("\nCRIME BY HOUR:")
print(hour_df)

# Chart
plt.figure(figsize=(10,5))
plt.plot(hour_df['hour'], hour_df['total'])
plt.title('Crime by Hour')
plt.xlabel('Hour')
plt.ylabel('Total Crime')
plt.tight_layout()
plt.savefig('crime_by_hour.png')

# ============================================================
# 7. DOMESTIC VS NON-DOMESTIC
# ============================================================

query_domestic = """
SELECT
    is_domestic,
    COUNT(*) AS total
FROM fact_incident
GROUP BY is_domestic
"""

domestic_df = pd.read_sql(query_domestic, engine)

print("\nDOMESTIC CRIME:")
print(domestic_df)

# Chart
plt.figure(figsize=(5,5))
plt.pie(
    domestic_df['total'],
    labels=['Non Domestic', 'Domestic'],
    autopct='%1.1f%%'
)
plt.title('Domestic Crime Distribution')
plt.savefig('domestic_distribution.png')

# ============================================================
# SELESAI
# ============================================================

print("\n" + "=" * 60)
print("EDA SELESAI")
print("Semua chart berhasil disimpan.")
print("=" * 60)