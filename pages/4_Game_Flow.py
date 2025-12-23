"""
Author: Tiago Monteiro
Date: 21-12-2025
Game Flow dashboard showing the match narrative using cumulative xG, momentum charts, and possession timelines.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src import data_loader, utils, visualizations, styling

PRIMARY_COLOR = "#32FF69"

styling.setup_page("Game Flow")

@st.cache_resource(ttl=3600)
def load_match_cached(match_id):
    """
    Load match data with caching.

    :param match_id: The ID of the match to load.
    :return: The loaded match data object.
    """
    return data_loader.load_match_data(match_id, sample_rate=1.0, limit=100) 

@st.cache_data(ttl=3600)
def load_events_cached(match_id):
    """
    Load match events with caching.

    :param match_id: The ID of the match events to load.
    :return: A DataFrame containing match events.
    """
    return data_loader.load_dynamic_events(match_id)

@st.cache_data(ttl=3600)
def load_phases_cached(match_id):
    """
    Load match phases with caching.

    :param match_id: The ID of the match phases to load.
    :return: A DataFrame containing match phases.
    """
    return data_loader.load_phases_of_play(match_id)

def main():
    """
    Main function to render the Game Flow page.
    Displays cumulative xG, match momentum, and possession timeline.
    """
    styling.load_css()
    
    st.sidebar.markdown("## Filters")
    matches = data_loader.get_available_matches()
    match_options = {f"{desc}": mid for mid, desc in matches.items()}
    
    selected_match_str = st.sidebar.selectbox("Select Match", list(match_options.keys()))
    selected_match_id = match_options[selected_match_str]

    with st.spinner("Loading match narrative..."):
        try:
            dataset = load_match_cached(selected_match_id)
            events = load_events_cached(selected_match_id)
            phases = load_phases_cached(selected_match_id)
            metadata = data_loader.get_match_metadata(dataset, match_id=selected_match_id)
            
            st.session_state['dataset'] = dataset
            st.session_state['events'] = events
            st.session_state['metadata'] = metadata
            st.session_state['match_id'] = selected_match_id
            
            home_color = utils.get_team_color(metadata['home_team_name'])
            away_color = utils.get_team_color(metadata['away_team_name'])
            
            if home_color == away_color:
                home_color = "#FF3333" 
                away_color = "#3385FF" 
                
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    goals = events[(events['end_type'] == 'shot') & (events['lead_to_goal'] == True)]
    home_goals = len(goals[goals['team_id'] == metadata['home_team_id']])
    away_goals = len(goals[goals['team_id'] == metadata['away_team_id']])
    
    home_logo = utils.get_team_logo_base64(metadata['home_team_name'])
    away_logo = utils.get_team_logo_base64(metadata['away_team_name'])
    
    home_logo_html = f'<img src="{home_logo}" class="scoreboard-logo" style="margin-right: 20px;">' if home_logo else ''
    away_logo_html = f'<img src="{away_logo}" class="scoreboard-logo" style="margin-left: 20px;">' if away_logo else ''

    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
            {home_logo_html}
            <div style="background-color: {home_color}; color: white; padding: 10px 40px; border-radius: 20px 0 0 20px; font-weight: bold; font-size: 24px; min_width: 200px; text-align: center;">
                {metadata['home_team_name']}
            </div>
            <div style="background-color: {away_color}; color: white; padding: 10px 40px; border-radius: 0 20px 20px 0; font-weight: bold; font-size: 24px; min_width: 200px; text-align: center;">
                {metadata['away_team_name']}
            </div>
            {away_logo_html}
        </div>
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="font-size: 60px; margin: 0;">{home_goals} - {away_goals}</h1>
            <p style="color: gray;">Match Story & Analysis</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Cumulative Expected Goals (xG)")
    
    if 'expected_goal_value' not in events.columns:
        events['expected_goal_value'] = 0.0
        
    if events['expected_goal_value'].sum() == 0:
         
         if pd.notna(events['x_start']).any() and events['x_start'].abs().max() <= 1.2:
             events.loc[:, 'x_start'] *= 105
             events.loc[:, 'y_start'] *= 68

         def calculate_period_xg(df, team_id):
             """
             Calculate xG for a team per period, handling attacking direction.

             :param df: The DataFrame of events.
             :param team_id: The ID of the team.
             """
             team_shots = df[(df['team_id'] == team_id) & (df['end_type'] == 'shot')].copy()
             if team_shots.empty:
                 return
             
             period_col = 'half' if 'half' in df.columns else ('period' if 'period' in df.columns else None)
             
             if period_col:
                 periods = team_shots[period_col].unique()
             else:
                 periods = [None]
                 
             for p in periods:
                 if period_col:
                     period_mask = (team_shots[period_col] == p)
                 else:
                     period_mask = slice(None)
                     
                 shots_subset = team_shots[period_mask]
                 if shots_subset.empty:
                     continue
                 
                 avg_x = shots_subset['x_start'].mean()
                 target_x = 52.5 if avg_x > 0 else -52.5
                 
                 dists = np.sqrt((shots_subset['x_start'] - target_x)**2 + (shots_subset['y_start'] - 0)**2)
                 
                 xg_values = 0.82 * np.exp(-0.11 * dists)
                 
                 events.loc[shots_subset.index, 'expected_goal_value'] = xg_values

         calculate_period_xg(events, metadata['home_team_id'])
         calculate_period_xg(events, metadata['away_team_id'])

         events['expected_goal_value'] = events['expected_goal_value'].fillna(0)
    
    fig_xg, _ = visualizations.plot_cumulative_xg(
        events, 
        metadata['home_team_id'], 
        metadata['away_team_id'],
        metadata['home_team_name'],
        metadata['away_team_name'],
        home_color=home_color,
        away_color=away_color
    )
    st.pyplot(fig_xg)
    
    st.markdown("---")

    st.markdown("### Match Momentum")
    
    fig_mom, _ = visualizations.plot_momentum_chart(
        events,
        metadata['home_team_id'],
        metadata['away_team_id'],
        home_color=home_color,
        away_color=away_color
    )
    st.pyplot(fig_mom)
    
    st.markdown("---")

    st.markdown("### Possession Timeline")
    
    fig_poss, _ = visualizations.plot_possession_timeline(
        phases,
        metadata['home_team_id'],
        metadata['away_team_id'],
        metadata['home_team_name'],
        metadata['away_team_name'],
        home_color=home_color,
        away_color=away_color,
        fps=10.0
    )
    st.pyplot(fig_poss)

if __name__ == "__main__":
    main()
