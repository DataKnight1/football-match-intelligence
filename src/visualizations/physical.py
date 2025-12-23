"""
Author: Tiago Monteiro
Date: 21-12-2025
Physical performance metrics visualizations.
"""

from typing import Optional, List
import numpy as np
import matplotlib.pyplot as plt

def plot_speed_zones(
    velocities: np.ndarray,
    zone_thresholds: List[float] = [0, 11, 14, 19, 23, 25, 100],
    zone_labels: List[str] = ['Walking', 'Jogging', 'Running', 'High Speed', 'Sprinting', 'Explosive'],
    title: str = "Time in Speed Zones"
) -> plt.Figure:
    """
    Plot bar chart of time spent in different speed zones.

    :param velocities: Array of velocity values (assumed m/s).
    :param zone_thresholds: List of thresholds for zones (in km/h).
    :param zone_labels: List of labels for zones.
    :param title: Plot title.
    :return: Matplotlib Figure.
    """
    counts, _ = np.histogram(velocities * 3.6, bins=zone_thresholds) 
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(zone_labels, counts, color='teal', alpha=0.7)
    
    ax.set_title(title)
    ax.set_ylabel("Frame Count / Duration")
    ax.set_xlabel("Speed Zone")
    
    return fig

def plot_speed_distribution(
    velocities: np.ndarray,
    title: str = "Speed Profile (Distribution)",
    fps: Optional[float] = None,
    time_deltas: Optional[np.ndarray] = None,
    max_speed: Optional[float] = None
) -> plt.Figure:
    """
    Plot speed distribution histogram (Time Spent) with background zones.
    Assumes input `velocities` is in km/h.
    
    :param velocities: Array of velocity values (assumed km/h).
    :param title: Plot title.
    :param fps: Frames per second (used if time_deltas not provided).
    :param time_deltas: Array of time deltas in seconds for each frame.
    :param max_speed: Optional maximum speed to set chart range (km/h).
    :return: Matplotlib Figure.
    """
    zones = [
        (0, 7, 'Walking', '#D3D3D3'),
        (7, 14, 'Jogging', '#C1E1C1'),
        (14, 20, 'Running', '#90EE90'),
        (20, 25, 'HSR', '#32CD32'),
        (25, 45, 'Sprinting', '#32FF69')
    ]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if max_speed is not None:
        chart_max = min(40, int(np.ceil(max_speed / 5) * 5) + 5)
    else:
        chart_max = 40
    
    v_plot = velocities[velocities <= chart_max]
    
    bins = np.linspace(0, chart_max, chart_max + 1)
    
    if time_deltas is not None and len(time_deltas) == len(velocities):
        time_deltas_filtered = time_deltas[velocities <= chart_max]
        
        if len(time_deltas_filtered) == len(v_plot):
            hist, _ = np.histogram(v_plot, bins=bins, weights=time_deltas_filtered)
            time_minutes = hist / 60.0
        else:
            effective_fps = fps if fps else 10.0
            counts, _ = np.histogram(v_plot, bins=bins)
            time_minutes = (counts / effective_fps) / 60.0
    else:
        effective_fps = fps if fps else 10.0
        counts, _ = np.histogram(v_plot, bins=bins)
        time_minutes = (counts / effective_fps) / 60.0
    
    width = bins[1] - bins[0]
    ax.bar(bins[:-1], time_minutes, width=width, align='edge',
           color='#32FF69', edgecolor='#1A1A1A', alpha=0.9, zorder=2)
    
    y_max = time_minutes.max() * 1.15 if len(time_minutes) > 0 else 1
    ax.set_ylim(0, y_max)
    ax.set_xlim(0, chart_max)
    
    for start, end, label, color in zones:
        ax.axvspan(start, end, facecolor=color, alpha=0.3, zorder=0)
        label_x = (start + min(end, chart_max)) / 2
        if label_x < chart_max:
            ax.text(label_x, y_max * 0.95, label, ha='center', va='top', 
                   fontsize=10, fontweight='bold', color='white', rotation=0,
                   bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))

    ax.set_title(title, pad=20, fontsize=14, fontweight='bold', color='#1A1A1A')
    ax.set_xlabel("Speed (km/h)", fontsize=10, color='#1A1A1A')
    ax.set_ylabel("Time Spent (min)", fontsize=10, color='#1A1A1A')
    
    ax.tick_params(axis='x', colors='#1A1A1A')
    ax.tick_params(axis='y', colors='#1A1A1A')
    ax.spines['bottom'].set_color='#1A1A1A'
    ax.spines['left'].set_color='#1A1A1A'
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    
    return fig
