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





st.plotly_chart(fig_map, width='stretch')

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
    st.plotly_chart(fig_bar, width='stretch')

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
# After loading data, add:
print("Available columns:", drill_df.columns.tolist())

if a1.button(" Generate Site Summary"):
    try:
        result = generate_site_summary(drill_df)
        
        # =====================================================
        # 🧠 AI RISK INTELLIGENCE
        # =====================================================
        st.markdown("## 🧠 AI Risk Intelligence")
        
        if "narrative" in result:
            narrative = result["narrative"]
            
            # Split the narrative into sections if it contains sections
            if "SECTION A" in narrative and "SECTION B" in narrative:
                # Split into executive summary and details
                sections = narrative.split("SECTION B")
                exec_summary = sections[0].replace("SECTION A — AI RISK INTELLIGENCE (CONCISE)", "").strip()
                details = "SECTION B" + sections[1] if len(sections) > 1 else ""
                
                # Display executive summary in expander
                with st.expander("📋 Executive Summary", expanded=True):
                    # Clean up the text
                    exec_summary = exec_summary.replace("Executive Insight (≤120 words)", "**Executive Insight**")
                    st.markdown(exec_summary)
                
                # Display details in another expander
                if details:
                    with st.expander("📊 Detailed Analysis", expanded=False):
                        st.markdown(details)
            else:
                # Simple display if no sections
                st.markdown("### Executive Insight")
                st.write(narrative)
        
        # Check if result has metrics
        if isinstance(result, dict) and "metrics" in result:
            metrics = result["metrics"]
            
            # ---- Confidence Meter ----
            if "confidence_score" in metrics:
                st.markdown("### 📊 Data Readiness Confidence")
                confidence = metrics["confidence_score"]
                
                # Color code based on confidence
                if confidence >= 70:
                    color = "green"
                elif confidence >= 40:
                    color = "orange"
                else:
                    color = "red"
                
                st.markdown(f"""
                <div style="background-color:#1a1a2e; padding:15px; border-radius:10px; border-left:5px solid {color};">
                    <h4 style="margin:0; color:white;">Confidence Score: <span style="color:{color}">{confidence}%</span></h4>
                    <div style="width:100%; background-color:#333; border-radius:5px; margin-top:10px;">
                        <div style="width:{confidence}%; background-color:{color}; height:20px; border-radius:5px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Interpretation
                if confidence < 40:
                    st.warning("⚠️ Low confidence score indicates need for manual validation and deeper analysis.")
            
            # ---- Risk Fingerprint ----
            if "risk_fingerprint" in metrics and metrics["risk_fingerprint"]:
                st.markdown("### 🔎 Risk Fingerprint (Top Sites)")
                
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
                        width='stretch',
                        height=250
                    )
            
            # ---- Action Priority Stack ----
            if "action_stack" in metrics and metrics["action_stack"]:
                st.markdown("### 🚨 Action Priority (Next 7 Days)")
                
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
        
        # =====================================================
        # 📋 OVERALL SITE PERFORMANCE SUMMARY
        # =====================================================
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
                width='stretch',
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
        
        # =====================================================
        # 📊 COMPOSITION PIE CHARTS
        # =====================================================
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
                fig_status.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_status, width='stretch')
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
                fig_dqi.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_dqi, width='stretch')
            else:
                st.info("DQI data not available")
        
        # =====================================================
        # ⬇ DOWNLOAD OPTIONS
        # =====================================================
        if 'site_perf' in locals():
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
                    width='stretch'
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
                    width='stretch'
                )
    
    except Exception as e:
        st.error(f"❌ Error generating site summary: {str(e)}")
        import traceback
        with st.expander("See error details"):
            st.code(traceback.format_exc())
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