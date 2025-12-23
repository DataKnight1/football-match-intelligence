"""
Author: Tiago Monteiro
Date: 21-12-2025
Overview dashboard for a specific football match, showing scoreboard, pass networks, and match statistics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src import data_loader, utils, visualizations, styling

PRIMARY_COLOR = "#32FF69"
BACKGROUND_COLOR = "#F0F0F0"
HOME_COLOR = "#FF3333"
AWAY_COLOR = "#3385FF"

styling.setup_page("Match Overview")

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
    Main function to render the Match Overview page.
    Displays scoreboard, pass networks, momentum chart, and other match statistics.
    """
    styling.load_css()
    
    st.sidebar.markdown("## Filters")
    matches = data_loader.get_available_matches()
    match_options = {f"{desc}": mid for mid, desc in matches.items()}
    
    selected_match_str = st.sidebar.selectbox("Select Match", list(match_options.keys()))
    selected_match_id = match_options[selected_match_str]

    with st.spinner("Loading match statistics..."):
        try:
            dataset = load_match_cached(selected_match_id)
            events = load_events_cached(selected_match_id)
            phases = load_phases_cached(selected_match_id)
            metadata = data_loader.get_match_metadata(dataset, match_id=selected_match_id)
            
            st.session_state['dataset'] = dataset
            st.session_state['events'] = events
            st.session_state['metadata'] = metadata
            st.session_state['match_id'] = selected_match_id
            
            st.session_state['match_id'] = selected_match_id
            
            global HOME_COLOR, AWAY_COLOR
            HOME_COLOR = utils.get_team_color(metadata['home_team_name'])
            AWAY_COLOR = utils.get_team_color(metadata['away_team_name'])
            
            if HOME_COLOR == AWAY_COLOR:
                 HOME_COLOR = "#FF3333"
                 AWAY_COLOR = "#3385FF"

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
    
    match_date = metadata.get('date_time', 'October 08, 2023')
    competition = metadata.get('competition_name', 'Premier League')

    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
            {home_logo_html}
            <div style="background-color: {HOME_COLOR}; color: white; padding: 10px 40px; border-radius: 20px 0 0 20px; font-weight: bold; font-size: 24px; min_width: 200px; text-align: center;">
                {metadata['home_team_name']}
            </div>
            <div style="background-color: {AWAY_COLOR}; color: white; padding: 10px 40px; border-radius: 0 20px 20px 0; font-weight: bold; font-size: 24px; min_width: 200px; text-align: center;">
                {metadata['away_team_name']}
            </div>
            {away_logo_html}
        </div>
        <div style="text-align: center;">
            <h1 style="font-size: 60px; margin: 0;">{home_goals} - {away_goals}</h1>
            <p style="color: gray;">{competition}<br>{match_date}</p>
        </div>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 1.5, 1])
    

    with col_left:
        st.markdown(f"<h3 style='text-align: center; color: {HOME_COLOR};'>Pass Network</h3>", unsafe_allow_html=True)
        
        home_passes = events[(events['end_type'] == 'pass') & (events['team_id'] == metadata['home_team_id'])]
        
        dataset = st.session_state.get('dataset')
        home_starters = set()
        if dataset:
             try:
                 p1_frames = [f for f in dataset.records if f.period.id == 1]
                 if p1_frames:
                     first_frame = p1_frames[0]
                     home_starters = {int(p.player_id) for p in first_frame.players_coordinates.keys() if p.team.team_id == metadata['home_team_id']}
             except Exception as e:
                 st.warning(f"Could not determine starters from tracking data: {e}")
        
        if not home_starters:
             home_starters = {int(p['player_id']) for p in metadata['home_players'] if p['position'] and p['position'] != 'None'}
        
        home_player_pos = home_passes.groupby(['player_id', 'player_name']).agg({
            'x_start': 'mean',
            'y_start': 'mean'
        }).reset_index().rename(columns={'x_start': 'x', 'y_start': 'y', 'player_name': 'name'})
        
        home_player_pos['node_color'] = home_player_pos['player_id'].apply(
            lambda pid: HOME_COLOR if pid in home_starters else "#32FF69"
        )
        
        if 'player_targeted_id' in home_passes.columns:
             pass_network_df = home_passes[['player_id', 'player_targeted_id']].rename(
                 columns={'player_id': 'passer_id', 'player_targeted_id': 'receiver_id'}
             ).dropna()
        else:
            pass_network_df = pd.DataFrame(columns=['passer_id', 'receiver_id'])

        pitch_length = 105
        pitch_width = 68
        if metadata.get('pitch_dimensions'):
            dim = metadata['pitch_dimensions']
            if hasattr(dim, 'length') and hasattr(dim, 'width'):
                pitch_length = dim.length
                pitch_width = dim.width

        fig_home_pass, _ = visualizations.plot_vertical_pass_network(
            pass_network_df,
            home_player_pos,
            pitch_length=pitch_length,
            pitch_width=pitch_width,
            pitch_color='white',
            line_color='gray',
            node_color=HOME_COLOR,
            title=""
        )
        st.pyplot(fig_home_pass)
        
        st.markdown("---")
        st.markdown("#### Start XI")
        st.markdown(visualizations.render_lineup_html(metadata['home_players'], HOME_COLOR), unsafe_allow_html=True)

    with col_center:
        away_events_subset = events[events['team_id'] == metadata['away_team_id']]
        if not away_events_subset.empty:
            away_shots = away_events_subset[away_events_subset['end_type'] == 'shot']
            if not away_shots.empty:
                direction_metric = away_shots['x_start'].mean()
            else:
                direction_metric = away_events_subset['x_start'].mean()
            
            if direction_metric > 0:
                 mask_away = events['team_id'] == metadata['away_team_id']
                 cols_to_flip = ['x_start', 'y_start', 'x_end', 'y_end']
                 cols_to_flip = [c for c in cols_to_flip if c in events.columns]
                 events.loc[mask_away, cols_to_flip] *= -1

        if 'expected_goal_value' not in events.columns:
            events['expected_goal_value'] = 0.0
            
            is_home_shot = (events['team_id'] == metadata['home_team_id']) & (events['end_type'] == 'shot')
            if is_home_shot.any():
                 dist_home = np.sqrt((events.loc[is_home_shot, 'x_start'] - 52.5)**2 + (events.loc[is_home_shot, 'y_start'] - 0)**2)
                 events.loc[is_home_shot, 'expected_goal_value'] = 0.82 * np.exp(-0.11 * dist_home)
             
            is_away_shot = (events['team_id'] == metadata['away_team_id']) & (events['end_type'] == 'shot')
            if is_away_shot.any():
                 dist_away = np.sqrt((events.loc[is_away_shot, 'x_start'] - (-52.5))**2 + (events.loc[is_away_shot, 'y_start'] - 0)**2)
                 events.loc[is_away_shot, 'expected_goal_value'] = 0.82 * np.exp(-0.11 * dist_away)

            events['expected_goal_value'] = events['expected_goal_value'].fillna(0)

        home_events = events[events['team_id'] == metadata['home_team_id']].copy()
        away_events = events[events['team_id'] == metadata['away_team_id']].copy()
        
        total_duration = phases['frame_end'].max() - phases['frame_start'].min()
        home_poss_mask = (phases['team_in_possession_id'] == metadata['home_team_id'])
        home_poss_frames = (phases.loc[home_poss_mask, 'frame_end'] - phases.loc[home_poss_mask, 'frame_start']).sum()
        home_poss_pct = (home_poss_frames / total_duration) * 100 if total_duration > 0 else 50
        
        home_final_third_events = len(home_events[home_events['x_start'] > 17.5])
        away_final_third_events = len(away_events[away_events['x_start'] < -17.5])
        
        total_final_third = home_final_third_events + away_final_third_events
        home_field_tilt = (home_final_third_events / total_final_third * 100) if total_final_third > 0 else 50
        
        home_xg = home_events['expected_goal_value'].sum()
        away_xg = away_events['expected_goal_value'].sum()
        
        home_pass_events = home_events[home_events['end_type'] == 'pass']
        away_pass_events = away_events[away_events['end_type'] == 'pass']
        
        home_pass_completed = len(home_pass_events[home_pass_events['pass_outcome'] == 'successful'])
        away_pass_completed = len(away_pass_events[away_pass_events['pass_outcome'] == 'successful'])
        
        home_pass_acc = (home_pass_completed / len(home_pass_events) * 100) if len(home_pass_events) > 0 else 0
        away_pass_acc = (away_pass_completed / len(away_pass_events) * 100) if len(away_pass_events) > 0 else 0

        def count_end_type(df, etype):
            """
            Count events with a specific end type.

            :param df: The DataFrame of events.
            :param etype: The end type to count.
            :return: The count of events.
            """
            if 'end_type' not in df.columns: return 0
            return len(df[df['end_type'] == etype])

        def count_interceptions(df):
            """
            Count interception events.

            :param df: The DataFrame of events.
            :return: The count of interceptions.
            """
            if 'start_type' not in df.columns: return 0
            return len(df[df['start_type'].astype(str).str.contains('interception')])

        def count_recoveries(df):
            """
            Count recovery events.

            :param df: The DataFrame of events.
            :return: The count of recoveries.
            """
            if 'start_type' not in df.columns: return 0
            return len(df[df['start_type'] == 'recovery'])

        def count_tackles_won(df):
            """
            Count successful tackles.

            :param df: The DataFrame of events.
            :return: The count of tackles won.
            """
            if 'end_type' not in df.columns: return 0
            return len(df[(df['event_type'] == 'on_ball_engagement') & 
                          (df['end_type'].isin(['direct_regain', 'direct_disruption']))])
        
        def count_dribbles(df):
            """
            Count dribble events.

            :param df: The DataFrame of events.
            :return: The count of dribbles.
            """
            if 'carry' in df.columns:
                 return len(df[df['carry'] == True])
            return 0
        
        stats_map = {}
        for team, df in [('Home', home_events), ('Away', away_events)]:
            stats_map[team] = {
                'Shots': len(df[df['end_type'] == 'shot']),
                'Dribbles': count_dribbles(df),
                'Tackles': count_tackles_won(df),
                'Interceptions': count_interceptions(df),
                'Clearances': count_end_type(df, 'clearance'),
                'Recoveries': count_recoveries(df),
            }

        st.markdown("<h3 style='text-align: center;'>Momentum</h3>", unsafe_allow_html=True)
        fig_momentum, _ = visualizations.plot_momentum_chart(
            events, 
            metadata['home_team_id'], 
            metadata['away_team_id'],
            home_color=HOME_COLOR,
            away_color=AWAY_COLOR
        )
        st.pyplot(fig_momentum)
        
        st.markdown("<h3 style='text-align: center;'>Zone Control & Territory</h3>", unsafe_allow_html=True)
        
        zone_events = events[events['event_type'] == 'player_possession']
        
        fig_zone, _ = visualizations.plot_zone_control(
            zone_events, 
            metadata['home_team_id'], 
            metadata['away_team_id'],
            home_color=HOME_COLOR,
            away_color=AWAY_COLOR,
            n_x_zones=6,
            n_y_zones=3
        )
        st.pyplot(fig_zone)
        
        st.markdown("<h3 style='text-align: center;'>Match Stats</h3>", unsafe_allow_html=True)
        
        stats_data = [
            {"Metric": "Goals", "Home": str(home_goals), "Away": str(away_goals)},
            {"Metric": "Expected Goals (xG)", "Home": f"{home_xg:.2f}", "Away": f"{away_xg:.2f}"},
            {"Metric": "Possession", "Home": f"{home_poss_pct:.1f}%", "Away": f"{100-home_poss_pct:.1f}%"},
            {"Metric": "Field Tilt", "Home": f"{home_field_tilt:.1f}%", "Away": f"{100-home_field_tilt:.1f}%"},
            {"Metric": "Shots", "Home": str(stats_map['Home']['Shots']), "Away": str(stats_map['Away']['Shots'])},
            {"Metric": "Passes", "Home": f"{home_pass_completed}/{len(home_pass_events)}", "Away": f"{away_pass_completed}/{len(away_pass_events)}"},
            {"Metric": "Pass Accuracy", "Home": f"{home_pass_acc:.1f}%", "Away": f"{away_pass_acc:.1f}%"},
            {"Metric": "Dribbles", "Home": str(stats_map['Home']['Dribbles']), "Away": str(stats_map['Away']['Dribbles'])},
            {"Metric": "Tackles", "Home": str(stats_map['Home']['Tackles']), "Away": str(stats_map['Away']['Tackles'])},
            {"Metric": "Interceptions", "Home": str(stats_map['Home']['Interceptions']), "Away": str(stats_map['Away']['Interceptions'])},
            {"Metric": "Clearances", "Home": str(stats_map['Home']['Clearances']), "Away": str(stats_map['Away']['Clearances'])},
            {"Metric": "Recoveries", "Home": str(stats_map['Home']['Recoveries']), "Away": str(stats_map['Away']['Recoveries'])},
        ]

        st.dataframe(pd.DataFrame(stats_data), hide_index=True, use_container_width=True, column_config={
            "Metric": st.column_config.TextColumn("Metric", width="medium"),
            "Home": st.column_config.TextColumn(metadata['home_team_name'], width="small"),
            "Away": st.column_config.TextColumn(metadata['away_team_name'], width="small")
        })
        
        st.markdown("<h3 style='text-align: center;'>Shot Map</h3>", unsafe_allow_html=True)
        shots = events[events['end_type'] == 'shot']

        col_home_shot, col_away_shot = st.columns(2)
        
        with col_home_shot:
            home_shots = shots[shots['team_id'] == metadata['home_team_id']]
            fig_home_shot, _ = visualizations.plot_team_shot_map(
                home_shots,
                metadata['home_team_name'],
                HOME_COLOR
            )
            st.pyplot(fig_home_shot)
            
        with col_away_shot:
            away_shots = shots[shots['team_id'] == metadata['away_team_id']]
            fig_away_shot, _ = visualizations.plot_team_shot_map(
                away_shots,
                metadata['away_team_name'],
                AWAY_COLOR
            )
            st.pyplot(fig_away_shot)

    with col_right:
        st.markdown(f"<h3 style='text-align: center; color: {AWAY_COLOR};'>Pass Network</h3>", unsafe_allow_html=True)
        
        away_passes = events[(events['end_type'] == 'pass') & (events['team_id'] == metadata['away_team_id'])]
        
        away_starters = set()
        if dataset:
             try:
                 p1_frames = [f for f in dataset.records if f.period.id == 1]
                 if p1_frames:
                     first_frame = p1_frames[0]
                     away_starters = {int(p.player_id) for p in first_frame.players_coordinates.keys() if p.team.team_id == metadata['away_team_id']}
             except Exception as e:
                 pass
        
        if not away_starters:
            away_starters = {int(p['player_id']) for p in metadata['away_players'] if p['position'] and p['position'] != 'None'}
        
        away_player_pos = away_passes.groupby(['player_id', 'player_name']).agg({
            'x_start': 'mean',
            'y_start': 'mean'
        }).reset_index().rename(columns={'x_start': 'x', 'y_start': 'y', 'player_name': 'name'})
        
        away_player_pos['node_color'] = away_player_pos['player_id'].apply(
            lambda pid: AWAY_COLOR if pid in away_starters else "#32FF69"
        )
        
        if 'player_targeted_id' in away_passes.columns:
             away_pass_network_df = away_passes[['player_id', 'player_targeted_id']].rename(
                 columns={'player_id': 'passer_id', 'player_targeted_id': 'receiver_id'}
             ).dropna()
        else:
            away_pass_network_df = pd.DataFrame(columns=['passer_id', 'receiver_id'])

        fig_away_pass, _ = visualizations.plot_vertical_pass_network(
            away_pass_network_df,
            away_player_pos,
            pitch_length=pitch_length,
            pitch_width=pitch_width,
            pitch_color='white',
            line_color='gray',
            node_color=AWAY_COLOR,
            title=""
        )
        st.pyplot(fig_away_pass)
        
        st.markdown("---")
        st.markdown("#### Start XI")
        st.markdown(visualizations.render_lineup_html(metadata['away_players'], AWAY_COLOR), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
