"""
Author: Tiago Monteiro
Date: 21-12-2025
Team analysis dashboard showing tactical DNA, possession chains, and defensive structure.
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from src import styling, data_loader, preprocessing, visualizations, metrics

styling.setup_page("Team Analysis")
styling.load_css()

PRIMARY_COLOR = '#32FF69'

def main():
    """
    Main function to render the Team Analysis page.
    Displays tactical DNA, possession chains, defensive structure, and build-up patterns.
    """
    st.sidebar.markdown("## Filters")
    available_matches = data_loader.get_available_matches()
    
    match_options = {f"{desc}": match_id for match_id, desc in available_matches.items()}
    selected_match_desc = st.sidebar.selectbox(
        "Select Match:",
        options=list(match_options.keys())
    )
    match_id = match_options[selected_match_desc]
    
    @st.cache_resource(ttl=3600)
    def load_dataset_cached(match_id):
        """
        Load match dataset with caching.

        :param match_id: The ID of the match to load.
        :return: The loaded dataset object.
        """
        return data_loader.load_match_data(match_id, sample_rate=0.1, limit=None)

    try:
        dataset = load_dataset_cached(match_id)
        
        raw_tracking_data = dataset.to_df()
        
        metadata = data_loader.get_match_metadata(dataset, match_id=match_id)
        
        tracking_data = preprocessing.convert_tracking_wide_to_long(raw_tracking_data, metadata)
        
        home_team = metadata.get('home_team_name', 'Home Team')
        away_team = metadata.get('away_team_name', 'Away Team')
        
        selected_team_name = st.sidebar.radio("Select Team:", [home_team, away_team])
        
        if selected_team_name == home_team:
            selected_team_id = metadata.get('home_team_id')
        else:
            selected_team_id = metadata.get('away_team_id')
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return
    
    st.title(f"Team Analysis: {selected_team_name}")
    
    st.markdown("### Tactical DNA")
    
    if not tracking_data.empty:
        tilt_data = metrics.calculate_field_tilt(tracking_data, selected_team_id)
        fig_tilt = visualizations.plot_field_tilt_bar(
            tilt_data['percentage'],
            team_name=selected_team_name,
            opp_name=away_team if selected_team_name == home_team else home_team
        )
        st.pyplot(fig_tilt, use_container_width=True)
        plt.close(fig_tilt)
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs([
        "Possession Chains",
        "Defensive Structure",
        "Build-Up Patterns"
    ])
    
    try:
        events = data_loader.load_dynamic_events(match_id)
        phases = data_loader.load_phases_of_play(match_id)
    except:
        events = pd.DataFrame()
        phases = pd.DataFrame()
    
    with tab1:
        
        if not events.empty:
            target_type = st.selectbox(
                "Filter by end product:",
                ["All Sequences", "Shot", "Goal", "Corner", "Line Break"]
            )
            
            target_filter = target_type.lower() if target_type != "All Sequences" else None
            sequences = preprocessing.build_event_sequences(
                events, phases,
                target_event_type=target_filter,
                team_id=selected_team_id
            )
            
            if not sequences.empty:
                st.success(f"Found {len(sequences)} sequences")
                
                sequence_options = sequences['description'].tolist()
                selected_seq_desc = st.selectbox("Select sequence to view:", sequence_options)
                
                selected_seq_idx = sequences[sequences['description'] == selected_seq_desc].index[0]
                selected_sequence = sequences.iloc[selected_seq_idx]
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Events in Sequence", selected_sequence['num_events'])
                with col_b:
                    st.metric("Duration (frames)", 
                             selected_sequence['end_frame'] - selected_sequence['start_frame'])
                
                events_list = selected_sequence['events_list']
                
                viz_col, leg_col = st.columns([3, 1])
                
                fig_seq, legend_steps = visualizations.plot_event_sequence(
                    events_list,
                    title=f"{selected_seq_desc}",
                    tracking_df=tracking_data if not tracking_data.empty else None,
                    team_id=selected_team_id
                )
                
                with viz_col:
                    st.pyplot(fig_seq)
                    
                with leg_col:
                    st.markdown("#### Sequence Flow")
                    st.markdown("---")
                    for step in legend_steps:
                        st.markdown(f"{step}")
                        
                plt.close(fig_seq)
            else:
                st.info(f"No {target_type} sequences found for this team.")
        else:
            st.warning("No event data available")
    
    with tab2:
        st.markdown("### Defensive Structure (Out of Possession)")
        
        if not tracking_data.empty:
            col_c, col_d = st.columns(2)
            
            with col_c:
                st.markdown("#### Defensive Line Height")
                line_heights = metrics.calculate_defensive_line_heights(
                    tracking_data, selected_team_id
                )
                
                if not line_heights.empty:
                    fig_box = visualizations.plot_defensive_line_box(
                        line_heights, team_name=selected_team_name
                    )
                    st.pyplot(fig_box)
                    plt.close(fig_box)
                else:
                    st.info("Insufficient positional data for defensive line analysis")
            
            with col_d:
                st.markdown("#### Team Shape (Convex Hull)")
                st.markdown("Coverage area at a specific moment")
                
                if 'frame' in tracking_data.columns:
                    sample_frame = tracking_data['frame'].median()
                    
                    fig_hull = visualizations.plot_team_convex_hull(
                        tracking_data, selected_team_id, frame_id=int(sample_frame)
                    )
                    st.pyplot(fig_hull)
                    plt.close(fig_hull)
                else:
                    st.info("Frame data not available")
        else:
            st.warning("No tracking data loaded")
    
    with tab3:
        st.markdown("### Passing & Construction (Build-up)")
        
        if not events.empty:
                passes_df = events[
                    (events['event_type'] == 'player_possession') &
                    (events['end_type'].str.lower() == 'pass')
                ].copy() if 'end_type' in events.columns else pd.DataFrame()
                
                if not passes_df.empty:
                    passes_df = passes_df.sort_values('frame_start')
                    if 'start' in phases.columns: 
                        phases_sorted = phases.sort_values('start')
                        
                        merged_passes = pd.merge_asof(
                            passes_df, 
                            phases_sorted[['start', 'end', 'team_in_possession_phase_type']], 
                            left_on='frame_start', 
                            right_on='start',
                            direction='backward'
                        )
                        mask_valid = (merged_passes['frame_start'] >= merged_passes['start']) & \
                                     (merged_passes['frame_start'] <= merged_passes['end'])
                        
                        passes_df['phase_type'] = merged_passes.loc[mask_valid, 'team_in_possession_phase_type']
                    
                if 'team_id' in passes_df.columns:
                    passes_df = passes_df[passes_df['team_id'] == selected_team_id]
                
                if 'phase_type' in passes_df.columns:
                     passes_df = passes_df[passes_df['phase_type'] != 'set_play']
                
                if not passes_df.empty:
                    phase_filter = st.radio(
                        "Filter by phase:",
                        ["All Phases", "Build-Up", "Progression", "Final Third"]
                    )
                    
                    filtered_passes = passes_df.copy()
                    
                    if phase_filter != "All Phases":
                        if 'phase_type' in filtered_passes.columns:
                            if phase_filter == "Build-Up":
                                filtered_passes = filtered_passes[filtered_passes['phase_type'] == 'build_up']
                            elif phase_filter == "Progression":
                                filtered_passes = filtered_passes[filtered_passes['phase_type'].isin(['transition', 'direct', 'quick_break'])]
                            elif phase_filter == "Final Third":
                                filtered_passes = filtered_passes[filtered_passes['phase_type'].isin(['create', 'finish'])]
                        else:
                            if 'x_start' in filtered_passes.columns:
                                if phase_filter == "Build-Up":
                                    filtered_passes = filtered_passes[filtered_passes['x_start'] < -17.5]
                                elif phase_filter == "Progression":
                                    filtered_passes = filtered_passes[
                                        (filtered_passes['x_start'] >= -17.5) & (filtered_passes['x_start'] < 17.5)
                                    ]
                                elif phase_filter == "Final Third":
                                    filtered_passes = filtered_passes[filtered_passes['x_start'] >= 17.5]

                    st.success(f"Showing {len(filtered_passes)} passes in {phase_filter}")
                    
                    fig_pass = visualizations.plot_phase_pass_network(
                        filtered_passes,
                        title=f"{phase_filter} Pass Network"
                    )
                    st.pyplot(fig_pass)
                    plt.close(fig_pass)
                else:
                    st.info("No passes found for this team (check filters)")
        else:
            st.warning("No event data available")

if __name__ == "__main__":
    main()
