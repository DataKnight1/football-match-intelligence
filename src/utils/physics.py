"""
Author: Tiago Monteiro
Date: 21-12-2025
Physics utility functions for velocity, acceleration, and movement classification.
"""

from typing import Tuple, Optional
import numpy as np
import pandas as pd


def calculate_velocity(
    x: np.ndarray,
    y: np.ndarray,
    fps: float = 10.0,
    unit: str = "m/s",
    timestamps: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Calculate velocity from position data.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param fps: Frames per second (default: 10.0).
    :param unit: Output unit 'm/s' or 'km/h' (default: 'm/s').
    :param timestamps: Optional timestamps for variable fps.
    :return: Velocity array.
    """
    dx = np.diff(x)
    dy = np.diff(y)
    
    if timestamps is not None:
        dt = np.diff(timestamps)
        dt = np.where(dt <= 0, 1e-6, dt)
    else:
        dt = 1.0 / fps

    velocity = np.sqrt(dx**2 + dy**2) / dt

    if unit == "km/h":
        velocity = velocity * 3.6

    return velocity


def calculate_acceleration(
    x: np.ndarray,
    y: np.ndarray,
    fps: float = 10.0
) -> np.ndarray:
    """
    Calculate acceleration from position data.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param fps: Frames per second (default: 10.0).
    :return: Acceleration array.
    """
    velocity = calculate_velocity(x, y, fps=fps, unit="m/s")
    dt = 1.0 / fps

    acceleration = np.diff(velocity) / dt

    acceleration = np.concatenate([[acceleration[0]], acceleration])

    return acceleration


def classify_speed(
    velocity: np.ndarray,
    unit: str = "km/h"
) -> np.ndarray:
    """
    Classify velocity into movement categories.

    :param velocity: Velocity array.
    :param unit: Unit of velocity 'km/h' or 'm/s' (default: 'km/h').
    :return: Array of movement categories.
    """
    if unit == "m/s":
        velocity = velocity * 3.6

    categories = np.where(
        velocity < 1, 'standing',
        np.where(velocity < 11, 'walking',
        np.where(velocity < 14, 'jogging',
        np.where(velocity < 20, 'running',
        np.where(velocity < 25, 'hsr', 'sprint'))))
    )

    return categories


def smooth_trajectory(
    x: np.ndarray,
    y: np.ndarray,
    window_size: int = 5,
    method: str = "moving_average"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Smooth player trajectory to reduce noise.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param window_size: Size of smoothing window (default: 5).
    :param method: Smoothing method (default: 'moving_average').
    :return: Tuple of smoothed coordinates (x, y).
    """
    if method == "moving_average":
        from scipy.ndimage import uniform_filter1d
        x_smooth = uniform_filter1d(x, size=window_size)
        y_smooth = uniform_filter1d(y, size=window_size)

    elif method == "savgol":
        from scipy.signal import savgol_filter
        x_smooth = savgol_filter(x, window_size, polyorder=2)
        y_smooth = savgol_filter(y, window_size, polyorder=2)

    elif method == "exponential":
        alpha = 2 / (window_size + 1)
        x_smooth = pd.Series(x).ewm(alpha=alpha).mean().values
        y_smooth = pd.Series(y).ewm(alpha=alpha).mean().values

    else:
        raise ValueError(f"Unknown smoothing method: {method}")

    return x_smooth, y_smooth


def calculate_covered_distance(
    x: np.ndarray,
    y: np.ndarray
) -> float:
    """
    Calculate total distance covered along a trajectory.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :return: Total distance in meters.
    """
    dx = np.diff(x)
    dy = np.diff(y)
    distances = np.sqrt(dx**2 + dy**2)
    return np.sum(distances)
