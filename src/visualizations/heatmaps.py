"""
Author: Tiago Monteiro
Date: 21-12-2025
Heatmap visualization functions.
"""

from typing import Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import seaborn as sns

def plot_heatmap(
    x: np.ndarray,
    y: np.ndarray,
    pitch_length: float,
    pitch_width: float,
    pitch_color: str = "#22312b",
    line_color: str = "white",
    cmap: str = 'hot',
    figsize: Tuple[int, int] = (12, 8),
    title: Optional[str] = None,
    bins: int = 30,
    **kwargs
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a 2D heatmap of player positions.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param pitch_length: Length of the pitch.
    :param pitch_width: Width of the pitch.
    :param pitch_color: Background color of the pitch.
    :param line_color: Line color of the pitch.
    :param cmap: Colormap for heatmap.
    :param figsize: Figure size.
    :param title: Plot title.
    :param bins: Number of hexagonal bins.
    :return: Matplotlib Figure and Axes.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        pitch_color=pitch_color,
        line_color=line_color,
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=figsize)

    hexbin_kwargs = {'gridsize': bins, 'cmap': cmap, 'alpha': 0.6, 'zorder': 5}
    hexbin_kwargs.update(kwargs)

    hb = ax.hexbin(x, y, **hexbin_kwargs)
    plt.colorbar(hb, ax=ax, label='Count')

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=20)

    return fig, ax


def plot_dual_heatmap(
    home_x: np.ndarray,
    home_y: np.ndarray,
    away_x: np.ndarray,
    away_y: np.ndarray,
    pitch_length: float = 105,
    pitch_width: float = 68,
    home_color: str = "Reds",
    away_color: str = "Blues",
    figsize: Tuple[int, int] = (12, 8)
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot heatmaps for both teams on the same pitch.

    :param home_x: Home team x-coordinates.
    :param home_y: Home team y-coordinates.
    :param away_x: Away team x-coordinates.
    :param away_y: Away team y-coordinates.
    :param pitch_length: Length of the pitch.
    :param pitch_width: Width of the pitch.
    :param home_color: Colormap for home team.
    :param away_color: Colormap for away team.
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
    
    sns.kdeplot(
        x=home_x, y=home_y,
        fill=True,
        cmap=home_color,
        alpha=0.5,
        levels=10,
        thresh=0.1,
        ax=ax,
        zorder=2
    )
    
    sns.kdeplot(
        x=away_x, y=away_y,
        fill=True,
        cmap=away_color,
        alpha=0.5,
        levels=10,
        thresh=0.1,
        ax=ax,
        zorder=2
    )
    
    return fig, ax

def plot_proximity_map(
    proximity_df: pd.DataFrame,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0,
    title: str = "Direct Duels"
) -> plt.Figure:
    """
    Plot heatmap/scatter of where two players clashed (distance < 8m).

    :param proximity_df: DataFrame containing clash metrics.
    :param pitch_length: Length of the pitch.
    :param pitch_width: Width of the pitch.
    :param title: Plot title.
    :return: Matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
                  pitch_color='#FAFAFA', line_color='#A0A0A0')
    pitch.draw(ax=ax)
    
    if proximity_df.empty:
        ax.text(0, 0, "No Direct Duels Recorded", color='#1A1A1A', ha='center')
        return fig
        
    sns.kdeplot(
        x=proximity_df['x'],
        y=proximity_df['y'],
        fill=True,
        thresh=0.05,
        alpha=0.5,
        cmap='Greens',
        ax=ax,
        levels=10
    )
    
    pitch.scatter(proximity_df['x'], proximity_df['y'], ax=ax,
                 c='#32FF69', s=20, alpha=0.3)
                 
    ax.set_title(title, fontsize=16, color='#1A1A1A', fontweight='bold', pad=15)
    return fig


def plot_delta_heatmap(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    player_a_name: str,
    player_b_name: str,
    pitch_length: float = 105.0,
    pitch_width: float = 68.0
) -> plt.Figure:
    """
    Plot Delta Heatmap: A (Green) - B (Purple/Grey).

    :param df_a: DataFrame for player A.
    :param df_b: DataFrame for player B.
    :param player_a_name: Name of player A.
    :param player_b_name: Name of player B.
    :param pitch_length: Length of the pitch.
    :param pitch_width: Width of the pitch.
    :return: Matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
                  pitch_color='#FAFAFA', line_color='#A0A0A0')
    pitch.draw(ax=ax)
    
    stat_a = pitch.bin_statistic(df_a['x'], df_a['y'], statistic='count', bins=(20, 15))
    stat_b = pitch.bin_statistic(df_b['x'], df_b['y'], statistic='count', bins=(20, 15))
    
    total_a = len(df_a) if len(df_a) > 0 else 1
    total_b = len(df_b) if len(df_b) > 0 else 1
    
    norm_a = stat_a['statistic'] / total_a
    norm_b = stat_b['statistic'] / total_b
    
    delta = norm_a - norm_b
    
    stat_a['statistic'] = delta
    
    pcm = pitch.heatmap(stat_a, ax=ax, cmap='PRGn', edgecolors='#FAFAFA', alpha=0.9)
    
    ax.set_title(f"Space Dominance: {player_a_name} (Green) vs {player_b_name} (Purple)", 
                fontsize=16, color='#1A1A1A', fontweight='bold', pad=15)
                
    return fig

def plot_advanced_heatmap(
    x: np.ndarray,
    y: np.ndarray,
    pitch_length: float = 105,
    pitch_width: float = 68,
    pitch_color: str = "#22312b",
    line_color: str = "white",
    cmap: str = 'hot',
    figsize: Tuple[int, int] = (12, 8),
    title: Optional[str] = None,
    hexbin: bool = True,
    gridsize: int = 30,
    **kwargs
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Wrapper for plot_heatmap to match previous API.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param pitch_length: Pitch length.
    :param pitch_width: Pitch width.
    :param pitch_color: Pitch color.
    :param line_color: Line color.
    :param cmap: Colormap.
    :param figsize: Figure size.
    :param title: Title.
    :param hexbin: Whether to use hexbin.
    :param gridsize: Grid size for hexbin.
    :return: Matplotlib Figure and Axes.
    """
    return plot_heatmap(
        x, y, 
        pitch_length, pitch_width, 
        pitch_color, line_color, 
        cmap, figsize, title, 
        bins=gridsize, 
        **kwargs
    )
