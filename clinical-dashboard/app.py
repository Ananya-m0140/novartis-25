import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from pathlib import Path  # Add this import


from ai.generate_summary import generate_site_summary
from ai.agent_recommender import generate_agent_recommendations
from ai.nlq_chat import nlq_interface

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Clinical Trial Data Quality Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS - ENHANCED FOR ENTIRE PAGE
# =========================
st.markdown("""
<style>
    /* ===== GLOBAL STYLES ===== */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {
    visibility: visible;
    height: 0px;
}

    
    /* ===== SIDEBAR ENHANCEMENT ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #2d3748 100%) !important;
        border-right: 2px solid #4299e1 !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stSlider {
        background-color: #2d3748 !important;
        border-radius: 10px !important;
        padding: 10px !important;
        border: 1px solid #4a5568 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #4a5568 !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stSlider > div {
        color: #e2e8f0 !important;
    }
    
    /* ===== MAIN CONTENT AREA ===== */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Main headers */
    h1, h2, h3, h4, h5, h6 {
        color: #1a365d !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    h1 {
        font-size: 2.8rem !important;
        background: linear-gradient(90deg, #1a365d, #4299e1) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 3px solid #4299e1 !important;
    }
    
    h2 {
        font-size: 2rem !important;
        color: #2d3748 !important;
        border-left: 4px solid #4299e1 !important;
        padding-left: 1rem !important;
        margin-top: 2rem !important;
    }
    
    h3 {
        font-size: 1.5rem !important;
        color: #4a5568 !important;
    }
    
    /* Paragraph text */
    p, div, span {
        color: #2d3748 !important;
    }
    
    /* ===== KPI CARDS ENHANCEMENT ===== */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%) !important;
        border-radius: 16px !important;
        padding: 25px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid #e2e8f0 !important;
        transition: all 0.3s ease !important;
        text-align: center !important;
        min-height: 150px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15) !important;
        border-color: #4299e1 !important;
    }
    
    .kpi-card h3 {
        color: #718096 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin-bottom: 10px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .kpi-card h2 {
        color: #1a365d !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* ===== MAP STYLING ===== */
    .js-plotly-plot {
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* ===== DATA TABLES ENHANCEMENT ===== */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    .dataframe {
        background-color: white !important;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px !important;
        border: none !important;
    }
    
    .dataframe td {
        padding: 10px !important;
        border: none !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f7fafc !important;
    }
    
    .dataframe tr:hover {
        background-color: #ebf8ff !important;
    }
    
    /* ===== SUCCESS/WARNING/ERROR MESSAGES ===== */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%) !important;
        border-left: 4px solid #38a169 !important;
        color: #22543d !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #feebc8 0%, #fbd38d 100%) !important;
        border-left: 4px solid #d69e2e !important;
        color: #744210 !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%) !important;
        border-left: 4px solid #e53e3e !important;
        color: #742a2a !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%) !important;
        border-left: 4px solid #4299e1 !important;
        color: #1a365d !important;
    }
    
    /* ===== BUTTON ENHANCEMENT ===== */
    .stButton > button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 28px !important;
        border-radius: 10px !important;
        border: none !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(66, 153, 225, 0.2) !important;
        margin: 5px 0 !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 15px rgba(66, 153, 225, 0.3) !important;
        background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(-1px) !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 100%) !important;
        box-shadow: 0 4px 6px rgba(56, 161, 105, 0.2) !important;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #2f855a 0%, #276749 100%) !important;
        box-shadow: 0 8px 15px rgba(56, 161, 105, 0.3) !important;
    }
    
    /* ===== EXPANDER STYLING ===== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%) !important;
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%) !important;
    }
    
    .streamlit-expanderContent {
        background-color: white !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        padding: 20px !important;
    }
    
    /* ===== METRIC CARDS ===== */
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stMetric label {
        color: #718096 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .stMetric div {
        color: #1a365d !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }
    
    /* ===== TABS ENHANCEMENT ===== */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: space-between !important;
        gap: 2px !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 30px 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        flex: 1 !important;
        height: 70px !important;
        white-space: nowrap !important;
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%) !important;
        border-radius: 12px 12px 0 0 !important;
        padding: 20px 10px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #4a5568 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        border: 2px solid #e2e8f0 !important;
        border-bottom: none !important;
        transition: all 0.3s ease !important;
        text-align: center !important;
        margin: 0 2px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1) !important;
        color: #2d3748 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        color: white !important;
        border-color: #3182ce !important;
        border-bottom: 3px solid #3182ce !important;
        box-shadow: 0 8px 20px rgba(66, 153, 225, 0.3) !important;
        font-weight: 700 !important;
        position: relative !important;
        z-index: 2 !important;
    }
    
    .stTabs [aria-selected="true"]::after {
        content: '' !important;
        position: absolute !important;
        bottom: -3px !important;
        left: 0 !important;
        right: 0 !important;
        height: 3px !important;
        background: linear-gradient(90deg, #3182ce, #63b3ed) !important;
        border-radius: 0 0 3px 3px !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%) !important;
        border-radius: 0 12px 12px 12px !important;
        padding: 40px !important;
        margin-top: -10px !important;
        border: 2px solid #e2e8f0 !important;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.08) !important;
        min-height: 500px !important;
    }
    
    /* ===== FORM ELEMENTS ===== */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        background-color: white !important;
        color: #2d3748 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4299e1 !important;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #a0aec0 !important;
    }
    
    /* ===== SCROLLBAR STYLING ===== */
    ::-webkit-scrollbar {
        width: 10px !important;
        height: 10px !important;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1 !important;
        border-radius: 5px !important;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        border-radius: 5px !important;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%) !important;
    }
    
    /* ===== CUSTOM CLASSES FOR CONTENT ===== */
    .content-card {
        background: white !important;
        border-radius: 16px !important;
        padding: 30px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
        margin: 20px 0 !important;
    }
    
    .highlight-text {
        background: linear-gradient(90deg, #4299e1, #63b3ed) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# DATA LOADING & CLEANING
# =========================


@st.cache_data(ttl=600)
def load_data():
    BASE_DIR = Path(__file__).parent
    DATA_PATH = BASE_DIR / "data" / "master_dataset.csv"

    if not DATA_PATH.exists():
        st.error(f"Dataset not found at {DATA_PATH}")
        st.stop()

    df = pd.read_csv(DATA_PATH, low_memory=False)

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    rename_map = {
        "region": "region",
        "country": "country",
        "site_id": "site_id",
        "subject_id": "patient_id",
        "dqi": "dqi"
    }

    df = df.rename(columns=rename_map)

    df = df.dropna(subset=["country", "dqi"])
    df["dqi"] = pd.to_numeric(df["dqi"], errors="coerce")
    df = df.dropna(subset=["dqi"])

    return df


# Load full dataset
df_full = load_data()
df = df_full.copy()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.markdown("<h2 style='color: #e2e8f0;'>🔍 Filters</h2>", unsafe_allow_html=True)

region_sel = st.sidebar.selectbox(
    "Region",
    ["All"] + sorted(df_full["region"].dropna().unique()),
    key="region_filter"
)

country_sel = st.sidebar.selectbox(
    "Country",
    ["All"] + sorted(df_full["country"].dropna().unique()),
    key="country_filter"
)

site_sel = st.sidebar.selectbox(
    "Site",
    ["All"] + sorted(df_full["site_id"].dropna().unique()),
    key="site_filter"
)

patient_sel = st.sidebar.selectbox(
    "Patient",
    ["All"] + sorted(df_full["patient_id"].dropna().unique()),
    key="patient_filter"
)

st.sidebar.markdown("---")

critical_threshold = st.sidebar.slider(
    "Critical DQI Alert Threshold",
    0, 100, 40,
    key="critical_threshold"
)

high_perf_threshold = st.sidebar.slider(
    "High Performing DQI Threshold",
    0, 100, 50,
    key="high_perf_threshold"
)

# =========================
# APPLY FILTERS
# =========================
df = df_full.copy()

if region_sel != "All":
    df = df[df["region"] == region_sel]

if country_sel != "All":
    df = df[df["country"] == country_sel]

if site_sel != "All":
    df = df[df["site_id"] == site_sel]

if patient_sel != "All":
    df = df[df["patient_id"] == patient_sel]

# =========================
# TITLE
# =========================
st.markdown("<h1>📊 Global Clinical Trial Data Quality Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.2rem; color: #4a5568;'>From global oversight → site → patient-level operational insights</p>", unsafe_allow_html=True)

# =========================
# KPI CARDS
# =========================
st.markdown("## 📈 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

col1.markdown(
    f"<div class='kpi-card'><h3>Sites</h3><h2>{df['site_id'].nunique():,}</h2></div>",
    unsafe_allow_html=True
)
col2.markdown(
    f"<div class='kpi-card'><h3>Patients</h3><h2>{df['patient_id'].nunique():,}</h2></div>",
    unsafe_allow_html=True
)
col3.markdown(
    f"<div class='kpi-card'><h3>Avg DQI</h3><h2>{round(df['dqi'].mean(),1)}</h2></div>",
    unsafe_allow_html=True
)
col4.markdown(
    f"<div class='kpi-card'><h3>Critical Alerts</h3><h2>{(df['dqi'] < critical_threshold).sum():,}</h2></div>",
    unsafe_allow_html=True
)

# =========================
# 🌍 WORLD MAP (FULLY DYNAMIC)
# =========================
st.markdown("## 🌍 Global Data Quality Overview")

map_df = (
    df.groupby("country")
    .agg(avg_dqi=("dqi", "mean"))
    .reset_index()
)

def dqi_band(score, critical_threshold, high_perf_threshold):
    if score >= high_perf_threshold:
        return "High Performing"
    elif score >= critical_threshold:
        return "Average"
    else:
        return "Critical"

map_df["DQI Level"] = map_df["avg_dqi"].apply(
    lambda x: dqi_band(x, critical_threshold, high_perf_threshold)
)

fig_map = px.choropleth(
    map_df,
    locations="country",
    locationmode="ISO-3",
    color="DQI Level",
    hover_name="country",
    hover_data={"avg_dqi": ":.1f"},
    color_discrete_map={
        "High Performing": "#38a169",
        "Average": "#d69e2e",
        "Critical": "#e53e3e"
    },
    title="Global DQI Distribution"
)

fig_map.update_layout(
    template="plotly_white",
    height=500,
    margin=dict(l=0, r=0, t=50, b=0),
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font=dict(size=20, color="#1a365d"),
    legend=dict(
        font=dict(color="#4a5568"),
        title_font=dict(color="#2d3748"),
        bgcolor="white",
        bordercolor="#e2e8f0",
        borderwidth=1
    ),
    geo=dict(
        bgcolor="white",
        lakecolor="white",
        landcolor="#f7fafc",
        subunitcolor="#e2e8f0"
    )
)

st.plotly_chart(fig_map, use_container_width=True)

# =========================
# CRITICAL SITES TABLE
# =========================
st.markdown("## ⚠️ Critical Sites")

site_df = (
    df.groupby("site_id")
    .agg(
        avg_dqi=("dqi", "mean"),
        patients=("patient_id", "nunique")
    )
    .reset_index()
)

site_df["critical"] = site_df["avg_dqi"] < critical_threshold
site_df["DQI Level"] = site_df["avg_dqi"].apply(
    lambda x: dqi_band(x, critical_threshold, high_perf_threshold)
)

if site_df[site_df.critical].empty:
    st.success("✅ No critical sites detected")
else:
    # Style critical sites table
    critical_sites = site_df[site_df.critical].copy()
    critical_sites = critical_sites.sort_values("avg_dqi").head(10)
    critical_sites["avg_dqi"] = critical_sites["avg_dqi"].round(2)
    
    st.dataframe(
        critical_sites[["site_id", "avg_dqi", "patients", "DQI Level"]].rename(
            columns={
                "site_id": "Site ID",
                "avg_dqi": "Average DQI",
                "patients": "Patient Count",
                "DQI Level": "Status"
            }
        ),
        use_container_width=True
    )

# =========================
# SITE-LEVEL BAR CHART
# =========================
st.markdown("## 📊 Site-Level Average DQI")

if site_df.shape[0] > 1:
    # Sort sites by DQI for better visualization
    site_chart_df = site_df.sort_values("avg_dqi", ascending=False).head(20)
    
    fig_bar = px.bar(
        site_chart_df,
        x="site_id",
        y="avg_dqi",
        color="avg_dqi",
        color_continuous_scale=[[0, "#e53e3e"], [0.5, "#d69e2e"], [1, "#38a169"]],
        title="Top 20 Sites by DQI Score",
        labels={"site_id": "Site ID", "avg_dqi": "Average DQI"}
    )
    
    fig_bar.update_layout(
        template="plotly_white",
        height=420,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font=dict(size=18, color="#1a365d"),
        xaxis_title_font=dict(size=14, color="#4a5568"),
        yaxis_title_font=dict(size=14, color="#4a5568"),
        coloraxis_colorbar=dict(
            title="DQI Score",
            title_font=dict(color="#4a5568"),
            tickfont=dict(color="#4a5568")
        )
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

# =========================
# DRILL-DOWN TABLE
# =========================
st.markdown("## 🔍 Drill-Down View")

# Show limited rows for better performance
display_df = df.head(100).copy()  # Show first 100 rows

# Create a nicer display with selected columns
display_columns = ["site_id", "patient_id", "country", "dqi"]
if "subject_status" in df.columns:
    display_columns.append("subject_status")
if "latest_visit" in df.columns:
    display_columns.append("latest_visit")

# Filter to available columns
available_columns = [col for col in display_columns if col in df.columns]

if available_columns:
    st.dataframe(
        display_df[available_columns].rename(
            columns={
                "site_id": "Site ID",
                "patient_id": "Patient ID",
                "country": "Country",
                "dqi": "DQI Score",
                "subject_status": "Status",
                "latest_visit": "Latest Visit"
            }
        ),
        use_container_width=True,
        height=400
    )
else:
    st.dataframe(display_df, use_container_width=True, height=400)

# =========================
# 🤖 AI TOOLS WITH TABS
# =========================
st.markdown("## 🤖 AI Tools")

# Create beautifully styled tabs
tab1, tab2, tab3 = st.tabs([
    "📊 SITE SUMMARY", 
    "🤖 AGENT RECOMMENDATIONS", 
    "💬 NATURAL LANGUAGE QUERY"
])

# Use the currently filtered DataFrame
drill_df = df.copy()

# Tab 1: Site Summary
# Tab 1: Site Summary
with tab1:
    st.markdown("### AI-Powered Site Summary Generator")
    st.markdown("<p style='color: #4a5568; font-size: 16px;'>Generate comprehensive site performance analysis with risk intelligence and actionable insights.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Site Summary", key="gen_site_summary", use_container_width=True):
            try:
                result = generate_site_summary(drill_df)
                
                # Display results in content cards
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                
                st.markdown("## 📋 Executive Summary")
                
                if "narrative" in result:
                    narrative = result["narrative"]
                    
                    if "SECTION A" in narrative and "SECTION B" in narrative:
                        sections = narrative.split("SECTION B")
                        exec_summary = sections[0].replace("SECTION A — AI RISK INTELLIGENCE (CONCISE)", "").strip()
                        details = "SECTION B" + sections[1] if len(sections) > 1 else ""
                        
                        with st.expander("📄 View Executive Summary", expanded=True):
                            exec_summary = exec_summary.replace("Executive Insight (≤120 words)", "**Key Insights**")
                            st.markdown(exec_summary)
                        
                        if details:
                            with st.expander("🔍 View Detailed Analysis", expanded=False):
                                st.markdown(details)
                    else:
                        st.markdown("### Key Insights")
                        st.write(narrative)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Metrics display
                if isinstance(result, dict) and "metrics" in result:
                    metrics = result["metrics"]
                    
                    # ---- Confidence Meter ----
                    if "confidence_score" in metrics:
                        st.markdown('<div class="content-card">', unsafe_allow_html=True)
                        st.markdown("## 📊 Data Readiness Confidence")
                        confidence = metrics["confidence_score"]
                        
                        # Color based on confidence
                        if confidence >= 70:
                            color = "#38a169"
                            emoji = "✅"
                        elif confidence >= 40:
                            color = "#d69e2e"
                            emoji = "⚠️"
                        else:
                            color = "#e53e3e"
                            emoji = "❌"
                        
                        st.markdown(f"""
                        <div style="text-align: center; padding: 20px;">
                            <div style="font-size: 48px; margin-bottom: 10px;">{emoji}</div>
                            <div style="font-size: 3rem; font-weight: 800; color: {color}; margin-bottom: 10px;">
                                {confidence}%
                            </div>
                            <div style="color: #718096; font-size: 1.1rem;">
                                Overall Data Confidence Score
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Progress bar
                        st.markdown(f"""
                        <div style="background: #edf2f7; border-radius: 10px; height: 20px; margin: 20px 0;">
                            <div style="background: linear-gradient(90deg, {color}, {color}99); 
                                     width: {confidence}%; height: 100%; border-radius: 10px; 
                                     transition: width 1s ease;"></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if confidence < 40:
                            st.warning("Low confidence score indicates need for manual validation and deeper analysis.")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # ---- Risk Fingerprint ----
                    if "risk_fingerprint" in metrics and metrics["risk_fingerprint"]:
                        st.markdown('<div class="content-card">', unsafe_allow_html=True)
                        st.markdown("## 🔎 Risk Fingerprint (Top Sites)")
                        
                        rf_df = pd.DataFrame(metrics["risk_fingerprint"])
                        if not rf_df.empty and "site_id" in rf_df.columns:
                            # Create a formatted table
                            display_df = rf_df.copy()
                            
                            # Add risk indicators
                            if "low_dqi" in display_df.columns:
                                display_df["DQI Status"] = display_df["low_dqi"].apply(
                                    lambda x: "🔴 Critical" if x else "🟢 Good"
                                )
                            
                            if "high_load" in display_df.columns:
                                display_df["Load Status"] = display_df["high_load"].apply(
                                    lambda x: "🔴 High" if x else "🟢 Normal"
                                )
                            
                            # Select and rename columns for display
                            display_cols = ["site_id"]
                            rename_map = {"site_id": "Site ID"}
                            
                            if "DQI Status" in display_df.columns:
                                display_cols.append("DQI Status")
                                rename_map["DQI Status"] = "DQI Status"
                            
                            if "Load Status" in display_df.columns:
                                display_cols.append("Load Status")
                                rename_map["Load Status"] = "Load Status"
                            
                            if "severity" in display_df.columns:
                                display_cols.append("severity")
                                rename_map["severity"] = "Severity Score"
                            
                            st.dataframe(
                                display_df[display_cols].rename(columns=rename_map),
                                use_container_width=True,
                                height=250
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # ---- Action Priority Stack ----
                    if "action_stack" in metrics and metrics["action_stack"]:
                        st.markdown('<div class="content-card">', unsafe_allow_html=True)
                        st.markdown("## 🚨 Action Priority (Next 7 Days)")
                        
                        for i, item in enumerate(metrics["action_stack"], start=1):
                            if isinstance(item, dict):
                                # Create a card for each action item
                                cols = st.columns([1, 4])
                                with cols[0]:
                                    st.markdown(f"### #{i}")
                                
                                with cols[1]:
                                    details = []
                                    if "site_id" in item:
                                        details.append(f"**Site:** {item['site_id']}")
                                    if "avg_dqi" in item:
                                        # Color code DQI
                                        dqi = item['avg_dqi']
                                        color = "red" if dqi < 50 else "orange" if dqi < 70 else "green"
                                        details.append(f"**DQI:** <span style='color:{color}'>{dqi}</span>")
                                    if "patients" in item:
                                        details.append(f"**Patients:** {item['patients']}")
                                    if "severity" in item:
                                        details.append(f"**Severity:** {item['severity']:.1f}")
                                    
                                    st.markdown(" | ".join(details), unsafe_allow_html=True)
                                
                                st.markdown("---")
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # =====================================================
                # 📋 OVERALL SITE PERFORMANCE SUMMARY
                # =====================================================
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                st.markdown("## 📋 Overall Site Performance Summary")
                
                # Check if required columns exist
                required_cols = ["site_id", "patient_id", "dqi"]
                missing_cols = [col for col in required_cols if col not in drill_df.columns]
                
                if missing_cols:
                    st.warning(f"Missing columns: {missing_cols}. Cannot generate site performance summary.")
                else:
                    # Group by site
                    agg_dict = {
                        "total_subjects": ("patient_id", "nunique"),
                        "avg_dqi": ("dqi", "mean"),
                    }
                    
                    # Add subject_status if it exists
                    if "subject_status" in drill_df.columns:
                        agg_dict["active_subjects"] = ("subject_status", lambda x: (x == "On Trial").sum())
                        agg_dict["screen_failures"] = ("subject_status", lambda x: (x == "Screen Failure").sum())
                    
                    site_perf = (
                        drill_df.groupby("site_id")
                        .agg(**agg_dict)
                        .reset_index()
                        .round(1)
                    )
                    
                    # Function to determine observation
                    def site_observation(row):
                        if row["avg_dqi"] < 40:
                            return "🔴 Critical DQI Risk"
                        elif "screen_failures" in row and row["screen_failures"] > row["total_subjects"] / 2:
                            return "🟠 High Screen Failure Rate"
                        elif row["avg_dqi"] < 60:
                            return "🟡 Needs Attention"
                        else:
                            return "🟢 Good Performance"
                    
                    site_perf["Status"] = site_perf.apply(site_observation, axis=1)
                    
                    # Rename columns
                    rename_dict = {
                        "site_id": "Site ID",
                        "total_subjects": "Total Subjects",
                        "avg_dqi": "Avg DQI",
                        "Status": "Status"
                    }
                    
                    if "active_subjects" in site_perf.columns:
                        rename_dict["active_subjects"] = "Active Subjects"
                    if "screen_failures" in site_perf.columns:
                        rename_dict["screen_failures"] = "Screen Failures"
                    
                    site_perf = site_perf.rename(columns=rename_dict)
                    
                    # Display with sorting by DQI (worst first)
                    display_df = site_perf.sort_values("Avg DQI", ascending=True).head(20)
                    
                    # Apply color formatting
                    def color_dqi(val):
                        if val < 40:
                            color = "red"
                        elif val < 60:
                            color = "orange"
                        elif val < 85:
                            color = "gold"
                        else:
                            color = "green"
                        return f"color: {color}; font-weight: bold"
                    
                    # Apply formatting
                    styled_df = display_df.style.applymap(color_dqi, subset=["Avg DQI"])
                    
                    # Display
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        height=350
                    )
                    
                    # Summary stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Sites", len(site_perf))
                    with col2:
                        critical_sites = len(site_perf[site_perf["Avg DQI"] < 60])
                        st.metric("Sites Needing Attention", critical_sites, delta=None)
                    with col3:
                        avg_dqi = site_perf["Avg DQI"].mean()
                        st.metric("Average DQI", f"{avg_dqi:.1f}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # =====================================================
                # 📊 COMPOSITION PIE CHARTS
                # =====================================================
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                st.markdown("## 📊 Composition Overview")
                
                c1, c2 = st.columns(2)
                
                # ---- Subject Status Pie ----
                with c1:
                    # Check for different possible column names
                    status_col = None
                    for col in drill_df.columns:
                        if "status" in col.lower():
                            status_col = col
                            break
                    
                    if status_col:
                        status_counts = drill_df[status_col].value_counts().reset_index()
                        status_counts.columns = ["Status", "Count"]
                        
                        fig_status = px.pie(
                            status_counts,
                            names="Status",
                            values="Count",
                            hole=0.45,
                            title="Subject Status Distribution"
                        )
                        fig_status.update_layout(template="plotly_white", height=350)
                        st.plotly_chart(fig_status, use_container_width=True)
                    else:
                        st.info("Subject status data not available")
                
                # ---- DQI Band Pie ----
                with c2:
                    if "dqi" in drill_df.columns:
                        dqi_bins = pd.cut(
                            drill_df["dqi"],
                            bins=[0, 40, 60, 85, 100],
                            labels=[
                                "Critical (<40)",
                                "At Risk (40–59)",
                                "Acceptable (60–84)",
                                "High Quality (85+)"
                            ]
                        )
                        
                        dqi_dist = dqi_bins.value_counts().reset_index()
                        dqi_dist.columns = ["DQI Band", "Count"]
                        
                        fig_dqi = px.pie(
                            dqi_dist,
                            names="DQI Band",
                            values="Count",
                            hole=0.45,
                            title="DQI Quality Breakdown",
                            color="DQI Band",
                            color_discrete_map={
                                "Critical (<40)": "#FF0000",
                                "At Risk (40–59)": "#FFA500",
                                "Acceptable (60–84)": "#FFD700",
                                "High Quality (85+)": "#00FF00"
                            }
                        )
                        fig_dqi.update_layout(template="plotly_white", height=350)
                        st.plotly_chart(fig_dqi, use_container_width=True)
                    else:
                        st.info("DQI data not available")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # =====================================================
                # ⬇ DOWNLOAD OPTIONS
                # =====================================================
                if 'site_perf' in locals():
                    st.markdown('<div class="content-card">', unsafe_allow_html=True)
                    st.markdown("## ⬇ Downloads")
                    
                    # Prepare data for download
                    csv_data = site_perf.to_csv(index=False)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Download Site Performance (CSV)",
                            csv_data,
                            "site_performance_summary.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        # Create a summary report
                        report_text = f"""
CLINICAL TRIAL SITE PERFORMANCE REPORT
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
============================================

OVERALL SUMMARY
---------------
Total Sites: {len(site_perf)}
Total Subjects: {site_perf['Total Subjects'].sum():,}
Average DQI: {site_perf['Avg DQI'].mean():.1f}
Critical Sites (DQI < 60): {len(site_perf[site_perf['Avg DQI'] < 60])}

TOP 10 SITES NEEDING ATTENTION
------------------------------
{site_perf.sort_values('Avg DQI').head(10).to_string(index=False)}

AI EXECUTIVE INSIGHTS
---------------------
{result.get('narrative', 'No narrative available')[:500]}...
"""
                        
                        st.download_button(
                            "📥 Download Executive Report (TXT)",
                            report_text,
                            "clinical_site_summary.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"❌ Error generating site summary: {str(e)}")
                import traceback
                with st.expander("See error details"):
                    st.code(traceback.format_exc())
        else:
            st.info("Click the button above to generate a comprehensive site summary analysis.")   
# Tab 2: Agent Recommendations
with tab2:
    st.markdown("### AI Agent Recommendations")
    st.markdown("<p style='color: #4a5568; font-size: 16px;'>Get personalized agent deployment recommendations based on data quality patterns.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Generate Agent Recommendations", key="gen_agent_recs", use_container_width=True):
            result = generate_agent_recommendations(drill_df)
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown("## 📋 Recommendations")
            st.markdown(result)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download button
            st.download_button(
                "📥 Download Recommendations",
                result,
                "agent_recommendations.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("Click the button above to generate agent deployment recommendations.")

# Tab 3: Natural Language Query
with tab3:
    st.markdown("### Natural Language Query")
    st.markdown("<p style='color: #4a5568; font-size: 16px;'>Ask questions about your data in plain English and get instant insights.</p>", unsafe_allow_html=True)
    
    # Call the NLQ interface directly
    nlq_interface(drill_df)

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; padding: 20px; font-size: 14px;">
    <p>📊 Clinical Trial Data Quality Dashboard | Powered by AI Analytics</p>
    <p style="font-size: 12px; margin-top: 10px;">Data refreshed automatically | Last updated: Real-time</p>
</div>
""", unsafe_allow_html=True)