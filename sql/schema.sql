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
