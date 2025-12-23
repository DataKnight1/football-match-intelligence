"""
Author: Tiago Monteiro
Date: 22-12-2025
Player comparison dashboard allowing head-to-head analysis of two players including tactical, physical, and direct duel metrics.
"""
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src import data_loader, utils, visualizations, preprocessing, styling
from src.visualizations import scatter, radarPolygon, swarm

styling.setup_page("Player Comparison")

def load_data_cached(match_id):
    """
    Load tracking data and events for the specified match.
    """
    dataset = data_loader.load_match_data(match_id, sample_rate=1.0, limit=None)
    metadata = data_loader.get_match_metadata(dataset, match_id)
    tracking_data = dataset.to_df(engine="pandas")
    
    events = data_loader.load_dynamic_events(match_id)
    return tracking_data, events, metadata

def get_player_team_id(player_id, metadata):
    """
    Retrieve the team ID for a given player.

    :param player_id: The ID of the player to find.
    :param metadata: The match metadata containing player information.
    :return: The team ID of the player, or None if not found.
    """
    for p in metadata.get('home_players', []):
        if p['player_id'] == player_id: return metadata['home_team_id']
    for p in metadata.get('away_players', []):
        if p['player_id'] == player_id: return metadata['away_team_id']
    return None

def process_match_wide_metrics(tracking_df, events_df, metadata, fps=10):
    """
    Calculate metrics for ALL players in the match to enable population comparison.
    """
    player_stats = []
    
    all_players = metadata.get('home_players', []) + metadata.get('away_players', [])
    
    for p in all_players:
        pid = p['player_id']
        team_id = p['team_id']
        name = p['name']
        
        raw_pos = p.get('detailed_position')
        if not raw_pos or str(raw_pos).lower() in ['none', 'nan', 'unknown', 'substitute', 'none']:
             raw_pos = p.get('position')
             
        s_pos = str(raw_pos).upper().strip()
        
        mapping = {
            'GK': 'GR', 'GOALKEEPER': 'GR',
            'RWB': 'RB',
            'LWB': 'LB',
            'CDM': 'DM', 'LDM': 'DM', 'RDM': 'DM',
            'CAM': 'AM', 'RAC': 'RAM', 'LAC': 'LAM',
            'RM': 'RW',
            'LM': 'LW',
            'ST': 'CF', 'LS': 'CF', 'RS': 'CF', 'SS': 'CF', 'FORWARD': 'CF',
            'RB': 'RB', 'LB': 'LB', 'RCB': 'RCB', 'LCB': 'LCB', 'CB': 'RCB',
            'DM': 'DM', 'RW': 'RW', 'LW': 'LW', 'CF': 'CF', 'AM': 'AM', 'LAM': 'LAM', 'RAM': 'RAM', 'GR': 'GR'
        }
        
        group = mapping.get(s_pos, s_pos)
        
        if group == 'CB': group = 'RCB'
        
        cols = [f"{pid}_x", f"{pid}_y"]
        if cols[0] in tracking_df.columns:
            p_tracks = tracking_df[cols].dropna()
            if not p_tracks.empty:
                phys = preprocessing.calculate_distance_metrics(
                    p_tracks[cols[0]].values,
                    p_tracks[cols[1]].values,
                    fps=fps
                )
            else:
                phys = {'total_distance': 0, 'sprint_distance': 0, 'hsr_distance': 0, 'max_speed': 0, 'avg_speed': 0}
        else:
            phys = {'total_distance': 0, 'sprint_distance': 0, 'hsr_distance': 0, 'max_speed': 0, 'avg_speed': 0}

        tactical = preprocessing.calculate_tactical_events(events_df, pid)
        
        threat = (tactical['shots'] * 2.0) + \
                 (tactical['prog_passes'] * 1.0) + \
                 (tactical['dribbles'] * 1.0) + \
                 (tactical['off_ball_runs'] * 0.5)
        
        stats = {
            'player_id': pid,
            'name': name,
            'team_id': team_id,
            'position': group,
            'total_dist_km': phys['total_distance'] / 1000,
            'hsr_dist_m': phys['hsr_distance'],
            'sprint_dist_m': phys['sprint_distance'],
            'max_speed_kmh': phys['max_speed'],
            'threat_score': threat,
            **tactical
        }
        player_stats.append(stats)
        
    return pd.DataFrame(player_stats)

def main():
    """
    Main function to render the Player Comparison page.
    Handles match selection, player selection, metric calculations, and renders all comparison visualizations.
    """
    styling.load_css()
    st.markdown("## Tactical Head-to-Head")
    
    st.sidebar.markdown("## Filters")
    matches = data_loader.get_available_matches()
    match_options = {f"{desc}": mid for mid, desc in matches.items()}
    
    selected_match_str = st.sidebar.selectbox("Select Match", list(match_options.keys()))
    selected_match_id = match_options[selected_match_str]
    
    with st.spinner("Loading tactical data..."):
        try:
            tracking_df, events_df, metadata = load_data_cached(selected_match_id)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if 'match_stats_df' not in st.session_state or st.session_state.get('last_match_id') != selected_match_id:
        with st.spinner("Processing player statistics (this may take a moment)..."):
            match_stats_df = process_match_wide_metrics(tracking_df, events_df, metadata)
            st.session_state['match_stats_df'] = match_stats_df
            st.session_state['last_match_id'] = selected_match_id
    else:
        match_stats_df = st.session_state['match_stats_df']

    player_options = {}
    for p in metadata.get('home_players', []):
        player_options[f"{p['name']} ({metadata.get('home_team_name')})"] = p['player_id']
    for p in metadata.get('away_players', []):
        player_options[f"{p['name']} ({metadata.get('away_team_name')})"] = p['player_id']
    
    if not player_options:
        st.error("No player metadata found for this match.")
        return
    
    keys = list(player_options.keys())
    
    col1, col2 = st.columns(2)
    with col1:
        p1_name = st.selectbox("Select Player 1", keys, index=0)
        p1_id = player_options[p1_name] if p1_name else None
    with col2:
        idx_2 = 1 if len(keys) > 1 else 0
        p2_name = st.selectbox("Select Player 2", keys, index=idx_2)
        p2_id = player_options[p2_name] if p2_name else None
        
    if not p1_id or not p2_id:
        st.warning("Please select valid players.")
        return
        
    if p1_id == p2_id:
        st.warning("Select two different players for comparison.")
        return
        
    t1_id = get_player_team_id(p1_id, metadata)
    t2_id = get_player_team_id(p2_id, metadata)
    
    p1_short = p1_name.split(' (')[0]
    p2_short = p2_name.split(' (')[0]

    with st.spinner("Calculating detailed metrics..."):
        p1_cols_exist = all(col in tracking_df.columns for col in [f"{p1_id}_x", f"{p1_id}_y"])
        p2_cols_exist = all(col in tracking_df.columns for col in [f"{p2_id}_x", f"{p2_id}_y"])
        
        if not p1_cols_exist or not p2_cols_exist:
            st.error(f"⚠️ Tracking data not available for the selected players.")
            st.info("This may happen if players did not participate in the match or tracking data is incomplete.")
            if not p1_cols_exist:
                st.warning(f"Missing tracking data for: {p1_short}")
            if not p2_cols_exist:
                st.warning(f"Missing tracking data for: {p2_short}")
            return
        
        df_a = tracking_df[[f"{p1_id}_x", f"{p1_id}_y"]].dropna()
        df_b = tracking_df[[f"{p2_id}_x", f"{p2_id}_y"]].dropna()

        metrics_a = preprocessing.calculate_distance_metrics(df_a[f"{p1_id}_x"].values, df_a[f"{p1_id}_y"].values)
        metrics_b = preprocessing.calculate_distance_metrics(df_b[f"{p2_id}_x"].values, df_b[f"{p2_id}_y"].values)
        
        split_a = preprocessing.calculate_split_physical_stats(tracking_df, p1_id, t1_id)
        split_b = preprocessing.calculate_split_physical_stats(tracking_df, p2_id, t2_id)
        
        tact_a = preprocessing.calculate_tactical_events(events_df, p1_id)
        tact_b = preprocessing.calculate_tactical_events(events_df, p2_id)

        duel_mins, duel_df = preprocessing.calculate_proximity_stats(tracking_df, p1_id, p2_id)
    
    st.markdown("### Physical Profiling")
    
    col_scat, col_stats = st.columns([2, 1])
    
    with col_scat:
        fig_scatter = scatter.plot_physical_scatter(
            match_stats_df,
            x_metric='total_dist_km',
            y_metric='hsr_dist_m',
            x_label='Total Distance (km)',
            y_label='HSR Distance (>20km/h) (m)',
            highlight_p1_id=p1_id,
            highlight_p2_id=p2_id,
            p1_name=p1_short,
            p2_name=p2_short
        )
        st.pyplot(fig_scatter)
        plt.close(fig_scatter)
        
    with col_stats:
        st.markdown("#### Comparison")
        st.metric(f"Total Dist", 
                  f"{metrics_a['total_distance']/1000:.2f} km",
                  delta=f"{(metrics_a['total_distance'] - metrics_b['total_distance'])/1000:.2f} km")
        
        st.metric(f"HSR Dist", 
                  f"{metrics_a['hsr_distance']:.0f} m",
                  delta=f"{metrics_a['hsr_distance'] - metrics_b['hsr_distance']:.0f} m")
        
        st.metric(f"Max Speed", 
                  f"{metrics_a['max_speed']:.1f} km/h",
                  delta=f"{metrics_a['max_speed'] - metrics_b['max_speed']:.1f} km/h")

    st.markdown("---")
    
    st.markdown("### Tactical Run Profile")
    
    c_rad1, c_rad2 = st.columns(2)
    
    run_metrics = ['passes', 'prog_passes', 'dribbles', 'shots', 'off_ball_runs']
    run_labels = {
        'passes': 'Volume', 
        'prog_passes': 'Progression', 
        'dribbles': 'Carry', 
        'shots': 'Finish', 
        'off_ball_runs': 'Movement'
    }
    
    with c_rad1:
        st.markdown(f"**{p1_short}**")
        fig_rad1 = radarPolygon.plot_run_stats_radar(
            match_stats_df, p1_id, run_metrics, run_labels, 
            title="Play Style", highlight_color='#32FF69'
        )
        st.pyplot(fig_rad1)
        plt.close(fig_rad1)
        
    with c_rad2:
        st.markdown(f"**{p2_short}**")
        fig_rad2 = radarPolygon.plot_run_stats_radar(
            match_stats_df, p2_id, run_metrics, run_labels, 
            title="Play Style", highlight_color='#3385FF'
        )
        st.pyplot(fig_rad2)
        plt.close(fig_rad2)
        
    st.markdown("---")
    
    st.markdown("### Threat Distribution")
    st.info("Swarm plot showing where these players sit compared to positional peers based on composite Threat Score.")
    
    pos_order = ['GR', 'RB', 'RCB', 'LCB', 'LB', 'DM', 'RW', 'LW', 'CF', 'AM', 'LAM', 'RAM']
    
    fig_swarm = swarm.plot_swarm_violin(
        match_stats_df,
        y_metric='threat_score',
        x_group='position',
        y_label='Threat Score',
        title='League Context: Threat Score by Position',
        highlight_p1_id=p1_id,
        highlight_p2_id=p2_id,
        p1_name=p1_short,
        p2_name=p2_short,
        order=pos_order
    )
    st.pyplot(fig_swarm)
    plt.close(fig_swarm)

    st.markdown("---")
    
    st.markdown("### Technical Performance (Pizza)")
    
    params = [
        "Passes", "Prog Passes", "Dribbles", 
        "Shots", "Crosses", 
        "Interceptions", "Tackles", "Recoveries"
    ]
    
    min_a = 90
    min_b = 90
    if len(df_a) > 0: min_a = len(df_a) / 600
    if len(df_b) > 0: min_b = len(df_b) / 600
    
    f_a = 90 / min_a if min_a > 10 else 1
    f_b = 90 / min_b if min_b > 10 else 1

    values_a = [
        tact_a['passes'] * f_a,
        tact_a['prog_passes'] * f_a,
        tact_a['dribbles'] * f_a,
        tact_a['shots'] * f_a,
        tact_a['crosses'] * f_a,
        tact_a['interceptions'] * f_a,
        tact_a['tackles'] * f_a,
        tact_a['recoveries'] * f_a
    ]

    values_b = [
        tact_b['passes'] * f_b,
        tact_b['prog_passes'] * f_b,
        tact_b['dribbles'] * f_b,
        tact_b['shots'] * f_b,
        tact_b['crosses'] * f_b,
        tact_b['interceptions'] * f_b,
        tact_b['tackles'] * f_b,
        tact_b['recoveries'] * f_b
    ]
    
    ranges = {
        "Passes": (0, 80),
        "Prog Passes": (0, 15),
        "Dribbles": (0, 10),
        "Shots": (0, 5),
        "Crosses": (0, 10),
        "Interceptions": (0, 8),
        "Tackles": (0, 8),
        "Recoveries": (0, 12)
    }
    
    min_range = [ranges[p][0] for p in params]
    max_range = [ranges[p][1] for p in params]
    
    col_rad_l, col_rad_viz, col_rad_r = st.columns([1, 2, 1])
    with col_rad_viz:
        st.markdown(f"#### Head-to-Head: {p1_short} vs {p2_short}")
        fig_pizza = visualizations.plot_comparison_pizza(
            params, values_a, values_b, 
            p1_short, p2_short,
            min_range=min_range, max_range=max_range
        )
        st.pyplot(fig_pizza)
        plt.close(fig_pizza)
        
    st.markdown("---")
    
    st.markdown("### Phase Breakdown")
    
    col_in, col_out = st.columns(2)
    
    with col_in:
        st.markdown("#### In Possession (Attacking)")
        st.markdown(f"**{p1_short}** vs **{p2_short}**")
        st.metric("Attacking Distance", f"{split_a['in_poss_dist']:.1f} km",
                 delta=f"{split_a['in_poss_dist'] - split_b['in_poss_dist']:.1f} km")
        st.metric("Sprint Distance (Att)", f"{split_a['in_poss_sprint']:.0f} m",
                 delta=f"{split_a['in_poss_sprint'] - split_b['in_poss_sprint']:.0f} m")
        st.metric("Progressive Passes", f"{tact_a['prog_passes']}",
                 delta=f"{tact_a['prog_passes'] - tact_b['prog_passes']}")
        st.metric("Off-Ball Runs", f"{tact_a['off_ball_runs']}",
                 delta=f"{tact_a['off_ball_runs'] - tact_b['off_ball_runs']}")

    with col_out:
        st.markdown("#### Out of Possession (Defending)")
        st.markdown(f"**{p1_short}** vs **{p2_short}**")
        st.metric("Defensive Workrate (Dist)", f"{split_a['out_poss_dist']:.1f} km",
                 delta=f"{split_a['out_poss_dist'] - split_b['out_poss_dist']:.1f} km")
        st.metric("Pressing/Recovery Sprints", f"{split_a['out_poss_sprint']:.0f} m",
                 delta=f"{split_a['out_poss_sprint'] - split_b['out_poss_sprint']:.0f} m")

    st.markdown("---")
    
    st.markdown("### Direct Interaction")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### Direct Duels Map")
        st.markdown(f"Time Spent Head-to-Head (<8m): **{duel_mins:.1f} min**")
        fig_duel = visualizations.plot_proximity_map(duel_df, title=f"Clash Zones: {p1_short} vs {p2_short}")
        st.pyplot(fig_duel)
        plt.close(fig_duel)
        
    with c2:
        st.markdown("#### Space Dominance (Delta Map)")
        st.markdown(f"Green = {p1_short} | Purple = {p2_short}")
        
        if all(col in tracking_df.columns for col in [f"{p1_id}_x", f"{p1_id}_y", f"{p2_id}_x", f"{p2_id}_y"]):
            p1_tracks = tracking_df[[f"{p1_id}_x", f"{p1_id}_y"]].dropna().rename(
                columns={f"{p1_id}_x": 'x', f"{p1_id}_y": 'y'}
            )
            p2_tracks = tracking_df[[f"{p2_id}_x", f"{p2_id}_y"]].dropna().rename(
                columns={f"{p2_id}_x": 'x', f"{p2_id}_y": 'y'}
            )
            
            fig_delta = visualizations.plot_delta_heatmap(
                p1_tracks, p2_tracks, p1_short, p2_short
            )
            st.pyplot(fig_delta)
            plt.close(fig_delta)
        else:
            st.warning("Tracking data unavailable for delta heatmap visualization.")

if __name__ == "__main__":
    main()
