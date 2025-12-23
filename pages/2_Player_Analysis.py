"""
Author: Tiago Monteiro
Date: 21-12-2025
Player analysis dashboard providing detailed tactical, physical, and movement profiles for individual players.
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent.parent))

from src import visualizations, preprocessing, metrics, utils, styling, data_loader
from src.preprocessing.time import calculate_match_clock, get_period_starts

styling.setup_page("Player Analysis")

PRIMARY_COLOR = "#32FF69"

def determine_player_style(player_df, events_df, player_id):
    """
    Determine player style badge based on metrics.

    :param player_df: DataFrame containing player tracking data.
    :param events_df: DataFrame containing match event data.
    :param player_id: The ID of the player to analyze.
    :return: A string representing the player's style badge.
    """
    badges = []
    
    if not events_df.empty:
        p_events = events_df[events_df['player_id'] == player_id]
        lb_passes = len(p_events[p_events['event_type'] == 'line_breaking_pass'])
        if lb_passes > 5:
            badges.append("Progressor")
            
        runs = len(p_events[p_events['event_type'] == 'off_ball_run'])
        if runs > 20:
            badges.append("Raumdeuter")
            
    if not player_df.empty:
        total_dist = 0 
        
    return badges[0] if badges else "Generalist"

def main():
    """
    Main function to render the Player Analysis page.
    Handles data loading, player selection, and rendering of tactical, physical, and movement analysis tabs.
    """
    styling.load_css()

    st.sidebar.markdown("## Filters")
    matches = data_loader.get_available_matches()
    match_options = {f"{desc}": mid for mid, desc in matches.items()}
    
    current_match_id = st.session_state.get('match_id')
    default_index = 0
    if current_match_id in match_options.values():
        val_list = list(match_options.values())
        default_index = val_list.index(current_match_id)

    selected_match_str = st.sidebar.selectbox("Select Match", list(match_options.keys()), index=default_index)
    selected_match_id = match_options[selected_match_str]
    
    if selected_match_id != st.session_state.get('match_id'):
        st.session_state['match_id'] = selected_match_id
        if 'dataset' in st.session_state: del st.session_state['dataset']
        if 'events' in st.session_state: del st.session_state['events']
        if 'metadata' in st.session_state: del st.session_state['metadata']
        st.rerun()

    match_id = selected_match_id
    
    @st.cache_resource(ttl=3600)
    def load_full_match_cached(match_id):
        """
        Load full match data with caching.

        :param match_id: The ID of the match to load.
        :return: The loaded match data object.
        """
        return data_loader.load_match_data(match_id, sample_rate=0.1) 

    dataset = st.session_state.get('dataset')
    
    need_reload = False
    if dataset is None:
        need_reload = True
    else:
        if hasattr(dataset, 'frames') and len(dataset.frames) < 500:
            need_reload = True
        elif hasattr(dataset, 'records') and len(dataset.records) < 500: 
            need_reload = True
            
    if need_reload:
        with st.spinner("Loading full match data for analysis (this may take a moment)..."):
            dataset = load_full_match_cached(match_id)
            st.session_state['dataset'] = dataset
            params_meta = data_loader.get_match_metadata(dataset, match_id=match_id)
            st.session_state['metadata'] = params_meta

    metadata = st.session_state['metadata']

    if 'events' not in st.session_state or st.session_state.get('events') is None or st.session_state.get('events').empty:
        events = data_loader.load_dynamic_events(match_id)
        st.session_state['events'] = events
    else:
        events = st.session_state['events']
        
    if 'phases' not in st.session_state:
        phases_df = data_loader.load_phases_of_play(match_id)
        st.session_state['phases'] = phases_df
    else:
        phases_df = st.session_state.get('phases')
    
    all_players = []
    for p in metadata['home_players']:
        p['team'] = metadata['home_team_name']
        all_players.append(p)
    for p in metadata['away_players']:
        p['team'] = metadata['away_team_name']
        all_players.append(p)
        
    player_options = {f"{p['name']} ({p['team']})": p['player_id'] for p in all_players}
    
    selected_player_id = st.sidebar.selectbox("Select Player", list(player_options.values()), 
                                              format_func=lambda x: [k for k, v in player_options.items() if v == x][0])
    
    player_info = next((p for p in all_players if p['player_id'] == selected_player_id), None)
    
    if player_info is None:
        st.warning("No player selected or player info not found.")
        return

    player_id = player_info['player_id']
    player_name = player_info['name']
    team_selection = player_info['team']
    role = player_info.get('detailed_position', player_info.get('position', 'Unknown'))

    if team_selection == metadata['home_team_name']:
        team_id = metadata['home_team_id']
        team_color = utils.get_team_color(metadata['home_team_name'])
    else:
        team_id = metadata['away_team_id']
        team_color = utils.get_team_color(metadata['away_team_name'])
    
    player_df = preprocessing.extract_player_data(dataset, player_info.get('kloppy_id', player_id))

    if player_df.empty:
        st.warning("No tracking data available for this player.")
        return

    badge = determine_player_style(player_df, events, player_id)

    st.markdown(f"""
    <div style='padding: 2rem; background: linear-gradient(135deg, {team_color}CC 0%, {team_color} 100%);
                border-radius: 16px; margin-bottom: 2rem; color: white;
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);'>
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.9rem; font-weight: 600;">
                    {team_selection}
                </span>
                <h1 style='margin: 10px 0 5px 0; font-size: 3rem; font-weight: 800; letter-spacing: -1px;'>
                    {player_name}
                </h1>
                </h1>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <span style="font-size: 1.2rem; font-weight: 500; opacity: 0.9;">
                        {role}
                    </span>
                </div>
            </div>
            <div style="text-align: right; opacity: 0.8;">
                 <h3 style="margin:0; font-size: 2rem;">#{player_info.get('jersey_no', '')}</h3>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Tactical Profile", 
        "Physical Profile", 
        "Movement Analysis",
        "On-Ball Actions"
    ])

    if 'x_smooth' in player_df.columns and 'y_smooth' in player_df.columns:
        distance_metrics = preprocessing.calculate_distance_metrics(
            player_df['x_smooth'].values, 
            player_df['y_smooth'].values
        )
    else:
        distance_metrics = preprocessing.calculate_distance_metrics(
            player_df['x'].values, 
            player_df['y'].values
        )
    
    periods_data = metadata.get('periods_extra', metadata.get('periods', []))
    if periods_data:
        player_df = preprocessing.calculate_match_minute(player_df, periods_data)
        
    minutes_played = 0
    if player_info and player_info.get('minutes_played') is not None:
         
        try:
            minutes_played = int(float(player_info['minutes_played']))
        except:
             pass
             
    if minutes_played == 0 and not player_df.empty and 'period' in player_df.columns:
        for pid in player_df['period'].unique():
            p_data = player_df[player_df['period'] == pid]
            if not p_data.empty:
                duration_mins = (p_data['frame'].max() - p_data['frame'].min()) / 600
                minutes_played += duration_mins
        
        minutes_played = int(round(minutes_played))
        
    if minutes_played == 0 and not player_df.empty:
         minutes_played = int(len(player_df) / 600)
    
    if not phases_df.empty:
        phases_df.columns = [c.lower().replace(' ', '_') for c in phases_df.columns]
        
        if 'start_frame' not in phases_df.columns:
            if 'start' in phases_df.columns:
                phases_df['start_frame'] = phases_df['start']
            elif 'phase_start' in phases_df.columns:
                phases_df['start_frame'] = phases_df['phase_start']
            elif 'frame_start' in phases_df.columns:
                phases_df['start_frame'] = phases_df['frame_start']
                
            if 'end' in phases_df.columns:
                phases_df['end_frame'] = phases_df['end']
            elif 'phase_end' in phases_df.columns:
                phases_df['end_frame'] = phases_df['phase_end']
            elif 'frame_end' in phases_df.columns:
                phases_df['end_frame'] = phases_df['frame_end']
                
            if 'possession_team_id' not in phases_df.columns:
                if 'team_in_possession_id' in phases_df.columns:
                     phases_df['possession_team_id'] = phases_df['team_in_possession_id']
                
            if 'possession_phase' not in phases_df.columns:
                if 'team_in_possession_phase_type' in phases_df.columns:
                    phases_df['possession_phase'] = phases_df['team_in_possession_phase_type']
                    
            if 'non_possession_phase' not in phases_df.columns:
                if 'team_out_of_possession_phase_type' in phases_df.columns:
                    phases_df['non_possession_phase'] = phases_df['team_out_of_possession_phase_type']
                
        if 'start_frame' not in phases_df.columns or 'end_frame' not in phases_df.columns:
            st.warning("Could not identify phase start/end frames in data. Phase analysis disabled.")
            phases_df = pd.DataFrame() 
    
    if not phases_df.empty:
        
        player_df['tactical_phase'] = None
        
        for _, phase in phases_df.iterrows():
            mask = (player_df['frame'] >= phase['start_frame']) & (player_df['frame'] <= phase['end_frame'])
            if phase['possession_team_id'] == team_id:
                player_df.loc[mask, 'tactical_phase'] = f"Attacking: {phase['possession_phase']}"
                player_df.loc[mask, 'phase_type'] = 'In Possession'
            else:
                player_df.loc[mask, 'tactical_phase'] = f"Defending: {phase['non_possession_phase']}"
                player_df.loc[mask, 'phase_type'] = 'Out of Possession'

    with tab1:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("### Tactical Context")
            st.metric("Minutes Played", f"{minutes_played:.0f}'")
            
            territory_area = 0
            if len(player_df) >= 3:
                try:
                    from scipy.spatial import ConvexHull
                    points = np.column_stack([player_df['x'].values, player_df['y'].values])
                    hull = ConvexHull(points)
                    territory_area = hull.volume
                except:
                    pass
            st.metric("Territory Coverage", f"{territory_area:.0f} m²")
            
            if 'tactical_phase' in player_df.columns:
                phase_counts = player_df['tactical_phase'].value_counts()
                st.markdown("#### Time by Phase")
                st.dataframe(phase_counts, height=200, use_container_width=True)
            
        with col2:
            st.markdown("### Positional Discipline")
            
            if 'phase_type' in player_df.columns:
                heatmap_mode = st.radio("Select Phase Mode", ["All", "In Possession", "Out of Possession"], 
                                      horizontal=True, key="heatmap_mode")
                
                filtered_df = player_df.copy()
                if heatmap_mode == "In Possession":
                    filtered_df = player_df[player_df['phase_type'] == 'In Possession']
                elif heatmap_mode == "Out of Possession":
                    filtered_df = player_df[player_df['phase_type'] == 'Out of Possession']
                
                if not filtered_df.empty:
                    col_hm, col_hull = st.columns(2)
                    with col_hm:
                        st.markdown(f"**Heatmap ({heatmap_mode})**")
                        fig, ax = visualizations.plot_advanced_heatmap(
                            filtered_df['x'].values,
                            filtered_df['y'].values,
                            title="",
                            pitch_color='#F8F8F6',
                            line_color='#CCCCCC',
                            hexbin=True,
                            gridsize=20,
                            cmap='Greens' if heatmap_mode != "Out of Possession" else 'Reds'
                        )
                        st.pyplot(fig)
                        
                    with col_hull:
                        st.markdown(f"**Territory ({heatmap_mode})**")
                        fig, ax = visualizations.plot_convex_hull(
                            filtered_df['x'].values,
                            filtered_df['y'].values,
                            poly_color=PRIMARY_COLOR if heatmap_mode != "Out of Possession" else '#FF3333',
                            pitch_color='#F8F8F6',
                            line_color='#CCCCCC',
                            title=""
                        )
                        st.pyplot(fig)
                else:
                    st.info(f"No data for {heatmap_mode}")
            else:
                fig, ax = visualizations.plot_advanced_heatmap(
                    player_df['x'].values,
                    player_df['y'].values,
                    pitch_color='#F8F8F6',
                    hexbin=True
                )
                st.pyplot(fig)

    with tab2:
        st.markdown("### Physical Output")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Distance", f"{distance_metrics['total_distance']/1000:.2f} km")
        col2.metric("Sprint Distance", f"{distance_metrics['sprint_distance']:.0f} m")
        col3.metric("Top Speed", f"{distance_metrics['max_speed']:.1f} km/h")
        col4.metric("HSR Distance", f"{distance_metrics['hsr_distance']:.0f} m")

        st.markdown("---")
        
        if 'tactical_phase' in player_df.columns and 'velocity' in player_df.columns:
            st.markdown("#### Energy Expenditure by Phase")
            
            player_df['dist_frame'] = np.sqrt(player_df['x'].diff()**2 + player_df['y'].diff()**2).fillna(0)
            
            phase_stats = player_df.groupby('tactical_phase')['dist_frame'].sum().reset_index()
            phase_stats['Distance (m)'] = phase_stats['dist_frame']
            
            fig_pizza = visualizations.plot_energy_expenditure_pizza(phase_stats)
            st.pyplot(fig_pizza)
            
            st.markdown("#### Speed Zones")
            
            fps = getattr(dataset.metadata, 'frame_rate', 10.0) if dataset else 10.0
            
            time_deltas = player_df['time_delta'].values if 'time_delta' in player_df.columns else None
            
            fig = visualizations.plot_speed_distribution(
                player_df['velocity_kmh'], 
                title="Speed Zones", 
                fps=fps, 
                time_deltas=time_deltas,
                max_speed=distance_metrics['max_speed']
            )
            st.pyplot(fig)

    with tab3:
        st.markdown("### Off-Ball Movement Profile")
        
        if not events.empty:
            p_events = events[events['player_id'] == int(player_id)]
            runs = p_events[p_events['event_type'] == 'off_ball_run'].copy()
            
            if 'event_subtype' in runs.columns and 'run_type' not in runs.columns:
                runs['run_type'] = runs['event_subtype']
            if 'targeted' in runs.columns and 'is_targeted' not in runs.columns:
                runs['is_targeted'] = runs['targeted']
            if 'received' in runs.columns and 'is_received' not in runs.columns:
                runs['is_received'] = runs['received']
            
            if not runs.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Run Types")
                    if 'run_type' in runs.columns:
                        run_counts = runs['run_type'].value_counts()
                        
                        fig_pizza = visualizations.plot_run_types_pizza(run_counts)
                        st.pyplot(fig_pizza)
                    else:
                         st.info(f"Run type data not available. Columns: {runs.columns.tolist()}")

                with col2:
                    st.markdown("#### Run Efficiency")
                    total_runs = len(runs)
                    targeted_runs = len(runs[runs['is_targeted'] == True]) if 'is_targeted' in runs.columns else 0
                    received_runs = len(runs[runs['is_received'] == True]) if 'is_received' in runs.columns else 0
                    
                    efficiency_data = pd.DataFrame({
                        'Stage': ['Total Runs', 'Targeted', 'Received'],
                        'Count': [total_runs, targeted_runs, received_runs]
                    })
                    
                    fig = px.funnel(efficiency_data, x='Count', y='Stage', title="",
                                  color_discrete_sequence=['#32FF69', '#28CC54', '#1E993F'])
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig)
            else:
                st.info("No off-ball runs detected.")
        else:
            st.info("No event data available.")

    with tab4:
        st.markdown("### On-Ball Actions & Progression")
        
        if not events.empty:
            p_events = events[events['player_id'] == int(player_id)]
            
            st.markdown("#### Interactive Event Timeline (Click to View)")
            
            periods_data = metadata.get('match_periods', metadata.get('periods', []))
            
            start_col = 'start_frame' if 'start_frame' in p_events.columns else 'frame_start'
            end_col = 'end_frame' if 'end_frame' in p_events.columns else 'frame_end'
            
            if start_col in p_events.columns:
                p_events_viz = p_events.copy()
                p_events_viz['frame'] = p_events_viz[start_col]
                
                if periods_data:
                     try:
                         p_events_viz['frame'] = pd.to_numeric(p_events_viz['frame'], errors='coerce')
                         p_events_viz = preprocessing.calculate_match_minute(p_events_viz, periods_data)
                     except Exception as e:
                         st.warning(f"Could not calculate match minute with periods logic: {e}")
                         p_events_viz['match_minute'] = (p_events_viz[start_col] / 600).fillna(0).astype(int)
                else:
                     p_events_viz['match_minute'] = (p_events_viz['frame'] / 600).fillna(0).astype(int)
                
                if 'end_type' in p_events_viz.columns:
                    p_events_viz['Event'] = p_events_viz.apply(
                        lambda x: x['end_type'].replace('_', ' ').title() if pd.notna(x.get('end_type')) and x['event_type'] == 'player_possession' 
                        else (x['event_subtype'].replace('_', ' ').title() if pd.notna(x.get('event_subtype')) 
                              else x['event_type'].replace('_', ' ').title()), 
                        axis=1
                    )
                else:
                    p_events_viz['Event'] = p_events_viz['event_type'].astype(str).str.replace('_', ' ').str.title()
                
                p_events_viz = p_events_viz.sort_values(start_col).reset_index(drop=True)
                
                fps = getattr(dataset.metadata, 'frame_rate', 10.0) if dataset else 10.0
                period_starts = get_period_starts(metadata)
                
                event_options = []
                for i, row in p_events_viz.iterrows():
                    evt_period = row.get('period', 1)
                    if 'period' not in row and period_starts:
                         p2_start = period_starts.get(2, 999999)
                         if row[start_col] >= p2_start:
                             evt_period = 2
                             
                    clock_str = calculate_match_clock(
                        frame=row[start_col], 
                        period=evt_period, 
                        period_start_frames=period_starts, 
                        fps=fps
                    )
                    event_options.append(f"{i}: {row['Event']} ({clock_str})")
                
                if 'timeline_idx' not in st.session_state:
                    st.session_state.timeline_idx = 0
                
                if st.session_state.timeline_idx >= len(p_events_viz):
                    st.session_state.timeline_idx = 0
                
                selected_event_str = st.selectbox("Select Event to View:", options=event_options, index=st.session_state.timeline_idx)
                
                selected_idx = int(selected_event_str.split(':')[0])
                if selected_idx != st.session_state.timeline_idx:
                    st.session_state.timeline_idx = selected_idx
                    
                total_events = len(p_events_viz)
                
                if total_events > 0:
                    col_prev, col_info, col_next = st.columns([1, 4, 1])
                    
                    with col_prev:
                        if st.button("Previous"):
                            st.session_state.timeline_idx = max(0, st.session_state.timeline_idx - 1)
                            st.rerun()
                    
                    with col_next:
                        if st.button("Next"):
                            st.session_state.timeline_idx = min(total_events - 1, st.session_state.timeline_idx + 1)
                            st.rerun()
                            
                    if st.session_state.timeline_idx >= total_events:
                        st.session_state.timeline_idx = total_events - 1
                        
                    current_idx = st.session_state.timeline_idx
                    current_event = p_events_viz.iloc[current_idx]
                    
                    with col_info:
                        pass
                    
                    start_f = int(current_event[start_col]) - 50 
                    end_f = int(current_event[end_col]) + 50     
                    context_label = "Sequence Context"
                    
                    if 'phase_index' in current_event and 'phase_index' in events.columns:
                        phase_idx = current_event['phase_index']
                        
                        phase_events = events[events['phase_index'] == phase_idx]
                        if not phase_events.empty:
                            start_f = int(phase_events[start_col].min())
                            end_f = int(phase_events[end_col].max())
                            start_f -= 10
                            end_f += 10
                            context_label = f"Full Sequence (Phase {phase_idx})"

                    import matplotlib.pyplot as plt
                    from mplsoccer import Pitch
                    
                    fig_traj, ax = plt.subplots(figsize=(10, 6))
                    pitch = Pitch(pitch_type='skillcorner', pitch_length=105, pitch_width=68, 
                                 pitch_color='#F8F8F6', line_color='#A9A9A9')
                    pitch.draw(ax=ax)
                    
                    subset_df = player_df[(player_df['frame'] >= start_f) & (player_df['frame'] <= end_f)].copy()
                    
                    if not subset_df.empty:
                        pitch.plot(subset_df['x'], subset_df['y'], ax=ax, color='#D3D3D3', linewidth=2, alpha=0.6, label=context_label, zorder=1)
                        
                        if len(subset_df) > 10:
                            skip = 10
                            pitch.arrows(subset_df['x'].iloc[::skip][:-1], subset_df['y'].iloc[::skip][:-1],
                                        subset_df['x'].iloc[::skip][1:], subset_df['y'].iloc[::skip][1:],
                                        ax=ax, width=1, color='#D3D3D3', alpha=0.5, zorder=1)

                        evt_start_f_exact = current_event[start_col]
                        evt_end_f_exact = current_event.get(end_col, evt_start_f_exact + 10) 
                        
                        event_segment = subset_df[(subset_df['frame'] >= evt_start_f_exact) & (subset_df['frame'] <= evt_end_f_exact)]
                        
                        if not event_segment.empty:
                            pitch.plot(event_segment['x'], event_segment['y'], ax=ax, color='#32FF69', linewidth=4, alpha=1.0, label='Event Action', zorder=4)
                            
                            pitch.arrows(event_segment['x'].iloc[:-1], event_segment['y'].iloc[:-1],
                                         event_segment['x'].iloc[1:], event_segment['y'].iloc[1:],
                                         ax=ax, width=3, color='#32FF69', alpha=0.8, zorder=4)
                            
                            pitch.scatter(event_segment.iloc[0]['x'], event_segment.iloc[0]['y'], ax=ax, c='#32FF69', s=100, marker='o', edgecolors='black', zorder=6)
                            
                            mx = event_segment['x'].mean()
                            my = event_segment['y'].mean()
                            ax.text(mx, my+2, current_event['Event'], ha='center', fontsize=12, fontweight='bold',
                                   bbox=dict(facecolor='white', alpha=0.8, edgecolor='#32FF69', boxstyle='round,pad=0.3'), zorder=7)

                        else:
                             event_frame_row = subset_df.iloc[(subset_df['frame'] - evt_start_f_exact).abs().argsort()[:1]]
                             if not event_frame_row.empty:
                                 ex, ey = event_frame_row.iloc[0]['x'], event_frame_row.iloc[0]['y']
                                 pitch.scatter(ex, ey, ax=ax, c='#32FF69', s=150, marker='*', edgecolors='black', zorder=6, label='Event Location')
                        
                        pitch.scatter(subset_df.iloc[0]['x'], subset_df.iloc[0]['y'], ax=ax, c='#D3D3D3', s=40, marker='o', zorder=2)
                        pitch.scatter(subset_df.iloc[-1]['x'], subset_df.iloc[-1]['y'], ax=ax, c='#D3D3D3', s=40, marker='s', zorder=2)
                        
                        fps = getattr(dataset.metadata, 'frame_rate', 10.0) if dataset else 10.0
                        period_starts = get_period_starts(metadata)
                        
                        evt_period = current_event.get('period', 1)
                        if 'period' not in current_event and period_starts:
                             p2_start = period_starts.get(2, 999999)
                             if current_event[start_col] >= p2_start:
                                 evt_period = 2
                        
                        clock_str = calculate_match_clock(
                            frame=current_event[start_col], 
                            period=evt_period, 
                            period_start_frames=period_starts, 
                            fps=fps
                        )
                        
                        ax.set_title(f"Time: {clock_str} | Frame: {current_event[start_col]} | {current_event['Event']}", fontsize=14)
                        ax.legend(loc='lower left')
                    else:
                        ax.text(52.5, 34, "No tracking data available for this timeframe", ha='center', va='center', fontsize=12)
                    
                    st.pyplot(fig_traj)
                else:
                    st.info("No events found for this player in timeline.")
            else:
                 st.info(f"No timeline data available. Missing {start_col} column.")

if __name__ == "__main__":
    main()
