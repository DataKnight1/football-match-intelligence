"""
Author: Tiago Monteiro
Date: 21-12-2025
Event analysis dashboard for deeper dive into match events and player movements using animations and frame visualizations.
"""
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib import animation
from mplsoccer import Pitch
import sys
from pathlib import Path
import base64

PRIMARY_COLOR = "#32FF69"
SECONDARY_COLOR = "#3385FF"
PITCH_SURFACE_COLOR = "#F8F9FA"
PITCH_LINE_COLOR = "#28A745"
CAMERA_OUTLINE_COLOR = PRIMARY_COLOR
ENGAGEMENT_BORDER_COLOR = "#FF7A00"

sys.path.append(str(Path(__file__).parent.parent))

from src import data_loader, utils, visualizations, styling

styling.setup_page("Event Analysis")

@st.cache_resource(ttl=3600)
def load_match_cached(match_id, sample_rate=1.0, limit=None):
    """
    Load match data with caching.

    :param match_id: The ID of the match to load.
    :param sample_rate: The sample rate for loading data.
    :param limit: The maximum number of frames to load.
    :return: The loaded match data object.
    """
    return data_loader.load_match_data(
        match_id=match_id,
        sample_rate=sample_rate,
        limit=limit
    )

@st.cache_data(ttl=3600)
def load_events_cached(match_id):
    """
    Load dynamic events with caching.

    :param match_id: The ID of the match events to load.
    :return: A DataFrame containing match events, or None if loading fails.
    """
    try:
        return data_loader.load_dynamic_events(match_id)
    except Exception as e:
        st.warning(f"Could not load events: {e}")
        return None

def create_animation_html(dataset, start_frame, end_frame, fps, show_camera):
    """
    Create HTML5 video animation using matplotlib FuncAnimation.

    :param dataset: The dataset containing match frames.
    :param start_frame: The starting frame index.
    :param end_frame: The ending frame index.
    :param fps: Frames per second for the animation.
    :param show_camera: Boolean indicating whether to show the camera polygon.
    :return: HTML string containing the video element.
    """
    frames_data = []
    for idx in range(start_frame, end_frame):
        frame = dataset.frames[idx]
        home_players, away_players, ball_pos, camera_polygon = visualizations.extract_frame_data(frame)

        timestamp_seconds = frame.timestamp.total_seconds() if hasattr(frame.timestamp, 'total_seconds') else frame.timestamp
        minutes = int(timestamp_seconds // 60)
        seconds = int(timestamp_seconds % 60)

        frames_data.append({
            'home_x': [p['x'] for p in home_players],
            'home_y': [p['y'] for p in home_players],
            'away_x': [p['x'] for p in away_players],
            'away_y': [p['y'] for p in away_players],
            'ball_x': [ball_pos['x']] if ball_pos else [],
            'ball_y': [ball_pos['y']] if ball_pos else [],
            'camera_polygon': camera_polygon,
            'frame_id': frame.frame_id,
            'period': frame.period.id,
            'time_str': f"{minutes:02d}:{seconds:02d}"
        })

    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_length=105,
        pitch_width=68,
        pitch_color=PITCH_SURFACE_COLOR,
        line_color=PITCH_LINE_COLOR,
        linewidth=2.5
    )
    fig, ax = pitch.draw(figsize=(16, 9))
    fig.set_dpi(80)
    fig.patch.set_facecolor('white')
    fig.tight_layout(rect=[0, 0, 0.9, 0.85]) 

    marker_kwargs = {'marker': 'o', 'markeredgecolor': '#1A1A1A', 'linestyle': 'None', 'linewidth': 3}

    home_plot, = ax.plot([], [], ms=16, markerfacecolor=PRIMARY_COLOR, zorder=10,
                         alpha=1.0, label='Home', **marker_kwargs)
    away_plot, = ax.plot([], [], ms=16, markerfacecolor=SECONDARY_COLOR, zorder=10,
                         alpha=1.0, label='Away', **marker_kwargs)
    ball_plot, = ax.plot([], [], ms=10, markerfacecolor='#FF6B35',
                         markeredgecolor='#1A1A1A', zorder=15, label='Ball',
                         marker='o', linewidth=3, linestyle='None')

    camera_patch = None
    title_text = ax.text(0.5, 1.02, '', color='#1A1A1A', fontsize=18,
                        fontweight='bold', ha='center', va='bottom',
                        transform=ax.transAxes, zorder=30)

    ax.legend(
        bbox_to_anchor=(1.01, 0.5),
        loc='center left',
        fontsize=12,
        framealpha=0.95,
        facecolor='white',
        edgecolor=PRIMARY_COLOR,
        labelcolor='#1A1A1A',
        shadow=True,
        title="Legend",
        title_fontsize=14
    )

    def animate(i):
        nonlocal camera_patch
        data = frames_data[i]

        home_plot.set_data(data['home_x'], data['home_y'])
        away_plot.set_data(data['away_x'], data['away_y'])
        ball_plot.set_data(data['ball_x'], data['ball_y'])

        if camera_patch:
            camera_patch.remove()
            camera_patch = None

        if show_camera and data['camera_polygon'] is not None and len(data['camera_polygon']) > 0:
            try:
                polygon_points = np.array(data['camera_polygon'])
                camera_patch = MplPolygon(
                    polygon_points,
                    fill=True,
                    facecolor=PRIMARY_COLOR,
                    edgecolor=PRIMARY_COLOR,
                    linewidth=3,
                    linestyle='--',
                    alpha=0.15
                )
                ax.add_patch(camera_patch)
            except:
                pass

        title_text.set_text(f"Frame {data['frame_id']} | Period {data['period']} | {data['time_str']}")
        return home_plot, away_plot, ball_plot, title_text

    interval = 1000 / fps
    anim = animation.FuncAnimation(fig, animate, frames=len(frames_data),
                                  interval=interval, blit=True, repeat=True)

    html_video = anim.to_jshtml()
    
    plt.close(fig)
    return html_video

def main():
    """
    Main function to render the Event Analysis page.
    Provides tools for viewing event data, filtering events, and generating animations for specific frames.
    """
    styling.load_css()
    st.markdown("## Event Analysis")

    
    st.sidebar.markdown("## Filters")
    st.sidebar.markdown("")

    app_mode = st.sidebar.radio(
        "Select Mode",
        ["Animation", "Event Viewer"],
        index=0
    )

    st.sidebar.markdown("---")

    matches = data_loader.get_available_matches()
    match_options = {f"{desc}": mid for mid, desc in matches.items()}

    selected_match_str = st.sidebar.selectbox(
        "Select Match",
        options=list(match_options.keys()),
        index=0
    )
    selected_match_id = match_options[selected_match_str]

    st.sidebar.markdown("### Data Loading")
    st.sidebar.markdown("")

    sample_rate = st.sidebar.select_slider(
        "Sample Rate (FPS)",
        options=[0.1, 0.2, 0.5, 1.0],
        value=0.5,
        format_func=lambda x: f"{int(x*10)} fps"
    )

    max_frames = st.sidebar.slider(
        "Max Frames to Load (0 = All)",
        min_value=0,
        max_value=150000,
        value=0,
        step=1000,
        help="Set to 0 to load the entire match. Warning: High frame counts may be slow."
    )
    
    limit_arg = None if max_frames == 0 else max_frames

    if st.sidebar.button("Load Match Data", type="primary"):
        st.session_state['load_trigger'] = True

    if 'dataset' not in st.session_state or st.session_state.get('load_trigger', False):
        with st.spinner("Loading match data..."):
            try:
                dataset = load_match_cached(
                    selected_match_id,
                    sample_rate=sample_rate,
                    limit=limit_arg
                )
                events = load_events_cached(selected_match_id)

                st.session_state['dataset'] = dataset
                st.session_state['events'] = events
                st.session_state['match_id'] = selected_match_id
                st.session_state['load_trigger'] = False

                if events is not None:
                    st.success(f"Loaded {len(dataset.frames)} frames and {len(events)} events.")
                else:
                    st.success(f"Loaded {len(dataset.frames)} frames.")
            except Exception as e:
                st.error(f"Error loading data: {e}")
                return

    dataset = st.session_state.get('dataset')
    events = st.session_state.get('events')

    if dataset is None:
        st.info('Select a match and click "Load Match Data" to begin.')
        return

    metadata = data_loader.get_match_metadata(dataset)
    st.session_state['metadata'] = metadata

    st.markdown("### Match Overview")
    col1, col2, col3, col4 = st.columns(4, gap="large")
    with col1:
        st.metric("Home Team", metadata['home_team_name'])
    with col2:
        st.metric("Away Team", metadata['away_team_name'])
    with col3:
        st.metric("Total Frames", f"{len(dataset.frames):,}")
    with col4:
        if events is not None:
            st.metric("Events", f"{len(events):,}")
        else:
            st.metric("Events", "N/A")

    st.markdown("---")

    if app_mode == "Animation":
        st.markdown("### Animation Settings")
        st.markdown("")

        use_full_duration = st.checkbox("Animate Entire Loaded Duration (from Start Frame)", value=False, key="full_duration_toggle")
        
        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            if not use_full_duration:
                anim_start = st.number_input(
                    "Start Frame",
                    min_value=0,
                    max_value=max(0, len(dataset.frames) - 1),
                    value=0
                )
            else:
                anim_start = 0
                st.info("Start: Beginning")

        with col2:
            if not use_full_duration:
                anim_length = st.slider(
                    "Number of Frames",
                    min_value=10,
                    max_value=min(3000, len(dataset.frames) - anim_start) if len(dataset.frames) > anim_start else 3000,
                    value=min(300, len(dataset.frames) - anim_start) if len(dataset.frames) > anim_start else 300,
                    step=10
                )
            else:
                anim_length = len(dataset.frames)
                st.info(f"Duration: {anim_length} frames")

        with col3:
            fps = st.slider(
                "Speed (fps)",
                min_value=5,
                max_value=30,
                value=10,
                step=5
            )

        anim_end = min(anim_start + anim_length, len(dataset.frames))

        show_camera = st.checkbox("Show Broadcast Camera View", value=True)
        
        if (anim_end - anim_start) > 5000:
             st.warning(f"Generating animation for {anim_end - anim_start} frames. This may take a significant amount of time and memory.")

        st.caption(
            f"{anim_end - anim_start} frames, approximately {(anim_end - anim_start) / fps:.1f} seconds of action."
        )

        st.markdown("---")

        generate_button = st.button("Generate Animation", type="primary", use_container_width=True)

        if generate_button:
            with st.spinner("Building animation... This may take a minute."):
                try:
                    html_video = create_animation_html(
                        dataset,
                        anim_start,
                        anim_end,
                        fps,
                        show_camera
                    )

                    st.success("Animation created.")
                    st.markdown("---")
                    st.markdown("### Animation Player")
                    st.markdown("**Controls**: Use the player controls below to play, pause, adjust speed, and navigate frames.")
                    st.markdown(html_video, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error creating animation: {e}")
                    st.exception(e)

    else:
        st.markdown("### Event Viewer")
        st.markdown("")

        if events is None or len(events) == 0:
            st.warning("No events data available for this match.")
            return

        with st.expander("View All Events Data", expanded=False):
            st.dataframe(events, use_container_width=True)

        start_frame_col = None
        for col in ['start_frame', 'frame_start', 'start_frame_id', 'frame']:
            if col in events.columns:
                start_frame_col = col
                break

        end_frame_col = None
        for col in ['end_frame', 'frame_end', 'end_frame_id']:
            if col in events.columns:
                end_frame_col = col
                break

        col1, col2 = st.columns(2, gap="large")
        with col1:
            event_types = events['event_type'].unique().tolist()
            selected_event_type = st.selectbox(
                "Filter by Event Type",
                ["All"] + event_types
            )
        with col2:
            period_filter = st.selectbox(
                "Filter by Period",
                ["All", 1, 2]
            )

        filtered_events = events.copy()
        if selected_event_type != "All":
            filtered_events = filtered_events[filtered_events['event_type'] == selected_event_type]
        if period_filter != "All":
            filtered_events = filtered_events[filtered_events['period'] == period_filter]

        st.markdown("---")

        display_cols = ['event_type']
        if start_frame_col:
            display_cols.append(start_frame_col)
        if end_frame_col:
            display_cols.append(end_frame_col)
        if 'duration' in filtered_events.columns:
            display_cols.append('duration')
        if 'player_id' in filtered_events.columns:
            display_cols.append('player_id')

        for col in ['start_x', 'start_y', 'end_x', 'end_y', 'x_start', 'y_start', 'x_end', 'y_end']:
            if col in filtered_events.columns and col not in display_cols:
                display_cols.append(col)

        st.write(f"**Select an event from the table** ({len(filtered_events)} events found):")

        if start_frame_col:
            filtered_events = filtered_events.sort_values(start_frame_col)

        selected_event_rows = st.dataframe(
            filtered_events[display_cols].dropna(axis=1, how='all'),
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            use_container_width=True,
            height=300
        )

        if len(selected_event_rows["selection"]["rows"]) == 0:
            st.info("Select one or more events from the table above to visualize them.")
            st.stop()

        selected_indices = selected_event_rows["selection"]["rows"]
        selected_events_df = filtered_events.iloc[selected_indices]
        
        if start_frame_col and end_frame_col:
            clip_start_frame = int(selected_events_df[start_frame_col].min())
            clip_end_frame = int(selected_events_df[end_frame_col].max())
            
            if len(selected_indices) == 1:
                padding = 50
            else:
                padding = 20
        else:
             st.error("Cannot determine clip range from selected events.")
             st.stop()
             
        selected_event = selected_events_df.iloc[0]

        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        with col1:
            if len(selected_indices) > 1:
                st.metric("Selection", f"{len(selected_indices)} Events")
            else:
                st.metric("Selection", selected_event['event_type'])
        with col2:
             st.metric("Clip Start", f"{clip_start_frame:,}")
        with col3:
             st.metric("Clip End", f"{clip_end_frame:,}")
        with col4:
             duration_s = (clip_end_frame - clip_start_frame) / 10.0
             st.metric("Clip Duration", f"{duration_s:.1f}s")

        if len(selected_indices) == 1:
            with st.expander("Full Event Data"):
                st.json(selected_event.to_dict())



        st.markdown("---")

        st.markdown("### Interactive Event Sequence Viewer")

        loaded_frames_min = dataset.frames[0].frame_id if dataset.frames else 0
        loaded_frames_max = dataset.frames[-1].frame_id if dataset.frames else 0
        
        if clip_end_frame < loaded_frames_min or clip_start_frame > loaded_frames_max:
             st.error(
                 f"**Clip Range ({clip_start_frame}-{clip_end_frame}) is completely OUTSIDE the loaded data range ({loaded_frames_min} - {loaded_frames_max}).**\n\n"
                 "Please increase 'Max Frames to Load' in the sidebar (set to 0 for All) or reload the data."
             )
             st.stop()

        if clip_start_frame < loaded_frames_min:
             st.caption(f"Note: Clip start adjusted from {clip_start_frame} to {loaded_frames_min} to match loaded data.")
             clip_start_frame = loaded_frames_min
             
        if clip_end_frame > loaded_frames_max:
             st.caption(f"Note: Clip end adjusted from {clip_end_frame} to {loaded_frames_max} to match loaded data.")
             clip_end_frame = loaded_frames_max

        try:
            from src.visualizations.sequence import build_sequence_viewer
            from src.preprocessing.data import convert_tracking_wide_to_long

            tracking_df_wide = dataset.to_df(engine='pandas')

            if 'frame_id' not in tracking_df_wide.columns and 'frame' not in tracking_df_wide.columns:
                 tracking_df_wide = tracking_df_wide.reset_index()

            if 'frame_id' in tracking_df_wide.columns and 'frame' not in tracking_df_wide.columns:
                tracking_df_wide = tracking_df_wide.rename(columns={'frame_id': 'frame'})
            if 'period_id' in tracking_df_wide.columns and 'period' not in tracking_df_wide.columns:
                tracking_df_wide = tracking_df_wide.rename(columns={'period_id': 'period'})

            start_slice = max(loaded_frames_min, clip_start_frame - padding)
            end_slice = min(loaded_frames_max, clip_end_frame + padding)
            
            window_df = tracking_df_wide[
                (tracking_df_wide['frame'] >= start_slice) & 
                (tracking_df_wide['frame'] <= end_slice)
            ].copy()

            if not window_df.empty:
                window_long = convert_tracking_wide_to_long(window_df, metadata)

                if not window_long.empty:
                    start_frame = start_slice
                    end_frame = end_slice

                    nearby_events = filtered_events[
                        (filtered_events[start_frame_col] >= start_frame) &
                        (filtered_events[start_frame_col] <= end_frame)
                    ]

                    
                    team_colors = {}
                    team_names = {}

                    if metadata:
                        home_color = "#32FF69"
                        away_color = "#3385FF"
                        if 'home_team_id' in metadata:
                            tid = str(metadata['home_team_id'])
                            team_colors[tid] = home_color
                            team_names[tid] = metadata.get('home_team_name', f"Team {tid}")
                            
                        if 'away_team_id' in metadata:
                            tid = str(metadata['away_team_id'])
                            team_colors[tid] = away_color
                            team_names[tid] = metadata.get('away_team_name', f"Team {tid}")

                    event_list_for_viz = []
                    for _, evt in nearby_events.iterrows():
                        evt_dict = evt.to_dict()
                        evt_dict['frame'] = int(evt[start_frame_col])
                        evt_dict['event_id'] = evt.get('event_id', -1)
                        
                        if 'x' in evt and 'y' in evt and pd.notna(evt['x']):
                            evt_dict['x'] = evt['x']
                            evt_dict['y'] = evt['y']
                        elif 'start_x' in evt and 'start_y' in evt and pd.notna(evt['start_x']):
                            evt_dict['x'] = evt['start_x']
                            evt_dict['y'] = evt['start_y']
                        elif 'location_x' in evt and 'location_y' in evt and pd.notna(evt['location_x']):
                             evt_dict['x'] = evt['location_x']
                             evt_dict['y'] = evt['location_y']
                        elif 'player_id' in evt and pd.notna(evt['player_id']) and not window_long.empty:
                             pid_lookup = evt['player_id']
                             frame_lookup = evt_dict['frame']
                             track_row = window_long[
                                 (window_long['frame'] == frame_lookup) & 
                                 (window_long['player_id'] == pid_lookup)
                             ] if 'player_id' in window_long.columns else pd.DataFrame()
                             
                             if not track_row.empty:
                                 evt_dict['x'] = track_row.iloc[0].get('x')
                                 evt_dict['y'] = track_row.iloc[0].get('y')

                        event_list_for_viz.append(evt_dict)
                            
                    selected_ids = selected_events_df['event_id'].tolist() if 'event_id' in selected_events_df.columns else []

                    fig = build_sequence_viewer(
                        tracking_df=window_long,
                        start_frame=start_frame,
                        end_frame=end_frame,
                        context=None,
                        show_event_markers=True,
                        event_list=event_list_for_viz,
                        fps=10,
                        visible_trails=15,
                        team_colors=team_colors,
                        team_names=team_names,
                        active_event_ids=selected_ids
                    )

                    st.plotly_chart(fig, use_container_width=True)



            else:
                st.warning("Could not sync event to tracking data (event may be outside loaded frames)")

        except Exception as e:
            st.error(f"Error creating sequence viewer: {e}")
            import traceback
            st.exception(traceback.format_exc())

        st.markdown("---")

        events_in_frame = pd.DataFrame([selected_event]) 
        
        if start_frame_col:
            event_frame_id = int(selected_event[start_frame_col])
        else:
            event_frame_id = 0

        if start_frame_col and end_frame_col:
            overlapping_events = events[
                (events[start_frame_col] <= event_frame_id) &
                (events[end_frame_col] >= event_frame_id) &
                (events.index != selected_event.name) 
            ]

            if len(overlapping_events) > 0:
                events_in_frame = pd.concat([events_in_frame, overlapping_events], ignore_index=True)

        if 'event_id' in selected_event.index:
            associated_col = None
            for col in ['associated_player_possession_event_id', 'associated_event_id']:
                if col in events.columns:
                    associated_col = col
                    break

            if associated_col:
                associated_events = events[
                    (events[associated_col] == selected_event['event_id']) &
                    (~events.index.isin(events_in_frame.index))
                ]
                if len(associated_events) > 0:
                    events_in_frame = pd.concat([events_in_frame, associated_events], ignore_index=True)
        
        if 'event_id' in events_in_frame.columns:
            events_in_frame = events_in_frame.drop_duplicates(subset=['event_id'])
        else:
            events_in_frame = events_in_frame.drop_duplicates()

        st.markdown(f"### Events at Frame {event_frame_id}")
        st.write(f"**Select which events to visualize on the pitch** ({len(events_in_frame)} events at this frame):")
        
        matching_frame, frame_diff = utils.find_frame_by_id(dataset, event_frame_id)
        
        if not matching_frame:
             st.warning(f"Static visualization disabled: Frame {event_frame_id} not found locally.")
             st.markdown("---")
        else:
            events_selection = st.dataframe(
                events_in_frame[display_cols].dropna(axis=1, how='all'),
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                use_container_width=True
            )

            if len(events_selection["selection"]["rows"]) == 0:
                st.info("Select one or more events from the table above to add them to the visualization.")
                df_events_to_plot = pd.DataFrame()
            else:
                df_events_to_plot = events_in_frame.iloc[events_selection["selection"]["rows"]]

            st.markdown("---")
            
            if frame_diff and frame_diff > 0:
                st.info(
                    f"Frame {event_frame_id} is not in the loaded sample. "
                    f"Showing closest frame {matching_frame.frame_id} (Δ={frame_diff}). "
                    "Increase sample rate or frame limit for exact alignment."
                )
            st.markdown("### Frame Visualization")

            show_camera_event = st.checkbox("Show Camera View", value=True, key="event_camera")

            if len(df_events_to_plot) > 0:
                
                home_players, away_players, ball_pos, camera_polygon = visualizations.extract_frame_data(matching_frame)
                all_players = home_players + away_players

                player_positions = pd.DataFrame(all_players)
                if len(player_positions) > 0 and 'player_id' in player_positions.columns:
                    player_positions = player_positions[['player_id', 'x', 'y']].rename(
                        columns={'x': 'x_current_frame', 'y': 'y_current_frame'}
                    )

                    if 'player_id' in df_events_to_plot.columns:
                        player_positions['player_id'] = player_positions['player_id'].astype(str)
                        df_events_to_plot_copy = df_events_to_plot.copy()
                        df_events_to_plot_copy['player_id'] = df_events_to_plot_copy['player_id'].astype(str)

                        df_events_with_positions = df_events_to_plot_copy.merge(
                            player_positions,
                            on='player_id',
                            how='left'
                        )
                    else:
                        df_events_with_positions = df_events_to_plot
                else:
                    df_events_with_positions = df_events_to_plot
            else:
                df_events_with_positions = None

            fig = visualizations.plot_frame_with_events(
                matching_frame,
                dataset,
                df_events_with_positions,
                show_camera_event
            )

            st.pyplot(fig, use_container_width=True, bbox_inches='tight')
            plt.close(fig)

            if df_events_with_positions is not None and len(df_events_with_positions) > 0:
                st.markdown("### Event Sequence")

                ordered_events = df_events_with_positions.copy()
                if {"frame_start", "frame_end"}.issubset(ordered_events.columns):
                    ordered_events = ordered_events.sort_values(["frame_start", "frame_end"]).reset_index(drop=True)

                sequence_lines = []
                for seq_idx, (_, event_row) in enumerate(ordered_events.iterrows(), start=1):
                    frame_info = ""
                    if "frame_start" in event_row and not pd.isna(event_row["frame_start"]):
                        frame_info = f"[Frame {int(event_row['frame_start'])}] "
                    description = utils.format_event_description(event_row)
                    sequence_lines.append(f"{seq_idx}. {frame_info}{description}")

                st.markdown("\n".join(sequence_lines))

            if len(df_events_to_plot) > 0:
                st.success(f"Displaying {len(df_events_to_plot)} event(s) on frame {event_frame_id}.")
            else:
                st.info(f"Showing frame {event_frame_id} (no events selected).")

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0; color: #6C757D;'>
            <p style='font-size: 0.9rem; margin: 0;'>
                <strong>PySport Analytics Cup 2024/2025</strong> | SkillCorner OpenData
            </p>
            <p style='font-size: 0.8rem; margin-top: 0.5rem;'>
                Built with Streamlit & Kloppy
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
