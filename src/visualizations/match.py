"""
Author: Tiago Monteiro
Date: 21-12-2025
Match-level visualizations (Possession, Momentum, Shot Maps, Lineups).
"""

from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.patches as patches
from mplsoccer import Pitch, VerticalPitch
import seaborn as sns
import io
from src import utils

SOLUTION_GREEN = '#32FF69'

def plot_possession_timeline(
    phases_df: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    home_team_name: str,
    away_team_name: str,
    home_color: str = "#FF3333",
    away_color: str = "#3385FF",
    fps: float = 10.0,
    figsize: Tuple[int, int] = (12, 3),
    title: str = "Possession Timeline"
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot a timeline of possession phases.

    :param phases_df: DataFrame containing match phases.
    :param home_team_id: Home team ID.
    :param away_team_id: Away team ID.
    :param home_team_name: Home team name.
    :param away_team_name: Away team name.
    :param home_color: Home team color.
    :param away_color: Away team color.
    :param fps: Frames per second.
    :param figsize: Figure size.
    :param title: Plot title.
    :return: Matplotlib Figure and Axes.
    """
    bg_color = '#F8F9FA'
    text_color = '#1A1A1A'
    
    fig, ax = plt.subplots(figsize=figsize, facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    if 'team_in_possession_phase_type' in phases_df.columns:
        possession_phases = phases_df[phases_df['team_in_possession_phase_type'].notna()]
    else:
        possession_phases = phases_df[phases_df['team_in_possession_id'].notna()]
    
    home_ranges = []
    away_ranges = []
    
    for _, phase in possession_phases.iterrows():
        start_min = phase['frame_start'] / fps / 60
        duration_min = (phase['frame_end'] - phase['frame_start']) / fps / 60
        
        phase_team_id = phase['team_in_possession_id']
        
        if phase_team_id == home_team_id:
            home_ranges.append((start_min, duration_min))
        elif phase_team_id == away_team_id:
            away_ranges.append((start_min, duration_min))
            
    if home_ranges:
        ax.broken_barh(home_ranges, (10, 8), facecolors=home_color, label=home_team_name, edgecolor='None')
    if away_ranges:
        ax.broken_barh(away_ranges, (0, 8), facecolors=away_color, label=away_team_name, edgecolor='None')
        
    ax.set_ylim(-5, 25)
    ax.set_xlabel("Time (minutes)", color=text_color, fontsize=12)
    ax.set_yticks([4, 14])
    ax.set_yticklabels([away_team_name, home_team_name], color=text_color, fontsize=12, fontweight='bold')
    
    ax.tick_params(axis='x', colors=text_color)
    ax.grid(True, axis='x', linestyle='--', alpha=0.3, color='#999999')
    
    for spine in ax.spines.values():
        spine.set_visible(False)
        
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', color=text_color, pad=10)
        
    return fig, ax

def plot_momentum_chart(
    events: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    home_color: str = "#FF3333",
    away_color: str = "#3385FF",
    figsize: Tuple[int, int] = (12, 5)
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot momentum chart (Tug of War style) with goals highlighted.

    :param events: DataFrame containing match events.
    :param home_team_id: Home team ID.
    :param away_team_id: Away team ID.
    :param home_color: Home team color.
    :param away_color: Away team color.
    :param figsize: Figure size.
    :return: Matplotlib Figure and Axes.
    """
    bg_color = '#F8F9FA'
    text_color = '#1A1A1A'
    
    events = events.copy()
    if 'minute_start' in events.columns:
        events['minute'] = events['minute_start']
    elif 'timestamp' in events.columns:
        events['minute'] = (events['timestamp'] / 60).astype(int)
    else:
        return plt.subplots(figsize=figsize)
    
    max_min = int(events['minute'].max())
    minute_grid = np.arange(0, max_min + 2)
    
    momentum_values = []
    
    for m in minute_grid:
        min_events = events[events['minute'] == m]
        
        def calc_score(team_events):
            xg = team_events['expected_goal_value'].sum() if 'expected_goal_value' in team_events.columns else 0
            shots = len(team_events[team_events['end_type'] == 'shot'])
            passes = len(team_events[team_events['end_type'] == 'pass'])
            return (xg * 5) + (shots * 1) + (passes * 0.05)
            
        home_score = calc_score(min_events[min_events['team_id'] == home_team_id])
        away_score = calc_score(min_events[min_events['team_id'] == away_team_id])
        
        momentum_values.append(home_score - away_score)
        
    momentum_series = pd.Series(momentum_values).rolling(window=5, center=True, min_periods=1).mean().fillna(0)
    
    fig, ax = plt.subplots(figsize=figsize, facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    colors = np.where(momentum_series > 0, home_color, away_color)
    ax.bar(minute_grid, momentum_series, color=colors, width=1.0, alpha=0.9, zorder=3)
    
    goals = events[(events['end_type'] == 'shot') & (events['lead_to_goal'] == True)]
    for _, goal in goals.iterrows():
        minute = goal['minute']
        team_id = goal['team_id']
        
        idx = int(minute)
        if idx < len(momentum_series):
            mom_val = momentum_series[idx]
        else:
            mom_val = 0
            
        if team_id == home_team_id:
            y_pos = max(mom_val, 0) + 1.0
            ax.scatter(minute, y_pos, s=120, c=home_color, edgecolors='black', marker='o', zorder=10)
        elif team_id == away_team_id:
            y_pos = min(mom_val, 0) - 1.0
            ax.scatter(minute, y_pos, s=120, c=away_color, edgecolors='black', marker='o', zorder=10)

    ax.axhline(0, color=text_color, linewidth=1, alpha=0.5, zorder=4)
    ax.set_xlim(0, max_min + 1)
    ax.set_yticks([])
    
    xticks = np.arange(0, max_min + 5, 15)
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{x}'" for x in xticks], fontsize=10, color=text_color)
    
    ax.grid(True, axis='x', linestyle='--', alpha=0.2, color='#999999', zorder=1)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color(text_color)
    
    return fig, ax

def plot_cumulative_xg(
    events: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    home_team_name: str,
    away_team_name: str,
    home_color: str = "#FF3333",
    away_color: str = "#3385FF",
    figsize: Tuple[int, int] = (12, 5)
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot cumulative Expected Goals (xG) over time.

    :param events: DataFrame containing match events.
    :param home_team_id: Home team ID.
    :param away_team_id: Away team ID.
    :param home_team_name: Home team name.
    :param away_team_name: Away team name.
    :param home_color: Home team color.
    :param away_color: Away team color.
    :param figsize: Figure size.
    :return: Matplotlib Figure and Axes.
    """
    bg_color = '#F8F9FA'
    text_color = '#1A1A1A'
    
    fig, ax = plt.subplots(figsize=figsize, facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    df = events.copy()
    if 'minute_start' in df.columns:
        df['minute'] = df['minute_start']
    elif 'timestamp' in df.columns:
        df['minute'] = df['timestamp'] / 60
    else:
        return fig, ax
        
    if 'expected_goal_value' not in df.columns:
        df['expected_goal_value'] = 0.0
        
    df = df.sort_values('minute', kind='mergesort')
    
    home_xg = df[df['team_id'] == home_team_id][['minute', 'expected_goal_value']].copy()
    away_xg = df[df['team_id'] == away_team_id][['minute', 'expected_goal_value']].copy()
    
    home_xg['cumulative'] = home_xg['expected_goal_value'].cumsum()
    away_xg['cumulative'] = away_xg['expected_goal_value'].cumsum()
    
    max_min = df['minute'].max() if not df.empty else 90
    
    def add_endpoints(min_xg_df):
        if min_xg_df.empty:
            return pd.DataFrame({'minute': [0, max_min], 'cumulative': [0, 0]})
        
        start = pd.DataFrame({'minute': [0], 'cumulative': [0]})
        end = pd.DataFrame({'minute': [max_min], 'cumulative': [min_xg_df['cumulative'].iloc[-1]]})
        
        return pd.concat([start, min_xg_df, end])
        
    home_xg_plot = add_endpoints(home_xg)
    away_xg_plot = add_endpoints(away_xg)
    
    ax.step(home_xg_plot['minute'], home_xg_plot['cumulative'], where='post',
            label=home_team_name, color=home_color, linewidth=2.5)
            
    ax.step(away_xg_plot['minute'], away_xg_plot['cumulative'], where='post',
            label=away_team_name, color=away_color, linewidth=2.5)
            
    ax.fill_between(home_xg_plot['minute'], home_xg_plot['cumulative'], step='post',
                   color=home_color, alpha=0.1)
    ax.fill_between(away_xg_plot['minute'], away_xg_plot['cumulative'], step='post',
                   color=away_color, alpha=0.1)
                   
    ax.set_xlabel("Time (minutes)", fontsize=12, color=text_color)
    ax.set_ylabel("Cumulative xG", fontsize=12, color=text_color)
    
    ax.grid(True, linestyle='--', alpha=0.3, color='#999999')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ax.legend(loc='upper left', frameon=False, labelcolor=text_color)
    
    return fig, ax

def plot_shot_map(
    shots: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    pitch_length: float = 105,
    pitch_width: float = 68,
    home_color: str = "red",
    away_color: str = "blue",
    figsize: Tuple[int, int] = (12, 8)
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot shot map for both teams.

    :param shots: DataFrame containing shot events.
    :param home_team_id: Home team ID.
    :param away_team_id: Away team ID.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param home_color: Home team color.
    :param away_color: Away team color.
    :param figsize: Figure size.
    :return: Matplotlib Figure and Axes.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        pitch_color='white',
        line_color='black',
        linewidth=1
    )
    fig, ax = pitch.draw(figsize=figsize)
    
    home_shots = shots[shots['team_id'] == home_team_id]
    
    home_misses = home_shots[home_shots['lead_to_goal'] != True]
    pitch.scatter(
        home_misses['x_start'], home_misses['y_start'],
        ax=ax, s=100, c=home_color, edgecolors='black', marker='o', label='Home Shot', alpha=0.7
    )
    
    home_goals = home_shots[home_shots['lead_to_goal'] == True]
    pitch.scatter(
        home_goals['x_start'], home_goals['y_start'],
        ax=ax, s=300, c=home_color, edgecolors='black', marker='*', label='Home Goal', zorder=10
    )
    
    away_shots = shots[shots['team_id'] == away_team_id]
    
    away_x = -away_shots['x_start']
    away_y = -away_shots['y_start']
    
    away_misses_mask = away_shots['lead_to_goal'] != True
    pitch.scatter(
        away_x[away_misses_mask], away_y[away_misses_mask],
        ax=ax, s=100, c=away_color, edgecolors='black', marker='o', label='Away Shot', alpha=0.7
    )
    
    away_goals_mask = away_shots['lead_to_goal'] == True
    pitch.scatter(
        away_x[away_goals_mask], away_y[away_goals_mask],
        ax=ax, s=300, c=away_color, edgecolors='black', marker='*', label='Away Goal', zorder=10
    )
    
    return fig, ax

def plot_team_shot_map(
    shots: pd.DataFrame,
    team_name: str,
    team_color: str,
    pitch_length: float = 105,
    pitch_width: float = 68,
    figsize: Tuple[int, int] = (14, 9)
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot shot map in Stats Perform style (Robust v4) with fixed Logo Visibility.

    :param shots: DataFrame containing shot events.
    :param team_name: Name of the team.
    :param team_color: Color of the team.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param figsize: Figure size.
    :return: Matplotlib Figure and Axes (pitch axes).
    """
    bg_color = '#F8F9FA'
    text_color = '#1A1A1A'
    line_color = '#666666'
    
    fig = plt.figure(figsize=figsize, facecolor=bg_color)
    gs = fig.add_gridspec(1, 2, width_ratios=[2, 1])
    
    ax_pitch = fig.add_subplot(gs[0])
    
    pitch = VerticalPitch(
        pitch_type='skillcorner',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        pitch_color=bg_color,
        line_color=line_color,
        half=True,
        linewidth=1.2,
        pad_bottom=0.5
    )
    pitch.draw(ax=ax_pitch)
    
    ax_stats = fig.add_subplot(gs[1])
    ax_stats.set_facecolor(bg_color)
    ax_stats.axis('off')
    
    ax_stats.set_xlim(0, 1)
    ax_stats.set_ylim(0, 1)
    
    logo_file = utils.get_team_logo_file(team_name)
    
    header_y = 0.92
    logo_x = 0.12
    text_x = 0.25
    logo_target_height = 65
    
    if logo_file:
        try:
            im = None
            if str(logo_file).lower().endswith('.svg'):
                try:
                    import cairosvg
                    png_data = cairosvg.svg2png(url=str(logo_file))
                    im = plt.imread(io.BytesIO(png_data))
                except Exception:
                    try:
                        from svglib.svglib import svg2rlg
                        from reportlab.graphics import renderPM
                        drawing = svg2rlg(str(logo_file))
                        png_data = io.BytesIO()
                        renderPM.drawToFile(drawing, png_data, fmt="PNG")
                        png_data.seek(0)
                        im = plt.imread(png_data)
                    except Exception:
                        pass
                        im = None
            else:
                im = plt.imread(logo_file)
            
            if im is not None:
                img_height = im.shape[0]
                zoom_factor = logo_target_height / img_height
                imagebox = OffsetImage(im, zoom=zoom_factor)
                ab = AnnotationBbox(
                    imagebox, 
                    (logo_x, header_y), 
                    frameon=False, 
                    pad=0,
                    box_alignment=(0.5, 0.5),
                    zorder=50
                )
                ax_stats.add_artist(ab)
            else:
                text_x = 0.05
        except Exception:
            text_x = 0.05
    else:
        text_x = 0.05
        
    ax_stats.text(text_x, header_y + 0.01, team_name, fontsize=20, color=text_color, fontweight='bold', ha='left', va='center')
    ax_stats.text(text_x, header_y - 0.035, "Shot Map", fontsize=12, color=line_color, ha='left', va='center')
    ax_stats.plot([0.05, 0.9], [0.84, 0.84], color=line_color, linewidth=0.5)

    df = shots.copy()
    
    if not df.empty:
        max_x = df['x_start'].abs().max()
        max_y = df['y_start'].abs().max()
        
        if max_x <= 1.5 and max_y <= 1.5:
            df['x_start'] = df['x_start'] * pitch_length
            df['y_start'] = df['y_start'] * pitch_width
            
        is_centered = (df['x_start'].min() < -5) or (df['y_start'].min() < -5)
        
        if is_centered:
            goal_x = pitch_length / 2
            goal_y = 0
        else:
            goal_x = pitch_length
            goal_y = pitch_width / 2

        if 'expected_goal_value' not in df.columns:
            df['expected_goal_value'] = 0.0
            
        df['expected_goal_value'] = pd.to_numeric(df['expected_goal_value'], errors='coerce').fillna(0)
        
        is_xg_zero = (df['expected_goal_value'].sum() == 0)
        xg_source = "Provider"
        
        if is_xg_zero:
            df['dist_to_goal'] = np.sqrt((df['x_start'] - goal_x)**2 + (df['y_start'] - goal_y)**2)
            df['expected_goal_value'] = 0.75 * np.exp(-0.16 * df['dist_to_goal'])
            xg_source = "Distance Model"
    else:
         total_goals = 0
         total_shots = 0
         total_xg = 0.0
         xg_per_shot = 0.0
         xg_source = "N/A"

    if not df.empty:
        goals = df[df['lead_to_goal'] == True].copy()
        non_goals = df[df['lead_to_goal'] != True].copy()
        
        total_goals = len(goals)
        total_shots = len(df)
        total_xg = df['expected_goal_value'].sum()
        xg_per_shot = total_xg / total_shots if total_shots > 0 else 0
        
        def get_marker_size(x, scale=800):
            return x * scale + 60

        if not non_goals.empty:
            pitch.scatter(
                non_goals['x_start'], non_goals['y_start'],
                ax=ax_pitch, s=get_marker_size(non_goals['expected_goal_value'], 700),
                edgecolors='#C9A050', facecolors='none', linewidths=1.2, marker='o', alpha=0.7, zorder=5
            )
            
        if not goals.empty:
            pitch.scatter(
                goals['x_start'], goals['y_start'],
                ax=ax_pitch, s=get_marker_size(goals['expected_goal_value'], 900),
                color=team_color, edgecolors='black', linewidths=1.0, marker='o', alpha=0.9, zorder=10
            )
            pitch.scatter(
                goals['x_start'], goals['y_start'],
                ax=ax_pitch, s=get_marker_size(goals['expected_goal_value'], 1400),
                color=team_color, alpha=0.2, zorder=9
            )

    y_start = 0.75
    y_step = 0.08
    
    ax_stats.scatter(0.1, y_start, s=500, color=team_color, edgecolors='black', zorder=10)
    ax_stats.text(0.1, y_start, str(total_goals), fontsize=14, color='white', fontweight='bold', ha='center', va='center')
    ax_stats.text(0.25, y_start, "Goals", fontsize=16, color=text_color, va='center')
    
    ax_stats.text(0.1, y_start - y_step, f"{total_xg:.2f}", fontsize=18, color=text_color, fontweight='bold', ha='center')
    ax_stats.text(0.25, y_start - y_step, "xG", fontsize=16, color=text_color, va='center')
    
    ax_stats.scatter(0.1, y_start - 2*y_step, s=500, facecolors='none', edgecolors='#C9A050', linewidths=2)
    ax_stats.text(0.1, y_start - 2*y_step, str(total_shots), fontsize=13, color='#C9A050', fontweight='bold', ha='center', va='center')
    ax_stats.text(0.25, y_start - 2*y_step, "Shots", fontsize=16, color=text_color, va='center')

    ax_stats.text(0.1, y_start - 3*y_step, f"{xg_per_shot:.2f}", fontsize=18, color=text_color, fontweight='bold', ha='center')
    ax_stats.text(0.25, y_start - 3*y_step, "xG per shot", fontsize=14, color=text_color, va='center')
    
    ax_stats.text(0.5, 0.25, "Shot Quality", color=line_color, fontsize=11, ha='center', va='bottom')
    
    y_circ = 0.18
    ax_stats.scatter(0.3, y_circ, s=100, facecolors='none', edgecolors='#C9A050', linewidths=1)
    ax_stats.scatter(0.5, y_circ, s=350, facecolors='none', edgecolors='#C9A050', linewidths=1)
    ax_stats.scatter(0.7, y_circ, s=600, facecolors='none', edgecolors='#C9A050', linewidths=1)
    
    ax_stats.text(0.3, 0.10, "Low", color=line_color, fontsize=8, ha='center', va='bottom')
    ax_stats.text(0.5, 0.10, "Med", color=line_color, fontsize=8, ha='center', va='bottom')
    ax_stats.text(0.7, 0.10, "High", color=line_color, fontsize=8, ha='center', va='bottom')
    
    ax_stats.text(0.0, 0.01, f"xG Source: {xg_source}\nExcluding own goals", color=line_color, fontsize=8, ha='left', va='bottom')

    plt.tight_layout()
    return fig, ax_pitch

def plot_team_metric_over_time(
    metrics_df: pd.DataFrame,
    metric: str,
    team_name: str,
    fig: Optional[plt.Figure] = None,
    ax: Optional[plt.Axes] = None,
    figsize: Tuple[int, int] = (12, 6),
    title: Optional[str] = None
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot a team metric over time.

    :param metrics_df: DataFrame containing metrics over time.
    :param metric: The column name of the metric to plot.
    :param team_name: Name of the team.
    :param fig: Optional existing Figure.
    :param ax: Optional existing Axes.
    :param figsize: Figure size.
    :param title: Plot title.
    :return: Matplotlib Figure and Axes.
    """
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    ax.plot(metrics_df['timestamp'] / 60, metrics_df[metric], 
            label=team_name, linewidth=2)

    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel(metric.replace('_', ' ').title())
    ax.legend()
    ax.grid(True, alpha=0.3)

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

    return fig, ax


def render_lineup_html(players_data: List[Dict[str, Any]], team_color: str) -> str:
    """
    Render an HTML lineup table with enhanced visuals.

    :param players_data: List of player dictionaries.
    :param team_color: Color specific to the team.
    :return: HTML string representing the lineup table.
    """
    pos_order = {
        "GK": 0, "GR": 0, "RB": 1, "RCB": 2, "CB": 2.5, "LCB": 3, "LB": 4,
        "CDM": 5, "DM": 5, "LDM": 5, "RDM": 5, "RCM": 6, "CM": 6.5,
        "LCM": 7, "RW": 8, "RM": 8, "LW": 9, "LM": 9, "ST": 10, "CF": 10, "SUB": 99
    }

    def get_pos_rank(pos):
        return pos_order.get(pos, 100) if pos else 100

    starters = []
    subs = []
    
    for p in players_data:
        start_time = p.get('start_time', '00:00:00')
        pos = p.get('detailed_position') or p.get('position')
        if pos == 'Substitute': pos = 'SUB'
        
        p_obj = {
            'name': p['name'], 'jersey': p['jersey_no'], 'pos': pos,
            'start_time': start_time, 'end_time': p.get('end_time'),
            'yellow': p.get('yellow_card', 0), 'red': p.get('red_card', 0),
            'goals': p.get('goals', 0), 'minutes_played': p.get('minutes_played', 0)
        }
        
        is_starter = (start_time == "00:00:00" or start_time == "00:00:00.000") and pos != 'SUB'
        if is_starter:
            starters.append(p_obj)
        else:
            subs.append(p_obj)
    
    starters.sort(key=lambda x: get_pos_rank(x['pos']))
    subs.sort(key=lambda x: str(x['start_time']))

    html = f"""
<style>
    .lineup-container {{ font-family: sans-serif; font-size: 14px; width: 100%; border-collapse: collapse; }}
    .lineup-row {{ border-bottom: 1px solid #ddd; padding: 8px 4px; display: flex; align-items: center; }}
    .jersey {{ font-weight: bold; width: 30px; }}
    .name {{ flex-grow: 1; font-weight: 500; }}
    .pos {{ color: #888; font-size: 12px; width: 40px; text-align: right; }}
    .events {{ margin-left: 10px; display: flex; gap: 4px; align-items: center; }}
    .sub-info {{ font-size: 11px; margin-left: 5px; display: flex; align-items: center; }}
    .sub-in {{ color: #28a745; }}
    .sub-out {{ color: #dc3545; }}
</style>
<div class="lineup-container">
"""
    
    for p in starters:
        events_html = ""
        if p['goals']: events_html += f"<span>{'Goals' * p['goals']}</span>"
        if p['yellow']: events_html += f"<span>{'Yellow' * p['yellow']}</span>"
        if p['red']: events_html += "<span>Red</span>"
        
        sub_html = ""
        if p['end_time']:
            try:
                h, m, s = map(float, p['end_time'].split(':'))
                sub_html = f"<span class='sub-info sub-out'>↓ {int(h*60+m)}'</span>"
            except: pass

        html += f"""
<div class="lineup-row">
    <span class="jersey" style="color: {team_color}">{p['jersey']}</span>
    <span class="name">{p['name']}</span>
    <div class="events">{events_html} {sub_html}</div>
    <span class="pos">{p['pos']}</span>
</div>"""
        
    html += "<div style='padding: 8px 4px; font-weight: bold; color: #555; background-color: #f9f9f9;'>Substitutes</div>"
    
    for p in subs:
        events_html = ""
        if p['goals']: events_html += f"<span>{'Goals' * p['goals']}</span>"
        if p['yellow']: events_html += f"<span>{'Yellow' * p['yellow']}</span>"
        if p['red']: events_html += "<span>Red</span>"
            
        sub_html = ""
        if p['start_time'] and p['minutes_played'] > 0:
            try:
                h, m, s = map(float, p['start_time'].split(':'))
                sub_html = f"<span class='sub-info sub-in'>↑ {int(h*60+m)}'</span>"
            except: pass

        html += f"""
<div class="lineup-row">
    <span class="jersey" style="color: {team_color}">{p['jersey']}</span>
    <span class="name">{p['name']}</span>
    <div class="events">{events_html} {sub_html}</div>
    <span class="pos">{p['pos']}</span>
</div>"""
        
    html += "</div>"
    return html

def extract_frame_data(frame: Any) -> Tuple[List[Dict], List[Dict], Dict, List]:
    """
    Extract player and ball data from a Kloppy frame, including velocity if available.

    :param frame: The frame object from Kloppy.
    :return: Lists of home players, away players, ball data, and camera polygon.
    """
    home_players = []
    away_players = []
    ball = None
    camera_polygon = []
    
    teams_map = {} 
    
    source_data = frame.players_data if hasattr(frame, 'players_data') else frame.players_coordinates
    
    for player, data in source_data.items():
        coords = data.coordinates if hasattr(data, 'coordinates') else data
        
        if not coords: 
            continue
            
        tid = str(player.team.team_id)
        if tid not in teams_map:
            teams_map[tid] = []
            
        p_info = {
            'player_id': player.player_id,
            'name': player.name,
            'jersey_no': player.jersey_no,
            'x': coords.x,
            'y': coords.y,
            'team_obj': player.team,
            'vx': getattr(data, 'vx', 0) if hasattr(data, 'vx') else 0,
            'vy': getattr(data, 'vy', 0) if hasattr(data, 'vy') else 0,
            'speed': getattr(data, 'speed', 0) if hasattr(data, 'speed') else 0
        }
        teams_map[tid].append(p_info)

    team_ids = sorted(teams_map.keys())
    
    home_id = None
    away_id = None
    
    for tid in team_ids:
        players = teams_map[tid]
        if players:
            team_obj = players[0]['team_obj']
            if hasattr(team_obj, 'ground'):
                if str(team_obj.ground) == 'home':
                    home_id = tid
                elif str(team_obj.ground) == 'away':
                    away_id = tid
    
    if home_id is None and len(team_ids) > 0:
        home_id = team_ids[0]
    if away_id is None and len(team_ids) > 1:
        away_id = team_ids[1]
        
    if home_id and home_id in teams_map:
        home_players = teams_map[home_id]
    if away_id and away_id in teams_map:
        away_players = teams_map[away_id]
            
    if frame.ball_coordinates:
         ball = {'x': frame.ball_coordinates.x, 'y': frame.ball_coordinates.y}
          
    return home_players, away_players, ball, camera_polygon

def draw_wavy_path(ax, start, end, color, amplitude=0.5, wavelength=2.0, zorder=2):
    """
    Draw a wavy line (sine wave) between two points to represent a Carry.

    :param ax: Matplotlib axes.
    :param start: Start coordinates.
    :param end: End coordinates.
    :param color: Line color.
    :param amplitude: Wave amplitude.
    :param wavelength: Wave wavelength.
    :param zorder: Plot zorder.
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

def plot_frame_with_events(
    frame: Any,
    dataset: Any,
    events_df: Optional[pd.DataFrame] = None,
    show_camera: bool = True,
    pitch_length: float = 105,
    pitch_width: float = 68,
    figsize: Tuple[int, int] = (12, 8)
) -> plt.Figure:
    """
    Plot a single frame in 'Ghost' / 'Tactical Board' style.
    
    Style Rules:
    - Players: Light Grey (#E0E0E0) with Dark Grey Outline.
    - Numbers: Black/Dark Grey.
    - Events: Colored Lines/Arrows (Home=Green, Away=Blue).
    - Pass: Dashed Arrow.
    - Carry: Wavy Arrow.

    :param frame: Frame object to plot.
    :param dataset: Dataset containing the frame.
    :param events_df: DataFrame of match events.
    :param show_camera: Whether to show camera polygon.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param figsize: Figure size.
    :return: Matplotlib Figure.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        pitch_color='white',
        line_color='black',
        linewidth=1.5
    )
    fig, ax = pitch.draw(figsize=figsize)
    
    home_p, away_p, ball, _ = extract_frame_data(frame)
    
    for p in home_p + away_p:
        pitch.scatter(p['x'], p['y'], ax=ax, c='#E0E0E0', s=350, edgecolors='#404040', linewidth=2, zorder=3)
        ax.text(p['x'], p['y'], str(p['jersey_no']), 
                ha='center', va='center', fontsize=12, fontweight='bold', color='#202020', zorder=4)
        
        speed = p.get('speed') or 0
        if speed > 4.0:
            vx, vy = p.get('vx', 0), p.get('vy', 0)
            pitch.arrows(p['x'], p['y'], p['x'] + vx*0.5, p['y'] + vy*0.5, 
                        ax=ax, color='#404040', alpha=0.5, width=2, headwidth=4, zorder=2)
            
    if ball:
        pitch.scatter(ball['x'], ball['y'], ax=ax, c='black', s=120, edgecolors='white', linewidth=1.5, zorder=5)
    
    if events_df is not None and not events_df.empty:
        frame_time = frame.timestamp.total_seconds() if hasattr(frame.timestamp, 'total_seconds') else float(frame.timestamp)
        
        if 'timestamp' in events_df.columns:
            window_events = events_df[
                (events_df['timestamp'] >= frame_time - 2.0) & 
                (events_df['timestamp'] <= frame_time)
            ]
        elif 'frame_start' in events_df.columns:
            frame_id = frame.frame_id if hasattr(frame, 'frame_id') else 0
            window_events = events_df[
                (events_df['frame_start'] >= frame_id - 20) & 
                (events_df['frame_start'] <= frame_id)
            ]
        else:
            window_events = pd.DataFrame()
        
        home_avg_x = np.mean([p['x'] for p in home_p]) if home_p else 0
        away_avg_x = np.mean([p['x'] for p in away_p]) if away_p else 0
        
        for _, ev in window_events.iterrows():
            if pd.isna(ev['x_start']): continue
            
            x_start = float(ev['x_start'])
            y_start = float(ev['y_start'])
            x_end = ev.get('x_end')
            y_end = ev.get('y_end')
            
            if pd.notna(x_end):
                x_end = float(x_end)
                y_end = float(y_end)
            
            p_id = ev['player_id']
            is_home = False
            player_team_avg_x = away_avg_x
            
            for p in home_p:
                if str(p['player_id']) == str(p_id):
                    is_home = True
                    player_team_avg_x = home_avg_x
                    break
            
            if player_team_avg_x > 0:
                x_start = -x_start
                y_start = -y_start
                if pd.notna(x_end):
                    x_end = -x_end
                    y_end = -y_end
            
            color = '#32FF69' if is_home else '#3385FF'
            
            etype = str(ev.get('event_type', '')).lower()
            
            if 'passing_option' in etype:
                if pd.notna(x_end):
                    pitch.scatter(x_start, y_start, ax=ax, 
                                s=600, facecolors='none', edgecolors=color, 
                                linewidth=3, alpha=0.8, zorder=8)
                    
                    pitch.arrows(x_start, y_start, x_end, y_end,
                               ax=ax, color=color, width=2, headwidth=6, zorder=9, alpha=0.7)
                               
            elif 'player_possession' in etype or 'possession' in etype:
                from matplotlib.patches import Circle
                circle = Circle((x_start, y_start), radius=1.5, 
                              fill=False, edgecolor=color, linewidth=3, 
                              linestyle='--', alpha=0.9, zorder=8)
                ax.add_patch(circle)
                
                pitch.scatter(x_start, y_start, ax=ax, 
                            c=color, s=250, edgecolors='white', 
                            linewidth=2, zorder=9, marker='o', alpha=0.8)
            
            elif 'pass' in etype and pd.notna(x_end):
                pitch.arrows(x_start, y_start, x_end, y_end,
                            ax=ax, color=color, width=3, linestyle='--', zorder=6, alpha=0.9)
                
            elif 'carry' in etype and pd.notna(x_end):
                draw_wavy_path(ax, (x_start, y_start), (x_end, y_end), color, zorder=6)
                
            pitch.scatter(x_start, y_start, ax=ax, c=color, s=200, edgecolors='black', zorder=7, marker='*')
             
    timestamp_seconds = frame.timestamp.total_seconds() if hasattr(frame.timestamp, 'total_seconds') else float(frame.timestamp)
    title_text = f"Tactical Board | {int(timestamp_seconds // 60):02d}:{int(timestamp_seconds % 60):02d}"
    ax.set_title(title_text, fontsize=16, fontweight='bold', pad=15)
    
    return fig
