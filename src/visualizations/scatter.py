"""
Author: Tiago Monteiro
Date: 22-12-2025
Scatter plot visualization for physical metrics comparison.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Optional, List

def plot_physical_scatter(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    x_label: str = None,
    y_label: str = None,
    title: str = "Physical Performance Scatter",
    highlight_p1_id: int = None,
    highlight_p2_id: int = None,
    p1_name: str = "Player 1",
    p2_name: str = "Player 2",
    figsize=(10, 7)
):
    """
    Create a scatter plot comparing two metrics for all players, highlighting the selected two.

    :param df: DataFrame containing player metrics.
    :param x_metric: Column name for X-axis.
    :param y_metric: Column name for Y-axis.
    :param x_label: Label for X-axis.
    :param y_label: Label for Y-axis.
    :param title: Plot title.
    :param highlight_p1_id: Player ID to highlight in Solution Green.
    :param highlight_p2_id: Player ID to highlight in Contrast Blue.
    :param p1_name: Name of Player 1.
    :param p2_name: Name of Player 2.
    :param figsize: Tuple for figure size.
    :return: Matplotlib Figure.
    """
    if df.empty or x_metric not in df.columns or y_metric not in df.columns:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Insufficient Data", ha='center', va='center')
        return fig

    sns.set_style("whitegrid")
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.scatterplot(
        data=df, 
        x=x_metric, 
        y=y_metric, 
        color='#E0E0E0', 
        s=80, 
        alpha=0.6, 
        ax=ax,
        edgecolor='grey'
    )
    
    if highlight_p1_id is not None:
        p1_data = df[df['player_id'] == highlight_p1_id]
        if not p1_data.empty:
            ax.scatter(
                p1_data[x_metric], 
                p1_data[y_metric], 
                color='#32FF69', 
                s=200, 
                edgecolor='black', 
                label=p1_name,
                zorder=5
            )
            ax.text(
                p1_data[x_metric].values[0], 
                p1_data[y_metric].values[0] + (df[y_metric].max() * 0.02),
                p1_name,
                ha='center',
                fontweight='bold',
                zorder=6
            )

    if highlight_p2_id is not None:
        p2_data = df[df['player_id'] == highlight_p2_id]
        if not p2_data.empty:
            ax.scatter(
                p2_data[x_metric], 
                p2_data[y_metric], 
                color='#3385FF', 
                s=200, 
                edgecolor='black', 
                label=p2_name,
                zorder=5
            )
            ax.text(
                p2_data[x_metric].values[0], 
                p2_data[y_metric].values[0] + (df[y_metric].max() * 0.02),
                p2_name,
                ha='center',
                fontweight='bold',
                zorder=6
            )

    mean_x = df[x_metric].mean()
    mean_y = df[y_metric].mean()
    
    ax.axvline(mean_x, color='grey', linestyle='--', alpha=0.5, zorder=1)
    ax.axhline(mean_y, color='grey', linestyle='--', alpha=0.5, zorder=1)
    
    ax.set_xlabel(x_label if x_label else x_metric, fontsize=12)
    ax.set_ylabel(y_label if y_label else y_metric, fontsize=12)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    sns.despine()
    
    return fig
