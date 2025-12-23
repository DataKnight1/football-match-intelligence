"""
Author: Tiago Monteiro
Date: 21-12-2025
UI styling configuration for the Streamlit application.
"""

import streamlit as st
from pathlib import Path

def setup_page(page_title: str, layout: str = "wide"):
    """
    Configures the Streamlit page with standard settings and icon.

    :param page_title: The title of the page.
    :param layout: The layout of the page (default: "wide").
    """
    icon_path = Path("assets") / "Logo.ico"
    st.set_page_config(
        page_title=page_title,
        page_icon=str(icon_path) if icon_path.exists() else None,
        layout=layout,
        initial_sidebar_state="expanded"
    )

def load_css():
    """
    Loads the custom CSS for the customized UI.
    """
    st.markdown(
        """
        <style>
        :root {
            --pysport-primary: #32FF69;
            --pysport-accent: #1FC96D;
            --pysport-background: #FFFFFF;
            --pysport-surface: #F8F9FA;
            --pysport-border: rgba(40, 167, 69, 0.2);
            --pysport-text: #1A1A1A;
            --pysport-muted: #6C757D;
            --pysport-divider: rgba(40, 167, 69, 0.15);
        }
        body, .stApp {
            background-color: var(--pysport-background);
            color: var(--pysport-text);
        }
        .main {
            padding: 1.5rem 2rem 2rem 2rem;
            max-width: 1600px;
            margin: 0 auto;
        }
        .app-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 2.5rem;
            margin-bottom: 0.75rem;
            padding: 0.75rem 1rem;
            background: linear-gradient(135deg, var(--pysport-surface) 0%, #FFFFFF 100%);
            border-radius: 8px;
            border: 2px solid var(--pysport-border);
        }
        .app-logo img {
            width: 64px !important;
            height: 64px !important;
            max-width: 64px !important;
            max-height: 64px !important;
            border-radius: 8px;
            object-fit: contain;
            border: 2px solid var(--pysport-primary);
            padding: 4px;
            background: white;
            display: block;
        }
        .app-header img {
            width: 40px !important;
            height: 40px !important;
            max-width: 40px !important;
            max-height: 40px !important;
        }
        .app-headline {
            color: var(--pysport-text);
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.3px;
            line-height: 1.3;
        }
        .app-subtitle {
            color: var(--pysport-muted);
            font-size: 0.8rem;
            margin: 0.25rem 0 0 0;
            font-weight: 400;
            line-height: 1.3;
        }
        h1, h2, h3, h4, h5 {
            color: var(--pysport-text);
            font-weight: 700;
        }
        h1 {
            font-size: 2.25rem;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }
        h2 {
            font-size: 1.75rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 3px solid var(--pysport-primary);
            padding-bottom: 0.5rem;
        }
        h3 {
            font-size: 1.25rem;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: var(--pysport-accent);
        }
        .stButton>button {
            width: 100%;
            font-size: 1rem;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            border: 2px solid var(--pysport-primary);
            background: white;
            color: var(--pysport-primary);
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(50, 255, 105, 0.1);
        }
        .stButton>button:hover {
            background-color: white;
            color: var(--pysport-primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(50, 255, 105, 0.3);
            border: 2px solid var(--pysport-primary);
        }
        .stButton>button[kind="primary"],
        .stButton>button[data-testid="baseButton-primary"] {
            background-color: var(--pysport-primary) !important;
            color: white !important;
            border-color: var(--pysport-primary) !important;
        }
        .stButton>button[kind="primary"]:hover,
        .stButton>button[data-testid="baseButton-primary"]:hover {
            background-color: var(--pysport-accent) !important;
            color: white !important;
            border-color: var(--pysport-accent) !important;
        }
        .stSelectbox label,
        .stSlider label,
        .stCheckbox label,
        .stNumberInput label,
        .stRadio label {
            font-weight: 600;
            color: var(--pysport-text);
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }
        .stSelectbox div[data-baseweb="select"] > div,
        .stNumberInput div[data-baseweb="input"] > div {
            background-color: white !important;
            border-radius: 8px;
            border: 2px solid var(--pysport-border);
            padding: 0.5rem 0.75rem !important; 
            min-height: 48px;
            display: flex !important;
            align-items: center !important;
            font-size: 0.95rem;
            color: #1A1A1A !important;
        }

        .stSelectbox div[data-baseweb="select"] span,
        .stSelectbox div[data-baseweb="select"] div {
            color: #1A1A1A !important;
        }
        .stSelectbox div[data-baseweb="select"] > div * {
            color: #1A1A1A !important;
        }
        .stSelectbox div[data-baseweb="select"] > div svg {
            fill: #1A1A1A !important;
        }
        .stSelectbox div[data-baseweb="select"] > div:hover,
        .stNumberInput div[data-baseweb="input"] > div:hover {
            border-color: var(--pysport-primary);
            box-shadow: 0 0 0 3px rgba(50, 255, 105, 0.1);
        }
        .stSelectbox div[data-baseweb="select"] input {
            color: #1A1A1A !important;
        }
        .stSelectbox [data-baseweb="select"] [role="button"] {
            color: #1A1A1A !important;
        }
        
        .stSelectbox div[data-baseweb="select"] > div:first-child {
            background-color: white !important;
            border-color: var(--pysport-border) !important;
            color: #1A1A1A !important;
        }

        .stSelectbox div[data-baseweb="select"] > div:first-child > div {
            color: #1A1A1A !important;
        }

        .stSelectbox div[data-baseweb="select"] svg {
            fill: #1A1A1A !important;
            color: #1A1A1A !important;
        }
        
        [role="option"] p, [role="option"] div, [role="option"] span {
            color: #1A1A1A !important;
        }
        
        [role="option"][aria-selected="true"], [role="option"]:hover {
            background-color: #F8F9FA !important;
        }
        .stSelectbox [data-baseweb="popover"] {
            margin-top: 4px;
        }
        .stSelectbox [data-baseweb="menu"] {
            max-height: 400px;
        }
        .stSelectbox ul {
            padding: 0.5rem 0 !important;
        }
        .stSidebar {
            border-right: 3px solid var(--pysport-primary);
            background-color: var(--pysport-surface);
            padding: 1rem;
            min-width: 380px !important;
            max-width: 450px !important;
        }
        .stSidebar > div:first-child {
            width: 380px !important;
        }
        .stSidebar .stButton>button {
            background-color: white;
        }
        .stSidebar .stButton>button:hover {
            background-color: var(--pysport-primary);
            color: white;
        }
        .stSidebar [data-testid="stSidebarNav"] {
            background-color: var(--pysport-surface);
        }
        .block-container {
            padding-top: 5rem !important;
            padding-bottom: 3rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.75rem;
            border-bottom: 2px solid var(--pysport-border);
            padding-bottom: 0;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1.5rem;
            border-radius: 8px 8px 0 0;
            background-color: white;
            border: 2px solid var(--pysport-border);
            border-bottom: none;
            color: var(--pysport-muted);
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--pysport-surface);
            color: var(--pysport-primary);
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--pysport-primary);
            color: white;
            border-color: var(--pysport-primary);
        }
        .element-container img:not(.app-header img):not(.app-logo img):not(.scoreboard-logo) {
            max-width: 100% !important;
            width: 100% !important;
            height: auto !important;
            display: block;
            margin: 0 auto;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .app-header .app-logo img,
        .app-header img[alt="App logo"] {
            width: 64px !important;
            height: 64px !important;
            max-width: 64px !important;
            max-height: 64px !important;
            border-radius: 8px !important;
        }
        .scoreboard-logo {
            width: auto !important;
            height: 80px !important;
            max-width: none !important;
            max-height: 80px !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
            display: inline-block !important;
            vertical-align: middle !important;
        }
        .element-container video {
            max-width: 100% !important;
            width: 100% !important;
            height: auto !important;
            display: block;
            margin: 0 auto;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .stPlotlyChart, .stPyplot {
            width: 100% !important;
        }
        .stPyplot > div {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        .stPyplot img {
            max-width: 100% !important;
            width: auto !important;
            height: auto !important;
            object-fit: contain !important;
        }
        .stSlider > div[data-baseweb="slider"] > div:nth-child(1) {
            background-color: rgba(50, 255, 105, 0.25);
        }
        .stSlider > div[data-baseweb="slider"] > div:nth-child(2) > div {
            background-color: var(--pysport-primary);
        }
        .stSlider [role="slider"] {
            background: var(--pysport-primary);
            box-shadow: 0 0 0 4px rgba(50, 255, 105, 0.2) !important;
            width: 20px;
            height: 20px;
        }
        iframe {
            width: 100% !important;
            max-width: 100% !important;
            border-radius: 12px;
        }
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            border: 2px solid var(--pysport-border);
            color: var(--pysport-text);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        .stCheckbox [data-baseweb="checkbox"] {
            border-radius: 6px;
            border: 2px solid var(--pysport-border);
            background-color: white;
        }
        .stCheckbox [data-baseweb="checkbox"]:hover {
            border-color: var(--pysport-primary);
            box-shadow: 0 0 0 3px rgba(50, 255, 105, 0.1);
        }
        .stCheckbox [data-baseweb="checkbox"] svg {
            color: var(--pysport-primary) !important;
            fill: var(--pysport-primary) !important;
            width: 18px;
            height: 18px;
        }
        .stCheckbox label {
            font-size: 0.95rem;
        }
        .stCheckbox input[type="checkbox"]:checked + div {
            background-color: var(--pysport-primary) !important;
            border-color: var(--pysport-primary) !important;
        }
        .stCheckbox input[type="checkbox"]:checked + div svg {
            fill: white !important;
        }
        .stCheckbox input:checked ~ div[data-baseweb="checkbox"] {
            background-color: var(--pysport-primary) !important;
            border-color: var(--pysport-primary) !important;
        }
        .stCheckbox input:checked ~ div[data-baseweb="checkbox"] svg {
            fill: white !important;
            color: white !important;
        }
        .stMetric {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid var(--pysport-border);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        .stMetric:hover {
            border-color: var(--pysport-primary);
            box-shadow: 0 4px 16px rgba(50, 255, 105, 0.15);
            transform: translateY(-2px);
        }
        .stMetric label {
            color: var(--pysport-muted);
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stMetric div[data-testid="stMetricValue"] {
            color: var(--pysport-text);
            font-weight: 700;
            font-size: 1.75rem;
        }
        .stMetric div[data-testid="stMetricDelta"] {
            color: var(--pysport-primary);
            font-weight: 600;
        }
        .stAlert {
            border-radius: 12px;
            border: 2px solid var(--pysport-border);
            background-color: var(--pysport-surface);
            padding: 1rem;
        }
        .stProgress > div > div > div {
            background-color: var(--pysport-primary);
        }
        .stMarkdown p {
            color: var(--pysport-text);
            line-height: 1.6;
        }
        .stMarkdown a {
            color: var(--pysport-primary);
            text-decoration: none;
            font-weight: 600;
        }
        .stMarkdown a:hover {
            text-decoration: underline;
        }
        hr {
            border: none;
            border-top: 2px solid var(--pysport-divider);
            margin: 2rem 0;
        }
        [data-testid="stExpander"] {
            border: 2px solid var(--pysport-border);
            border-radius: 12px;
            background-color: white;
        }
        [data-testid="stExpander"]:hover {
            border-color: var(--pysport-primary);
        }
        .stRadio > div {
            gap: 1rem;
        }
        .stRadio label {
            background-color: white;
            padding: 0.75rem 1.25rem;
            border-radius: 8px;
            border: 2px solid var(--pysport-border);
            transition: all 0.2s ease;
            color: #1A1A1A !important;
        }
        .stRadio label:hover {
            border-color: var(--pysport-primary);
            background-color: var(--pysport-surface);
        }
        .stRadio div[role="radiogroup"] label p {
            color: #1A1A1A !important;
        }
        .stRadio input[type="radio"]:checked + div {
            background-color: var(--pysport-primary) !important;
            border-color: var(--pysport-primary) !important;
        }
        .stRadio input[type="radio"]:checked + div::before {
            background-color: white !important;
        }
        .stRadio [role="radio"][aria-checked="true"] > div:first-child {
            background-color: var(--pysport-primary) !important;
            border-color: var(--pysport-primary) !important;
        }
        .stRadio [role="radio"][aria-checked="true"] > div:first-child > div {
            background-color: white !important;
        }
        .stRadio [data-baseweb="radio"] > div:first-child {
            border-color: var(--pysport-border);
        }
        .stRadio [data-baseweb="radio"] > div:first-child > div {
            background-color: var(--pysport-primary) !important;
            border-color: var(--pysport-primary) !important;
        }
        .stRadio input:checked ~ div[data-baseweb="radio"] > div:first-child {
            border-color: var(--pysport-primary) !important;
            background-color: var(--pysport-primary) !important;
        }
        .stNumberInput input {
            color: #1A1A1A !important;
        }
        .stDataFrame {
            border: 2px solid var(--pysport-border);
            border-radius: 12px;
            overflow: hidden;
        }
        .stDataFrame table {
            color: #1A1A1A !important;
        }
        .stDataFrame th {
            background-color: var(--pysport-primary) !important;
            color: white !important;
            font-weight: 600;
        }
        .stDataFrame td {
            color: #1A1A1A !important;
        }
        [data-testid="stCaptionContainer"] {
            color: var(--pysport-muted);
        }
        .stSpinner > div {
            border-top-color: var(--pysport-primary) !important;
        }
        .stToggle > label > div[data-baseweb="toggle"] {
            background-color: rgba(50, 255, 105, 0.3) !important;
        }
        .stToggle > label > div[data-baseweb="toggle"] > div {
            background-color: var(--pysport-primary) !important;
        }
        .stToggle input:checked + div[data-baseweb="toggle"] {
            background-color: var(--pysport-primary) !important;
        }
        .stToggle input:checked + div[data-baseweb="toggle"] > div {
            background-color: white !important;
        }
        [data-baseweb="radio"] {
            align-items: flex-start !important;
        }
        [data-baseweb="radio"] > div:first-child {
            background-color: white !important;
            border: 2px solid var(--pysport-border) !important;
        }
        [data-baseweb="radio"][aria-checked="true"] > div:first-child {
            background-color: white !important;
            border: 2px solid var(--pysport-primary) !important;
        }
        [data-baseweb="radio"][aria-checked="true"] > div:first-child::after {
            content: "";
            width: 10px;
            height: 10px;
            background-color: var(--pysport-primary) !important;
            border-radius: 50%;
        }
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background-color: var(--pysport-primary) !important;
        }
        .stSlider [data-baseweb="slider"] [role="slider"]:focus {
            box-shadow: 0 0 0 4px rgba(50, 255, 105, 0.3) !important;
        }
        
        .stSidebar [data-testid="stSidebarNav"] ul {
            padding: 0.5rem 0;
        }
        .stSidebar [data-testid="stSidebarNav"] li {
            margin: 0.25rem 0;
        }
        .stSidebar [data-testid="stSidebarNav"] a {
            display: flex;
            align-items: center;
            padding: 0.85rem 1rem;
            border-radius: 10px;
            border: 2px solid transparent;
            background-color: white;
            color: var(--pysport-text);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            position: relative;
            overflow: hidden;
        }
        .stSidebar [data-testid="stSidebarNav"] a::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            width: 0;
            background: linear-gradient(90deg, var(--pysport-primary) 0%, rgba(50, 255, 105, 0.1) 100%);
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 0;
        }
        .stSidebar [data-testid="stSidebarNav"] a span {
            position: relative;
            z-index: 1;
        }
        .stSidebar [data-testid="stSidebarNav"] a:hover {
            border-color: var(--pysport-primary);
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(50, 255, 105, 0.25);
            background-color: rgba(50, 255, 105, 0.05);
        }
        .stSidebar [data-testid="stSidebarNav"] a:hover::before {
            width: 4px;
        }
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"],
        .stSidebar [data-testid="stSidebarNav"] li:has(> a[aria-current="page"]) a {
            background: rgba(50, 255, 105, 0.1);
            color: var(--pysport-primary);
            border-color: var(--pysport-primary);
            box-shadow: 0 2px 6px rgba(50, 255, 105, 0.15);
            font-weight: 700;
        }
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]::before {
            width: 4px;
            background: var(--pysport-primary);
        }
        .stSidebar h2 {
            color: var(--pysport-primary);
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--pysport-primary);
            letter-spacing: 0.5px;
        }
        .stSidebar [data-testid="stExpander"] {
            border: 2px solid var(--pysport-border);
            border-radius: 10px;
            background-color: white;
            margin-bottom: 0.75rem;
            transition: all 0.3s ease;
        }
        .stSidebar [data-testid="stExpander"]:hover {
            border-color: var(--pysport-primary);
            box-shadow: 0 2px 8px rgba(50, 255, 105, 0.15);
        }
        .stSidebar [data-testid="stExpander"] summary {
            padding: 0.75rem 1rem;
            font-weight: 600;
            color: var(--pysport-text);
            cursor: pointer;
        }
        .stSidebar [data-testid="stExpander"][open] {
            border-color: var(--pysport-primary);
            box-shadow: 0 4px 12px rgba(50, 255, 105, 0.2);
        }
        .stSidebar [data-testid="stExpander"][open] summary {
            color: var(--pysport-primary);
            border-bottom: 1px solid var(--pysport-border);
            margin-bottom: 0.75rem;
        }
        button[data-testid="collapsedControl"] {
            background-color: var(--pysport-primary) !important;
            color: white !important;
            border-radius: 0 8px 8px 0 !important;
            padding: 0.75rem !important;
            border: none !important;
            box-shadow: 0 2px 8px rgba(50, 255, 105, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        button[data-testid="collapsedControl"]:hover {
            background-color: var(--pysport-accent) !important;
            box-shadow: 0 4px 16px rgba(50, 255, 105, 0.5) !important;
            transform: translateX(2px) !important;
        }
        button[data-testid="collapsedControl"] svg {
            color: white !important;
            fill: white !important;
        }
        [data-testid="stSidebar"][aria-expanded="false"] {
            min-width: 80px !important;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] a {
            font-size: 0.75rem !important;
            padding: 0.5rem !important;
            text-align: center !important;
            justify-content: center !important;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] a span {
            display: none;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:nth-child(1) a::after {
            content: "Home";
            font-weight: 700;
            font-size: 0.85rem;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:nth-child(2) a::after {
            content: "MO";
            font-weight: 700;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:nth-child(3) a::after {
            content: "PA";
            font-weight: 700;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:nth-child(4) a::after {
            content: "TA";
            font-weight: 700;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:nth-child(5) a::after {
            content: "PC";
            font-weight: 700;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:nth-child(6) a::after {
            content: "GF";
            font-weight: 700;
        }
        [data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] li:nth-child(7) a::after {
            content: "EA";
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
