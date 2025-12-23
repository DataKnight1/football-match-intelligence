"""
Author: Tiago Monteiro
Date: 21-12-2025
Event sequence visualizations.
"""

from typing import Tuple, List, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from matplotlib.lines import Line2D

SOLUTION_GREEN = '#32FF69'

def draw_wavy_path(ax, start, end, color, amplitude=0.5, wavelength=2.0, zorder=2):
    """
    Draw a wavy line (sine wave) between two points to represent a Carry.
    
    :param ax: Matplotlib axes.
    :param start: Start coordinate tuple (x, y).
    :param end: End coordinate tuple (x, y).
    :param color: Line color.
    :param amplitude: Wave amplitude (default: 0.5).
    :param wavelength: Wave wavelength (default: 2.0).
    :param zorder: Plot zorder (default: 2).
    """
    x1, y1 = start
    x2, y2 = end
    
    dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
    if dist < 0.1: return
    
    t = np.linspace(0, dist, num=int(dist*5)) 
    angle = np.arctan2(y2-y1, x2-x1)
    
    offset = amplitude * np.sin(2 * np.pi * t / wavelength)
    
    x_wave = t * np.cos(angle) - offset * np.sin(angle) + x1
    y_wave = t * np.sin(angle) + offset * np.cos(angle) + y1
    
    ax.plot(x_wave, y_wave, color=color, linewidth=2, zorder=zorder, alpha=0.9)

def plot_event_sequence(
    sequence_events: list,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0,
    title: str = "Event Sequence",
    tracking_df: Optional[pd.DataFrame] = None,
    team_id: Optional[int] = None
) -> Tuple[plt.Figure, List[str]]:
    """
    Plot valid event sequence with numbered steps, connected flow, and tactical context.

    :param sequence_events: List of event dictionaries.
    :param pitch_length: Length of the pitch (default: 105.0).
    :param pitch_width: Width of the pitch (default: 68.0).
    :param title: Plot title.
    :param tracking_df: Optional tracking DataFrame for context.
    :param team_id: Optional team ID for context.
    :return: Tuple containing the figure and a list of legend steps.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
                 pitch_color='#2b2b2b', line_color='#4a4a4a') 
    pitch.draw(ax=ax)
    
    if not sequence_events:
        ax.text(pitch_length/2, pitch_width/2, "No events to display", 
               ha='center', va='center', color='white', fontsize=14)
        return fig, []

    active_events = []
    context_events = []
    
    for ev in sequence_events:
        etype = str(ev.get('event_type') or '').lower()
        if etype == 'passing_option':
            context_events.append(ev)
        else:
            active_events.append(ev)
            
    if context_events:
         x_ctx = [e.get('x_start') for e in context_events]
         y_ctx = [e.get('y_start') for e in context_events]
         pitch.scatter(x_ctx, y_ctx, ax=ax, c='grey', s=30, alpha=0.3, zorder=1)

    legend_steps = []
    
    for i, event in enumerate(active_events):
        idx = i + 1
        x_start = event.get('x_start')
        y_start = event.get('y_start')
        x_end = event.get('x_end', x_start)
        y_end = event.get('y_end', y_start)
        
        event_type_raw = str(event.get('event_type') or 'Action').lower()
        event_type_title = event_type_raw.replace('_', ' ').title()
        
        player_name = event.get('player_name', 'Player')
        if player_name == 'Unknown': 
             player_name = f"Player {event.get('player_id', '')}"
             
        step_desc = f"**{idx}. {event_type_title}** by {player_name}"
        end_type_val = event.get('end_type')
        if end_type_val and isinstance(end_type_val, str):
             step_desc += f" ({end_type_val.replace('_', ' ')})"
        legend_steps.append(step_desc)
        
        if x_start is not None and x_end is not None:
            active_dist = np.sqrt((x_end-x_start)**2 + (y_end-y_start)**2)
            
            if event_type_raw == 'player_possession' and active_dist > 2.0:
                draw_wavy_path(ax, (x_start, y_start), (x_end, y_end), SOLUTION_GREEN)
            elif event_type_raw == 'off_ball_run':
                pitch.lines(x_start, y_start, x_end, y_end, ax=ax,
                           color=SOLUTION_GREEN, lw=2, ls='--', alpha=0.8, zorder=2)
            elif active_dist > 0.5:
                pitch.lines(x_start, y_start, x_end, y_end, ax=ax,
                           color=SOLUTION_GREEN, lw=3, alpha=0.8, zorder=2)

        if i < len(active_events) - 1:
            next_ev = active_events[i+1]
            x_next = next_ev.get('x_start')
            y_next = next_ev.get('y_start')
            
            if x_end is not None and x_next is not None:
                curr_end = str(event.get('end_type') or '').lower()
                
                ls_gap = ':' 
                lw_gap = 1.5
                alpha_gap = 0.6
                
                if curr_end == 'pass':
                    ls_gap = '-' 
                    lw_gap = 2.5
                    alpha_gap = 0.9
                elif curr_end == 'shot':
                    ls_gap = '-' 
                    lw_gap = 3.0
                 
                pitch.lines(x_end, y_end, x_next, y_next, ax=ax,
                           color=SOLUTION_GREEN, lw=lw_gap, ls=ls_gap, alpha=alpha_gap, zorder=2)

        if tracking_df is not None and not tracking_df.empty and team_id is not None:
            if 'frame' in tracking_df.columns:
                frame = event.get('frame_start') or event.get('frame')
                if frame:
                    frame_data = tracking_df[tracking_df['frame'] == frame]
                    defenders = frame_data[frame_data['team_id'] != team_id]
                
                if not defenders.empty and x_start is not None:
                    defenders = defenders.copy()
                    defenders['dist'] = np.sqrt((defenders['x'] - x_start)**2 + (defenders['y'] - y_start)**2)
                    nearest = defenders.nsmallest(3, 'dist')
                    
                    pitch.scatter(nearest['x'], nearest['y'], ax=ax, 
                                 c='#ff4d4d', s=50, alpha=0.4, zorder=1, edgecolors='none')

        if x_start is not None:
            is_shot = str(event.get('end_type') or '').lower() == 'shot'
            
            if is_shot and i == len(active_events) - 1:
                xg = event.get('xshot_player_possession_start')
                if pd.isna(xg): xg = 0.1 
                
                size = 300 + (xg * 1000)
                
                is_goal = 'goal' in str(event.get('end_type') or '').lower() 
                if event.get('lead_to_goal'): is_goal = True
                
                fc = SOLUTION_GREEN if is_goal else 'none'
                ec = SOLUTION_GREEN
                
                pitch.scatter(x_start, y_start, ax=ax, marker='*', s=size,
                             facecolors=fc, edgecolors=ec, linewidths=2, zorder=5)
                
                if xg > 0.05:
                    ax.text(x_start, y_start+2, f"{xg:.2f} xG", ha='center', color='white', fontsize=8)
                    
            else:
                pitch.scatter(x_start, y_start, ax=ax, c=SOLUTION_GREEN, s=400,
                             edgecolors='black', zorder=3)
                ax.text(x_start, y_start, str(idx), ha='center', va='center',
                       fontsize=12, fontweight='bold', color='black', zorder=4)

    ax.set_title(title, fontsize=18, fontweight='bold', color='white', pad=15)
    
    return fig, legend_steps


def plot_player_event_sequence(
    events_df: pd.DataFrame,
    player_id: int,
    player_name: str,
    pitch_length: float = 105,
    pitch_width: float = 68,
    max_sequences: int = 5,
    figsize: Tuple[int, int] = (14, 10)
) -> plt.Figure:
    """
    Plot event sequences where the player participates, highlighting their actions.

    :param events_df: DataFrame containing all events.
    :param player_id: ID of the player to highlight.
    :param player_name: Name of the player.
    :param pitch_length: Length of the pitch (default: 105).
    :param pitch_width: Width of the pitch (default: 68).
    :param max_sequences: Maximum number of sequences to show (default: 5).
    :param figsize: Figure size dimensions.
    :return: Matplotlib Figure object.
    """
    player_events = events_df[events_df['player_id'] == player_id].copy()

    if player_events.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'No events found for this player',
                ha='center', va='center', fontsize=16)
        ax.axis('off')
        return fig

    player_phases = player_events['phase_index'].unique()

    selected_phases = player_phases[-max_sequences:] if len(player_phases) > max_sequences else player_phases

    n_sequences = len(selected_phases)
    n_cols = min(2, n_sequences)
    n_rows = (n_sequences + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, facecolor='#F8F8F6')
    if n_sequences == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    fig.suptitle(f"{player_name} - Event Sequences", fontsize=18, fontweight='bold', y=0.98)

    for idx, phase_idx in enumerate(selected_phases):
        ax = axes[idx]

        phase_events = events_df[events_df['phase_index'] == phase_idx].copy()

        phase_events = phase_events.sort_values('frame_start')

        pitch = Pitch(
            pitch_type='skillcorner',
            pitch_length=pitch_length,
            pitch_width=pitch_width,
            pitch_color='#F8F8F6',
            line_color='#CCCCCC',
            linewidth=1.5
        )
        pitch.draw(ax=ax)

        for _, event in phase_events.iterrows():
            if pd.notna(event['x_start']) and pd.notna(event['y_start']) and \
               pd.notna(event['x_end']) and pd.notna(event['y_end']):

                is_player_event = event['player_id'] == player_id

                pitch.arrows(
                    event['x_start'], event['y_start'],
                    event['x_end'], event['y_end'],
                    width=3 if is_player_event else 1.5,
                    headwidth=8 if is_player_event else 4,
                    headlength=8 if is_player_event else 4,
                    color='#32FF69' if is_player_event else '#555555',
                    alpha=0.9 if is_player_event else 0.4,
                    ax=ax,
                    zorder=3 if is_player_event else 2
                )

                pitch.scatter(
                    event['x_start'], event['y_start'],
                    s=150 if is_player_event else 60,
                    color='#32FF69' if is_player_event else '#777777',
                    edgecolors='white',
                    linewidth=2 if is_player_event else 1,
                    alpha=0.9 if is_player_event else 0.5,
                    ax=ax,
                    zorder=4 if is_player_event else 2
                )

                if is_player_event:
                    event_type = event['event_type'].lower()

                    event_icons = {
                        'pass': '',
                        'dribble': '',
                        'shot': '',
                        'cross': '',
                        'clearance': '',
                        'interception': '',
                        'tackle': '',
                        'on_ball_engagement': '',
                        'off_ball_run': '',
                        'carry': '',
                        'reception': '',
                        'recovery': '',
                    }

                    icon = '●'
                    for key, emoji in event_icons.items():
                        if key in event_type:
                            icon = emoji
                            break

                    pitch.text(
                        event['x_start'], event['y_start'] - 2,
                        icon,
                        fontsize=14,
                        ha='center',
                        va='bottom',
                        ax=ax,
                        zorder=6
                    )

                    event_type_short = event['event_type'].replace('_', ' ').title()
                    if len(event_type_short) > 12:
                        event_type_short = event_type_short[:9] + '...'

                    pitch.text(
                        event['x_start'], event['y_start'] - 4,
                        event_type_short,
                        fontsize=7,
                        color='#1A1A1A',
                        ha='center',
                        va='top',
                        fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='#32FF69',
                                 alpha=0.7, edgecolor='none'),
                        ax=ax,
                        zorder=5
                    )

        last_event = phase_events.iloc[-1]
        if pd.notna(last_event['x_end']) and pd.notna(last_event['y_end']):
            is_player_last = last_event['player_id'] == player_id
            pitch.scatter(
                last_event['x_end'], last_event['y_end'],
                s=150 if is_player_last else 60,
                color='#FF3333' if is_player_last else '#999999',
                edgecolors='white',
                linewidth=2,
                alpha=0.9,
                ax=ax,
                zorder=4,
                marker='X'
            )

        player_touches = len(phase_events[phase_events['player_id'] == player_id])
        total_touches = len(phase_events)

        ax.text(
            0.02, 0.98,
            f"Sequence {idx + 1}\n{player_touches}/{total_touches} touches",
            transform=ax.transAxes,
            fontsize=9,
            va='top',
            ha='left',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='#CCCCCC'),
            fontweight='bold'
        )

    for idx in range(n_sequences, len(axes)):
        axes[idx].axis('off')

    player_legend = [
        Line2D([0], [0], color='#32FF69', linewidth=3, marker='o', markersize=8,
               markerfacecolor='#32FF69', label=f'{player_name}'),
        Line2D([0], [0], color='#555555', linewidth=1.5, alpha=0.4, marker='o',
               markersize=6, markerfacecolor='#777777', label='Teammates'),
        Line2D([0], [0], color='#FF3333', linewidth=0, marker='X', markersize=8,
               markerfacecolor='#FF3333', label='End of Sequence'),
    ]

    event_type_legend = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=12, label='Pass'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=12, label='Dribble'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=12, label='Shot'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=12, label='Engagement'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=12, label='Off-Ball Run'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=12, label='Reception'),
    ]

    legend1 = fig.legend(handles=player_legend, loc='upper right', bbox_to_anchor=(0.98, 0.96),
                        frameon=True, fancybox=True, shadow=True, title='Players', title_fontsize=10, fontsize=9)

    legend2 = fig.legend(handles=event_type_legend, loc='center right', bbox_to_anchor=(0.98, 0.5),
                        frameon=True, fancybox=True, shadow=True, title='Event Types', title_fontsize=10, fontsize=8, ncol=1)

    fig.add_artist(legend1) 

    plt.tight_layout(rect=[0, 0, 0.85, 0.96])

    return fig
