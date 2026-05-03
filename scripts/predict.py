# scripts/predict.py
import pandas as pd
import joblib

# --- Assumptions: input CSV path and features ---
INPUT_CSV = "data/cleaned/crimes_2021_2026.csv"  # or path to new incidents to predict

# Load model and feature columns
try:
    rf = joblib.load("models/rf_model.pkl")
    print("Model loaded from 'models/rf_model.pkl'.")
    FEATURE_COLS = joblib.load("models/model_features.pkl")
    print("Feature columns loaded from 'models/model_features.pkl'.")
except FileNotFoundError as e:
    print(f"Error loading model/features: {e}")
    print("Please run preprocess_ml.py and train_rf.py first.")
    exit(1)

# Load data to predict (we can use a sample for demonstration)
# For prediction, we usually only load new data, but here we load from the same CSV
# and we must do the exact same preprocessing steps minus dropping missing TARGET
df = pd.read_csv(INPUT_CSV, usecols=["Date", "Primary Type", "Domestic", "District", "Ward", "Community Area"], parse_dates=["Date"])
df = df.dropna(subset=["District"])

df["Hour"] = df["Date"].dt.hour
df["Month"] = df["Date"].dt.month
df["Domestic"] = df["Domestic"].map({True:1, False:0, 'Y':1, 'N':0}).fillna(0).astype(int)

# One-hot encode Primary Type
# Instead of hardcoding the top types, we just get dummies
df = pd.get_dummies(df, columns=["Primary Type"])

# Reindex the dataframe using the FEATURE_COLS from training
# This ensures that all columns needed by the model exist, and any extra are dropped
# Missing columns will be filled with 0 (which is correct for missing dummy variables)
X_pred_df = df.reindex(columns=FEATURE_COLS, fill_value=0)

X_pred = X_pred_df.values

# Predict
probs = rf.predict_proba(X_pred)[:,1]
labels = rf.predict(X_pred)

# Output predictions
output = df.copy()
output["Predicted_Arrest"] = labels
output["Prob_Arrest"] = probs
output.to_csv("predictions.csv", index=False)
print(f"Predictions for {len(output)} records written to 'predictions.csv'.")
