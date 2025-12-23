"""
Author: Tiago Monteiro
Date: 21-12-2025
Pitch-related utility functions.
"""

from typing import Tuple, Union
import numpy as np

def pitch_dimensions(pitch_type: str = "skillcorner") -> Tuple[float, float]:
    """
    Get pitch dimensions in meters.

    :param pitch_type: Type of pitch coordinate system (default: "skillcorner").
    :return: Pitch dimensions (length, width) in meters.
    """
    dimensions = {
        "skillcorner": (105, 68),
        "standard": (105, 68),
        "opta": (100, 100),
        "wyscout": (100, 100),
        "statsbomb": (120, 80),
    }
    return dimensions.get(pitch_type, (105, 68))


def get_pitch_zone(
    x: Union[float, np.ndarray],
    y: Union[float, np.ndarray],
    pitch_length: float = 105,
    pitch_width: float = 68
) -> Union[str, np.ndarray]:
    """
    Determine pitch zone from coordinates.

    :param x: X-coordinate(s).
    :param y: Y-coordinate(s).
    :param pitch_length: Length of the pitch (default: 105).
    :param pitch_width: Width of the pitch (default: 68).
    :return: Zone identifier(s).
    """
    third = pitch_length / 3
    if np.isscalar(x):
        if x < -third:
            long_zone = "defensive_third"
        elif x > third:
            long_zone = "attacking_third"
        else:
            long_zone = "middle_third"
    else:
        long_zone = np.where(
            x < -third, "defensive_third",
            np.where(x > third, "attacking_third", "middle_third")
        )

    channel_width = pitch_width / 3
    if np.isscalar(y):
        if y < -channel_width:
            lat_zone = "left_channel"
        elif y > channel_width:
            lat_zone = "right_channel"
        else:
            lat_zone = "center_channel"
    else:
        lat_zone = np.where(
            y < -channel_width, "left_channel",
            np.where(y > channel_width, "right_channel", "center_channel")
        )

    if np.isscalar(x):
        return f"{long_zone}_{lat_zone}"
    else:
        return np.char.add(np.char.add(long_zone, "_"), lat_zone)
