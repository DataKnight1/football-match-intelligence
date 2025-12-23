"""
Author: Tiago Monteiro
Date: 21-12-2025
Animation functions for match frames.
"""

from typing import Tuple, Dict, Any
import matplotlib.pyplot as plt
from mplsoccer import Pitch

def create_animation_frame(
    frame_data: Dict[str, Any],
    pitch_color: str = "#22312b",
    line_color: str = "white",
    figsize: Tuple[int, int] = (12, 8)
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a single frame for animation.

    :param frame_data: Dictionary containing frame data (positions).
    :param pitch_color: Pitch ground color.
    :param line_color: Pitch line color.
    :param figsize: Figure size dimensions.
    :return: Matplotlib Figure and Axes objects.
    """
    pitch = Pitch(
        pitch_type='skillcorner',
        pitch_color=pitch_color,
        line_color=line_color,
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=figsize)

    ax.scatter(
        frame_data['home_x'], frame_data['home_y'],
        s=400, c='#3385FF', edgecolors='white',
        linewidths=2, zorder=10, alpha=0.9
    )
    ax.scatter(
        frame_data['away_x'], frame_data['away_y'],
        s=400, c='#FF3333', edgecolors='white',
        linewidths=2, zorder=10, alpha=0.9
    )

    ax.scatter(
        frame_data['ball_x'], frame_data['ball_y'],
        s=200, c='white', edgecolors='black',
        linewidths=2, zorder=15, marker='o'
    )

    timestamp = frame_data.get('timestamp', 0)
    minutes = int(timestamp // 60)
    seconds = int(timestamp % 60)
    ax.text(
        0, 24, 
        f"Frame: {frame_data.get('frame_num', 0)} | Time: {minutes:02d}:{seconds:02d}",
        ha='center',
        fontsize=12,
        fontweight='bold',
        color='white',
        bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
        zorder=20
    )

    return fig, ax
