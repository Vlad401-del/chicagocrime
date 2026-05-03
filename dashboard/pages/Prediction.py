# dashboard/pages/Prediction.py
import streamlit as st
import joblib
import pandas as pd
import os

st.set_page_config(page_title="Simulasi Prediksi Penangkapan", page_icon="🤖")
st.title("🤖 Simulasi Prediksi Penangkapan")
st.markdown("Masukkan detail skenario insiden kejahatan di bawah ini untuk memprediksi probabilitas pelaku ditangkap oleh pihak kepolisian Chicago.")

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
        return None, None

rf, FEATURE_COLS = load_model_and_features()

if rf is None or FEATURE_COLS is None:
    st.error("Model prediksi belum tersedia. Pastikan Anda telah melatih model.")
    st.stop()

# --- FORM INPUT ---
with st.form("prediction_form"):
    st.subheader("Detail Skenario Kejadian")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Crime types based on the ones we kept during training
        crime_options = [
            "THEFT", "BATTERY", "CRIMINAL DAMAGE", "NARCOTICS", 
            "OTHER OFFENSE", "ASSAULT", "DECEPTIVE PRACTICE", 
            "ROBBERY", "MOTOR VEHICLE THEFT", "BURGLARY", "WEAPONS VIOLATION", "Other"
        ]
        selected_crime = st.selectbox("Jenis Kejahatan (Primary Type)", crime_options)
        selected_hour = st.slider("Jam Kejadian (0 - 23)", 0, 23, 12, format="%d:00")
        selected_month = st.selectbox("Bulan", range(1, 13), format_func=lambda x: [
            "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"][x-1])
        
    with col2:
        selected_district = st.number_input("Distrik (District No)", min_value=1, max_value=31, value=1)
        selected_ward = st.number_input("Ward", min_value=1, max_value=50, value=1)
        selected_community = st.number_input("Community Area", min_value=1, max_value=77, value=1)
        is_domestic = st.radio("Apakah Tergolong Kasus Domestik?", ["Tidak", "Ya"])

    submit_button = st.form_submit_button("Prediksi Kemungkinan Penangkapan", type="primary")

if submit_button:
    # 1. Buat single row DataFrame berdasarkan input user
    input_data = {
        "Hour": [selected_hour],
        "Month": [selected_month],
        "District": [selected_district],
        "Ward": [selected_ward],
        "Community Area": [selected_community],
        "Domestic": [1 if is_domestic == "Ya" else 0],
        "Primary Type": [selected_crime]
    }
    
    df_input = pd.DataFrame(input_data)
    
    # 2. Lakukan One-Hot Encoding pada 'Primary Type'
    df_encoded = pd.get_dummies(df_input, columns=["Primary Type"])
    
    # 3. Sesuaikan dengan urutan kolom model latih
    X_pred_df = df_encoded.reindex(columns=FEATURE_COLS, fill_value=0)
    X = X_pred_df.values
    
    # 4. Prediksi
    prob_arrest = rf.predict_proba(X)[0][1] * 100
    
    # 5. Tampilkan Hasil yang Cantik
    st.markdown("---")
    st.subheader("🎯 Hasil Prediksi")
    
    if prob_arrest >= 75:
        color = "#28a745" # Green
        conclusion = "Sangat Memungkinkan Tertangkap (Arrest Very Likely)"
    elif prob_arrest >= 50:
        color = "#17a2b8" # Blue
        conclusion = "Kemungkinan Besar Tertangkap (Arrest Likely)"
    elif prob_arrest >= 25:
        color = "#ffc107" # Yellow
        conclusion = "Kemungkinan Kecil Tertangkap (Arrest Unlikely)"
    else:
        color = "#dc3545" # Red
        conclusion = "Sangat Sulit Tertangkap (Arrest Very Unlikely)"
        
    st.markdown(f"""
    <div style="background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid {color}; margin-top:10px;">
        <h2 style="color:{color}; margin-top:0;">{conclusion}</h2>
        <p style="font-size:18px; margin-bottom:0;">Probabilitas Kepolisian Menangkap Pelaku: <strong>{prob_arrest:.1f}%</strong></p>
    </div>
    """, unsafe_allow_html=True)
