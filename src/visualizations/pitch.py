"""
Author: Tiago Monteiro
Date: 21-12-2025
Basic pitch visualization functions.
"""

from typing import Optional, Tuple, List
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch

def plot_player_positions(
    x: np.ndarray,
    y: np.ndarray,
    labels: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    pitch_color: str = "#22312b",
    line_color: str = "white",
    figsize: Tuple[int, int] = (12, 8),
    title: Optional[str] = None,
    **kwargs
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot player positions on a football pitch.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param labels: List of player labels.
    :param colors: List of player colors.
    :param pitch_color: Pitch color.
    :param line_color: Line color.
    :param figsize: Figure size.
    :param title: Plot title.
    :return: Matplotlib Figure and Axes.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_color=pitch_color,
        line_color=line_color,
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=figsize)

    if colors is None:
        colors = ['#32FE6B'] * len(x)

    scatter_kwargs = {
        's': 600,
        'edgecolors': 'white',
        'linewidths': 2.5,
        'zorder': 10,
        'alpha': 0.9
    }
    scatter_kwargs.update(kwargs)

    ax.scatter(x, y, c=colors, **scatter_kwargs)

    if labels is not None:
        for xi, yi, label in zip(x, y, labels):
            ax.text(
                xi, yi, str(label),
                color='black',
                fontweight='bold',
                fontsize=10,
                ha='center',
                va='center',
                zorder=15
            )

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=20)

    return fig, ax


def plot_player_trajectory(
    x: np.ndarray,
    y: np.ndarray,
    color: str = '#32FE6B',
    pitch_color: str = "#22312b",
    line_color: str = "white",
    figsize: Tuple[int, int] = (12, 8),
    title: Optional[str] = None,
    show_start_end: bool = True,
    **kwargs
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot player movement trajectory on a football pitch.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param color: Trajectory color.
    :param pitch_color: Pitch color.
    :param line_color: Line color.
    :param figsize: Figure size.
    :param title: Plot title.
    :param show_start_end: Whether to show start/end markers.
    :return: Matplotlib Figure and Axes.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_color=pitch_color,
        line_color=line_color,
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=figsize)

    plot_kwargs = {'linewidth': 2, 'alpha': 0.7, 'zorder': 5}
    plot_kwargs.update(kwargs)
    ax.plot(x, y, color=color, **plot_kwargs)

    if show_start_end:
        ax.scatter(x[0], y[0], s=300, c='green', edgecolors='white',
                  linewidths=2, zorder=10, label='Start', marker='o')
        ax.scatter(x[-1], y[-1], s=300, c='red', edgecolors='white',
                  linewidths=2, zorder=10, label='End', marker='X')
        ax.legend(loc='upper right', framealpha=0.7)

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', color='white', pad=20)

    return fig, ax
