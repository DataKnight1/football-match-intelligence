"""
Author: Tiago Monteiro
Date: 21-12-2025
Passing network visualizations.
"""

from typing import Tuple, Optional, Dict, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
from src import utils

SOLUTION_GREEN = '#32FF69'

def plot_pass_network(
    pass_events: pd.DataFrame,
    average_positions: pd.DataFrame,
    pitch_length: float = 105,
    pitch_width: float = 68,
    team_name: Optional[str] = None,
    team_color: str = 'red',
    min_passes: int = 2,
    figsize: Tuple[int, int] = (12, 8)
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot a passing network for a team.
    
    :param pass_events: DataFrame containing pass events with player_id, receiver_id.
    :param average_positions: DataFrame with player_id, x, y (average positions).
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param team_name: Name of the team for the title.
    :param team_color: Color for nodes and edges.
    :param min_passes: Minimum number of passes to draw a line.
    :param figsize: Figure size.
    :return: Matplotlib Figure and Axes.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        pitch_color='#22312b',
        line_color='#c7d5cc',
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=figsize)

    pass_counts = pass_events.groupby(['player_id', 'receiver_id']).size().reset_index(name='count')
    
    pass_counts = pass_counts[pass_counts['count'] >= min_passes]

    pass_network = pass_counts.merge(
        average_positions, left_on='player_id', right_on='player_id', how='inner'
    ).rename(columns={'x': 'x_start', 'y': 'y_start'})
    
    pass_network = pass_network.merge(
        average_positions, left_on='receiver_id', right_on='player_id', how='inner', suffixes=('', '_receiver')
    ).rename(columns={'x': 'x_end', 'y': 'y_end'})

    max_passes = pass_network['count'].max()
    if max_passes > 0:
        pass_network['width'] = (pass_network['count'] / max_passes) * 10
    else:
        pass_network['width'] = 1

    pitch.lines(
        pass_network.x_start, pass_network.y_start,
        pass_network.x_end, pass_network.y_end,
        lw=pass_network.width,
        color=team_color,
        zorder=1,
        alpha=0.6,
        ax=ax
    )

    pitch.scatter(
        average_positions.x, average_positions.y,
        s=400,
        c='white',
        edgecolors=team_color,
        linewidth=3,
        zorder=2,
        ax=ax
    )

    for index, row in average_positions.iterrows():
        pitch.annotate(
            row.get('player_name', str(row.get('player_id', ''))),
            xy=(row.x, row.y),
            c='black',
            va='center',
            ha='center',
            size=8,
            weight='bold',
            ax=ax,
            zorder=3
        )

    if team_name:
        ax.set_title(f"Passing Network - {team_name}", fontsize=14, color='white', pad=20)

    return fig, ax

def _calculate_pass_network(events_df, min_passes=3):
    """
    Calculate nodes (avg pos) and edges (pass counts) from events.
    Infers receiver from the next event in the sequence.

    :param events_df: DataFrame containing events.
    :param min_passes: Minimum passes to consider connection.
    :return: Tuple of (nodes DataFrame, edges DataFrame).
    """
    events_df = events_df.sort_values('frame_start')
    
    events_df['next_team_id'] = events_df['team_id'].shift(-1)
    events_df['next_player_id'] = events_df['player_id'].shift(-1)
    
    connections = []
    
    for _, row in events_df.iterrows():
        end_type = str(row.get('end_type') or '').lower()
        if 'pass' in end_type:
            if (row['next_team_id'] == row['team_id'] and 
                pd.notna(row['player_id']) and pd.notna(row['next_player_id']) and
                row['player_id'] != row['next_player_id']):
                
                connections.append({
                    'passer': int(row['player_id']),
                    'receiver': int(row['next_player_id'])
                })

    nodes = events_df[events_df['event_type'] == 'player_possession'].groupby('player_id').agg({
        'x_start': 'mean',
        'y_start': 'mean',
        'player_name': 'first' 
    }).rename(columns={'x_start': 'x', 'y_start': 'y'})
    
    if not connections:
        return nodes, pd.DataFrame()
        
    edges_df = pd.DataFrame(connections)
    edges = edges_df.groupby(['passer', 'receiver']).size().reset_index(name='pass_count')
    
    edges = edges[edges['pass_count'] >= min_passes]
    
    return nodes, edges

def plot_phase_pass_network(
    phase_events_df: pd.DataFrame,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0,
    title: str = "Pass Network"
) -> plt.Figure:
    """
    Plot aggregated pass network for a phase.

    :param phase_events_df: DataFrame containing events for a specific phase.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param title: Plot title.
    :return: Matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
                 pitch_color='#2b2b2b', line_color='#4a4a4a')
    pitch.draw(ax=ax)
    
    if phase_events_df.empty:
        ax.text(0, 0, "No data for this phase", color='white', ha='center', fontsize=14)
        return fig

    try:
        nodes, edges = _calculate_pass_network(phase_events_df, min_passes=3)
    except Exception as e:
        ax.text(0, 0, f"Error calculating network: {e}", color='white', ha='center')
        return fig
    
    if nodes.empty:
        ax.text(0, 0, "Insufficient possession data", color='white', ha='center', fontsize=14)
        return fig

    if not edges.empty:
        max_passes = edges['pass_count'].max()
        edges['width'] = (edges['pass_count'] / max_passes) * 5 
        
        for _, edge in edges.iterrows():
            passer = int(edge['passer'])
            receiver = int(edge['receiver'])
            
            if passer in nodes.index and receiver in nodes.index:
                x_start, y_start = nodes.loc[passer, ['x', 'y']]
                x_end, y_end = nodes.loc[receiver, ['x', 'y']]
                
                pitch.lines(x_start, y_start, x_end, y_end, ax=ax,
                           color=SOLUTION_GREEN, alpha=0.6, lw=edge['width'], zorder=1)

    pitch.scatter(nodes['x'], nodes['y'], ax=ax, 
                 c='#2b2b2b', edgecolors=SOLUTION_GREEN, s=400, lw=2, zorder=2)
    
    for player_id, row in nodes.iterrows():
        name = str(row.get('player_name', player_id))
        label = "".join([n[0] for n in name.split()]) if name and name != 'Unknown' else str(player_id)
        
        pitch.annotate(label, xy=(row['x'], row['y']), ax=ax,
                      ha='center', va='center', color='white', fontsize=9, fontweight='bold', zorder=3)

    ax.set_title(title, fontsize=16, color='white', fontweight='bold', pad=10)
    
    return fig

def plot_vertical_pass_network(
    passes: pd.DataFrame,
    player_positions: pd.DataFrame,
    pitch_length: float = 105,
    pitch_width: float = 68,
    pitch_color: str = "#F0F0F0",
    line_color: str = "black",
    node_color: str = "#FF3333",
    figsize: Tuple[int, int] = (8, 12),
    title: Optional[str] = None,
    min_passes: int = 3,
    **kwargs
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Visualize team passing network on a vertical pitch.

    :param passes: DataFrame containing pass events/counts.
    :param player_positions: DataFrame containing player positions.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param pitch_color: Pitch color.
    :param line_color: Line color.
    :param node_color: Color of player nodes.
    :param figsize: Figure size.
    :param title: Plot title.
    :param min_passes: Minimum passes to show connection.
    :return: Matplotlib Figure and Axes.
    """
    pitch = VerticalPitch(
        pitch_type='skillcorner',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        pitch_color=pitch_color,
        line_color=line_color,
        linewidth=1
    )
    fig, ax = pitch.draw(figsize=figsize)

    pass_counts = passes.groupby(['passer_id', 'receiver_id']).size().reset_index(name='count')
    pass_counts = pass_counts[pass_counts['count'] >= min_passes]

    for _, row in pass_counts.iterrows():
        passer_pos = player_positions[player_positions['player_id'] == row['passer_id']]
        receiver_pos = player_positions[player_positions['player_id'] == row['receiver_id']]

        if len(passer_pos) > 0 and len(receiver_pos) > 0:
            x1, y1 = passer_pos.iloc[0]['x'], passer_pos.iloc[0]['y']
            x2, y2 = receiver_pos.iloc[0]['x'], receiver_pos.iloc[0]['y']

            width = row['count'] / pass_counts['count'].max() * 8

            pitch.lines(x1, y1, x2, y2, ax=ax, color=node_color, lw=width, alpha=0.4, zorder=5)

    if 'node_color' in player_positions.columns:
        scatter_colors = player_positions['node_color']
    else:
        scatter_colors = node_color

    pitch.scatter(
        player_positions['x'],
        player_positions['y'],
        ax=ax,
        s=400,
        c=scatter_colors,
        edgecolors='white',
        linewidths=2,
        zorder=10,
        alpha=1.0
    )

    for _, player in player_positions.iterrows():
        pitch.text(
            player['x'], player['y'],
            player['name'].split(' ')[-1], 
            ax=ax,
            color='black',
            fontweight='bold',
            fontsize=10,
            ha='center',
            va='center',
            zorder=15
        )

    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', color='black', pad=20)

    return fig, ax
