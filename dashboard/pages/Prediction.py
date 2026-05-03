# dashboard/pages/Prediction.py
import streamlit as st
import joblib
import pandas as pd
import os

st.set_page_config(page_title="Arrest Prediction Simulation", page_icon="🤖")
st.title("🤖 Arrest Prediction Simulation")
st.markdown("Unggah file CSV baru untuk menyimulasikan apakah kasus kejahatan akan berujung pada **Penangkapan (Arrest)** atau tidak menggunakan model Random Forest.")

# Karena file ini ada di dashboard/pages/, kita naik 3 level ke root
base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

uploaded = st.file_uploader("Upload Data Kasus Baru (CSV)", type="csv")
if uploaded and rf is not None and FEATURE_COLS is not None:
    df = pd.read_csv(uploaded)
    st.markdown("### Data Original")
    st.dataframe(df.head())
    
    with st.spinner("Memproses prediksi..."):
        # Preprocessing copy
        df_proc = df.copy()
        
        if "Date" in df_proc.columns:
            df_proc["Date"] = pd.to_datetime(df_proc["Date"], errors='coerce')
            df_proc["Hour"] = df_proc["Date"].dt.hour
            df_proc["Month"] = df_proc["Date"].dt.month
            
        if "Domestic" in df_proc.columns:
            df_proc["Domestic"] = df_proc["Domestic"].map({True:1, False:0, 'Y':1, 'N':0}).fillna(0).astype(int)
            
        if "Primary Type" in df_proc.columns:
            df_encoded = pd.get_dummies(df_proc, columns=["Primary Type"])
        else:
            df_encoded = df_proc.copy()
            
        # Reindex to match the training features exactly
        X_pred_df = df_encoded.reindex(columns=FEATURE_COLS, fill_value=0)
        X_pred_df = X_pred_df.fillna(0)
        X = X_pred_df.values
        
        # Predict
        probs = rf.predict_proba(X)[:, 1]
        preds = rf.predict(X)
        
        df["Probabilitas Penangkapan (%)"] = (probs * 100).round(2)
        df["Prediksi Arrest"] = ["Ya (Tertangkap)" if p == 1 else "Tidak" for p in preds]
        
    st.success("✅ Prediksi Berhasil!")
    st.markdown("### Hasil Prediksi")
    st.dataframe(df[["Case Number", "Primary Type", "Probabilitas Penangkapan (%)", "Prediksi Arrest"]] if "Case Number" in df.columns else df)
