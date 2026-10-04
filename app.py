"""
app.py - cpmeta Web Application.
Competitive Programming Metacognition Notes Analyzer using local Ollama LLMs.
Minimal Neobrutalist UI with custom CSS, SQLite persistence, and multi-session synthesis.
"""

import json
import os
import streamlit as st
from datetime import datetime

import analyzer
import database

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="cpmeta // Metacognition Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
database.init_db()


def render_html(html_str: str) -> None:
    """
    Renders custom HTML in Streamlit.
    Strips leading and trailing whitespace from each line and filters empty lines,
    ensuring CommonMark never interprets indented HTML tags as preformatted code blocks (<pre><code>)
    nor closes HTML blocks prematurely on blank lines.
    """
    lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    cleaned = "\n".join(lines)
    st.markdown(cleaned, unsafe_allow_html=True)


# ==========================================
# MINIMAL NEOBRUTALIST CSS INJECTION
# ==========================================
NEOBRUTALIST_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Hide Streamlit default chrome */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stHeader"] {display: none !important;}
[data-testid="stSidebarHeader"] {display: none !important;}

/* Root CSS Variables */
:root {
    --bg-base: #101010;
    --bg-surface: #171717;
    --bg-surface-elevated: #202020;
    --border-color: #2E2E2E;
    --border-stark: #4A4A4A;
    --text-primary: #F0F0F0;
    --text-secondary: #9E9E9E;
    --accent: #D4FF00; /* Acid Lime */
    --accent-hover: #E2FF4D;
    --accent-text: #000000;
    --danger: #FF3B30;
    --warning: #FFB800;
    --success: #00E676;
    --shadow-hard: 3px 3px 0px #000000;
    --shadow-hard-accent: 3px 3px 0px #D4FF00;
}

/* Base Body Styling */
body, .stApp {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', -apple-system, sans-serif !important;
}

/* Fix Streamlit Icon & Material Font Ligatures */
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-symbols-outlined, [class*="material-symbols"], span[class*="icon"] {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    font-style: normal !important;
    font-weight: normal !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
}

/* Custom Sleek Monospace Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #111111;
}
::-webkit-scrollbar-thumb {
    background: #2E2E2E;
    border-radius: 0px;
}
::-webkit-scrollbar-thumb:hover {
    background: #444444;
}

/* Sidebar Styling & Overflow Handling */
[data-testid="stSidebar"] {
    background-color: #131313 !important;
    border-right: 2px solid var(--border-color) !important;
}

[data-testid="stSidebarContent"] {
    padding: 1rem 0.9rem 3.5rem 0.9rem !important;
    overflow-y: auto !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--text-primary) !important;
}

hr {
    margin: 0.85rem 0 !important;
    border: none !important;
    border-top: 1.5px solid #262626 !important;
}

/* Neobrutalist Nav Item Buttons (Custom Radio Overhaul) */
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 5px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
    background: #181818 !important;
    border: 1.5px solid #2B2B2B !important;
    border-radius: 0px !important;
    padding: 0.55rem 0.8rem !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.12s ease !important;
    box-shadow: 2px 2px 0px #000000 !important;
    width: 100% !important;
}

/* Hide the default round radio circle */
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
    border-color: #555555 !important;
    background: #202020 !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 3px 3px 0px #000000 !important;
}

/* Active Nav State */
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    border-left: 4px solid var(--accent) !important;
    border-color: var(--accent) #3A3A3A #3A3A3A var(--accent) !important;
    background: #222222 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #EDEDED !important;
    margin: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
    color: var(--accent) !important;
    font-weight: 700 !important;
}

/* Unified Page Header Component (Zero Strike-Through or Cutoff) */
.nb-page-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: flex-start !important;
    border-bottom: 2px solid var(--border-color) !important;
    padding-bottom: 0.85rem !important;
    margin-bottom: 1.4rem !important;
    gap: 1.5rem !important;
    flex-wrap: wrap !important;
}

.nb-page-header-text {
    flex: 1 1 500px !important;
}

.nb-page-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-primary) !important;
    text-transform: uppercase !important;
    margin: 0 0 0.35rem 0 !important;
    padding: 0 !important;
    border-bottom: none !important;
    line-height: 1.15 !important;
}

.nb-page-subtitle {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-secondary) !important;
    font-size: 0.92rem !important;
    line-height: 1.45 !important;
    margin: 0 !important;
}

.nb-page-header-badge {
    white-space: nowrap !important;
    padding-top: 0.2rem !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-primary) !important;
    text-transform: uppercase;
    border-bottom: none !important;
}

h2 {
    font-size: 1.35rem !important;
    margin-top: 1rem;
    margin-bottom: 0.8rem;
}

h3 {
    font-size: 1.1rem !important;
    margin-top: 0.8rem;
}

p, label, li, [data-testid="stMarkdownContainer"] p {
    font-family: 'Space Grotesk', -apple-system, sans-serif !important;
    color: var(--text-primary);
}

code, pre, .mono-text {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Native Container Border Wrapper as Neobrutalist Card */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--bg-surface) !important;
    border: 2px solid var(--border-color) !important;
    border-radius: 0px !important;
    box-shadow: var(--shadow-hard) !important;
    padding: 1.25rem 1.4rem 1.4rem 1.4rem !important;
    margin-bottom: 1.25rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border-stark) !important;
}

/* Neobrutalist HTML Cards */
.nb-card {
    background-color: var(--bg-surface);
    border: 2px solid var(--border-color);
    border-radius: 0px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-hard);
    transition: transform 0.15s ease, border-color 0.15s ease;
}

.nb-card:hover {
    border-color: var(--border-stark);
}

.nb-card-accent {
    border-left: 5px solid var(--accent) !important;
}

.nb-card-danger {
    border-left: 5px solid var(--danger) !important;
}

.nb-card-warning {
    border-left: 5px solid var(--warning) !important;
}

.nb-card-success {
    border-left: 5px solid var(--success) !important;
}

/* Hard Section Header */
.nb-header-tag {
    display: inline-block;
    background-color: var(--accent);
    color: #000000;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    text-transform: uppercase;
}

/* Monospace Structural Tags (NO BUBBLE PILLS) */
.nb-topic-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 4px 10px;
    margin: 3px 6px 3px 0;
    background: #111111;
    border: 1.5px solid var(--border-stark);
    color: #EDEDED;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-radius: 0px;
}

.nb-severity-high {
    background-color: #2D1414;
    border-color: var(--danger);
    color: #FFA5A0;
}

.nb-severity-med {
    background-color: #2D2510;
    border-color: var(--warning);
    color: #FFE699;
}

.nb-severity-low {
    background-color: #122818;
    border-color: var(--success);
    color: #A3FFC2;
}

/* Stall Point Row Box */
.nb-stall-item {
    background: #131313;
    border: 1.5px solid #282828;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    border-left: 3px solid var(--warning);
}

/* Key Value Row */
.nb-kv-row {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid #252525;
    padding: 0.4rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

.nb-kv-key {
    color: var(--text-secondary);
    text-transform: uppercase;
}

.nb-kv-val {
    font-weight: 600;
    color: var(--text-primary);
}

/* Form Inputs, Text Areas, Selects */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea,
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: #161616 !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 0px !important;
    color: #FFFFFF !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* Strictly hide text caret / cursor artifacts inside dropdown selects */
[data-baseweb="select"],
[data-baseweb="select"] *,
[data-baseweb="select"] input {
    caret-color: transparent !important;
    cursor: pointer !important;
}

textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    line-height: 1.4 !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
textarea:focus,
[data-baseweb="select"]:focus-within > div {
    border-color: var(--accent) !important;
    box-shadow: 2px 2px 0px var(--accent) !important;
    outline: none !important;
}

/* Number Input Step Buttons */
[data-testid="stNumberInput"] button {
    border-radius: 0px !important;
    border: 1px solid #333333 !important;
    background-color: #1F1F1F !important;
    color: #FFFFFF !important;
}

[data-testid="stNumberInput"] button:hover {
    background-color: #2A2A2A !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* Selectbox Dropdown Menu */
[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: #161616 !important;
    border: 2px solid #333333 !important;
    border-radius: 0px !important;
    box-shadow: 4px 4px 0px #000000 !important;
}

[data-baseweb="menu"] li {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #E0E0E0 !important;
    border-radius: 0px !important;
}

[data-baseweb="menu"] li:hover {
    background-color: #222222 !important;
    color: var(--accent) !important;
}

/* Checkbox Override */
[data-testid="stCheckbox"] label span[role="checkbox"] {
    border-radius: 0px !important;
    border: 1.5px solid #444444 !important;
    background-color: #161616 !important;
}

[data-testid="stCheckbox"] label span[role="checkbox"][aria-checked="true"] {
    background-color: var(--accent) !important;
    border-color: #000000 !important;
}

[data-testid="stCheckbox"] label span[role="checkbox"][aria-checked="true"] svg {
    color: #000000 !important;
    fill: #000000 !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background-color: #161616 !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 0px !important;
    margin-bottom: 0.7rem !important;
    box-shadow: 2px 2px 0px #000000 !important;
}

[data-testid="stExpander"] summary {
    border-radius: 0px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #E0E0E0 !important;
    padding: 0.55rem 0.8rem !important;
    gap: 0.5rem !important;
}

[data-testid="stExpander"] summary:hover {
    background-color: #1C1C1C !important;
    color: var(--accent) !important;
}

[data-testid="stExpander"] summary svg, [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
    color: var(--accent) !important;
    fill: var(--accent) !important;
}

/* ========================================= */
/* BUTTONS - TACTILE NEOBRUTALIST SYSTEM     */
/* ========================================= */

/* Primary Action Buttons (Acid Lime with Stark Black Text) */
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"] {
    background-color: var(--accent) !important;
    border: 2px solid #000000 !important;
    border-radius: 0px !important;
    box-shadow: 3px 3px 0px #000000 !important;
    padding: 0.65rem 1.4rem !important;
    transition: transform 0.08s ease, box-shadow 0.08s ease, background-color 0.08s ease !important;
    cursor: pointer !important;
}

/* Ensure ALL internal text nodes are pitch-black without stray shadows or borders */
div.stButton > button[kind="primary"] *,
div.stButton > button[data-testid="stBaseButton-primary"] * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    transform: none !important;
}

/* Hover State - ONLY applied to the button container */
div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background-color: var(--accent-hover) !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 5px 5px 0px #000000 !important;
}

div.stButton > button[kind="primary"]:hover *,
div.stButton > button[data-testid="stBaseButton-primary"]:hover * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    transform: none !important;
}

/* Active / Click State - ONLY applied to the button container */
div.stButton > button[kind="primary"]:active,
div.stButton > button[data-testid="stBaseButton-primary"]:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 1px 1px 0px #000000 !important;
}

div.stButton > button[kind="primary"]:active *,
div.stButton > button[data-testid="stBaseButton-primary"]:active * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    transform: none !important;
}

/* Secondary Buttons */
div.stButton > button[kind="secondary"],
div.stButton > button[data-testid="stBaseButton-secondary"] {
    background-color: #1A1A1A !important;
    color: #EDEDED !important;
    border: 1.5px solid #383838 !important;
    border-radius: 0px !important;
    box-shadow: 3px 3px 0px #000000 !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.1s ease !important;
}

div.stButton > button[kind="secondary"] *,
div.stButton > button[data-testid="stBaseButton-secondary"] * {
    color: inherit !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    transform: none !important;
}

div.stButton > button[kind="secondary"]:hover,
div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background-color: #242424 !important;
    border-color: var(--accent) !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 4px 4px 0px #000000 !important;
}

div.stButton > button[kind="secondary"]:hover *,
div.stButton > button[data-testid="stBaseButton-secondary"]:hover * {
    color: var(--accent) !important;
    -webkit-text-fill-color: var(--accent) !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    transform: none !important;
}

div.stButton > button[kind="secondary"]:active,
div.stButton > button[data-testid="stBaseButton-secondary"]:active {
    transform: translate(2px, 2px) !important;
    box-shadow: 1px 1px 0px #000000 !important;
}

/* Metric Override */
[data-testid="stMetric"] {
    background: #171717 !important;
    border: 2px solid var(--border-color) !important;
    padding: 0.8rem 1rem !important;
    box-shadow: var(--shadow-hard) !important;
    border-radius: 0px !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
}

[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 800 !important;
    color: var(--accent) !important;
}

/* Custom Warning / Alert Banner */
.nb-alert {
    background: #181408;
    border: 2px solid var(--warning);
    border-left: 6px solid var(--warning);
    padding: 0.9rem 1.2rem;
    margin-bottom: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    box-shadow: var(--shadow-hard);
}

.nb-alert-danger {
    background: #1F0D0D;
    border-color: var(--danger);
    border-left: 6px solid var(--danger);
}

.nb-alert-success {
    background: #0D1F12;
    border-color: var(--success);
    border-left: 6px solid var(--success);
}

/* Status indicator badge */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 8px;
    border: 1px solid currentColor;
}
</style>
"""

st.markdown(NEOBRUTALIST_CSS, unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "ollama_url" not in st.session_state:
    st.session_state["ollama_url"] = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = "qwen2.5-coder:7b"

if "current_analysis" not in st.session_state:
    st.session_state["current_analysis"] = None

if "current_form_data" not in st.session_state:
    st.session_state["current_form_data"] = {}

if "sample_notes_prefilled" not in st.session_state:
    st.session_state["sample_notes_prefilled"] = False

# ==========================================
# SIDEBAR NAVIGATION & SERVER STATUS
# ==========================================
with st.sidebar:
    render_html(
        """
        <div style="padding: 0.2rem 0 0.8rem 0; border-bottom: 2px solid #2B2B2B; margin-bottom: 1rem;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #D4FF00; letter-spacing: 0.15em;">ENGINEERING / LOG</div>
            <div style="font-size: 1.4rem; font-weight: 800; letter-spacing: -0.03em; color: #FFFFFF;">CPMETA</div>
            <div style="font-size: 0.72rem; color: #888888; font-family: 'JetBrains Mono', monospace;">METACOGNITION INTELLIGENCE</div>
        </div>
        """
    )

    page = st.radio(
        "NAVIGATION",
        ["📝 New Session", "📚 Past Sessions", "📊 Cumulative Analysis"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Connection and Model Status
    render_html("<div style='font-family: \"JetBrains Mono\", monospace; font-size: 0.78rem; font-weight: 700; color: #CCCCCC; margin-bottom: 0.5rem;'>🔌 INFERENCE CORE</div>")
    is_connected, status_msg, detected_models = analyzer.check_ollama_connection(st.session_state["ollama_url"])

    if is_connected:
        render_html(
            f"""
            <div class="status-indicator" style="color: #00E676; border-color: #00E676; margin-bottom: 0.5rem;">
                ● OLLAMA ONLINE
            </div>
            <div style="font-size: 0.72rem; color: #888888; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.6rem;">
                Target: {st.session_state['ollama_url']}
            </div>
            """
        )
    else:
        render_html(
            f"""
            <div class="status-indicator" style="color: #FF3B30; border-color: #FF3B30; margin-bottom: 0.5rem;">
                ✕ OFFLINE / UNREACHABLE
            </div>
            <div style="font-size: 0.72rem; color: #FF9999; font-family: 'JetBrains Mono', monospace; line-height: 1.3; margin-bottom: 0.6rem;">
                {status_msg}
            </div>
            """
        )
        with st.expander("🛠 Troubleshooting"):
            st.markdown(
                """
                1. Ensure Ollama is running:
                ```bash
                ollama serve
                ```
                2. Pull the coding LLM:
                ```bash
                ollama pull qwen2.5-coder:7b
                ```
                """
            )

    # Dynamic Model Selection (Strictly Downloaded/Available Models Only)
    available_models_list = [m for m in detected_models if m.strip()]
    has_downloaded_models = len(available_models_list) > 0

    if not has_downloaded_models:
        available_models_list = ["No models downloaded"]
        selected_model_idx = 0
        st.session_state["selected_model"] = "No models downloaded"
    else:
        if st.session_state.get("selected_model") in available_models_list:
            selected_model_idx = available_models_list.index(st.session_state["selected_model"])
        else:
            selected_model_idx = 0
            st.session_state["selected_model"] = available_models_list[0]

    selected_model = st.selectbox(
        "ACTIVE MODEL",
        available_models_list,
        index=selected_model_idx,
        disabled=not has_downloaded_models,
        help="Dynamic list of models downloaded and available in Ollama",
    )
    st.session_state["selected_model"] = selected_model

    if st.button("🔄 Refresh Models", use_container_width=True, type="secondary", help="Rescan Ollama for newly downloaded models"):
        st.rerun()

    # Collapsible Endpoint Settings
    with st.expander("⚙️ Server Settings"):
        custom_endpoint = st.text_input(
            "Ollama Base URL",
            value=st.session_state["ollama_url"],
            help="E.g. http://localhost:11434 or your Ngrok / Cloudflare tunnel URL",
        )
        if st.button("Update Endpoint", use_container_width=True, type="secondary"):
            st.session_state["ollama_url"] = custom_endpoint
            st.rerun()

    # Fast Sample Seeder in Sidebar for Quick Testing
    st.markdown("---")
    render_html(
        """
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #888888; margin-bottom: 0.4rem; text-transform: uppercase;">
            QUICK EVALUATION TOOL
        </div>
        """
    )
    if st.button("⚡ Seed 3 Sample Sessions", use_container_width=True, type="secondary", help="Loads 3 realistic solved/failed sessions to test analytics"):
        added = database.seed_sample_sessions()
        st.toast(f"Added {added} realistic sessions to database!", icon="✅")
        st.rerun()


# ==========================================
# PAGE 1: 📝 NEW SESSION
# ==========================================
if page == "📝 New Session":
    render_html(
        """
        <div class="nb-page-header">
            <div class="nb-page-header-text">
                <h1 class="nb-page-title">LOG & ANALYZE SESSION</h1>
                <div class="nb-page-subtitle">
                    Input your raw timestamped problem-solving metacognition notes. The local LLM will deconstruct algorithmic insights, exact stall root causes, and behavioral habits.
                </div>
            </div>
            <div class="nb-page-header-badge">
                <span class="nb-header-tag">INFERENCE: OLLAMA / STRICT JSON</span>
            </div>
        </div>
        """
    )

    if not is_connected:
        render_html(
            f"""
            <div class="nb-alert nb-alert-danger">
                [!] OLLAMA SERVER UNREACHABLE AT <code>{st.session_state['ollama_url']}</code><br>
                Please verify that Ollama is active (`ollama serve`) or configure a remote tunnel in the sidebar.
            </div>
            """
        )

    # Form layout wrapped in native bordered container
    with st.container(border=True):
        # Row 1: Problem metadata with aligned Outcome dropdown (eliminates vertical misalignment)
        col1, col2, col3, col4 = st.columns([1.4, 2.5, 1.0, 1.4])

        platforms = ["LeetCode", "Codeforces", "AtCoder", "CodeChef", "CSES", "HackerRank", "Custom / Other"]
        default_plat_idx = 0
        if st.session_state.get("sample_platform") in platforms:
            default_plat_idx = platforms.index(st.session_state["sample_platform"])

        with col1:
            platform = st.selectbox("PLATFORM", platforms, index=default_plat_idx)

        with col2:
            problem_title = st.text_input(
                "PROBLEM TITLE",
                value=st.session_state.get("sample_title", ""),
                placeholder="e.g. 992. Subarrays with K Different Integers",
            )

        with col3:
            time_taken = st.number_input(
                "TIME (MIN)",
                min_value=1,
                max_value=300,
                value=st.session_state.get("sample_time", 25),
            )

        with col4:
            outcome_options = ["SOLVED / ACCEPTED", "UNSOLVED / TIMED OUT"]
            default_outcome_idx = 0 if st.session_state.get("sample_solved", True) else 1
            outcome_select = st.selectbox("OUTCOME STATUS", outcome_options, index=default_outcome_idx)
            solved = (outcome_select == "SOLVED / ACCEPTED")

        # Row 2: Model selector on left, Load Sample Case button aligned on right
        col_mod, col_sample = st.columns([3, 1.3])
        with col_mod:
            active_model = st.selectbox(
                "MODEL FOR THIS RUN",
                available_models_list,
                index=available_models_list.index(st.session_state["selected_model"])
                if st.session_state["selected_model"] in available_models_list
                else 0,
                disabled=not has_downloaded_models,
                help="Dynamically loaded from installed Ollama models",
            )
            st.session_state["selected_model"] = active_model
        with col_sample:
            render_html("<div style='margin-top: 1.7rem;'></div>")
            if st.button("📋 Load Sample Case", use_container_width=True, type="secondary", help="Fills inputs with a realistic Competitive Programming scenario"):
                st.session_state["sample_platform"] = "LeetCode"
                st.session_state["sample_title"] = "992. Subarrays with K Different Integers"
                st.session_state["sample_statement"] = (
                    "Given an integer array nums and an integer k, return the number of good subarrays of nums. "
                    "A good array is an array where the number of different integers in that array is exactly k. "
                    "Constraints: 1 <= nums.length <= 2 * 10^4, 1 <= nums[i], k <= nums.length."
                )
                st.session_state["sample_notes"] = (
                    "0:00 - read problem. count contiguous subarrays with exactly k distinct integers.\n"
                    "0:02 - initial thought: standard sliding window with two pointers and frequency map.\n"
                    "0:06 - issue: standard sliding window expands right and shrinks left when distinct > k, but how to count *exact* k without missing valid smaller left bounds?\n"
                    "0:12 - stuck: trying to move left pointer forward and back to count valid windows. Got messy with duplicated counts.\n"
                    "0:18 - realized exact(k) is hard because window condition isn't strictly monotonic for exact match.\n"
                    "0:21 - breakthrough: exact(k) = atMost(k) - atMost(k - 1)!\n"
                    "0:25 - wrote helper atMost(k) which is strictly monotonic: for each right pointer, valid left pointers are (right - left + 1).\n"
                    "0:29 - tested on sample cases. edge case with k=1 works smoothly.\n"
                    "0:32 - submitted -> Accepted! Runtime 45ms, Beats 92%."
                )
                st.session_state["sample_solved"] = True
                st.session_state["sample_time"] = 32
                st.session_state["sample_notes_prefilled"] = True
                st.rerun()

        # Row 3: Problem statement
        problem_statement = st.text_area(
            "PROBLEM STATEMENT & CONSTRAINTS",
            value=st.session_state.get("sample_statement", ""),
            height=120,
            placeholder="Paste problem description, input/output limits, and constraints here...",
        )

        # Row 4: Raw notes
        notes_placeholder = (
            "0:00 - read problem statement, noticing constraints...\n"
            "0:03 - thought about 2D DP, state dp[i][j]...\n"
            "0:07 - stuck on transition: how to avoid O(N^3)?\n"
            "0:14 - noticed monotonic property, switching to sliding window...\n"
            "0:22 - bug on off-by-one with 0-indexed arrays...\n"
            "0:26 - fixed edge case, submitted -> Accepted."
        )

        raw_notes = st.text_area(
            "TIMESTAMPED THINKING NOTES (METACOGNITION LOG)",
            value=st.session_state.get("sample_notes", ""),
            height=180,
            placeholder=notes_placeholder,
            help="Record what you thought, when you pivoted, what confused you, and what bugs you faced.",
        )

        render_html("<div style='margin-top: 0.8rem;'></div>")
        analyze_clicked = st.button("⚡ ANALYZE THINKING PROCESS", type="primary", use_container_width=True)

    # Trigger LLM Analysis
    if analyze_clicked:
        if not has_downloaded_models or active_model == "No models downloaded":
            st.error("No downloaded models found in Ollama. Please run `ollama pull qwen2.5-coder:7b` in a terminal first, then click Refresh.")
        elif not problem_statement.strip() or not raw_notes.strip():
            st.error("Please provide both the Problem Statement and your Timestamped Thinking Notes.")
        else:
            with st.spinner(f"Querying {active_model} at {st.session_state['ollama_url']}... Deconstructing thinking notes..."):
                analysis_result = analyzer.analyze_single_problem(
                    problem_statement=problem_statement,
                    raw_notes=raw_notes,
                    platform=platform,
                    problem_title=problem_title or "Untitled Problem",
                    solved=solved,
                    time_taken_minutes=time_taken,
                    model_name=active_model,
                    base_url=st.session_state["ollama_url"],
                )

                st.session_state["current_analysis"] = analysis_result
                st.session_state["current_form_data"] = {
                    "platform": platform,
                    "problem_title": problem_title or "Untitled Problem",
                    "problem_statement": problem_statement,
                    "raw_notes": raw_notes,
                    "solved": solved,
                    "time_taken_minutes": time_taken,
                }
                st.toast("Analysis complete!", icon="🧠")

    # Display Analysis Results
    if st.session_state.get("current_analysis"):
        analysis = st.session_state["current_analysis"]
        is_fallback = analysis.get("_is_fallback", False)

        st.markdown("---")
        render_html("<h2>COACH ANALYSIS & METRICS</h2>")

        if is_fallback:
            render_html(
                f"""
                <div class="nb-alert nb-alert-warning">
                    <strong>PARSING NOTICE:</strong> The model responded, but the JSON parser had to fall back. Raw output is logged below.<br>
                    <code>Error: {analysis.get('_error', 'Invalid JSON structure')}</code>
                </div>
                """
            )

        prob_analysis = analysis.get("problem_analysis", {})
        thinking = analysis.get("thinking_analysis", {})
        recs = analysis.get("recommendations", {})

        # Card 1: Problem Architecture
        topics_tags = ''.join([f'<span class="nb-topic-tag">{topic}</span>' for topic in prob_analysis.get('core_topics', ['None'])])
        render_html(
            f"""
            <div class="nb-card nb-card-accent">
                <span class="nb-header-tag">01 // PROBLEM ARCHITECTURE</span>
                <div style="font-size: 1.15rem; font-weight: 700; margin: 0.5rem 0 0.8rem 0;">
                    {prob_analysis.get('difficulty_tier', 'Difficulty: Unspecified')}
                </div>
                <div style="margin-bottom: 0.8rem;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #888888; margin-bottom: 4px;">CORE TOPICS / PATTERNS:</div>
                    {topics_tags}
                </div>
                <div style="background: #111111; border: 1.5px solid #2B2B2B; padding: 0.8rem 1rem;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #D4FF00; margin-bottom: 4px;">KEY INSIGHT:</div>
                    <div style="font-size: 0.95rem; color: #EDEDED; line-height: 1.45;">
                        {prob_analysis.get('key_insight', 'None recorded.')}
                    </div>
                </div>
            </div>
            """
        )

        # Card 2: Metacognitive Thinking Breakdown
        correct_moves_html = "".join(
            [
                f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.85rem; margin-bottom: 0.45rem; color: #CCCCCC; border-left: 2px solid #00E676; padding-left: 8px;">{move}</div>'
                for move in thinking.get("correct_moves", [])
            ]
        ) or "<div style='color: #666; font-size: 0.85rem;'>None logged.</div>"

        behaviors_html = "".join(
            [
                f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.85rem; margin-bottom: 0.45rem; color: #CCCCCC; border-left: 2px solid #D4FF00; padding-left: 8px;">{b}</div>'
                for b in thinking.get("behavioral_observations", [])
            ]
        ) or "<div style='color: #666; font-size: 0.85rem;'>None logged.</div>"

        stalls_html = "".join(
            [
                f'<div class="nb-stall-item">'
                f'<div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
                f'<span style="font-family: \'JetBrains Mono\', monospace; font-weight: 700; color: #FFB800; font-size: 0.82rem;">'
                f'{sp.get("timestamp_range", "Unknown Time")} ({sp.get("duration_minutes", "?")} min)'
                f'</span>'
                f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 0.75rem; color: #FF9999; text-transform: uppercase;">'
                f'CAUSE: {sp.get("root_cause", "General confusion")}'
                f'</span>'
                f'</div>'
                f'<div style="color: #DDDDDD; font-size: 0.88rem; line-height: 1.4;">'
                f'{sp.get("description", "")}'
                f'</div>'
                f'</div>'
                for sp in thinking.get("stall_points", [])
            ]
        ) or "<div style='color: #666; font-size: 0.85rem;'>No major stall points detected. Smooth execution.</div>"

        render_html(
            f"""
            <div class="nb-card">
                <span class="nb-header-tag">02 // THINKING PROCESS & STALL POINTS</span>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 0.8rem; margin-bottom: 1.2rem;">
                    <div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 700; color: #00E676; margin-bottom: 0.6rem;">
                            [+] CORRECT INTUITIONS & STRONG MOVES
                        </div>
                        {correct_moves_html}
                    </div>
                    <div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 700; color: #D4FF00; margin-bottom: 0.6rem;">
                            [!] BEHAVIORAL OBSERVATIONS
                        </div>
                        {behaviors_html}
                    </div>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 700; color: #FFB800; margin-bottom: 0.6rem;">
                    [▲] STALL POINTS & BOTTLENECKS
                </div>
                {stalls_html}
            </div>
            """
        )

        # Card 3: Actionable Recommendations
        rec_tags = ''.join([f'<span class="nb-topic-tag nb-severity-med">{t}</span>' for t in recs.get('topics_to_strengthen', ['General Invariants'])])
        sim_tags = ''.join([f'<span class="nb-topic-tag">{p}</span>' for p in recs.get('similar_problems', ['None recommended'])])
        render_html(
            f"""
            <div class="nb-card nb-card-warning">
                <span class="nb-header-tag">03 // COACH ACTION PLAN & SIMILAR PROBLEMS</span>
                <div style="margin-top: 0.6rem; margin-bottom: 0.8rem;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #888888; margin-bottom: 4px;">RECOMMENDED DRILLS:</div>
                    {rec_tags}
                </div>
                <div style="background: #111111; border: 1.5px solid #2B2B2B; padding: 0.8rem 1rem; margin-bottom: 0.8rem;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #FFB800; margin-bottom: 4px;">BEHAVIORAL ADVICE:</div>
                    <div style="font-size: 0.95rem; color: #EDEDED; line-height: 1.45;">
                        {recs.get('behavioral_advice', 'No advice generated.')}
                    </div>
                </div>
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #888888; margin-bottom: 4px;">SIMILAR PROBLEMS TO PRACTICE:</div>
                    {sim_tags}
                </div>
            </div>
            """
        )

        # Save to Database Button
        render_html("<br>")
        col_save_1, col_save_2 = st.columns([2, 1])
        with col_save_1:
            if st.button("💾 SAVE THIS SESSION TO ARCHIVE", type="primary", use_container_width=True):
                fdata = st.session_state["current_form_data"]
                saved_id = database.save_session(
                    platform=fdata.get("platform", "LeetCode"),
                    problem_title=fdata.get("problem_title", "Untitled"),
                    problem_statement=fdata.get("problem_statement", ""),
                    raw_notes=fdata.get("raw_notes", ""),
                    analysis_json=json.dumps(st.session_state["current_analysis"]),
                    solved=fdata.get("solved", True),
                    time_taken_minutes=fdata.get("time_taken_minutes", 0),
                )
                st.success(f"Session successfully saved to database with ID #{saved_id}!")
                st.toast(f"Session #{saved_id} archived!", icon="💾")


# ==========================================
# PAGE 2: 📚 PAST SESSIONS
# ==========================================
elif page == "📚 Past Sessions":
    render_html(
        """
        <div class="nb-page-header">
            <div class="nb-page-header-text">
                <h1 class="nb-page-title">PRACTICE ARCHIVE</h1>
                <div class="nb-page-subtitle">
                    Review your history of solved/unsolved problems, inspected stall points, and individual problem analyses.
                </div>
            </div>
            <div class="nb-page-header-badge">
                <span class="nb-header-tag">SQLITE STORE</span>
            </div>
        </div>
        """
    )

    all_sessions = database.get_all_sessions()

    if not all_sessions:
        render_html(
            """
            <div class="nb-alert nb-alert-warning">
                <strong>NO SESSIONS RECORDED YET.</strong><br>
                Log a new session from the "📝 New Session" tab or click below to seed sample sessions.
            </div>
            """
        )
        if st.button("⚡ Seed 3 Sample Sessions Now", type="secondary", use_container_width=False):
            database.seed_sample_sessions()
            st.rerun()
    else:
        # Top Metrics KPI Bar
        total_count = len(all_sessions)
        solved_count = sum(1 for s in all_sessions if s["solved"])
        solve_rate = round((solved_count / total_count) * 100, 1)
        total_minutes = sum(s["time_taken_minutes"] for s in all_sessions)
        avg_minutes = round(total_minutes / total_count, 1) if total_count else 0

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("TOTAL SESSIONS", total_count)
        with m2:
            st.metric("SOLVED RATE", f"{solve_rate}%", f"{solved_count}/{total_count}")
        with m3:
            st.metric("TOTAL PRACTICE TIME", f"{total_minutes}m", f"{round(total_minutes/60, 1)} hrs")
        with m4:
            st.metric("AVG TIME / PROBLEM", f"{avg_minutes}m")

        render_html("<br>")

        # Filters Toolbar
        col_f1, col_f2, col_f3 = st.columns([2, 1.5, 1.5])
        with col_f1:
            search_query = st.text_input("SEARCH SESSIONS", placeholder="Filter by title or topic...").strip().lower()
        with col_f2:
            platforms = ["All Platforms"] + sorted(list(set(s["platform"] for s in all_sessions)))
            plat_filter = st.selectbox("PLATFORM", platforms)
        with col_f3:
            status_filter = st.selectbox("STATUS", ["All", "Solved Only", "Unsolved Only"])

        # Filter logic
        filtered = []
        for s in all_sessions:
            if plat_filter != "All Platforms" and s["platform"] != plat_filter:
                continue
            if status_filter == "Solved Only" and not s["solved"]:
                continue
            if status_filter == "Unsolved Only" and s["solved"]:
                continue
            if search_query:
                title = s["problem_title"].lower()
                topics = " ".join(s.get("analysis", {}).get("problem_analysis", {}).get("core_topics", [])).lower()
                if search_query not in title and search_query not in topics:
                    continue
            filtered.append(s)

        render_html(
            f"""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #888888; margin-bottom: 1rem;">
                SHOWING {len(filtered)} OF {total_count} RECORDED SESSIONS
            </div>
            """
        )

        # Render list of cards
        for s in filtered:
            s_id = s["id"]
            analysis = s.get("analysis", {})
            prob_analysis = analysis.get("problem_analysis", {})
            thinking = analysis.get("thinking_analysis", {})
            recs = analysis.get("recommendations", {})

            status_style = "nb-card-success" if s["solved"] else "nb-card-danger"
            status_text = "SOLVED" if s["solved"] else "UNSOLVED / TIMED OUT"
            status_color = "#00E676" if s["solved"] else "#FF3B30"

            topics = prob_analysis.get("core_topics", [])
            topics_html = "".join([f'<span class="nb-topic-tag">{t}</span>' for t in topics])

            render_html(
                f"""
                <div class="nb-card {status_style}" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;">
                        <div>
                            <span style="font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 0.8rem; color: #888888;">
                                #{s_id} // {s['created_at']}
                            </span>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin: 3px 0;">
                                {s['problem_title']}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 0.85rem; color: {status_color}; border: 1.5px solid {status_color}; padding: 2px 8px;">
                                {status_text}
                            </span>
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #A0A0A0; margin-top: 4px;">
                                {s['platform']} • {s['time_taken_minutes']} min
                            </div>
                        </div>
                    </div>
                    <div style="margin-top: 0.6rem;">
                        {topics_html if topics_html else '<span style="color: #666; font-size: 0.8rem;">No topics logged</span>'}
                    </div>
                </div>
                """
            )

            # Details expander & delete button
            exp_col, del_col = st.columns([5, 1])
            with exp_col:
                with st.expander(f"Inspect Session #{s_id} Full Analysis & Raw Notes"):
                    tab_an, tab_prob, tab_notes = st.tabs(["📊 Deconstructed Analysis", "📜 Problem Statement", "📝 Raw Notes"])

                    with tab_an:
                        st.markdown(f"**Difficulty / Tier:** `{prob_analysis.get('difficulty_tier', 'N/A')}`")
                        st.markdown(f"**Key Insight:** {prob_analysis.get('key_insight', 'N/A')}")
                        st.markdown("---")

                        c_m, c_b = st.columns(2)
                        with c_m:
                            st.markdown("**Correct Moves:**")
                            for m in thinking.get("correct_moves", []):
                                st.markdown(f"- {m}")
                        with c_b:
                            st.markdown("**Behavioral Observations:**")
                            for b in thinking.get("behavioral_observations", []):
                                st.markdown(f"- {b}")

                        st.markdown("---")
                        st.markdown("**Stall Points:**")
                        for sp in thinking.get("stall_points", []):
                            st.markdown(
                                f"- **[{sp.get('timestamp_range', '?')}] ({sp.get('duration_minutes', 0)} min)**: {sp.get('description', '')} *(Root Cause: {sp.get('root_cause', '')})*"
                            )

                        st.markdown("---")
                        st.markdown(f"**Behavioral Advice:** {recs.get('behavioral_advice', 'N/A')}")
                        st.markdown(f"**Similar Problems:** {', '.join(recs.get('similar_problems', []))}")

                    with tab_prob:
                        st.code(s["problem_statement"], language="text")

                    with tab_notes:
                        st.code(s["raw_notes"], language="text")

            with del_col:
                if st.button("DELETE", key=f"del_{s_id}", type="secondary", help=f"Permanently delete session #{s_id}"):
                    deleted = database.delete_session(s_id)
                    if deleted:
                        st.toast(f"Session #{s_id} deleted.", icon="🗑️")
                        st.rerun()


# ==========================================
# PAGE 3: 📊 CUMULATIVE ANALYSIS
# ==========================================
elif page == "📊 Cumulative Analysis":
    render_html(
        """
        <div class="nb-page-header">
            <div class="nb-page-header-text">
                <h1 class="nb-page-title">CUMULATIVE SYNTHESIS</h1>
                <div class="nb-page-subtitle">
                    Aggregates your historical stall points, topic frequencies, and behavioral tendencies across multiple practice sessions to produce a prioritized study plan.
                </div>
            </div>
            <div class="nb-page-header-badge">
                <span class="nb-header-tag">LONGITUDINAL PATTERN RECOGNITION</span>
            </div>
        </div>
        """
    )

    summary_data = database.get_cumulative_summary()
    session_count = summary_data.get("session_count", 0)

    # 3-Session Warning Banner specification
    if session_count < 3:
        render_html(
            f"""
            <div class="nb-alert nb-alert-warning">
                <strong>[!] INSUFFICIENT DATA FOR RELIABLE PATTERN SYNTHESIS</strong><br>
                Cumulative analysis requires at least 3 logged practice sessions to identify recurring behavioral traps and topic weaknesses.<br>
                <strong>Current sessions: {session_count} / 3.</strong>
            </div>
            """
        )

        col_seed_a, _ = st.columns([2, 2])
        with col_seed_a:
            if st.button("⚡ Seed 3 Realistic Sample Sessions to Test", type="secondary", use_container_width=True):
                database.seed_sample_sessions()
                st.rerun()

    # Model & Execution Controller in native bordered container
    with st.container(border=True):
        c_inf1, c_inf2 = st.columns([3, 1.5])
        with c_inf1:
            render_html(
                f"""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #CCCCCC;">
                    DATASET STATUS: <strong>{session_count} SESSIONS</strong> ({summary_data.get('solved_count', 0)} Solved, {summary_data.get('unsolved_count', 0)} Unsolved, {summary_data.get('total_time_minutes', 0)} min total)
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #888888; margin-top: 4px;">
                    Identified Topics: {len(summary_data.get('topics_tackled', []))} unique | Stall Root Causes: {len(summary_data.get('stall_causes', []))} unique
                </div>
                """
            )
        with c_inf2:
            model_for_cumulative = st.selectbox(
                "SYNTHESIS MODEL",
                available_models_list,
                index=available_models_list.index(st.session_state["selected_model"])
                if st.session_state["selected_model"] in available_models_list
                else 0,
                disabled=not has_downloaded_models,
                help="Dynamically loaded from installed Ollama models",
            )
            st.session_state["selected_model"] = model_for_cumulative

        render_html("<div style='margin-top: 0.8rem;'></div>")
        run_cumulative_clicked = st.button("🚀 RUN CUMULATIVE ANALYSIS", type="primary", use_container_width=True)

    # Trigger Cumulative Analysis
    if run_cumulative_clicked:
        if not has_downloaded_models or model_for_cumulative == "No models downloaded":
            st.error("No downloaded models found in Ollama. Please run `ollama pull qwen2.5-coder:7b` in a terminal first, then click Refresh.")
        elif session_count == 0:
            st.error("No sessions found in database. Please log sessions or click Seed Sample Sessions.")
        else:
            with st.spinner(f"Aggregating {session_count} sessions into context window and querying {model_for_cumulative}..."):
                cumulative_result = analyzer.analyze_cumulative(
                    sessions_data=summary_data,
                    model_name=model_for_cumulative,
                    base_url=st.session_state["ollama_url"],
                )
                st.session_state["cumulative_analysis_result"] = cumulative_result
                st.toast("Cumulative synthesis complete!", icon="📈")

    # Display Cumulative Analysis Results
    if st.session_state.get("cumulative_analysis_result"):
        res = st.session_state["cumulative_analysis_result"]
        is_fallback = res.get("_is_fallback", False)

        if is_fallback:
            render_html(
                f"""
                <div class="nb-alert nb-alert-warning">
                    <strong>PARSING NOTICE:</strong> The model responded, but the JSON parser had to fall back. Raw output is logged below.<br>
                    <code>Error: {res.get('_error', 'Invalid JSON structure')}</code>
                </div>
                """
            )

        # 1. Overall Executive Assessment
        render_html(
            f"""
            <div class="nb-card nb-card-accent">
                <span class="nb-header-tag">HEAD COACH EXECUTIVE ASSESSMENT</span>
                <div style="font-size: 1.05rem; line-height: 1.5; color: #F0F0F0; margin-top: 0.6rem;">
                    {res.get('overall_assessment', 'No assessment available.')}
                </div>
            </div>
            """
        )

        col_w, col_s = st.columns(2)

        # 2. Weak Topics (with severity badges)
        with col_w:
            weak_topics = res.get("weak_topics", [])
            weak_items_html = ""
            if weak_topics:
                for w in weak_topics:
                    sev = (w.get("severity") or "Medium").upper()
                    sev_class = "nb-severity-high" if "HIGH" in sev else ("nb-severity-low" if "LOW" in sev else "nb-severity-med")
                    weak_items_html += (
                        f'<div style="border-bottom: 1px solid #2B2B2B; padding: 0.6rem 0;">'
                        f'<div style="display: flex; justify-content: space-between; align-items: baseline;">'
                        f'<span style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF;">'
                        f'{w.get("topic", "Topic")}'
                        f'</span>'
                        f'<span class="nb-topic-tag {sev_class}" style="font-size: 0.7rem;">'
                        f'{sev} • {w.get("frequency", 1)}x'
                        f'</span>'
                        f'</div>'
                        f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.78rem; color: #9E9E9E; margin-top: 4px;">'
                        f'{w.get("evidence", "")}'
                        f'</div>'
                        f'</div>'
                    )
            else:
                weak_items_html = "<div style='color: #666; font-size: 0.85rem;'>No persistent weak topics flagged.</div>"

            render_html(
                f"""
                <div class="nb-card nb-card-danger">
                    <span class="nb-header-tag" style="background: #FF3B30; color: #FFF;">TOPIC WEAKNESS PROFILE</span>
                    {weak_items_html}
                </div>
                """
            )

        # 3. Strong Topics
        with col_s:
            strong_topics = res.get("strong_topics", [])
            strong_items_html = ""
            if strong_topics:
                for s in strong_topics:
                    strong_items_html += (
                        f'<div style="border-bottom: 1px solid #2B2B2B; padding: 0.6rem 0;">'
                        f'<div style="display: flex; justify-content: space-between; align-items: baseline;">'
                        f'<span style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF;">'
                        f'{s.get("topic", "Topic")}'
                        f'</span>'
                        f'<span class="nb-topic-tag nb-severity-low" style="font-size: 0.7rem;">'
                        f'{s.get("frequency", 1)}x MASTERED'
                        f'</span>'
                        f'</div>'
                        f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.78rem; color: #9E9E9E; margin-top: 4px;">'
                        f'{s.get("evidence", "")}'
                        f'</div>'
                        f'</div>'
                    )
            else:
                strong_items_html = "<div style='color: #666; font-size: 0.85rem;'>No strong topics identified yet.</div>"

            render_html(
                f"""
                <div class="nb-card nb-card-success">
                    <span class="nb-header-tag" style="background: #00E676; color: #000;">PROVEN TOPIC STRENGTHS</span>
                    {strong_items_html}
                </div>
                """
            )

        # 4. Longitudinal Behavioral Patterns
        patterns = res.get("behavioral_patterns", [])
        patterns_html = ""
        if patterns:
            for p in patterns:
                ptype = (p.get("type") or "habit").upper()
                type_color = "#00E676" if "STRENGTH" in ptype else "#FFB800"
                patterns_html += (
                    f'<div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #222222; padding: 0.6rem 0;">'
                    f'<div>'
                    f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 0.75rem; font-weight: 800; color: {type_color}; border: 1px solid {type_color}; padding: 2px 6px; margin-right: 8px;">'
                    f'{ptype}'
                    f'</span>'
                    f'<span style="font-size: 0.92rem; color: #E0E0E0;">'
                    f'{p.get("pattern", "")}'
                    f'</span>'
                    f'</div>'
                    f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 0.75rem; color: #888888;">'
                    f'FREQ: {p.get("frequency", 1)}'
                    f'</div>'
                    f'</div>'
                )
        else:
            patterns_html = "<div style='color: #666; font-size: 0.85rem;'>No behavioral patterns detected yet.</div>"

        render_html(
            f"""
            <div class="nb-card">
                <span class="nb-header-tag">LONGITUDINAL BEHAVIORAL PATTERNS</span>
                {patterns_html}
            </div>
            """
        )

        # 5. Prioritized Action Study Plan
        study_plan = res.get("study_plan", [])
        study_plan_html = ""
        if study_plan:
            for item in study_plan:
                prio = item.get("priority", 1)
                study_plan_html += (
                    f'<div style="background: #111111; border: 1.5px solid #2F2F2F; padding: 0.9rem 1.1rem; margin-bottom: 0.75rem;">'
                    f'<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">'
                    f'<span style="background: #D4FF00; color: #000; font-family: \'JetBrains Mono\', monospace; font-weight: 800; font-size: 0.78rem; padding: 2px 8px;">'
                    f'PRIORITY #{prio}'
                    f'</span>'
                    f'<span style="font-size: 1rem; font-weight: 700; color: #FFFFFF;">'
                    f'{item.get("action", "")}'
                    f'</span>'
                    f'</div>'
                    f'<div style="font-size: 0.88rem; color: #A0A0A0; line-height: 1.45; margin-left: 2px;">'
                    f'<span style="font-family: \'JetBrains Mono\', monospace; color: #777777; font-size: 0.75rem;">RATIONALE:</span> {item.get("reason", "")}'
                    f'</div>'
                    f'</div>'
                )
        else:
            study_plan_html = "<div style='color: #666; font-size: 0.85rem;'>No study plan actions generated.</div>"

        render_html(
            f"""
            <div class="nb-card nb-card-accent">
                <span class="nb-header-tag">PRIORITIZED BREAKTHROUGH STUDY PLAN</span>
                {study_plan_html}
            </div>
            """
        )
