"""
Author: Tiago Monteiro
Date: 21-12-2025
Radar and Pizza chart visualizations.
"""

from typing import Tuple, Optional, List, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import PyPizza
import pandas as pd

def plot_athletic_style_pizza_chart(
    metrics_data: Dict[str, Any],
    player_name: str,
    figsize: Tuple[int, int] = (10, 10),
    background_color: str = '#F8F8F6'
) -> plt.Figure:
    """
    Create an Athletic-style polar bar chart (pizza chart) for player metrics.

    :param metrics_data: Dictionary of metrics with values and colors.
    :param player_name: Name of the player.
    :param figsize: Figure size.
    :param background_color: Background color.
    :return: Matplotlib Figure.
    """
    categories = []
    metric_names = []
    values = []
    colors = []

    for category, data in metrics_data.items():
        for i, (metric, value) in enumerate(zip(data['metrics'], data['values'])):
            categories.append(category)
            metric_names.append(metric)
            values.append(value)
            colors.append(data['color'])

    N = len(values)

    fig = plt.figure(figsize=figsize, facecolor=background_color)
    ax = fig.add_subplot(111, projection='polar')
    ax.set_facecolor(background_color)

    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
    width = 2 * np.pi / N

    bars = ax.bar(theta, values, width=width, bottom=0, alpha=0.9, zorder=3)

    for bar, color in zip(bars, colors):
        bar.set_facecolor(color)
        bar.set_edgecolor('white')
        bar.set_linewidth(2)

    ax.set_ylim(0, 100)
    grid_levels = [20, 40, 60, 80, 100]
    ax.set_yticks(grid_levels)
    ax.set_yticklabels([]) 

    ax.grid(True, linestyle='--', linewidth=1, color='gray', alpha=0.3, zorder=1)
    ax.spines['polar'].set_visible(False)

    ax.set_xticks([])

    for angle, metric, value in zip(theta, metric_names, values):
        label_radius = 115

        angle_deg = np.degrees(angle)

        rotation = angle_deg
        ha = 'left'

        if 90 < angle_deg < 270:
            rotation = angle_deg + 180
            ha = 'right'

        ax.text(angle, label_radius, metric,
                rotation=rotation,
                rotation_mode='anchor',
                ha=ha, va='center',
                fontsize=9, fontweight='bold',
                color='#1A1A1A')

        value_radius = value / 2
        ax.text(angle, value_radius, f'{int(value)}',
                ha='center', va='center',
                fontsize=11, fontweight='bold',
                color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6, edgecolor='none'))

    center_circle = plt.Circle((0, 0), 15, transform=ax.transData._b,
                              color=background_color, zorder=10)
    ax.add_patch(center_circle)

    fig.suptitle(f"{player_name} - Performance Profile",
                fontsize=18, fontweight='bold',
                color='#1A1A1A', y=0.98)

    fig.text(0.5, 0.94, "Percentile rankings vs league average",
            ha='center', fontsize=10, color='#6C757D')

    plt.tight_layout()

    return fig

def plot_energy_expenditure_pizza(
    phase_data: pd.DataFrame,
    title: str = "Energy Expenditure by Phase"
) -> plt.Figure:
    """
    Plot energy expenditure (distance) as a pizza chart.
    Splits into Attacking and Defending phases.

    :param phase_data: DataFrame containing phase data and distances.
    :param title: Plot title.
    :return: Matplotlib Figure.
    """
    def clean_phase(name):
        return str(name).replace('Attacking: ', '').replace('Defending: ', '').replace('_', ' ').title()

    attacking = phase_data[phase_data['tactical_phase'].str.contains('Attacking', case=False, na=False)].copy()
    defending = phase_data[phase_data['tactical_phase'].str.contains('Defending', case=False, na=False)].copy()
    
    params = []
    values = []
    colors = []
    
    for i, row in attacking.iterrows():
        params.append(clean_phase(row['tactical_phase']))
        values.append(round(row['dist_frame'], 2)) 
        colors.append("#32FF69") 
        
    for i, row in defending.iterrows():
        params.append(clean_phase(row['tactical_phase']))
        values.append(round(row['dist_frame'], 2))
        colors.append("#FF5555") 
        
    if not values:
        return plt.figure()
        
    max_val = max(values)
    min_range = [0] * len(values)
    max_range = [max_val * 1.1] * len(values)
        
    baker = PyPizza(
        params=params,
        min_range=min_range,
        max_range=max_range,
        background_color="#F8F9FA",
        straight_line_color="#E0E0E0",
        last_circle_lw=1,
        other_circle_lw=1,
        inner_circle_size=20 
    )
    
    fig, ax = baker.make_pizza(
        values,
        figsize=(8, 8),
        param_location=110,
        slice_colors=colors,
        kwargs_slices=dict(
            edgecolor="#F8F9FA",
            zorder=2, linewidth=1
        ),
        kwargs_params=dict(
            color="#000000", fontsize=9,
            va="center"
        ),
        kwargs_values=dict(
            color="#000000", fontsize=9,
            zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="white",
                boxstyle="round,pad=0.2", lw=1, alpha=0.8
            )
        )
    )
    
    fig.text(
        0.515, 0.97, title, size=16,
        ha="center", color="#000000", fontweight='bold'
    )
    
    fig.text(0.515, 0.93, "Green: In Possession | Red: Out of Possession", size=10, ha="center", color="#666666")
    
    return fig

def plot_run_types_pizza(
    run_counts: pd.Series,
    title: str = "Types of Runs Made"
) -> plt.Figure:
    """
    Plot run types as a pizza chart with green tones.

    :param run_counts: Series containing counts of different run types.
    :param title: Plot title.
    :return: Matplotlib Figure.
    """
    if run_counts.empty:
        return plt.figure()
        
    params = [str(x).replace('_', ' ').title() for x in run_counts.index]
    values = run_counts.values.tolist()
    
    green_shades = ['#1a8c49', '#1fc96d', '#32ff69', '#66ff8f', '#99ffb5', '#ccffdb']
    colors = [green_shades[i % len(green_shades)] for i in range(len(values))]
    
    max_val = max(values)
    min_range = [0] * len(values)
    max_range = [max_val * 1.05] * len(values)
    
    baker = PyPizza(
        params=params,
        min_range=min_range,
        max_range=max_range,
        background_color="#F8F9FA",
        straight_line_color="#E0E0E0",
        last_circle_lw=1,
        other_circle_lw=1,
        inner_circle_size=20
    )
    
    fig, ax = baker.make_pizza(
        values,
        figsize=(8, 8),
        param_location=110,
        slice_colors=colors,
        kwargs_slices=dict(
            edgecolor="#F8F9FA",
            zorder=2, linewidth=1
        ),
        kwargs_params=dict(
            color="#000000", fontsize=9,
            va="center"
        ),
        kwargs_values=dict(
            color="#000000", fontsize=9,
            zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="white",
                boxstyle="round,pad=0.2", lw=1, alpha=0.8
            )
        )
    )
    
    fig.text(
        0.515, 0.97, title, size=16,
        ha="center", color="#000000", fontweight='bold'
    )
    
    return fig

def plot_comparison_pizza(
    params: List[str],
    values_a: List[float],
    values_b: List[float],
    player_a_name: str = "Player A",
    player_b_name: str = "Player B",
    min_range: Optional[List[float]] = None,
    max_range: Optional[List[float]] = None
) -> plt.Figure:
    """
    Plot Comparison Pizza Chart.
    
    :param params: List of parameter names.
    :param values_a: List of values for Player A.
    :param values_b: List of values for Player B.
    :param player_a_name: Name of Player A.
    :param player_b_name: Name of Player B.
    :param min_range: List of minimum possible values for parameters.
    :param max_range: List of maximum possible values for parameters.
    :return: Matplotlib Figure.
    """
    baker = PyPizza(
        params=params,                  
        min_range=min_range,            
        max_range=max_range,            
        background_color="#FAFAFA",     
        straight_line_color="#EBEBE9",  
        straight_line_lw=1,             
        last_circle_lw=0,               
        last_circle_color="#EBEBE9",    
        other_circle_lw=0,              
        other_circle_ls="-",            
        inner_circle_size=20            
    )

    fig, ax = baker.make_pizza(
        values_a,                       
        compare_values=values_b,        
        figsize=(8, 8),                 
        color_blank_space="same",       
        slice_colors=["#32FF69"] * len(params), 
        value_colors=["#000000"] * len(params), 
        blank_alpha=0.4,                
        kwargs_slices=dict(
            facecolor="#32FF69", edgecolor="#F2F2F2",
            zorder=2, linewidth=1
        ),                              
        kwargs_compare=dict(
            facecolor="#3385FF", edgecolor="#F2F2F2",
            zorder=2, linewidth=1, alpha=0.6
        ),                              
        kwargs_params=dict(
            color="#000000", fontsize=10, fontname="Arial",
            va="center"
        ),                              
        kwargs_values=dict(
            color="#000000", fontsize=10,
            zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="#32FF69",
                boxstyle="round,pad=0.2", lw=1
            )
        ),                              
        kwargs_compare_values=dict(
            color="#000000", fontsize=10, zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="#3385FF",
                boxstyle="round,pad=0.2", lw=1
            )
        ),                              
    )
    
    fig.text(
        0.515, 0.97, f"{player_a_name} vs {player_b_name}", 
        size=16, ha="center", fontweight="bold", color="#1A1A1A"
    )
    
    fig.text(
        0.35, 0.93, f"{player_a_name}", 
        size=10, ha="right", fontweight="bold", color="#1A1A1A"
    )
    fig.text(
        0.65, 0.93, f"{player_b_name}", 
        size=10, ha="left", fontweight="bold", color="#1A1A1A"
    )
    
    fig.add_artist(plt.Rectangle((0.36, 0.935), 0.05, 0.015, color='#32FF69', transform=fig.transFigure))
    fig.add_artist(plt.Rectangle((0.59, 0.935), 0.05, 0.015, color='#3385FF', transform=fig.transFigure))

    texts = [t for t in ax.texts if t.get_text()]
    n_params = len(params)
    
    if len(texts) >= 3 * n_params:
        for i in range(n_params):
            idx_a = n_params + i
            raw_a = values_a[i]
            texts[idx_a].set_text(f"{raw_a:.2f}")
            
            idx_b = 2 * n_params + i
            raw_b = values_b[i]
            texts[idx_b].set_text(f"{raw_b:.2f}")
            
    return fig
