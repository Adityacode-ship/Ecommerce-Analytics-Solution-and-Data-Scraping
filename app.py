import streamlit as st
import pandas as pd
from data_cleaning import clean_data
from metrics import calculate_metrics
import eda_analysis as eda
import plotly.express as px
from powerbi_export import build_powerbi_excel
from google_maps_scraper import dataframe_to_excel_bytes, scrape_google_maps

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="◱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Custom Styles — Professional Modern Dark Theme with Light/Dark Contrast
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* ============================================================
       FONTS
       ============================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ============================================================
       ROOT VARIABLES
       ============================================================ */
    :root {
        --bg-primary: #0F172A;
        --bg-secondary: #1E293B;
        --bg-card: rgba(30, 41, 59, 0.7);
        --bg-card-hover: rgba(30, 41, 59, 0.9);
        --border-color: rgba(148, 163, 184, 0.15);
        --border-glow: rgba(6, 182, 212, 0.3);
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --accent-primary: #06B6D4;
        --accent-secondary: #0EA5E9;
        --accent-gradient: linear-gradient(135deg, #06B6D4, #0EA5E9);
        --accent-glow: rgba(6, 182, 212, 0.25);
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.4);
        --shadow-glow: 0 0 20px rgba(6, 182, 212, 0.15);
    }

    /* ============================================================
       MAIN APP CONTAINER
       ============================================================ */
    .stApp {
        background: var(--bg-primary);
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(6, 182, 212, 0.08), transparent),
            radial-gradient(ellipse 60% 40% at 80% 100%, rgba(14, 165, 233, 0.05), transparent);
    }

    /* ============================================================
       SIDEBAR
       ============================================================ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0C1322 0%, #111827 100%);
        border-right: 1px solid var(--border-color);
        padding-top: 1.5rem;
    }
    section[data-testid="stSidebar"] * {
        color: var(--text-secondary) !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    section[data-testid="stSidebar"] hr {
        border-color: var(--border-color);
        margin: 1.5rem 0;
    }
    section[data-testid="stSidebar"] .stFileUploader label {
        font-size: 0.875rem;
        font-weight: 500;
    }

    /* ============================================================
       SIDEBAR BOXED MENU (Radio) & SPACING
       ============================================================ */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 0.8rem;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 12px 16px;
        border-radius: 8px;
        transition: all 0.3s ease;
        margin: 0;
        cursor: pointer;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background-color: rgba(30, 41, 59, 0.8);
        border-color: rgba(6, 182, 212, 0.5);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transform: translateX(4px);
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
        margin-left: 0;
        font-weight: 600;
        font-size: 0.95rem;
        color: #F8FAFC !important;
    }
    /* Hide the default radio circle */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child {
        display: none;
    }
    /* Active State via :has() */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input[type="radio"]:checked) {
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.15) 0%, rgba(30, 41, 59, 0.4) 100%);
        border: 1px solid rgba(6, 182, 212, 0.6);
        border-left: 4px solid #06B6D4;
    }

    /* ============================================================
       TYPOGRAPHY
       ============================================================ */
    h1 {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.03em;
        line-height: 1.2;
        margin-bottom: 0.25rem !important;
    }
    h2 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        letter-spacing: -0.02em;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }
    h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
        letter-spacing: -0.01em;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    p, span, label, li {
        color: var(--text-secondary);
        line-height: 1.6;
    }

    /* ============================================================
       GLASS CARDS
       ============================================================ */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: var(--shadow-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-card:hover {
        border-color: var(--border-glow);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
        transform: translateY(-2px);
    }

    /* ============================================================
       METRIC CARDS (Custom HTML)
       ============================================================ */
    .metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 28px 24px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }
    .metric-card.revenue::before { background: var(--accent-gradient); }
    .metric-card.orders::before { background: linear-gradient(135deg, #10B981, #34D399); }
    .metric-card.aov::before { background: linear-gradient(135deg, #F59E0B, #FBBF24); }
    .metric-card:hover {
        border-color: var(--border-glow);
        box-shadow: var(--shadow-glow);
        transform: translateY(-3px);
    }
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 8px;
        display: block;
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    /* ============================================================
       STREAMLIT METRIC (built-in)
       ============================================================ */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetricDelta"] {
        font-weight: 600;
    }

    /* ============================================================
       BUTTONS — Primary
       ============================================================ */
    div.stButton > button {
        background: var(--accent-gradient);
        color: #FFFFFF;
        border: none;
        border-radius: var(--radius-sm);
        padding: 0.625rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        letter-spacing: 0.01em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(6, 182, 212, 0.25);
    }
    div.stButton > button:hover {
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.4);
        transform: translateY(-2px);
        color: #FFFFFF;
    }
    div.stButton > button:active {
        transform: translateY(0);
    }
    div.stButton > button:focus:not(:focus-visible) {
        color: #FFFFFF;
    }

    /* Form Submit Button */
    div.stFormSubmitButton > button {
        background: var(--accent-gradient);
        color: #FFFFFF !important;
        border: none;
        border-radius: var(--radius-sm);
        padding: 0.625rem 2rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(6, 182, 212, 0.25);
        width: 100%;
    }
    div.stFormSubmitButton > button:hover {
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.4);
        transform: translateY(-2px);
    }

    /* ============================================================
       BUTTONS — Download (Secondary)
       ============================================================ */
    div.stDownloadButton > button {
        background: transparent;
        color: var(--accent-primary) !important;
        border: 1px solid var(--border-glow);
        border-radius: var(--radius-sm);
        padding: 0.625rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div.stDownloadButton > button:hover {
        background: rgba(6, 182, 212, 0.1);
        border-color: var(--accent-primary);
        box-shadow: 0 0 12px rgba(6, 182, 212, 0.2);
        transform: translateY(-1px);
    }

    /* ============================================================
       INPUTS / SELECTS / SLIDERS
       ============================================================ */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        padding: 0.625rem 0.875rem !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px var(--accent-glow) !important;
    }
    .stSelectbox > div > div > div {
        background: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }

    /* ============================================================
       DATAFRAME
       ============================================================ */
    div[data-testid="stDataFrame"] {
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
        overflow: hidden;
    }

    /* ============================================================
       TABS
       ============================================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 0;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: auto;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        padding: 14px 24px;
        color: var(--text-muted) !important;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-secondary) !important;
        background: rgba(148, 163, 184, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: var(--accent-primary) !important;
        border-bottom: 2px solid var(--accent-primary) !important;
        font-weight: 600;
    }

    /* ============================================================
       ALERTS & INFO BOXES
       ============================================================ */
    div.stAlert > div[role="alert"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        border-radius: var(--radius-md);
        padding: 16px 20px;
    }

    /* ============================================================
       EXPANDER
       ============================================================ */
    details[data-testid="stExpander"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: 12px;
    }
    details[data-testid="stExpander"] summary {
        font-weight: 600;
        color: var(--text-primary);
        padding: 16px 20px;
    }

    /* ============================================================
       DIVIDERS
       ============================================================ */
    hr {
        border-color: var(--border-color) !important;
        margin: 2rem 0 !important;
    }

    /* ============================================================
       CAPTIONS
       ============================================================ */
    .stCaption, small {
        color: var(--text-muted) !important;
        font-size: 0.8rem;
    }

    /* ============================================================
       FILE UPLOADER
       ============================================================ */
    section[data-testid="stFileUploader"] {
        padding: 8px 0;
    }
    section[data-testid="stFileUploader"] > div {
        border-radius: var(--radius-md);
    }

    /* ============================================================
       SECTION HEADER (custom)
       ============================================================ */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-color);
    }
    .section-header .icon {
        font-size: 1.5rem;
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--accent-gradient);
        border-radius: var(--radius-sm);
        flex-shrink: 0;
    }
    .section-header .title {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }
    .section-header .subtitle {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-top: 2px;
    }

    /* ============================================================
       SPLASH SCREEN
       ============================================================ */
    .splash-screen {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        z-index: 9999999;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        animation: fadeOutSplash 0.6s ease-in-out 2.2s forwards;
    }
    .splash-content {
        text-align: center;
        font-family: 'Inter', sans-serif;
        animation: slideUpFade 0.8s ease-out;
    }
    .splash-icon {
        font-size: 3.5rem;
        margin-bottom: 16px;
        animation: pulseGlow 1.5s ease-in-out infinite;
    }
    .splash-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .splash-subtitle {
        font-size: 1rem;
        color: var(--text-muted);
        margin-top: 8px;
        font-weight: 400;
        letter-spacing: 0.05em;
    }
    .splash-dots {
        display: flex;
        gap: 8px;
        margin-top: 32px;
        justify-content: center;
    }
    .splash-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent-primary);
        animation: dotPulse 1.2s ease-in-out infinite;
    }
    .splash-dots span:nth-child(2) { animation-delay: 0.2s; }
    .splash-dots span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes fadeOutSplash {
        0% { opacity: 1; visibility: visible; }
        100% { opacity: 0; visibility: hidden; z-index: -1; }
    }
    @keyframes slideUpFade {
        0% { transform: translateY(30px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    @keyframes pulseGlow {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    @keyframes dotPulse {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }

    /* ============================================================
       LANDING / EMPTY STATE
       ============================================================ */
    .landing-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 60px 40px;
        text-align: center;
        max-width: 680px;
        margin: 3rem auto;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }
    .landing-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--accent-gradient);
    }
    .landing-icon {
        font-size: 4rem;
        margin-bottom: 20px;
        display: inline-block;
        animation: floatBounce 3s ease-in-out infinite;
    }
    .landing-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 12px;
        letter-spacing: -0.02em;
    }
    .landing-desc {
        font-size: 1rem;
        color: var(--text-secondary);
        max-width: 480px;
        margin: 0 auto 24px;
        line-height: 1.6;
    }
    .landing-steps {
        display: flex;
        justify-content: center;
        gap: 32px;
        margin-top: 32px;
        flex-wrap: wrap;
    }
    .landing-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    .step-number {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: var(--accent-gradient);
        color: white;
        font-weight: 700;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .step-text {
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    @keyframes floatBounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    /* ============================================================
       SCROLLBAR
       ============================================================ */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--text-muted);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }

    /* ============================================================
       FORM CONTAINER
       ============================================================ */
    div[data-testid="stForm"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 28px;
    }

    /* ============================================================
       CHECKBOX
       ============================================================ */
    .stCheckbox label {
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
    }

    /* ============================================================
       SLIDER
       ============================================================ */
    .stSlider label {
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
    }

    /* ============================================================
       SUCCESS / ERROR / WARNING STATES
       ============================================================ */
    div.stSuccess > div {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        color: #34D399 !important;
        border-radius: var(--radius-md) !important;
    }
    div.stError {
        border-radius: var(--radius-md) !important;
    }

    /* ============================================================
       RESPONSIVE SPACING UTILITIES
       ============================================================ */
    .spacer-sm { height: 12px; }
    .spacer-md { height: 24px; }
    .spacer-lg { height: 40px; }

</style>
""", unsafe_allow_html=True)

# Inject the Splash Screen HTML
st.markdown("""
<div class="splash-screen">
    <div class="splash-content">
        <div class="splash-icon">◱</div>
        <div class="splash-title">E-Commerce Analytics</div>
        <div class="splash-subtitle">POWERFUL INSIGHTS • BEAUTIFUL DATA</div>
        <div class="splash-dots">
            <span></span><span></span><span></span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ❖  Navigation")
    page = st.radio(
        "Select Page",
        ["◱  Analytics Dashboard", "⌖  Google Maps Scraper"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("### ☁  Data Upload")
    st.markdown("Upload your sales data to generate insights and analytics.")

    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"]
    )

    st.markdown("---")

    st.info(
        "**Note:** Ensure your file contains columns like `quantity`, `unit_price`, and `order_date`."
    )

    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

    st.markdown("### ⚙  Settings")
    show_raw = st.checkbox("Show Raw Data", value=True)

# =============================================================================
# PAGE: Google Maps Scraper
# =============================================================================
if page == "⌖  Google Maps Scraper":
    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    st.title("⌖  Google Maps Lead Scraper")
    st.markdown("##### Search Google Maps, collect business details, and download as Excel.")
    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

    st.markdown(
        "Search with queries like `cafe in nagpur` to collect phone, address, website, rating, "
        "and map links. Fields are captured when Google exposes them on the listing."
    )

    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

    with st.form("google_maps_scraper_form"):
        maps_col1, maps_col2, maps_col3 = st.columns([3, 1, 1], gap="medium")
        with maps_col1:
            maps_query = st.text_input("⌕  Search Query", value="cafe in nagpur")
        with maps_col2:
            maps_max_results = st.number_input("◱  Max Results", min_value=1, max_value=100, value=20, step=1)
        with maps_col3:
            maps_headless = st.checkbox("⎚  Headless", value=True)

        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        maps_delay = st.slider("◷  Delay between page loads (seconds)", min_value=1.0, max_value=5.0, value=2.0, step=0.5)
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        run_maps_scraper = st.form_submit_button("►  Scrape Google Maps")

    if run_maps_scraper:
        try:
            with st.spinner("⟳ Scraping Google Maps results..."):
                scraped_df = scrape_google_maps(
                    query=maps_query,
                    max_results=maps_max_results,
                    headless=maps_headless,
                    delay=maps_delay,
                )
            st.session_state["maps_scraper_results"] = scraped_df
            st.success(f"✓ Scraping finished. Collected **{len(scraped_df)}** rows.")
        except Exception as maps_error:
            st.error(f"✕ Google Maps scraping failed: {maps_error}")

    maps_results_df = st.session_state.get("maps_scraper_results")
    if maps_results_df is not None:
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.dataframe(maps_results_df, use_container_width=True)
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.download_button(
            label="⭳  Download Google Maps Results (.xlsx)",
            data=dataframe_to_excel_bytes(maps_results_df),
            file_name="google_maps_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.caption(
            "If some listings do not expose a website or phone number on Google Maps, those cells will be blank. "
            "Running with a slightly higher delay can improve stability."
        )

# =============================================================================
# PAGE: Analytics Dashboard
# =============================================================================
if page == "◱  Analytics Dashboard":
    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    st.title("◱  E-Commerce Analytics")
    st.markdown("##### Transform raw sales data into actionable insights — instantly.")
    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # File Upload — Data Processing
    # -----------------------------------------------------------------
    if uploaded_file:
        try:
            # Load Data
            with st.spinner("◫ Loading data..."):
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

            st.success("✓ File uploaded successfully!")
            st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

            # Tabs for better organization
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "⊟  Data Preview",
                "⌫  Data Cleaning",
                "◱  Exploratory Analysis",
                "⭈  KPI Dashboard",
                "⭱  Power BI Export"
            ])

            with tab1:
                st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("⊟  Raw Data Preview")
                st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
                st.dataframe(df.head(100), use_container_width=True)
                st.caption(f"Showing first 100 rows  •  Total rows: **{len(df):,}**  •  Columns: **{len(df.columns)}**")
                st.markdown('</div>', unsafe_allow_html=True)

            # Clean Data
            with st.spinner("⌫ Cleaning and validating data..."):
                cleaned_df = clean_data(df)

                # Enrich with Revenue (for EDA & Metrics)
                if "unit_price" in cleaned_df.columns and "quantity" in cleaned_df.columns:
                    cleaned_df["revenue"] = cleaned_df["unit_price"] * cleaned_df["quantity"]

            with tab2:
                st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("⌫  Cleaned Data Results")
                st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
                st.dataframe(cleaned_df.head(100), use_container_width=True)

                st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

                # Show what happened
                removed_rows = len(df) - len(cleaned_df)
                col1, col2, col3 = st.columns(3, gap="large")

                with col1:
                    st.metric("⭳  Original Rows", f"{len(df):,}")
                with col2:
                    st.metric("⍛  Rows Removed", f"{removed_rows:,}", delta_color="inverse")
                with col3:
                    st.metric("✓  Cleaned Rows", f"{len(cleaned_df):,}")

                st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

                # Download button
                csv = cleaned_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⭳  Download Cleaned Data (.csv)",
                    data=csv,
                    file_name="cleaned_sales_data.csv",
                    mime="text/csv",
                )
                st.markdown('</div>', unsafe_allow_html=True)

            # EDA Analysis
            with tab3:
                st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
                st.subheader("◱  Exploratory Data Analysis")

                if not cleaned_df.empty:
                    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)
                    col1, col2 = st.columns(2, gap="large")

                    with col1:
                        st.markdown("""
                        <div class="section-header">
                            <div class="icon">⊞</div>
                            <div><div class="title">Numerical Analysis</div></div>
                        </div>
                        """, unsafe_allow_html=True)
                        num_charts = eda.visualize_numerical_distributions(cleaned_df)
                        for col, figures in num_charts.items():
                            with st.expander(f"⭈  Distribution of {col}", expanded=True):
                                st.plotly_chart(figures['histogram'], use_container_width=True)
                                st.plotly_chart(figures['boxplot'], use_container_width=True)

                    with col2:
                        st.markdown("""
                        <div class="section-header">
                            <div class="icon">◱</div>
                            <div><div class="title">Categorical Analysis</div></div>
                        </div>
                        """, unsafe_allow_html=True)
                        cat_charts = eda.visualize_categorical_counts(cleaned_df)
                        if cat_charts:
                            for col, figure in cat_charts.items():
                                with st.expander(f"◱  Count of {col}", expanded=True):
                                    st.plotly_chart(figure, use_container_width=True)
                        else:
                            st.info("No categorical columns with low cardinality found.")

                    st.markdown("---")

                    st.markdown("""
                    <div class="section-header">
                        <div class="icon">▦</div>
                        <div><div class="title">Time Series Analysis</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    if "order_date" in cleaned_df.columns:
                        ts_charts = eda.visualize_time_series(cleaned_df, "order_date")
                        if ts_charts:
                            for col, figure in ts_charts.items():
                                st.plotly_chart(figure, use_container_width=True)
                    else:
                        st.warning("⚠️ No 'order_date' column found for time series analysis.")

                    st.markdown("---")

                    st.markdown("""
                    <div class="section-header">
                        <div class="icon">◈</div>
                        <div><div class="title">Correlation Heatmap</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    corr_plot = eda.visualize_correlation_heatmap(cleaned_df)
                    if corr_plot:
                        st.plotly_chart(corr_plot, use_container_width=True)
                    else:
                        st.info("Not enough numerical columns for correlation analysis.")

                else:
                    st.warning("⚠️ No data available for analysis.")

            # ── KPI Dashboard ────────────────────────────────────────────────
            with tab4:
                if not cleaned_df.empty:
                    metrics = calculate_metrics(cleaned_df)

                    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
                    st.subheader("⭈  Key Performance Indicators")
                    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

                    # Custom Metric Cards
                    col1, col2, col3 = st.columns(3, gap="large")

                    with col1:
                        st.markdown(f"""
                        <div class="metric-card revenue">
                            <span class="metric-icon">◆</span>
                            <div class="metric-label">Total Revenue</div>
                            <div class="metric-value">${metrics['Total Revenue']:,.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div class="metric-card orders">
                            <span class="metric-icon">▣</span>
                            <div class="metric-label">Total Orders</div>
                            <div class="metric-value">{metrics['Total Orders']:,}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"""
                        <div class="metric-card aov">
                            <span class="metric-icon">◎</span>
                            <div class="metric-label">Avg Order Value</div>
                            <div class="metric-value">${metrics['Average Order Value']:,.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

                    # Revenue Over Time Chart
                    if "order_date" in cleaned_df.columns and "revenue" in cleaned_df.columns:
                        st.markdown("""
                        <div class="section-header">
                            <div class="icon">⭈</div>
                            <div><div class="title">Revenue Over Time</div></div>
                        </div>
                        """, unsafe_allow_html=True)
                        daily_revenue = cleaned_df.groupby("order_date")["revenue"].sum()
                        fig_rev = px.line(
                            daily_revenue,
                            title='Revenue Trend',
                            template='plotly_dark',
                            color_discrete_sequence=['#06B6D4']
                        )
                        fig_rev.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(family='Inter', color='#94A3B8'),
                            title_font=dict(size=18, color='#F8FAFC'),
                            xaxis=dict(gridcolor='rgba(148,163,184,0.1)'),
                            yaxis=dict(gridcolor='rgba(148,163,184,0.1)'),
                        )
                        st.plotly_chart(fig_rev, use_container_width=True)
                else:
                    st.warning("⚠️ No data left after cleaning! Please check your input file format.")

            # ── Power BI Export ──────────────────────────────────────────────
            with tab5:
                st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)

                st.markdown("""
                <div class="section-header">
                    <div class="icon">⭱</div>
                    <div>
                        <div class="title">Export for Power BI</div>
                        <div class="subtitle">Download a ready-to-import Excel workbook for Power BI</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    "Download a ready-to-import Excel workbook containing **all analysis "
                    "sheets** pre-structured for Power BI. Each sheet becomes a separate "
                    "table — connect them in Power BI's Model view using `order_date` or "
                    "shared category columns."
                )

                st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

                st.markdown("#### 📑  Sheets Included in the Export")
                st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)

                sheet_info = [
                    ("Fact_Sales", "Full cleaned transactional dataset with revenue column"),
                    ("KPI_Summary", "Single table of all KPIs (revenue, orders, AOV, date range, etc.)"),
                    ("EDA_Numerical_Stats", "Descriptive statistics (mean, std, min, max, quartiles) per numeric column"),
                    ("EDA_Categorical_Counts", "Value counts for every categorical column"),
                    ("EDA_Time_Series", "Daily aggregated sums of all numeric columns"),
                    ("EDA_Monthly_Trend", "Monthly aggregated sums for trend analysis"),
                    ("EDA_Correlation_Matrix", "Pairwise Pearson correlation matrix between numeric columns"),
                    ("Rev_By_<column>", "Revenue breakdown per category column (up to 5 sheets)"),
                    ("Cht_Dist_<col>", "Histogram source data for each numeric column"),
                    ("Box_<col>", "Box plot source data and quartile stats for each numeric column"),
                    ("Cht_Cat_<col>", "Bar chart source data for each categorical column"),
                    ("Cht_TS_<col>", "Time series source data for each numeric column"),
                    ("Cht_Correlation", "Correlation heatmap source data"),
                    ("Cht_Revenue_Trend", "Revenue trend source data for the KPI dashboard chart"),
                    ("Cht_Rev_<col>", "Revenue-by-category chart source data (up to 5 sheets)"),
                    ("Chart_Gallery", "Embedded images of the same charts shown in the website for reference"),
                    ("PowerBI_Visual_Guide", "Recommended Power BI visual type and field mapping for each chart"),
                ]
                sheet_df = pd.DataFrame(sheet_info, columns=["Sheet Name", "Description"])
                st.dataframe(sheet_df, use_container_width=True, hide_index=True)

                st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

                if not cleaned_df.empty:
                    metrics = calculate_metrics(cleaned_df)
                    try:
                        with st.spinner("▣ Building Power BI workbook..."):
                            excel_bytes = build_powerbi_excel(cleaned_df.copy(), metrics)

                        st.success(
                            f"✓ Workbook ready — **{len(excel_bytes) / 1024:.1f} KB**. "
                            "Click the button below to download."
                        )
                        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
                        st.download_button(
                            label="⭳  Download Power BI Excel Workbook",
                            data=excel_bytes,
                            file_name="ecommerce_powerbi_export.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )

                        st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

                        st.markdown("""
                        <div class="section-header">
                            <div class="icon">ℹ</div>
                            <div><div class="title">How to Import into Power BI Desktop</div></div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown("""
1. Open **Power BI Desktop** → click **Get Data** → choose **Excel Workbook**.
2. Browse to `ecommerce_powerbi_export.xlsx` and click **Open**.
3. In the Navigator, tick **all the sheets** you want to load, then click **Load** (or **Transform Data** for further shaping).
4. In the **Model** view, create relationships between tables — e.g. link `Fact_Sales[order_date]` → `EDA_Time_Series[order_date]`.
5. Build your visuals using the loaded tables in the **Report** view.
                        """)
                    except Exception as export_err:
                        st.error(f"✕ Export failed: {export_err}")
                else:
                    st.warning("⚠️ No cleaned data available to export. Please upload a valid file.")

        except Exception as e:
            st.error(f"✕ An error occurred while processing the file: {str(e)}")

    else:
        # ── Beautiful Landing / Empty State ─────────────────────────────────
        st.markdown("""
        <div class="landing-card">
            <div class="landing-icon">◱</div>
            <div class="landing-title">Welcome to E-Commerce Analytics</div>
            <div class="landing-desc">
                Upload your sales data from the sidebar to unlock powerful insights,
                beautiful visualizations, and exportable reports.
            </div>
            <div class="landing-steps">
                <div class="landing-step">
                    <div class="step-number">1</div>
                    <div class="step-text">Open Sidebar</div>
                </div>
                <div class="landing-step">
                    <div class="step-number">2</div>
                    <div class="step-text">Upload CSV/Excel</div>
                </div>
                <div class="landing-step">
                    <div class="step-number">3</div>
                    <div class="step-text">Explore Insights</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

        # Example instructions
        with st.expander("ℹ  See File Format Instructions"):
            st.markdown("""
            Your uploaded file should contain at least the following columns:

            | Column | Type | Description |
            |--------|------|-------------|
            | `quantity` | Numeric | Number of items sold |
            | `unit_price` | Numeric | Price per item |
            | `order_date` | Date | Date of the order |
            | `order_id` | Text/Numeric | Unique identifier *(recommended)* |
            """)
