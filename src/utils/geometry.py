"""
Author: Tiago Monteiro
Date: 21-12-2025
Geometry utility functions for calculating distances, angles, etc.
"""

from typing import Tuple, Union
import numpy as np


def calculate_distance(
    x1: Union[float, np.ndarray],
    y1: Union[float, np.ndarray],
    x2: Union[float, np.ndarray],
    y2: Union[float, np.ndarray]
) -> Union[float, np.ndarray]:
    """
    Calculate Euclidean distance between two points.

    :param x1: First point x-coordinate.
    :param y1: First point y-coordinate.
    :param x2: Second point x-coordinate.
    :param y2: Second point y-coordinate.
    :return: Euclidean distance.
    """
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def calculate_angle(
    x1: float, y1: float,
    x2: float, y2: float,
    x3: float, y3: float
) -> float:
    """
    Calculate angle between three points (in degrees).

    :param x1: First point (origin) x-coordinate.
    :param y1: First point (origin) y-coordinate.
    :param x2: Second point (vertex) x-coordinate.
    :param y2: Second point (vertex) y-coordinate.
    :param x3: Third point x-coordinate.
    :param y3: Third point y-coordinate.
    :return: Angle in degrees (0-180).
    """
    v1 = np.array([x1 - x2, y1 - y2])
    v2 = np.array([x3 - x2, y3 - y2])

    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    angle = np.arccos(np.clip(cos_angle, -1, 1))

    return np.degrees(angle)


def calculate_team_centroid(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate team centroid (geometric center).

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :return: Tuple of centroid coordinates (x, y).
    """
    return np.mean(x), np.mean(y)


def calculate_team_spread(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate team spread (standard deviation of positions).

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :return: Tuple of spread values (std_x, std_y).
    """
    return np.std(x), np.std(y)
