"""
Author: Tiago Monteiro
Date: 21-12-2025
Pizza Chart visualizer using mplsoccer.PyPizza.
Implements correct percentile normalization against positional peer groups.
"""

import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import PyPizza
from typing import List, Dict

def plot_pizza_chart(
    player_data: Dict[str, float],
    parameter_list: List[str],
    peer_data: pd.DataFrame,
    player_name: str,
    team_name: str,
    minutes_played: float,
    min_minutes_baseline: int = 300
) -> plt.Figure:
    """
    Generate a Pizza Chart for a player comparing them to a peer group.
    
    :param player_data: Dict of {metric: raw_value_total}.
    :param parameter_list: List of metrics to plot.
    :param peer_data: DataFrame containing peer statistics (Total values).
    :param minutes_played: Minutes played by the target player.
    :param min_minutes_baseline: Minimum minutes for peers to be included.
    :return: Matplotlib Figure.
    """
    
    valid_peers = peer_data[peer_data['minutes_played'] >= min_minutes_baseline].copy()
    
    for param in parameter_list:
        if param in valid_peers.columns:
            valid_peers[f"{param}_p90"] = (valid_peers[param] / valid_peers['minutes_played']) * 90
        else:
             valid_peers[f"{param}_p90"] = 0.0

    player_values_p90 = []
    player_percentiles = []
    
    for param in parameter_list:
        val = player_data.get(param, 0.0)
        p90_val = (val / minutes_played) * 90 if minutes_played > 0 else 0
        player_values_p90.append(p90_val)
        
        peer_vals = valid_peers[f"{param}_p90"].values
        if len(peer_vals) > 0:
            import scipy.stats as stats
            pct = stats.percentileofscore(peer_vals, p90_val, kind='weak')
        else:
            pct = 0
        player_percentiles.append(int(pct))
        
    slice_colors = ["#32FF69"] * len(parameter_list) # All green for now
    text_colors = ["#F2F2F2"] * len(parameter_list)
    
    baker = PyPizza(
        params=parameter_list,
        background_color="#18181A",      # Dark Back
        straight_line_color="#E0E0E0",   # Grid
        straight_line_lw=1,
        last_circle_lw=1,
        last_circle_color="#E0E0E0",
        other_circle_ls="-.",
        other_circle_lw=1,
        inner_circle_size=20
    )
    
    fig, ax = baker.make_pizza(
        player_percentiles,
        figsize=(8, 8),
        param_location=110,
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        kwargs_slices=dict(edgecolor="#F2F2F2", zorder=2, linewidth=1),
        kwargs_params=dict(color="#F2F2F2", fontsize=10, va="center"),
        kwargs_values=dict(color="#000000", fontsize=10, zorder=3, bbox=dict(edgecolor="#000000", facecolor="#32FF69", boxstyle="round,pad=0.2", lw=1))
    )
    
    fig.text(
        0.515, 0.97, f"{player_name} - {team_name}", size=18,
        ha="center", color="#F2F2F2", fontweight='bold'
    )
    fig.text(
        0.515, 0.942,
        f"Per 90 | Comparison to {len(valid_peers)} Peers (> {min_minutes_baseline} mins)",
        size=11,
        ha="center", color="#F2F2F2"
    )
    
    return fig
