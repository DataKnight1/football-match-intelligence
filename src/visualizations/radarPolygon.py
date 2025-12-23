"""
Author: Tiago Monteiro
Date: 22-12-2025
Radar plot visualization for run profiles.
"""

from typing import List, Dict
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import textwrap

def plot_run_stats_radar(
    df: pd.DataFrame,
    player_id: int,
    metrics: List[str],
    metric_labels: Dict[str, str],
    title: str = "Off-Ball Run Profile",
    highlight_color: str = '#32FF69'
) -> plt.Figure:
    """
    Create a Radar chart for a player's run statistics vs the available population range.
    Using standard matplotlib polar plot for stability.
    
    :param df: DataFrame containing statistics for all players.
    :param player_id: The ID of the player to visualize.
    :param metrics: List of column names to use as metrics.
    :param metric_labels: Dictionary mapping column names to display labels.
    :param title: Plot title.
    :param highlight_color: Color for the player's polygon.
    :return: Matplotlib Figure.
    """
    if df.empty or player_id not in df['player_id'].values:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No Data Available", ha='center')
        ax.axis('off')
        return fig
        
    ranges = {}
    for m in metrics:
        if m in df.columns:
            min_v = df[m].min()
            max_v = df[m].max()
            if max_v == min_v: max_v += 0.001
            ranges[m] = (min_v, max_v)
        else:
            ranges[m] = (0, 1)

    player_stats = df[df['player_id'] == player_id].iloc[0]
    
    scaled_values = []
    for m in metrics:
        raw = float(player_stats[m]) if m in df.columns else 0.0
        min_v, max_v = ranges[m]
        val = (raw - min_v) / (max_v - min_v)
        scaled_values.append(val)

    num_vars = len(metrics)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    
    scaled_values += [scaled_values[0]]
    angles += [angles[0]]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    display_labels = [metric_labels.get(m, m) for m in metrics]
    display_labels = [textwrap.fill(l, 10) for l in display_labels]
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(display_labels, fontsize=10, fontweight='bold', color='#1A1A1A')
    
    ax.set_yticklabels([])
    ax.set_ylim(0, 1.1)
    
    ax.plot(angles, scaled_values, color=highlight_color, linewidth=2, linestyle='solid')
    ax.fill(angles, scaled_values, color=highlight_color, alpha=0.4)
    
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    ax.grid(color='#AAAAAA', linestyle='--', alpha=0.5)
    ax.spines['polar'].set_visible(False)
    
    plt.title(title, size=14, color='black', y=1.1, fontweight='bold')
    
    return fig
