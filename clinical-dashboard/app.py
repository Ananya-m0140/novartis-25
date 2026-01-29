import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

from ai.generate_summary import generate_site_summary
from ai.agent_recommender import generate_agent_recommendations
from ai.nlq_chat import nlq_interface

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Clinical Trial Data Quality Dashboard",
    layout="wide"
)

# =========================
# LOAD CSS
# =========================
# =========================
# LOAD CSS (SAFE PATH)
# =========================
from pathlib import Path

CSS_PATH = Path(__file__).parent / "assets" / "css" / "dashboard.css"

if CSS_PATH.exists():
    with open(CSS_PATH) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.error(f"CSS file not found: {CSS_PATH}")


# =========================
# DATA LOADING & CLEANING
# =========================
@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv("data/master_dataset.csv", low_memory=False)

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Rename required columns explicitly
    rename_map = {
        "region": "region",
        "country": "country",
        "site_id": "site_id",
        "subject_id": "patient_id",
        "dqi": "dqi"
    }

    df = df.rename(columns=rename_map)

    # Keep only valid rows
    df = df.dropna(subset=["country", "dqi"])

    # Ensure numeric DQI
    df["dqi"] = pd.to_numeric(df["dqi"], errors="coerce")
    df = df.dropna(subset=["dqi"])

    return df

# Load full dataset
df_full = load_data()
df = df_full.copy()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.markdown("##  Filters")

region_sel = st.sidebar.selectbox(
    "Region",
    ["All"] + sorted(df_full["region"].dropna().unique())
)

country_sel = st.sidebar.selectbox(
    "Country",
    ["All"] + sorted(df_full["country"].dropna().unique())
)

site_sel = st.sidebar.selectbox(
    "Site",
    ["All"] + sorted(df_full["site_id"].dropna().unique())
)

patient_sel = st.sidebar.selectbox(
    "Patient",
    ["All"] + sorted(df_full["patient_id"].dropna().unique())
)

critical_threshold = st.sidebar.slider(
    "⚠️ Critical DQI Alert Threshold",
    0, 100, 60
)

high_perf_threshold = st.sidebar.slider(
    "🌟 High Performing DQI Threshold",
    0, 100, 85
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
st.markdown("<h1> Global Clinical Trial Data Quality Dashboard</h1>", unsafe_allow_html=True)
st.write("From global oversight → site → patient-level operational insights")

# =========================
# KPI CARDS
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.markdown(
    f"<div class='kpi-card'><h3>Sites</h3><h2>{df['site_id'].nunique()}</h2></div>",
    unsafe_allow_html=True
)
col2.markdown(
    f"<div class='kpi-card'><h3>Patients</h3><h2>{df['patient_id'].nunique()}</h2></div>",
    unsafe_allow_html=True
)
col3.markdown(
    f"<div class='kpi-card'><h3>Avg DQI</h3><h2>{round(df['dqi'].mean(),1)}</h2></div>",
    unsafe_allow_html=True
)
col4.markdown(
    f"<div class='kpi-card'><h3>Critical Alerts</h3><h2>{(df['dqi'] < critical_threshold).sum()}</h2></div>",
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
print(map_df.head())

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
    locationmode="ISO-3",   # <-- important!
    color="DQI Level",
    hover_name="country",
    hover_data={"avg_dqi": ":.1f"},
    color_discrete_map={
        "High Performing": "green",
        "Average": "gold",
        "Critical": "red"
    }
)
# Customize background and map appearance
fig_map.update_layout(
    template="plotly_dark",
    height=500,
    margin=dict(l=0, r=0, t=0, b=0),
    plot_bgcolor="#001f3f",
    paper_bgcolor="#0a192f",
    legend=dict(
        font=dict(color="white"),   # make legend text white
        title_font=dict(color="white"),  # make legend title white
        bgcolor="#0a192f",          # optional: background of legend box
        bordercolor="white",        # optional: border color
        borderwidth=1
    )
)





st.plotly_chart(fig_map, use_container_width=True)

# =========================
#  CRITICAL SITES TABLE
# =========================
st.markdown("##  Critical Sites")

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
    st.success("No critical sites detected 🎉")
else:
    st.dataframe(site_df[site_df.critical])

# =========================
#  SITE-LEVEL BAR CHART
# =========================
st.markdown("##  Site-Level Average DQI")

if site_df.shape[0] > 1:
    fig_bar = px.bar(
        site_df,
        x="site_id",
        y="avg_dqi",
        color="avg_dqi",
        color_continuous_scale="Viridis"
    )
    fig_bar.update_layout(template="plotly_dark", height=420)
    st.plotly_chart(fig_bar, use_container_width=True)

# =========================
#  DRILL-DOWN TABLE
# =========================
st.markdown("##  Drill-Down View")

st.dataframe(df)
# 🤖 AI TOOLS
# ---------------------------------------------------
# 🤖 AI TOOLS
# ---------------------------------------------------
st.markdown("##  AI Tools")

a1, a2, a3 = st.columns(3)

# Use the currently filtered DataFrame
drill_df = df.copy()

if a1.button(" Generate Site Summary"):
    result = generate_site_summary(drill_df)
    st.write(result)
    st.download_button("⬇ Download", result, "site_summary.txt")

if a2.button(" Agent Recommendations"):
    result = generate_agent_recommendations(drill_df)
    st.write(result)
    st.download_button("⬇ Download", result, "agent_plan.txt")

if a3.button(" Natural Language Query"):
    nlq_interface()
st.markdown("""
<style>
.stButton>button:first-child {
    color: black;         /* Text color */
    font-size: 30px;      /* Font size */
    font-weight: bold;    
    background-color: #f0f0f0;  /* optional background */
}
</style>
""", unsafe_allow_html=True)