import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from textwrap import dedent


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
        padding: 20px !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid #e2e8f0 !important;
        transition: all 0.3s ease !important;
        text-align: center !important;
        min-height: 130px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.12) !important;
        border-color: #4299e1 !important;
    }
    
    .kpi-card h3 {
        color: #718096 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        margin-bottom: 8px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }
    
    .kpi-card h2 {
        color: #1a365d !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        border: none !important;
        padding: 0 !important;
    }
    
    .kpi-card .trend {
        font-size: 0.85rem !important;
        margin-top: 5px !important;
        font-weight: 600 !important;
    }
    
    .kpi-card .trend.up {
        color: #38a169 !important;
    }
    
    .kpi-card .trend.down {
        color: #e53e3e !important;
    }
    
    /* ===== METRIC CARDS ===== */
    .metric-card {
        background: white !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 10px !important;
    }
    
    .metric-card h4 {
        color: #4a5568 !important;
        font-size: 0.9rem !important;
        margin-bottom: 5px !important;
        font-weight: 600 !important;
    }
    
    .metric-card .value {
        color: #1a365d !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    .metric-card .progress-bar {
        height: 6px !important;
        background: #e2e8f0 !important;
        border-radius: 3px !important;
        margin-top: 8px !important;
        overflow: hidden !important;
    }
    
    .metric-card .progress-fill {
        height: 100% !important;
        border-radius: 3px !important;
        transition: width 0.5s ease !important;
    }
    
    /* ===== CHART CONTAINERS ===== */
    .chart-container {
        background: white !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
        margin-bottom: 20px !important;
        height: 100% !important;
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
    
    /* ===== CUSTOM CLASSES FOR CONTENT ===== */
    .content-card {
        background: white !important;
        border-radius: 16px !important;
        padding: 25px !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #e2e8f0 !important;
        margin: 20px 0 !important;
    }
    
    /* ===== AI PRELOADER ===== */
    .ai-loader {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        font-size: 18px;
        color: #4a5568;
    }
    .ai-loader .emoji {
        font-size: 48px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.4; }
        50% { opacity: 1; }
        100% { opacity: 0.4; }
    }
    
    /* ===== STATUS INDICATORS ===== */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-good { background-color: #38a169; }
    .status-warning { background-color: #d69e2e; }
    .status-critical { background-color: #e53e3e; }
    
    /* ===== BADGES ===== */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 2px;
    }
    
    .badge-success { background-color: #c6f6d5; color: #22543d; }
    .badge-warning { background-color: #feebc8; color: #744210; }
    .badge-danger { background-color: #fed7d7; color: #742a2a; }
    .badge-info { background-color: #bee3f8; color: #2c5282; }
    
    /* ===== HEATMAP STYLING ===== */
    .heatmap-cell {
        padding: 8px;
        text-align: center;
        font-weight: 600;
        border-radius: 4px;
    }
            
.nav-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 30px;
}

/* Navigation button */
.nav-btn {
    display: block;
    padding: 14px 18px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.08);
    color: #e2e8f0 !important;
    font-size: 15px;
    font-weight: 600;
    text-decoration: none !important;
    transition: all 0.25s ease;
    border-left: 4px solid transparent;
}

/* Hover */
.nav-btn:hover {
    background: rgba(66, 153, 225, 0.25);
    color: #ffffff !important;
    transform: translateX(6px);
    border-left: 4px solid #4299e1;
}

/* Active page highlight */
.nav-btn.active {
    background: linear-gradient(135deg, #4299e1, #3182ce);
    color: #ffffff !important;
    border-left: 4px solid #90cdf4;
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
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
    
    # Column mapping
    COLUMN_MAP = {
        "project_name_|_unnamed:_0_level_1_|_unnamed:_0_level_2_|_responsible_lf_for_action": "study",
        "region_|_unnamed:_1_level_1_|_unnamed:_1_level_2_|_unnamed:_1_level_3": "region",
        "country_|_unnamed:_2_level_1_|_unnamed:_2_level_2_|_unnamed:_2_level_3": "country",
        "site_id_|_unnamed:_3_level_1_|_unnamed:_3_level_2_|_unnamed:_3_level_3": "site_id",
        "subject_id_|_unnamed:_4_level_1_|_unnamed:_4_level_2_|_unnamed:_4_level_3": "patient_id",
        "latest_visit_(sv)_(source:_rave_edc:_bo4)_|_unnamed:_5_level_1_|_unnamed:_5_level_2_|_unnamed:_5_level_3": "latest_visit",
        "subject_status_(source:_primary_form)_|_unnamed:_6_level_1_|_unnamed:_6_level_2_|_unnamed:_6_level_3": "subject_status",
        "input_files_|_missing_visits_|_unnamed:_7_level_2_|_unnamed:_7_level_3": "missing_visits",
        "input_files_|_missing_page_|_unnamed:_8_level_2_|_unnamed:_8_level_3": "missing_pages",
        "input_files_|_#_coded_terms_|_unnamed:_9_level_2_|_unnamed:_9_level_3": "coded_terms",
        "input_files_|_#_uncoded_terms_|_unnamed:_10_level_2_|_unnamed:_10_level_3": "uncoded_terms",
        "input_files_|_#_open_issues_in_lnr_|_unnamed:_11_level_2_|_unnamed:_11_level_3": "open_lnr_issues",
        "input_files_|_#_open_issues_reported_for_3rd_party_reconciliation_in_edrr_|_unnamed:_12_level_2_|_unnamed:_12_level_3": "open_edrr_issues",
        "input_files_|_inactivated_forms_and_folders_|_unnamed:_13_level_2_|_unnamed:_13_level_3": "inactivated_forms",
        "input_files_|_#_esae_dashboard_review_for_dm_|_unnamed:_14_level_2_|_unnamed:_14_level_3": "esae_dm_reviews",
        "input_files_|_#_esae_dashboard_review_for_safety_|_unnamed:_15_level_2_|_unnamed:_15_level_3": "esae_safety_reviews",
        "cpmd_|_visit_status_|_#_expected_visits_(rave_edc_:_bo4)_|_unnamed:_16_level_3": "expected_visits",
        "cpmd_|_page_status_(source:_(rave_edc_:_bo4))_|_#_pages_entered_|_unnamed:_17_level_3": "pages_entered",
        "cpmd_|_page_status_(source:_(rave_edc_:_bo4))_|_#_pages_with_non-conformant_data_|_site/cra": "non_conformant_pages",
        "cpmd_|_page_status_(source:_(rave_edc_:_bo4))_|_#_total_crfs_with_queries_&_non-conformant_data_|_unnamed:_19_level_3": "crfs_with_queries",
        "cpmd_|_page_status_(source:_(rave_edc_:_bo4))_|_#_total_crfs_without_queries_&_non-conformant_data_|_unnamed:_20_level_3": "crfs_without_queries",
        "cpmd_|_page_status_(source:_(rave_edc_:_bo4))_|_%_clean_entered_crf_|_unnamed:_21_level_3": "clean_crf_percent",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#_dm_queries_|_dm": "dm_queries",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#_clinical_queries_|_cse/cdd": "clinical_queries",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#_medical_queries_|_cdmd/medical_lead": "medical_queries",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#_site_queries_|_site/cra": "site_queries",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#_field_monitor_queries_|_cra": "field_monitor_queries",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#_coding_queries_|_coder": "coding_queries",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#_safety_queries_|_safety_team": "safety_queries",
        "cpmd_|_queries_status_(source:(rave_edc_:_bo4))_|_#total_queries_|_unnamed:_29_level_3": "total_queries",
        "cpmd_|_page_action_status_(source:_(rave_edc_:_bo4))_|_#_crfs_require_verification_(sdv)_|_cra": "crfs_require_sdv",
        "cpmd_|_page_action_status_(source:_(rave_edc_:_bo4))_|_#_forms_verified_|_unnamed:_31_level_3": "forms_verified",
        "cpmd_|_page_action_status_(source:_(rave_edc_:_bo4))_|_#_crfs_frozen_|_unnamed:_32_level_3": "crfs_frozen",
        "cpmd_|_page_action_status_(source:_(rave_edc_:_bo4))_|_#_crfs_not_frozen_|_dm": "crfs_not_frozen",
        "cpmd_|_page_action_status_(source:_(rave_edc_:_bo4))_|_#_crfs_locked_|_unnamed:_34_level_3": "crfs_locked",
        "cpmd_|_page_action_status_(source:_(rave_edc_:_bo4))_|_#_crfs_unlocked_|_unnamed:_35_level_3": "crfs_unlocked",
        "cpmd_|_protocol_deviations_(source:(rave_edc_:_bo4))_|_#_pds_confirmed_|_cd_lf": "pds_confirmed",
        "cpmd_|_protocol_deviations_(source:(rave_edc_:_bo4))_|_#_pds_proposed_|_unnamed:_37_level_3": "pds_proposed",
        "ssm_|_pi_signatures_(source:_(rave_edc_:_bo4))_|_#_crfs_signed_|_investigator": "crfs_signed",
        "ssm_|_pi_signatures_(source:_(rave_edc_:_bo4))_|_crfs_overdue_for_signs_within_45_days_of_data_entry_|_unnamed:_39_level_3": "signs_overdue_45",
        "ssm_|_pi_signatures_(source:_(rave_edc_:_bo4))_|_crfs_overdue_for_signs_between_45_to_90_days_of_data_entry_|_unnamed:_40_level_3": "signs_overdue_90",
        "ssm_|_pi_signatures_(source:_(rave_edc_:_bo4))_|_crfs_overdue_for_signs_beyond_90_days_of_data_entry_|_unnamed:_41_level_3": "signs_overdue_90_plus",
        "ssm_|_pi_signatures_(source:_(rave_edc_:_bo4))_|_broken_signatures_|_unnamed:_42_level_3": "broken_signatures",
        "ssm_|_pi_signatures_(source:_(rave_edc_:_bo4))_|_crfs_never_signed_|_unnamed:_43_level_3": "crfs_never_signed",
        "dqi": "dqi"
    }

    # Apply mapping safely
    df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})
    
    # Convert numeric columns
    numeric_cols = ['missing_visits', 'missing_pages', 'expected_visits', 'pages_entered', 
                    'non_conformant_pages', 'total_queries', 'dm_queries', 'clinical_queries',
                    'medical_queries', 'site_queries', 'field_monitor_queries', 'coding_queries',
                    'safety_queries', 'crfs_require_sdv', 'forms_verified', 'crfs_frozen',
                    'crfs_not_frozen', 'crfs_locked', 'crfs_unlocked', 'pds_confirmed',
                    'pds_proposed', 'crfs_signed', 'signs_overdue_45', 'signs_overdue_90',
                    'signs_overdue_90_plus', 'broken_signatures', 'crfs_never_signed', 'dqi']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

# =========================
# CALCULATION FUNCTIONS
# =========================
def calculate_metrics(df):
    """Calculate all derived metrics"""
    
    # Patient Clean Status
    df['clean_patient'] = (
        (df['missing_visits'].fillna(0) == 0) &
        (df['missing_pages'].fillna(0) == 0) &
        (df['total_queries'].fillna(0) == 0) &
        (df['crfs_require_sdv'].fillna(0) == 0) &
        (df['crfs_signed'].fillna(0) > 0) &
        (df['broken_signatures'].fillna(0) == 0)
    ).astype(int)
    
    # Percentages
    df['missing_visits_pct'] = (df['missing_visits'].fillna(0) / df['expected_visits'].replace(0, 1)) * 100
    df['missing_pages_pct'] = (df['missing_pages'].fillna(0) / df['pages_entered'].replace(0, 1)) * 100
    df['non_conformant_pct'] = (df['non_conformant_pages'].fillna(0) / df['pages_entered'].replace(0, 1)) * 100
    df['verification_pct'] = (df['forms_verified'].fillna(0) / df['crfs_require_sdv'].replace(0, 1)) * 100
    df['signature_pct'] = (df['crfs_signed'].fillna(0) / (df['crfs_signed'] + df['crfs_never_signed']).replace(0, 1)) * 100
    
    # Query resolution rate (assuming some queries are resolved)
    df['query_resolution_rate'] = 100 - (df['total_queries'].fillna(0) / (df['total_queries'] + 10).replace(0, 1)) * 100
    
    # Data readiness score (composite)
    df['data_readiness_score'] = (
        df['clean_crf_percent'].fillna(0) * 0.3 +
        df['query_resolution_rate'].fillna(0) * 0.2 +
        (100 - df['missing_visits_pct'].fillna(0)) * 0.2 +
        df['verification_pct'].fillna(0) * 0.15 +
        df['signature_pct'].fillna(0) * 0.15
    )
    
    return df

# =========================
# VISUALIZATION FUNCTIONS
# =========================
def create_gauge_chart(value, title, color_scheme='RdYlGn'):
    """Create a gauge chart for metrics"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 16}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#2d3748"},
            'bar': {'color': "#3182ce"},
            'steps': [
                {'range': [0, 40], 'color': '#fc8181'},
                {'range': [40, 70], 'color': '#fbd38d'},
                {'range': [70, 100], 'color': '#9ae6b4'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        font={'color': "#2d3748"}
    )
    
    return fig

def create_heatmap(df, metric_col, title):
    """Create a heatmap of sites vs metrics"""
    heatmap_data = df.groupby('site_id')[metric_col].mean().sort_values(ascending=False).head(20)
    
    fig = go.Figure(data=go.Heatmap(
        z=[heatmap_data.values],
        x=heatmap_data.index,
        y=[''],
        colorscale='RdYlGn_r',
        showscale=True,
        hoverongaps=False,
        text=[heatmap_data.values.round(1)],
        texttemplate='%{text}%',
        textfont={"size": 12, "color": "white"}
    ))
    
    fig.update_layout(
        title=title,
        height=120,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Site ID",
        paper_bgcolor='white'
    )
    
    return fig

# =========================
# LOAD DATA
# =========================
df_full = load_data()
df_full = calculate_metrics(df_full)
df = df_full.copy()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.markdown("""
<div class="nav-container">
    <a href="/" class="nav-btn">📊 Dashboard</a>
    <a href="/Data_Upload" class="nav-btn">Data_Upload</a>
</div>
""", unsafe_allow_html=True)

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
st.markdown("<h1>📊 Clinical Trial Data Quality Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.2rem; color: #4a5568;'>Comprehensive data quality monitoring with advanced analytics</p>", unsafe_allow_html=True)

# =========================
# OVERALL KPI CARDS
# =========================
st.markdown("##  Key Performance Indicators")
col1, col2, col3, col4, col5, col6 = st.columns(6)

total_patients = df['patient_id'].nunique()
clean_patients = df['clean_patient'].sum() if 'clean_patient' in df.columns else 0
clean_patient_pct = (clean_patients / total_patients * 100) if total_patients > 0 else 0

col1.markdown(
    f"""<div class='kpi-card'>
        <h3>Sites</h3>
        <h2>{df['site_id'].nunique():,}</h2>
    </div>""",
    unsafe_allow_html=True
)

col2.markdown(
    f"""<div class='kpi-card'>
        <h3>Patients</h3>
        <h2>{total_patients:,}</h2>
    </div>""",
    unsafe_allow_html=True
)

col3.markdown(
    f"""<div class='kpi-card'>
        <h3>Clean Patients</h3>
        <h2>{clean_patients:,}</h2>
        <div class='trend {"up" if clean_patient_pct > 50 else "down"}'>
            {clean_patient_pct:.1f}% clean
        </div>
    </div>""",
    unsafe_allow_html=True
)

col4.markdown(
    f"""<div class='kpi-card'>
        <h3>Avg DQI</h3>
        <h2>{df['dqi'].mean():.1f}</h2>
        <div class='trend {"up" if df['dqi'].mean() > 60 else "down"}'>
            {df['dqi'].mean() - 60:+.1f} vs target
        </div>
    </div>""",
    unsafe_allow_html=True
)

col5.markdown(
    f"""<div class='kpi-card'>
        <h3>Open Queries</h3>
        <h2>{df['total_queries'].sum():,}</h2>
    </div>""",
    unsafe_allow_html=True
)

col6.markdown(
    f"""<div class='kpi-card'>
        <h3>Clean CRF %</h3>
        <h2>{df['clean_crf_percent'].mean():.1f}%</h2>
    </div>""",
    unsafe_allow_html=True
)

# =========================
# DATA QUALITY METRICS SECTION
# =========================
st.markdown("##  Data Quality Metrics")

# Row 1: Gauge Charts
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.plotly_chart(create_gauge_chart(
        df['clean_crf_percent'].mean(),
        "Clean CRF %"
    ), use_container_width=True)

with col2:
    st.plotly_chart(create_gauge_chart(
        df['query_resolution_rate'].mean() if 'query_resolution_rate' in df.columns else 0,
        "Query Resolution %"
    ), use_container_width=True)

with col3:
    st.plotly_chart(create_gauge_chart(
        100 - df['missing_visits_pct'].mean(),
        "Visit Completeness %"
    ), use_container_width=True)

with col4:
    st.plotly_chart(create_gauge_chart(
        df['verification_pct'].mean(),
        "Verification %"
    ), use_container_width=True)

# =========================
# ISSUE ANALYSIS SECTION
# =========================
st.markdown("## 🔍 Issue Analysis")

tab1, tab2, tab3 = st.tabs(["Missing Data", "Query Analysis", "Protocol Deviations"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(dedent("""
        <div class="chart-container">
            <h3> Sites with Most Missing Visits</h3>
        """), unsafe_allow_html=True)

        missing_visits_by_site = (
            df.groupby('site_id')['missing_visits']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        fig = px.bar(
            x=missing_visits_by_site.index,
            y=missing_visits_by_site.values,
            labels={'x': 'Site ID', 'y': 'Missing Visits'},
            color=missing_visits_by_site.values,
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False, height=300)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(dedent("""
        <div class="chart-container">
            <h3> Sites with Most Missing Pages</h3>
        """), unsafe_allow_html=True)

        missing_pages_by_site = (
            df.groupby('site_id')['missing_pages']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        fig = px.bar(
            x=missing_pages_by_site.index,
            y=missing_pages_by_site.values,
            labels={'x': 'Site ID', 'y': 'Missing Pages'},
            color=missing_pages_by_site.values,
            color_continuous_scale='Oranges'
        )
        fig.update_layout(showlegend=False, height=300)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(dedent("""
        <div class="chart-container">
            <h3> Query Types Distribution</h3>
        """), unsafe_allow_html=True)

        query_types = {
            'DM Queries': df['dm_queries'].sum(),
            'Clinical Queries': df['clinical_queries'].sum(),
            'Medical Queries': df['medical_queries'].sum(),
            'Site Queries': df['site_queries'].sum(),
            'Safety Queries': df['safety_queries'].sum()
        }
        query_df = pd.DataFrame(list(query_types.items()), columns=['Query Type', 'Count'])

        fig = px.pie(
            query_df,
            names='Query Type',
            values='Count',
            hole=0.4
        )
        fig.update_layout(height=350)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(dedent("""
        <div class="chart-container">
            <h3> Sites with Most Open Queries</h3>
        """), unsafe_allow_html=True)

        queries_by_site = (
            df.groupby('site_id')['total_queries']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        fig = px.bar(
            x=queries_by_site.index,
            y=queries_by_site.values,
            labels={'x': 'Site ID', 'y': 'Open Queries'},
            color=queries_by_site.values,
            color_continuous_scale='Purples'
        )
        fig.update_layout(showlegend=False, height=300)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(dedent("""
        <div class="chart-container">
            <h3>⚠️ Protocol Deviations by Site</h3>
        """), unsafe_allow_html=True)

        pds_by_site = (
            df.groupby('site_id')['pds_confirmed']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        fig = px.bar(
            x=pds_by_site.index,
            y=pds_by_site.values,
            labels={'x': 'Site ID', 'y': 'Confirmed PDs'},
            color=pds_by_site.values,
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False, height=300)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# SITE PERFORMANCE HEATMAPS
# =========================
st.markdown("##  Site Performance Heatmaps")

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("###  Clean CRF Percentage by Site")
    st.plotly_chart(create_heatmap(df, 'clean_crf_percent', ''), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### ✅ Data Readiness Score by Site")
    st.plotly_chart(create_heatmap(df, 'data_readiness_score', ''), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
# =========================
# CRITICAL ALERTS SECTION
# =========================
st.markdown("##  Critical Alerts & Immediate Attention")

# Calculate critical metrics
site_summary = df.groupby('site_id').agg({
    'dqi': 'mean',
    'total_queries': 'sum',
    'missing_visits': 'sum',
    'missing_pages': 'sum',
    'pds_confirmed': 'sum',
    'clean_patient': 'sum',
    'patient_id': 'nunique'
}).reset_index()

site_summary['clean_patient_pct'] = (site_summary['clean_patient'] / site_summary['patient_id']) * 100

# Create a better priority score
def calculate_priority_score(row):
    score = 0
    
    # DQI score (0-100, lower is worse)
    if row['dqi'] < 20: score += 40
    elif row['dqi'] < 40: score += 30
    elif row['dqi'] < 60: score += 20
    
    # Clean patient percentage
    if pd.notna(row['clean_patient_pct']):
        if row['clean_patient_pct'] < 20: score += 30
        elif row['clean_patient_pct'] < 50: score += 20
        elif row['clean_patient_pct'] < 80: score += 10
    
    # Open queries
    if pd.notna(row['total_queries']):
        if row['total_queries'] > 50: score += 20
        elif row['total_queries'] > 20: score += 15
        elif row['total_queries'] > 5: score += 10
    
    # Missing visits
    if pd.notna(row['missing_visits']):
        if row['missing_visits'] > 20: score += 10
    
    return score

site_summary['priority_score'] = site_summary.apply(calculate_priority_score, axis=1)

# Categorize priority
def categorize_priority(score):
    if score >= 60:
        return "🔴 Critical", "#feb2b2"
    elif score >= 40:
        return "🟠 High", "#fbd38d"
    elif score >= 20:
        return "🟡 Medium", "#fefcbf"
    else:
        return "🟢 Low", "#c6f6d5"

site_summary['priority_info'] = site_summary['priority_score'].apply(
    lambda x: categorize_priority(x)
)
site_summary['priority'] = site_summary['priority_info'].apply(lambda x: x[0])
site_summary['priority_color'] = site_summary['priority_info'].apply(lambda x: x[1])

# Determine DQI status
site_summary['dqi_status'] = site_summary['dqi'].apply(
    lambda x: ("🔴 Critical", "#e53e3e") if x < 40 else 
              ("🟠 Warning", "#d69e2e") if x < 60 else 
              ("🟢 Good", "#38a169")
)
site_summary['dqi_status_text'] = site_summary['dqi_status'].apply(lambda x: x[0])
site_summary['dqi_color'] = site_summary['dqi_status'].apply(lambda x: x[1])

# Top 10 sites needing attention
critical_sites = site_summary.sort_values(
    ['priority_score', 'dqi', 'total_queries', 'missing_visits'], 
    ascending=[False, True, False, False]
).head(10)

# Create a clean DataFrame for display with consistent column names
display_df = critical_sites[['site_id', 'dqi', 'total_queries', 'missing_visits', 'clean_patient_pct', 'priority']].copy()
display_df.columns = ['Site_ID', 'DQI', 'Open_Queries', 'Missing_Visits', 'Clean_Patients_Pct', 'Priority']

# Apply styling with corrected column names
def style_row(row):
    # Get DQI color
    if row['DQI'] < 40:
        dqi_color = "#e53e3e"
    elif row['DQI'] < 60:
        dqi_color = "#d69e2e"
    else:
        dqi_color = "#38a169"
    
    # Get priority color
    if "Critical" in str(row['Priority']):
        priority_color = "#feb2b2"
    elif "High" in str(row['Priority']):
        priority_color = "#fbd38d"
    elif "Medium" in str(row['Priority']):
        priority_color = "#fefcbf"
    else:
        priority_color = "#c6f6d5"
    
    # Format values
    clean_pct = f"{row['Clean_Patients_Pct']:.1f}%" if pd.notna(row['Clean_Patients_Pct']) else "N/A"
    queries = int(row['Open_Queries']) if pd.notna(row['Open_Queries']) else 0
    missing_visits = int(row['Missing_Visits']) if pd.notna(row['Missing_Visits']) else 0
    dqi_value = f"{row['DQI']:.1f}" if pd.notna(row['DQI']) else "N/A"
    
    return [
        f"<strong>{row['Site_ID']}</strong>",
        f"<span style='color: {dqi_color}; font-weight: bold;'>{dqi_value}</span>",
        "🔴 Critical" if row['DQI'] < 40 else "🟠 Warning" if row['DQI'] < 60 else "🟢 Good",
        f"{queries}",
        f"{missing_visits}",
        f"{clean_pct}",
        f"<div style='background-color: {priority_color}; padding: 5px 10px; border-radius: 4px; font-weight: bold; text-align: center;'>{row['Priority']}</div>"
    ]

# Create styled rows
styled_rows = [style_row(row) for _, row in display_df.iterrows()]
styled_df = pd.DataFrame(styled_rows, columns=['Site ID', 'DQI Score', 'Status', 'Open Queries', 'Missing Visits', 'Clean Patients %', 'Priority'])

# Display using Streamlit's dataframe with HTML


# Alternative: Use a simpler approach with Streamlit's native components
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.markdown("### ⚠️ Sites Requiring Attention (Alternative View)")

# Create a simpler table view
for _, site in critical_sites.head(5).iterrows():
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        st.metric(
            label=f"Site {site['site_id']}",
            value=f"DQI: {site['dqi']:.1f}",
            delta="Critical" if site['dqi'] < 40 else "Warning" if site['dqi'] < 60 else "Good",
            delta_color="inverse"
        )
    
    with col2:
        clean_pct = f"{site['clean_patient_pct']:.1f}%" if pd.notna(site['clean_patient_pct']) else "N/A"
        st.metric(
            label="Clean Patients",
            value=clean_pct,
            delta_color="off"
        )
    
    with col3:
        st.metric(
            label="Open Queries",
            value=int(site['total_queries']) if pd.notna(site['total_queries']) else 0,
            delta_color="off"
        )
    
    with col4:
        # Create a colored priority badge
        priority_text, priority_color = categorize_priority(site['priority_score'])
        st.markdown(f"""
        <div style='background-color: {priority_color}; 
                    padding: 10px; 
                    border-radius: 8px; 
                    text-align: center;
                    font-weight: bold;
                    color: #2d3748;'>
            {priority_text}
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
   
# =========================
# DATA READINESS FOR ANALYSIS
# =========================
st.markdown("##  Data Readiness for Statistical Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### 🔬 Interim Analysis Readiness")
    
    # Calculate readiness score with error handling
    try:
        readiness_score = (
            (df['clean_crf_percent'].mean() * 0.3) +
            (100 - df['missing_visits_pct'].mean() * 0.2) +
            (df['verification_pct'].mean() * 0.2) +
            (df['signature_pct'].mean() * 0.15) +
            (df['query_resolution_rate'].mean() * 0.15)
        )
    except:
        readiness_score = 0
    
    readiness_level = "✅ Ready" if readiness_score > 80 else "⚠️ Needs Work" if readiness_score > 60 else "❌ Not Ready"
    readiness_color = "#38a169" if readiness_score > 80 else "#d69e2e" if readiness_score > 60 else "#e53e3e"
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="font-size: 3rem; font-weight: 800; color: {readiness_color}; margin-bottom: 10px;">
            {readiness_score:.1f}%
        </div>
        <div style="font-size: 1.2rem; color: #4a5568; margin-bottom: 20px;">
            {readiness_level}
        </div>
        <div style="font-size: 0.9rem; color: #718096;">
            Based on CRF cleanliness, verification, and query resolution
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("###  Submission Readiness Checklist")
    
    # Define checklist with error handling
    checklist_items = []
    
    # Check each condition with try-except
    try:
        checklist_items.append(("CRF Cleanliness > 85%", df['clean_crf_percent'].mean() > 85))
    except:
        checklist_items.append(("CRF Cleanliness > 85%", False))
    
    try:
        checklist_items.append(("Missing Visits < 5%", df['missing_visits_pct'].mean() < 5))
    except:
        checklist_items.append(("Missing Visits < 5%", False))
    
    try:
        checklist_items.append(("Verification > 90%", df['verification_pct'].mean() > 90))
    except:
        checklist_items.append(("Verification > 90%", False))
    
    try:
        checklist_items.append(("Signatures > 95%", df['signature_pct'].mean() > 95))
    except:
        checklist_items.append(("Signatures > 95%", False))
    
    try:
        checklist_items.append(("Query Resolution > 80%", df['query_resolution_rate'].mean() > 80))
    except:
        checklist_items.append(("Query Resolution > 80%", False))
    
    try:
        checklist_items.append(("PDs Resolved", df['pds_confirmed'].mean() > 0))
    except:
        checklist_items.append(("PDs Resolved", False))
    
    checklist_html = ""
    for item, status in checklist_items:
        icon = "✅" if status else "❌"
        color = "#38a169" if status else "#e53e3e"
        checklist_html += f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px; padding: 8px; background-color: {'#f0fff4' if status else '#fff5f5'}; border-radius: 8px;">
            <span style="font-size: 1.2rem; margin-right: 10px; color: {color};">{icon}</span>
            <span style="color: #2d3748;">{item}</span>
        </div>
        """
    
    st.markdown(checklist_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("###  Current Data Snapshot")
    
    # Calculate snapshot data
    total_patients = df['patient_id'].nunique()
    clean_patients = df['clean_patient'].sum() if 'clean_patient' in df.columns else 0
    
    snapshot_data = [
        ("Total Sites", df['site_id'].nunique()),
        ("Total Patients", total_patients),
        ("Clean Patients", clean_patients),
        ("Open Queries", int(df['total_queries'].sum())),
        ("Missing Visits", int(df['missing_visits'].sum())),
        ("Protocol Deviations", int(df['pds_confirmed'].sum()))
    ]
    
    snapshot_html = ""
    for label, value in snapshot_data:
        snapshot_html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e2e8f0;">
            <span style="color: #4a5568; font-weight: 500;">{label}</span>
            <span style="color: #1a365d; font-weight: 700; font-size: 1.1rem;">{value:,}</span>
        </div>
        """
    
    st.markdown(snapshot_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🌍 WORLD MAP (KEEPING ORIGINAL)
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
#  AI TOOLS SECTION (KEEPING ORIGINAL)
# =========================
st.markdown("## AI Tools")

# Create beautifully styled tabs
ai_tab1, ai_tab2, ai_tab3 = st.tabs([
    " SITE SUMMARY", 
    " AGENT RECOMMENDATIONS", 
    " NATURAL LANGUAGE QUERY"
])

# Use the currently filtered DataFrame
drill_df = df.copy()

# Tab 1: Site Summary (keeping original)
with ai_tab1:
    st.markdown("### AI-Powered Site Summary Generator")
    st.markdown("<p style='color: #4a5568; font-size: 16px;'>Generate comprehensive site performance analysis with risk intelligence and actionable insights.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(" Generate Site Summary", key="gen_site_summary", use_container_width=True):
            try:
                placeholder = st.empty()
                with placeholder.container():
                    st.markdown("""
                    <div class="ai-loader">
                        <div class="emoji">⏳</div>
                        <b>Generating AI Site Summary…</b>
                        <div style="font-size:14px;">Analyzing risks, trends & actions</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with st.spinner("Processing…"):
                    result = generate_site_summary(drill_df)
                
                placeholder.empty()
                
                # Display results (keeping original content)
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                st.markdown("##  Executive Summary")
                
                if "narrative" in result:
                    narrative = result["narrative"]
                    if "SECTION A" in narrative and "SECTION B" in narrative:
                        sections = narrative.split("SECTION B")
                        exec_summary = sections[0].replace("SECTION A — AI RISK INTELLIGENCE (CONCISE)", "").strip()
                        details = "SECTION B" + sections[1] if len(sections) > 1 else ""
                        
                        with st.expander(" View Executive Summary", expanded=True):
                            exec_summary = exec_summary.replace("Executive Insight (≤120 words)", "**Key Insights**")
                            st.markdown(exec_summary)
                        
                        if details:
                            with st.expander(" View Detailed Analysis", expanded=False):
                                st.markdown(details)
                    else:
                        st.markdown("### Key Insights")
                        st.write(narrative)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error generating site summary: {str(e)}")
                import traceback
                with st.expander("See error details"):
                    st.code(traceback.format_exc())
        else:
            st.info("Click the button above to generate a comprehensive site summary analysis.")

# Tab 2: Agent Recommendations (keeping original)
with ai_tab2:
    st.markdown("### AI Agent Recommendations")
    st.markdown("<p style='color: #4a5568; font-size: 16px;'>Get personalized agent deployment recommendations based on data quality patterns.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(" Generate Agent Recommendations", key="gen_agent_recs", use_container_width=True):
            placeholder = st.empty()
            with placeholder.container():
                st.markdown("""
                <div class="ai-loader">
                    <div class="emoji">⏳</div>
                    <b>Generating Agent Recommendations…</b>
                    <div style="font-size:14px;">Evaluating workload & risk signals</div>
                </div>
                """, unsafe_allow_html=True)
            
            with st.spinner("Analyzing…"):
                result = generate_agent_recommendations(drill_df)
            
            placeholder.empty()
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown("##  Recommendations")
            st.markdown(result)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download button
            st.download_button(
                "Download Recommendations",
                result,
                "agent_recommendations.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("Click the button above to generate agent deployment recommendations.")

# Tab 3: Natural Language Query (keeping original)
with ai_tab3:
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
    <p> Clinical Trial Data Quality Dashboard | Powered by AI Analytics</p>
    <p style="font-size: 12px; margin-top: 10px;">Data refreshed automatically | Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)