# dashboard/prediction.py
import streamlit as st
import joblib
import pandas as pd
import os

st.title("Arrest Prediction")

# Ensure paths work whether run from dashboard/ or root/
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(base_path, "models", "rf_model.pkl")
features_path = os.path.join(base_path, "models", "model_features.pkl")

@st.cache_resource
def load_model_and_features():
    try:
        rf = joblib.load(model_path)
        features = joblib.load(features_path)
        return rf, features
    except Exception as e:
        st.error(f"Error loading model: {e}. Pastikan Anda telah menjalankan train_rf.py")
        return None, None

rf, FEATURE_COLS = load_model_and_features()

# Example: let user upload a CSV or select a subset
uploaded = st.file_uploader("Upload crimes data CSV", type="csv")
if uploaded and rf is not None and FEATURE_COLS is not None:
    df = pd.read_csv(uploaded)
    
    # Preprocessing
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df["Hour"] = df["Date"].dt.hour
        df["Month"] = df["Date"].dt.month
        
    if "Domestic" in df.columns:
        df["Domestic"] = df["Domestic"].map({True:1, False:0, 'Y':1, 'N':0}).fillna(0).astype(int)
        
    if "Primary Type" in df.columns:
        df_encoded = pd.get_dummies(df, columns=["Primary Type"])
    else:
        df_encoded = df.copy()
        
    # Reindex to match the training features
    X_pred_df = df_encoded.reindex(columns=FEATURE_COLS, fill_value=0)
    
    # Fill any remaining NaNs with 0
    X_pred_df = X_pred_df.fillna(0)
    
    X = X_pred_df.values
    
    # Predict
    probs = rf.predict_proba(X)[:, 1]
    preds = rf.predict(X)
    
    df["Predicted Arrest Probability"] = probs
    df["Predicted Arrest"] = preds
    
    st.success("Prediksi Berhasil!")
    st.dataframe(df)
