"""
Author: Tiago Monteiro
Date: 21-12-2025
Team-level visualizations (Shape, Convex Hulls, Control).
"""

from typing import Tuple, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mplsoccer import Pitch
from scipy.spatial import ConvexHull

SOLUTION_GREEN = '#32FF69'

def plot_team_convex_hull(
    player_positions: pd.DataFrame,
    team_id: int,
    frame_id: Optional[int] = None,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0,
    team_color: str = SOLUTION_GREEN,
    title: str = "Team Shape (Convex Hull)"
) -> plt.Figure:
    """
    Plot team's convex hull showing shape and coverage area.

    :param player_positions: DataFrame containing player positions.
    :param team_id: Team ID.
    :param frame_id: Optional frame ID to filter.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param team_color: Color of the hull.
    :param title: Plot title.
    :return: Matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
                  pitch_color='#F8F8F6', line_color='#A9A9A9')
    pitch.draw(ax=ax)
    
    team_data = player_positions[player_positions['team_id'] == team_id] if 'team_id' in player_positions.columns else player_positions
    
    if frame_id is not None and 'frame' in team_data.columns:
        team_data = team_data[team_data['frame'] == frame_id]
    
    if team_data.empty or len(team_data) < 3:
        ax.text(pitch_length/2, pitch_width/2, "Insufficient data for convex hull",
               ha='center', va='center', fontsize=14)
        ax.set_title(title, fontsize=16, fontweight='bold')
        return fig
    
    positions = team_data[['x', 'y']].dropna().values
    
    if len(positions) < 3:
        ax.text(pitch_length/2, pitch_width/2, "Insufficient positions for convex hull",
               ha='center', va='center', fontsize=14)
        ax.set_title(title, fontsize=16, fontweight='bold')
        return fig
    
    try:
        hull = ConvexHull(positions)
        hull_points = positions[hull.vertices]
        
        polygon = plt.Polygon(hull_points, facecolor=team_color, alpha=0.2,
                             edgecolor=team_color, linewidth=3, zorder=2)
        ax.add_patch(polygon)
        
        pitch.scatter(positions[:, 0], positions[:, 1], ax=ax, 
                     c='white', s=100, edgecolors=team_color, linewidths=2, zorder=3)
        
        area = hull.volume 
        ax.text(0.02, 0.98, f"Coverage Area: {area:.0f} m²",
               transform=ax.transAxes, ha='left', va='top', fontsize=12,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
    except Exception as e:
        ax.text(pitch_length/2, pitch_width/2, f"Error calculating hull: {str(e)}",
               ha='center', va='center', fontsize=12)
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    return fig

def plot_defensive_line_box(
    line_heights: pd.Series,
    team_name: str = "Team"
) -> plt.Figure:
    """
    Box plot of defensive line heights showing consistency.

    :param line_heights: Series containing line heights.
    :param team_name: Name of the team.
    :return: Matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if line_heights.empty:
        ax.text(0.5, 0.5, "No defensive line data available",
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(f"{team_name} - Defensive Line Height", fontsize=14, fontweight='bold')
        return fig
    
    bp = ax.boxplot([line_heights.dropna()], vert=True, patch_artist=True,
                    boxprops=dict(facecolor=SOLUTION_GREEN, alpha=0.3),
                    medianprops=dict(color=SOLUTION_GREEN, linewidth=2),
                    whiskerprops=dict(color=SOLUTION_GREEN),
                    capprops=dict(color=SOLUTION_GREEN),
                    flierprops=dict(marker='o', markerfacecolor='red', markersize=8,
                                   markeredgecolor='darkred', alpha=0.7))
    
    ax.set_ylabel("Y-Coordinate (m)", fontsize=12)
    ax.set_xlabel("Defensive Line", fontsize=12)
    ax.set_title(f"{team_name} - Defensive Line Height Distribution", 
                fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    stats_text = f"Mean: {line_heights.mean():.1f}m\nStd: {line_heights.std():.1f}m"
    ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
           ha='right', va='top', fontsize=10,
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    return fig

def plot_field_tilt_bar(
    tilt_percentage: float,
    team_name: str = "Team",
    opp_name: str = "Opposition"
) -> plt.Figure:
    """
    Plot a horizontal bar showing field tilt (territory dominance).

    :param tilt_percentage: Field tilt percentage for the team.
    :param team_name: Name of the team.
    :param opp_name: Name of the opposition.
    :return: Matplotlib Figure.
    """
    NEUTRAL_GRAY = '#D3D3D3'
    
    fig, ax = plt.subplots(figsize=(10, 2))
    
    ax.barh([0], [tilt_percentage], color=SOLUTION_GREEN, height=0.5, label=team_name)
    ax.barh([0], [100 - tilt_percentage], left=[tilt_percentage], 
           color=NEUTRAL_GRAY, height=0.5, label=opp_name)
    
    ax.text(tilt_percentage/2, 0, f"{tilt_percentage:.1f}%", 
           ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(tilt_percentage + (100-tilt_percentage)/2, 0, f"{100-tilt_percentage:.1f}%",
           ha='center', va='center', fontsize=14, fontweight='bold', color='black')
    
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, 0.5)
    ax.axis('off')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.4), ncol=2, frameon=False)
    ax.set_title("Field Tilt (Territory Dominance)", fontsize=14, fontweight='bold', pad=30)
    
    plt.tight_layout()
    return fig

def plot_zone_control(
    events: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    home_color: str,
    away_color: str,
    pitch_length: float = 105,
    pitch_width: float = 68,
    figsize: Tuple[int, int] = (10, 7),
    n_x_zones: int = 4,
    n_y_zones: int = 3,
    title: str = "Zone Control Map"
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot a zone control map showing which team dominates each zone.

    :param events: DataFrame of events.
    :param home_team_id: Home team ID.
    :param away_team_id: Away team ID.
    :param home_color: Home team color.
    :param away_color: Away team color.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param figsize: Figure size.
    :param n_x_zones: Number of zones in x direction.
    :param n_y_zones: Number of zones in y direction.
    :param title: Plot title.
    :return: Matplotlib Figure and Axes.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        pitch_color='#F0F0F0',
        line_color='black',
        linewidth=1.5,
    )
    
    fig, ax = pitch.draw(figsize=figsize)
    
    x_min, x_max = -pitch_length/2, pitch_length/2
    y_min, y_max = -pitch_width/2, pitch_width/2
    
    x_edges = np.linspace(x_min, x_max, n_x_zones + 1)
    y_edges = np.linspace(y_min, y_max, n_y_zones + 1)
    
    df = events.dropna(subset=['x_start', 'y_start'])
    
    for i in range(n_x_zones):
        for j in range(n_y_zones):
            x0, x1 = x_edges[i], x_edges[i+1]
            y0, y1 = y_edges[j], y_edges[j+1]
            
            in_zone = df[
                (df['x_start'] >= x0) & (df['x_start'] < x1) &
                (df['y_start'] >= y0) & (df['y_start'] < y1)
            ]
            
            home_count = len(in_zone[in_zone['team_id'] == home_team_id])
            away_count = len(in_zone[in_zone['team_id'] == away_team_id])
            total = home_count + away_count
            
            if total > 0:
                home_share = home_count / total
                away_share = away_count / total
                
                if home_share >= 0.5:
                    base_color = home_color
                    alpha = 0.3 + (0.5 * (home_share - 0.5) / 0.5)
                    dominant_pct = home_share * 100
                else:
                    base_color = away_color
                    alpha = 0.3 + (0.5 * (away_share - 0.5) / 0.5)
                    dominant_pct = away_share * 100
                    
                rect = patches.Rectangle(
                    (x0, y0), x1-x0, y1-y0,
                    linewidth=1, edgecolor='white', facecolor=base_color, alpha=alpha,
                    zorder=1
                )
                ax.add_patch(rect)
                
                cx, cy = (x0 + x1)/2, (y0 + y1)/2
                ax.text(cx, cy, f"{int(dominant_pct)}%", 
                        ha='center', va='center', fontsize=10, 
                        fontweight='bold', color='black', alpha=0.7, zorder=2)
                
    if title:
        ax.set_title(title, fontsize=15, fontweight='bold', pad=15)
        
    return fig, ax

def plot_convex_hull(
    x: np.ndarray,
    y: np.ndarray,
    poly_color: str = SOLUTION_GREEN,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0,
    pitch_color: str = '#F8F8F6',
    line_color: str = '#A9A9A9',
    title: str = "Territory (Convex Hull)"
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Generic convex hull plot from x/y coordinates.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param poly_color: Color of the polygon.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param pitch_color: Pitch color.
    :param line_color: Line color.
    :param title: Plot title.
    :return: Matplotlib Figure and Axes.
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
                  pitch_color=pitch_color, line_color=line_color)
    pitch.draw(ax=ax)
    
    positions = np.column_stack((x, y))
    
    if len(positions) < 3:
        ax.text(pitch_length/2, pitch_width/2, "Insufficient data", ha='center', va='center')
        return fig, ax
        
    try:
        hull = ConvexHull(positions)
        hull_points = positions[hull.vertices]
        
        polygon = plt.Polygon(hull_points, facecolor=poly_color, alpha=0.3,
                             edgecolor=poly_color, linewidth=2, zorder=2)
        ax.add_patch(polygon)
        
        pitch.scatter(x, y, ax=ax, c=poly_color, s=30, alpha=0.6, zorder=3)
        
    except Exception as e:
        ax.text(0, 0, f"Error: {str(e)}", ha='center')
        
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
        
    return fig, ax
