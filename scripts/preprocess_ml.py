# scripts/preprocess_ml.py
import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split

# --- Assumptions (update if different) ---
CSV_PATH = "data/cleaned/crimes_2021_2026.csv"  # cleaned data CSV
TARGET_COL = "Arrest"                         # target column name
DATE_COL = "Date"                             # date column name
FEATURE_COLS = ["Primary Type", "Domestic", "District", "Ward", "Community Area"]
# Memory-saving: only read needed columns plus date
USE_COLS = FEATURE_COLS + [TARGET_COL, DATE_COL]

# Read data (in chunks if very large)
print("Loading data for preprocessing...")
chunks = []
for chunk in pd.read_csv(CSV_PATH, usecols=USE_COLS, parse_dates=[DATE_COL], 
                         low_memory=False, chunksize=200000):
    chunks.append(chunk)
df = pd.concat(chunks, ignore_index=True)
# Sampling data untuk menghindari MemoryError (sesuaikan dengan RAM Anda)
if len(df) > 200000:
    df = df.sample(n=200000, random_state=42)
print(f"Total records loaded (after sampling): {len(df)}")

# Drop rows with missing target or critical features
df = df.dropna(subset=[TARGET_COL, "District"])
print(f"After dropping missing values: {len(df)} records")

# Encode target to 0/1 if not already numeric
if df[TARGET_COL].dtype == object:
    df[TARGET_COL] = df[TARGET_COL].map({'Y':1, 'N':0, 'Yes':1, 'No':0, 'True':1, 'False':0})
df[TARGET_COL] = df[TARGET_COL].astype(int)

# Check class balance
counts = df[TARGET_COL].value_counts(normalize=True)
print(f"Class distribution (Arrest=1): {counts.get(1,0):.2%}, (No Arrest=0): {counts.get(0,0):.2%}")

# Convert boolean/domestic to numeric if needed
if df["Domestic"].dtype == object or df["Domestic"].dtype == bool:
    df["Domestic"] = df["Domestic"].map({True:1, False:0, 'Y':1, 'N':0}).fillna(0).astype(int)
df["Domestic"] = df["Domestic"].astype(int)

# Extract date/time features
df["Hour"] = df[DATE_COL].dt.hour
df["Month"] = df[DATE_COL].dt.month
# (Optionally) df["DayOfWeek"] = df[DATE_COL].dt.dayofweek

# Drop the original date column (if not needed further)
df = df.drop(columns=[DATE_COL])

# Handle categorical 'Primary Type'
top_types = df["Primary Type"].value_counts().nlargest(10).index
df["Primary Type"] = df["Primary Type"].where(df["Primary Type"].isin(top_types), other="Other")
# One-hot encode selected categorical features
df = pd.get_dummies(df, columns=["Primary Type"], drop_first=True)

# Now we have only numeric features
feature_cols = [col for col in df.columns if col != TARGET_COL]
print(f"Features used: {feature_cols}")

# Split into train/test
X = df[feature_cols]
y = df[TARGET_COL]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Training set size: {len(X_train)}, Validation set size: {len(X_test)}")

# Buat direktori jika belum ada
os.makedirs("models", exist_ok=True)

# Simpan nama fitur untuk prediksi nanti
joblib.dump(feature_cols, "models/model_features.pkl")
print("Feature columns saved to 'models/model_features.pkl'.")

# (Optional) Save train/test to disk for inspection or reuse
np.savez_compressed("data/cleaned/train_data.npz", X=X_train, y=y_train)
np.savez_compressed("data/cleaned/test_data.npz", X=X_test, y=y_test)
print("Preprocessing complete. Data saved to 'data/cleaned/'.")
