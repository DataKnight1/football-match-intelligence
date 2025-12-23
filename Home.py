"""
Author: Tiago Monteiro
Date: 21-12-2025
Main application entry point for the Football Match Visualizer.
"""
import streamlit as st
from pathlib import Path
import base64
import sys

sys.path.append(str(Path(__file__).parent))

from src import data_loader, utils


def main():
    """
    Main function to run the Streamlit application.
    Sets page config, loads CSS, displays logo in sidebar, and shows the header.
    """
    st.set_page_config(
        page_title="Home - Football Match Visualizer",
        page_icon=str(Path("assets") / "Logo.ico"),
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --apple-system-gray: #F5F5F7;
            --apple-card-bg: #FFFFFF;
            --apple-text-primary: #1D1D1F;
            --apple-text-secondary: #86868B;
            --apple-accent: #32FF69;
            --apple-accent-dark: #28D55F;
            --apple-border: rgba(0, 0, 0, 0.08);
            --apple-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
            --apple-shadow-md: 0 4px 16px rgba(0, 0, 0, 0.06);
            --apple-shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.08);
        }

        body, .stApp {
            background-color: var(--apple-system-gray);
            color: var(--apple-text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        .main {
            padding: 2rem 3rem;
            max-width: 1440px;
            margin: 0 auto;
        }

        /* Typography */
        h1, h2, h3, h4, h5 {
            color: var(--apple-text-primary);
            font-weight: 600;
            letter-spacing: -0.015em;
        }

        h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        h2 { font-size: 1.75rem; margin-bottom: 1rem; }
        h3 { font-size: 1.25rem; font-weight: 500; }

        p {
            color: var(--apple-text-secondary);
            font-size: 1.05rem;
            line-height: 1.6;
        }

        /* App Header - Minimalist */
        .app-header {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }

        .app-logo img {
            border-radius: 12px;
            box-shadow: var(--apple-shadow-sm);
        }

        .app-headline {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--apple-text-primary);
            margin: 0;
            letter-spacing: -0.02em;
        }

        .app-subtitle {
            font-size: 1rem;
            color: var(--apple-text-secondary);
            margin: 0.25rem 0 0 0;
            font-weight: 400;
        }

        /* Cards and Containers */
        .card-container {
            background: var(--apple-card-bg);
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: var(--apple-shadow-sm);
            border: 1px solid var(--apple-border);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card-container:hover {
            transform: translateY(-2px);
            box-shadow: var(--apple-shadow-md);
        }

        /* Feature Cards (Solution Overview) */
        .feature-card {
            background: #FFFFFF;
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(0,0,0,0.06);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .feature-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--apple-text-primary);
            margin-bottom: 0.5rem;
            letter-spacing: -0.03em;
            background: -webkit-linear-gradient(45deg, #1D1D1F, #424245);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .feature-label {
            font-size: 0.9rem;
            color: var(--apple-text-secondary);
            font-weight: 500;
        }

        /* Navigation Hint */
        .nav-hint {
            background: rgba(50, 255, 105, 0.1);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            color: #007D34;
            font-weight: 500;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 2rem;
            border: 1px solid rgba(50, 255, 105, 0.2);
        }

        /* Streamlit Element Overrides */
        .stButton>button {
            border-radius: 12px;
            font-weight: 500;
            padding: 0.6rem 1.2rem;
            border: none;
            background: #1D1D1F;
            color: white;
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            background: #333336;
            transform: scale(1.01);
            color: white;
        }

        /* Sidebar - Vertical Tab Style Restored */
        .stSidebar {
            background-color: var(--apple-system-gray);
            border-right: 1px solid var(--apple-border);
        }
        
        .stSidebar [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }

        .stSidebar [data-testid="stSidebarNav"] a {
            display: flex;
            align-items: center;
            padding: 0.85rem 1rem;
            border-radius: 10px;
            border: 1px solid transparent;
            background-color: white;
            color: var(--apple-text-primary);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95rem;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
            margin-bottom: 0.5rem;
            position: relative;
            overflow: hidden;
        }

        .stSidebar [data-testid="stSidebarNav"] a:hover {
            border-color: var(--apple-accent);
            transform: translateX(2px);
            box-shadow: 0 4px 12px rgba(50, 255, 105, 0.15);
        }

        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"],
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]:hover,
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]:focus,
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]:active {
            background: rgba(50, 255, 105, 0.12) !important;
            color: #007D34 !important;
            border-color: var(--apple-accent) !important;
            box-shadow: 0 4px 12px rgba(50, 255, 105, 0.2) !important;
            font-weight: 600 !important;
            transform: translateX(2px) !important;
        }
        
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]::before,
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]:hover::before,
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]:focus::before,
        .stSidebar [data-testid="stSidebarNav"] a[aria-current="page"]:active::before {
            content: "" !important;
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            height: 100% !important;
            width: 5px !important;
            background: var(--apple-accent) !important;
            border-radius: 0 !important;
            display: block !important;
        }

        /* Team Logo Grid - Custom CSS Grid */
        .team-grid {
            display: grid;
            grid-template-columns: repeat(4, 110px);
            gap: 12px;
            padding: 0.5rem 0.5rem;
            justify-content: start;
        }
        
        .team-logo-item {
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            border-radius: 20px;
            width: 110px;
            height: 110px;
            box-shadow: var(--apple-shadow-sm);
            border: 1px solid var(--apple-border);
            transition: all 0.2s ease;
            cursor: default;
        }
        
        .team-logo-item:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: var(--apple-shadow-md);
            border-color: var(--apple-accent);
        }
        
        .team-logo-img {
            width: 80px !important; 
            height: 80px !important; 
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.05));
        }

        /* Image Sizing Fix - CRITICAL */
        /* Exclude team logos from full-width forcing */
        .element-container img:not(.app-header img):not(.app-logo img):not(.team-logo-img) {
            max-width: 100% !important;
            width: 100% !important;
            border-radius: 12px;
            box-shadow: var(--apple-shadow-md);
        }

        /* Clean metrics list */
        .capability-item {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            font-size: 0.95rem;
            color: var(--apple-text-secondary);
        }
        
        .capability-dot {
            width: 6px;
            height: 6px;
            background: var(--apple-accent-dark);
            border-radius: 50%;
        }

        /* Hide Streamlit branding */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        
        </style>
        """,
        unsafe_allow_html=True,
    )

    logo_path = Path("assets") / "Logo.ico"
    logo_markup = ""
    if logo_path.exists():
        logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()
        logo_markup = (
            "<div class='app-logo'>"
            f"<img src='data:image/x-icon;base64,{logo_base64}' width='64' height='64' alt='App logo'/>"
            "</div>"
        )
    
    st.markdown(
        f"""
        <div class="app-header">
            {logo_markup}
            <div>
                <h1 class="app-headline">Football Match Visualizer</h1>
                <p class="app-subtitle">Interactive analysis of tracking data.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    main_col1, main_col2 = st.columns([1.2, 1], gap="large")
    
    with main_col1:
        st.markdown('<h3 style="margin-bottom: 1.5rem; padding-left: 0.5rem;">Teams in Analysis</h3>', unsafe_allow_html=True)
        
        matches = data_loader.get_available_matches()
        teams_in_data = set()
        
        for description in matches.values():
            if " vs " in description:
                home, away = description.split(" vs ")
                teams_in_data.add(home.strip())
                teams_in_data.add(away.strip())
        
        if teams_in_data:
            sorted_teams = sorted(teams_in_data)
            
            grid_html = '<div class="team-grid">'
            for team_name in sorted_teams:
                team_logo = utils.get_team_logo_base64(team_name)
                if team_logo:
                    grid_html += f'<div class="team-logo-item" title="{team_name}"><img src="{team_logo}" class="team-logo-img" alt="{team_name}"/></div>'
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)
            
        else:
             st.info("No matches loaded. Please check data source.")
    
    with main_col2:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("""
            <div class="card-container feature-card">
                <div class="feature-number">6</div>
                <div class="feature-label">Modules</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown("""
            <div class="card-container feature-card">
                <div class="feature-number">25<span style="font-size:1rem; color:var(--apple-text-secondary);">Hz</span></div>
                <div class="feature-label">Tracking</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown("""
            <div class="card-container feature-card">
                <div class="feature-number">50+</div>
                <div class="feature-label">Metrics</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("""
        <div class="card-container" style="margin-top: 1rem;">
            <h3 style="margin-bottom: 1rem;">Capabilities</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                   <div style="margin-bottom: 0.5rem; font-weight: 600; font-size: 0.9rem;">Match Intelligence</div>
                   <div class="capability-item"><div class="capability-dot"></div>Match Scoreboard</div>
                   <div class="capability-item"><div class="capability-dot"></div>Pass networks</div>
                   <div class="capability-item"><div class="capability-dot"></div>Shot maps & xG</div>
                   <div class="capability-item"><div class="capability-dot"></div>Momentum flow</div>
                </div>
                <div>
                   <div style="margin-bottom: 0.5rem; font-weight: 600; font-size: 0.9rem;">Player Analytics</div>
                   <div class="capability-item"><div class="capability-dot"></div>Speed zones</div>
                   <div class="capability-item"><div class="capability-dot"></div>Physical metrics</div>
                   <div class="capability-item"><div class="capability-dot"></div>Heatmaps</div>
                   <div class="capability-item"><div class="capability-dot"></div>H2H comparison</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="nav-hint">
        <div style="font-size: 1.2rem;">Get Started</div>
        <div style="height: 24px; width: 1px; background: rgba(50, 255, 105, 0.4);"></div>
        <div>Select a module from the sidebar to begin your analysis.</div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

