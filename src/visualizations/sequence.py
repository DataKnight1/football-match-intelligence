"""
Author: Tiago Monteiro
Date: 21-12-2025
Interactive Sequence Viewer using Plotly.
Visualizes a window of tracking frames around a specific event.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Optional, Dict, List, Union
from ..sync import SequenceContext

def build_sequence_viewer(
    tracking_df: pd.DataFrame,
    start_frame: int = None,
    end_frame: int = None,
    context: Optional[SequenceContext] = None,
    event_metadata: Optional[Dict] = None,
    visible_trails: int = 15, 
    fps: int = 10,
    show_event_markers: bool = True, 
    event_list: Optional[List[Dict]] = None,  
    team_colors: Optional[Dict[str, str]] = None, 
    team_names: Optional[Dict[str, str]] = None, 
    active_event_ids: Optional[List[Union[int, str]]] = None 
) -> go.Figure:
    """
    Build an interactive Plotly animation for a sequence of play.

    :param tracking_df: Full tracking DataFrame or Slice.
    :param context: SequenceContext object from src/sync.
    :param start_frame: explicit start frame (override context).
    :param end_frame: explicit end frame (override context).
    :param show_event_markers: Whether to overlay event markers.
    :param event_list: List of dicts with 'frame', 'x', 'y', 'end_type', 'event_id' for events in sequence.
    :param team_colors: Dict mapping team_id (str) to color (hex).
    :param team_names: Dict mapping team_id (str) to name (str).
    :param active_event_ids: List of IDs of primary events to highlight.
    :return: Plotly Figure object.
    """
    
    df_seq = pd.DataFrame()
    
    if not tracking_df.empty:
         df_seq = tracking_df.copy()
         if context:
             title_text = f"Event: {context.event_type} @ {context.match_time_str}"
         else:
             title_text = f"Sequence: {len(tracking_df['frame'].unique())} frames"
             
    elif context and context.window_frames is not None:
        df_seq = context.window_frames
        title_text = f"Event: {context.event_type} @ {context.match_time_str}"

    elif start_frame is not None and end_frame is not None:
         title_text = f"Sequence: Frames {start_frame}-{end_frame}"
    else:
        return go.Figure().add_annotation(text="No valid sequence context provided", showarrow=False)
    
    if df_seq.empty:
        return go.Figure().add_annotation(text="No data for this sequence", showarrow=False)

    df_seq = df_seq.sort_values(['frame', 'player_id'])
    
    for col in ['x', 'y']:
        if col in df_seq.columns:
            df_seq[col] = pd.to_numeric(df_seq[col], errors='coerce')
    
    if 'vx' not in df_seq.columns or 'vy' not in df_seq.columns:
        df_seq = df_seq.sort_values(['player_id', 'frame'])
        
        df_seq['vx'] = df_seq.groupby('player_id')['x'].diff()
        df_seq['vy'] = df_seq.groupby('player_id')['y'].diff()
        
        df_seq['vx'] = df_seq['vx'] * fps
        df_seq['vy'] = df_seq['vy'] * fps
        
    df_seq['vx'] = pd.to_numeric(df_seq['vx'], errors='coerce').fillna(0.0)
    df_seq['vy'] = pd.to_numeric(df_seq['vy'], errors='coerce').fillna(0.0)

    if 'speed' not in df_seq.columns:
        sq_sum = (df_seq['vx']**2 + df_seq['vy']**2).astype(float)
        df_seq['speed'] = np.sqrt(sq_sum)
        
    df_seq[['vx', 'vy', 'speed']] = df_seq[['vx', 'vy', 'speed']].fillna(0)
    
    frames = sorted(df_seq['frame'].unique())
    
    fig = go.Figure()
    
    pitch_color = "white" 
    line_color = "#28A745"

    shapes = [
        dict(type="rect", x0=-52.5, y0=-34, x1=52.5, y1=34, line=dict(color=line_color), layer="below"),
        dict(type="rect", x0=-52.5, y0=7.32, x1=-52.5-2.43, y1=-7.32, line=dict(color=line_color), layer="below"),
        dict(type="rect", x0=52.5, y0=7.32, x1=52.5+2.43, y1=-7.32, line=dict(color=line_color), layer="below"),
        dict(type="rect", x0=-52.5, y0=20.16, x1=-52.5+16.5, y1=-20.16, line=dict(color=line_color), layer="below"),
        dict(type="rect", x0=52.5, y0=20.16, x1=52.5-16.5, y1=-20.16, line=dict(color=line_color), layer="below"),
        dict(type="rect", x0=-52.5, y0=9.16, x1=-52.5+5.5, y1=-9.16, line=dict(color=line_color), layer="below"),
        dict(type="rect", x0=52.5, y0=9.16, x1=52.5-5.5, y1=-9.16, line=dict(color=line_color), layer="below"),
        dict(type="line", x0=0, y0=-34, x1=0, y1=34, line=dict(color=line_color), layer="below"),
        dict(type="circle", x0=-9.15, y0=-9.15, x1=9.15, y1=9.15, line=dict(color=line_color), layer="below"),
    ]

    events_by_frame = {}
    if event_list:
        for evt in event_list:
            f = evt.get('frame')
            if f:
                if f not in events_by_frame:
                    events_by_frame[f] = []
                events_by_frame[f].append(evt)

    if show_event_markers and event_list:
        markers_to_add = []
        for event in event_list:
            if 'frame' in event and 'x' in event and 'y' in event:
                if start_frame <= event['frame'] <= end_frame:
                    
                    is_active = str(event.get('event_id')) in [str(uid) for uid in (active_event_ids or [])]
                    
                    etype = str(event.get('event_type')).lower()
                    
                    symbol = 'circle'
                    color = "#FFD700" if is_active else "#FF4B4B"
                    
                    if 'shot' in etype:
                        symbol = 'triangle-up'
                        color = '#E63946' 
                    elif 'pass' in etype:
                        symbol = 'diamond'
                        color = '#457B9D' 
                    elif 'card' in etype:
                        symbol = 'square'
                    elif 'goal' in etype:
                        symbol = 'star'
                        color = '#FFD700' 
                    elif 'duel' in etype:
                        symbol = 'x'
                    elif 'on_ball_engagement' in etype:
                        symbol = 'hexagon'
                        color = '#8A2BE2' 
                    elif 'passing_option' in etype:
                        symbol = 'circle-open'
                        color = '#555555' 
                        size = 6 
                    
                    size = 12 if is_active else 8
                    
                    fig.add_trace(go.Scatter(
                        x=[event['x']], y=[event['y']],
                        mode='markers+text',
                        marker=dict(symbol=symbol, size=size, color=color, line=dict(color='black', width=1)),
                        text=[f"{etype.title()}" if is_active else ""],
                        textposition="top center",
                        textfont=dict(size=10, color='black'),
                        hoverinfo='text',
                        hovertext=f"{etype.upper()}<br>{event.get('player_name','')} ({event.get('match_time_str','')})",
                        showlegend=False,
                        opacity=0.7 if not is_active else 1.0,
                        name=f'Event: {etype}'
                    ))

    plotly_frames = []
    
    c_home = "#32FF69" 
    c_away = "#3385FF" 
    
    arrow_scale = 0.5 
    
    for f_idx in frames:
        frame_data = df_seq[df_seq['frame'] == f_idx]
        traces = []
        
        if visible_trails > 0:
            trail_data = df_seq[
                (df_seq['frame'] >= f_idx - visible_trails) & 
                (df_seq['frame'] < f_idx)
            ]
            if not trail_data.empty:
                ball_trail = trail_data[trail_data['player_id'] == -1]
                if not ball_trail.empty:
                    traces.append(go.Scatter(
                        x=ball_trail['x'], y=ball_trail['y'],
                        mode='lines',
                        line=dict(color='#FFA500', width=3), 
                        opacity=0.6,
                        name='Ball Trail',
                        showlegend=False,
                        hoverinfo='skip'
                    ))

        ball_curr = frame_data[frame_data['player_id'] == -1]
        if not ball_curr.empty:
            traces.append(go.Scatter(
                x=ball_curr['x'], y=ball_curr['y'],
                mode='markers',
                marker=dict(size=12, color='#FFA500', line=dict(color='black', width=2)), 
                name='Ball',
                hoverinfo='text',
                text='BALL'
            ))

        players_curr = frame_data[frame_data['player_id'] != -1]
        if not players_curr.empty:
            players_curr['team_id_str'] = players_curr['team_id'].astype(str).str.replace(r'\.0$', '', regex=True)
            
            teams = sorted(players_curr['team_id_str'].unique())
            
            for idx, tid_str in enumerate(teams):
                t_data = players_curr[players_curr['team_id_str'] == tid_str]
                
                color = c_home if idx == 0 else c_away
                
                if team_colors and tid_str in team_colors:
                    color = team_colors[tid_str]

                t_name = f'Team {tid_str}'
                if team_names and tid_str in team_names:
                    t_name = team_names[tid_str]

                if 'jersey_no' in t_data.columns:
                     jersey = t_data['jersey_no'].fillna('?').astype(str)
                else:
                     jersey = pd.Series(['?']*len(t_data), index=t_data.index)
                
                pid_series = t_data['player_id'].fillna('?').astype(str)
                
                if 'speed' in t_data.columns:
                     speed = t_data['speed'].round(1).astype(str)
                else:
                     speed = pd.Series(['0']*len(t_data), index=t_data.index)
                
                hover_text = "<b>" + jersey + " " + pid_series + "</b><br>" + t_name + "<br>Speed: " + speed + " m/s"
                
                traces.append(go.Scatter(
                    x=t_data['x'],
                    y=t_data['y'],
                    mode='markers+text',
                    text=jersey,
                    textposition='middle center',
                    marker=dict(size=16, color=color, line=dict(color='black', width=1.5)),
                    textfont=dict(size=10, color='white' if color != '#32FF69' else 'black', family='Arial Black'), 
                    name=t_name,
                    texttemplate="%{text}",
                    hovertemplate=hover_text,
                    showlegend=True
                ))
                
                moving = t_data[t_data['speed'] > 0.5] 
                
                if not moving.empty:
                    x_lines = []
                    y_lines = []
                    
                    for _, row in moving.iterrows():
                        x1 = row['x']
                        y1 = row['y']
                        x2 = x1 + (row['vx'] * arrow_scale)
                        y2 = y1 + (row['vy'] * arrow_scale)
                        
                        x_lines.extend([x1, x2, None])
                        y_lines.extend([y1, y2, None])
                        
                    traces.append(go.Scatter(
                        x=x_lines,
                        y=y_lines,
                        mode='lines',
                        line=dict(color='black', width=1.5), 
                        opacity=0.5,
                        showlegend=False,
                        hoverinfo='skip'
                    ))

        feed_content = []
        current_events = events_by_frame.get(f_idx, [])
        
        if current_events:
            for evt in current_events:
                etype = str(evt.get('event_type', 'Action')).upper()
                player = evt.get('player_name', 'Player')
                feed_content.append(f"• {etype}: {player}")
            
        feed_text = "<br>".join(feed_content[:3])
        
        layout_update = {}
        if current_events:
             layout_update = dict(
                 annotations=[
                     dict(
                         text=f"<b>Frame {f_idx}</b><br>{feed_text}",
                         x=0.02, y=0.98, xref="paper", yref="paper", 
                         showarrow=False, align="left",
                         font=dict(size=12, color="black"),
                         bgcolor="rgba(255,255,255,0.8)", bordercolor="#333", borderwidth=1,
                         width=200
                     )
                 ]
             )
        else:
             layout_update = dict(
                 annotations=[
                     dict(
                         text=f"<b>Frame {f_idx}</b>",
                         x=0.02, y=0.98, xref="paper", yref="paper", 
                         showarrow=False, align="left",
                         font=dict(size=10, color="#555"),
                         bgcolor="rgba(255,255,255,0.5)",
                         width=80
                     )
                 ]
             )

        plotly_frames.append(go.Frame(data=traces, layout=layout_update, name=str(f_idx)))
    
    fig.frames = plotly_frames
    
    if plotly_frames:
        fig.add_traces(plotly_frames[0].data)
        if plotly_frames[0].layout and plotly_frames[0].layout.annotations:
             fig.update_layout(annotations=plotly_frames[0].layout.annotations)
        
    fig.update_layout(
        shapes=shapes,
        xaxis=dict(range=[-58, 58], showgrid=False, zeroline=False, visible=False, fixedrange=True),
        yaxis=dict(range=[-38, 38], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1, fixedrange=True),
        plot_bgcolor="white",
        paper_bgcolor="white",
        width=1000,
        height=600,
        title=dict(text=title_text, y=0.96, x=0.5, xanchor='center'),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=0.02, xanchor="right", x=0.98),
        hovermode="closest",
        updatemenus=[
            dict(
                type="buttons",
                buttons=[
                    dict(label="▶ Play", method="animate", args=[None, dict(frame=dict(duration=1000/fps, redraw=False), fromcurrent=True)]),
                    dict(label="⏸ Pause", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                ],
                showactive=False,
                direction="left",
                pad={"r": 10, "t": 10},
                x=0.1, xanchor="right", y=0, yanchor="top"
            )
        ],
        sliders=[{
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {
                "font": {"size": 14},
                "prefix": "Frame: ",
                "visible": True,
                "xanchor": "right"
            },
            "transition": {"duration": 300, "easing": "cubic-in-out"},
            "pad": {"b": 10, "t": 50},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": [
                {
                    "args": [[str(f)], {"frame": {"duration": 300, "redraw": False}, "mode": "immediate", "transition": {"duration": 300}}],
                    "label": str(f),
                    "method": "animate"
                }
                for f in frames
            ]
        }]
    )

    return fig
