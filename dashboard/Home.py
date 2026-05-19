import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# KONFIGURASI HALAMAN
# =====================================================================
st.set_page_config(
    page_title="Chicago Crime Dashboard",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan yang lebih modern
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .metric-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4da6ff;
    }
    .metric-label {
        font-size: 1rem;
        color: #a0aab2;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# KONEKSI DATABASE
# =====================================================================
@st.cache_resource
def get_engine():
    # Menggunakan 127.0.0.1 seperti di script import
    engine = create_engine('mysql+pymysql://root:@127.0.0.1:3306/chicago_crime_db')
    return engine

engine = get_engine()

# =====================================================================
# FUNGSI UNTUK MENGAMBIL DATA (Dengan Caching)
# =====================================================================
@st.cache_data(ttl=3600) # Cache selama 1 jam
def get_filter_options():
    with engine.connect() as conn:
        years = pd.read_sql("SELECT DISTINCT year FROM dim_time ORDER BY year DESC", conn)['year'].tolist()
        crimes = pd.read_sql("SELECT DISTINCT primary_type FROM dim_crime_type ORDER BY primary_type", conn)['primary_type'].tolist()
        districts = pd.read_sql("SELECT district_no, district_name FROM dim_district ORDER BY district_no", conn)
    return years, crimes, districts

# =====================================================================
# SIDEBAR FILTERS
# =====================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Star_of_the_Chicago_Police_Department.svg/200px-Star_of_the_Chicago_Police_Department.svg.png", width=100)
st.sidebar.title("Filter Data")

years, crime_types, districts = get_filter_options()

# Filter Tahun
selected_years = st.sidebar.multiselect("Pilih Tahun:", options=years, default=years)

# Filter Distrik
dist_dict = dict(zip(districts['district_no'], districts['district_name']))
selected_districts = st.sidebar.multiselect("Pilih Distrik:", options=list(dist_dict.keys()), format_func=lambda x: dist_dict[x])

# Filter Jenis Kejahatan
selected_crimes = st.sidebar.multiselect("Jenis Kejahatan:", options=crime_types)

# Construct WHERE clause based on filters
where_clauses = ["1=1"]
if selected_years:
    where_clauses.append(f"t.year IN ({','.join(map(str, selected_years))})")
if selected_districts:
    where_clauses.append(f"d.district_no IN ({','.join(map(str, selected_districts))})")
if selected_crimes:
    # Handle strings for SQL
    crimes_str = ','.join([f"'{c}'" for c in selected_crimes])
    where_clauses.append(f"ct.primary_type IN ({crimes_str})")

where_sql = " AND ".join(where_clauses)

# =====================================================================
# HEADER DASHBOARD
# =====================================================================
st.title("🚔 Chicago Crime Analytics Dashboard")
st.markdown("Analisis data insiden kejahatan di kota Chicago (2021-2026). Gunakan panel di sebelah kiri untuk memfilter data.")

# =====================================================================
# MENGAMBIL DATA METRIK UTAMA
# =====================================================================
@st.cache_data
def get_kpi_data(where_sql):
    query = f"""
        SELECT 
            COUNT(*) as total_incidents,
            SUM(fi.arrest_made) as total_arrests,
            SUM(fi.is_domestic) as total_domestic
        FROM fact_incident fi
        JOIN dim_time t ON fi.time_id = t.time_id
        JOIN dim_district d ON fi.district_id = d.district_id
        JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
        WHERE {where_sql}
    """
    return pd.read_sql(query, engine)

with st.spinner("Memuat metrik..."):
    kpi_df = get_kpi_data(where_sql)

if not kpi_df.empty and kpi_df['total_incidents'][0] > 0:
    total_crimes = kpi_df['total_incidents'][0]
    arrest_rate = (kpi_df['total_arrests'][0] / total_crimes) * 100
    domestic_rate = (kpi_df['total_domestic'][0] / total_crimes) * 100
else:
    total_crimes, arrest_rate, domestic_rate = 0, 0, 0

# Tampilkan Metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Kejahatan</div>
        <div class="metric-value">{total_crimes:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Arrest Rate (Tingkat Penangkapan)</div>
        <div class="metric-value">{arrest_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kasus Domestik</div>
        <div class="metric-value">{domestic_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================================
# VISUALISASI DATA
# =====================================================================

st.markdown("---")
col_chart1, col_chart2 = st.columns(2)

# 1. Trend Over Time
@st.cache_data
def get_trend_data(where_sql):
    query = f"""
        SELECT 
            t.year, 
            t.month,
            COUNT(*) as total
        FROM fact_incident fi
        JOIN dim_time t ON fi.time_id = t.time_id
        JOIN dim_district d ON fi.district_id = d.district_id
        JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
        WHERE {where_sql}
        GROUP BY t.year, t.month
        ORDER BY t.year, t.month
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Format periode: "YYYY-MM"
        df['period'] = df.apply(lambda row: f"{row['year']}-{row['month']:02d}", axis=1)
    return df

with col_chart1:
    st.subheader("Tren Kejahatan Bulanan")
    trend_df = get_trend_data(where_sql)
    if not trend_df.empty:
        fig_trend = px.line(
            trend_df, x='period', y='total', 
            labels={'period': 'Bulan', 'total': 'Jumlah Insiden'},
            line_shape='spline', render_mode='svg'
        )
        fig_trend.update_traces(line_color='#00d4ff', line_width=3)
        fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Tidak ada data untuk grafik ini berdasarkan filter.")

# 2. Top Crime Types
@st.cache_data
def get_top_crimes(where_sql):
    query = f"""
        SELECT 
            ct.primary_type,
            COUNT(*) as total
        FROM fact_incident fi
        JOIN dim_time t ON fi.time_id = t.time_id
        JOIN dim_district d ON fi.district_id = d.district_id
        JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
        WHERE {where_sql}
        GROUP BY ct.primary_type
        ORDER BY total DESC
        LIMIT 10
    """
    return pd.read_sql(query, engine)

with col_chart2:
    st.subheader("Top 10 Jenis Kejahatan")
    top_crimes_df = get_top_crimes(where_sql)
    if not top_crimes_df.empty:
        fig_bar = px.bar(
            top_crimes_df, x='total', y='primary_type', orientation='h',
            labels={'total': 'Jumlah', 'primary_type': 'Jenis Kejahatan'},
            color='total', color_continuous_scale='Blues'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Tidak ada data untuk grafik ini.")

st.markdown("---")

# 3. Peta Lokasi (Sample Data)
st.subheader("🗺️ Sebaran Titik Kejahatan (Peta)")
st.markdown("*Menampilkan sampel maksimal 2.000 titik (untuk performa peramban).*")

@st.cache_data
def get_map_data(where_sql):
    query = f"""
        SELECT 
            l.latitude, 
            l.longitude,
            ct.primary_type,
            fi.arrest_made
        FROM fact_incident fi
        JOIN dim_time t ON fi.time_id = t.time_id
        JOIN dim_district d ON fi.district_id = d.district_id
        JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
        JOIN dim_location l ON fi.location_id = l.location_id
        WHERE {where_sql} AND l.latitude != 0.0 AND l.longitude != 0.0
        LIMIT 2000
    """
    return pd.read_sql(query, engine)

map_df = get_map_data(where_sql)
if not map_df.empty:
    # Rename columns to match what Streamlit expects if using st.map
    # or we can use Plotly Express
    fig_map = px.scatter_mapbox(
        map_df, lat="latitude", lon="longitude", hover_name="primary_type", 
        color="arrest_made", color_continuous_scale=["red", "green"],
        zoom=9, height=500
    )
    fig_map.update_layout(mapbox_style="carto-darkmatter")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("Tidak ada data koordinat yang valid untuk ditampilkan di peta.")

# =====================================================================
# DATA TABLE
# =====================================================================
st.markdown("---")
st.subheader("📋 Detail Data (100 Kasus Terbaru)")

@st.cache_data
def get_recent_cases(where_sql):
    query = f"""
        SELECT 
            fi.case_number as `Case Number`,
            t.full_date as `Tanggal`,
            t.shift as `Shift`,
            ct.primary_type as `Kejahatan`,
            l.block as `Blok Lokasi`,
            d.district_name as `Distrik`,
            IF(fi.arrest_made=1, 'Ya', 'Tidak') as `Ditangkap`
        FROM fact_incident fi
        JOIN dim_time t ON fi.time_id = t.time_id
        JOIN dim_district d ON fi.district_id = d.district_id
        JOIN dim_crime_type ct ON fi.crime_type_id = ct.crime_type_id
        JOIN dim_location l ON fi.location_id = l.location_id
        WHERE {where_sql}
        ORDER BY t.full_date DESC, t.hour DESC
        LIMIT 100
    """
    return pd.read_sql(query, engine)

recent_df = get_recent_cases(where_sql)
if not recent_df.empty:
    st.dataframe(recent_df, use_container_width=True)
else:
    st.info("Tidak ada detail data yang ditemukan.")
