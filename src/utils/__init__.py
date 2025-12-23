"""
Author: Tiago Monteiro
Date: 21-12-2025
Initialization info for utils module.
"""

from .pitch import pitch_dimensions, get_pitch_zone
from .geometry import calculate_distance, calculate_angle, calculate_team_centroid, calculate_team_spread
from .physics import calculate_velocity, calculate_acceleration, classify_speed, smooth_trajectory, calculate_covered_distance
from .misc import (
    safe_float, truthy, pick_first, format_event_description, find_frame_by_id, 
    get_team_logo_file, get_team_color, get_team_logo_base64, 
    TEAM_NAME_MAP, TEAM_COLOR_MAP, time_to_seconds, seconds_to_time
)
