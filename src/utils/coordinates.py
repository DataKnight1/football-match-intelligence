"""
Author: Tiago Monteiro
Date: 21-12-2025
Canonical coordinate transformation utilities.
Ensures all data (tracking, dynamic events) maps correctly to the SkillCorner 105x68 pitch.
"""

import numpy as np
import logging
from typing import Tuple, Union
from ..config import PITCH_LENGTH, PITCH_WIDTH, HALF_PITCH_LENGTH, HALF_PITCH_WIDTH

logger = logging.getLogger(__name__)

def to_pitch_meters(
    x: Union[float, np.ndarray], 
    y: Union[float, np.ndarray],
    source_type: str = "skillcorner"
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """
    Convert coordinates from source system to standard Pitch meters (origin center).
    Standard: X [-52.5, 52.5], Y [-34, 34]

    :param x: X-coordinate(s).
    :param y: Y-coordinate(s).
    :param source_type: Coordinate system source ('skillcorner', '0_1', '0_100').
    :return: Transformed X and Y coordinates in meters.
    """
    x = np.asarray(x)
    y = np.asarray(y)
    
    if source_type == "skillcorner":
        return x, y
    
    elif source_type == "0_1":
        x_m = (x * PITCH_LENGTH) - HALF_PITCH_LENGTH
        y_m = (y * PITCH_WIDTH) - HALF_PITCH_WIDTH
        return x_m, y_m

    elif source_type == "0_100":
        x_m = (x / 100.0 * PITCH_LENGTH) - HALF_PITCH_LENGTH
        y_m = (y / 100.0 * PITCH_WIDTH) - HALF_PITCH_WIDTH
        return x_m, y_m
        
    return x, y

def infer_and_scale_coordinates(
    x: np.ndarray, 
    y: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Strategy B: Deterministic Inference with Guardrails.
    
    Rules:
    - If max(x) <= 1.5 AND max(y) <= 1.5 -> Treat as [0, 1]
    - Else if max(x) <= 110 AND max(y) <= 110 -> Treat as [0, 100] (Percentage-ish)
    - Else -> Treat as Meters (SkillCorner native)

    :param x: Array of X-coordinates.
    :param y: Array of Y-coordinates.
    :return: Tuple of scaled X, scaled Y, and detected system name.
    """
    x_valid = x[~np.isnan(x)]
    y_valid = y[~np.isnan(y)]
    
    if len(x_valid) == 0:
        return x, y, "empty"
        
    min_x, max_x = np.min(x_valid), np.max(x_valid)
    min_y, max_y = np.min(y_valid), np.max(y_valid)
    
    scale_system = "skillcorner_or_unknown"
    
    if max_x <= 1.5 and max_y <= 1.5 and min_x >= 0 and min_y >= 0:
        scale_system = "0_1"
    elif max_x <= 110.0 and max_y <= 110.0 and (max_x > 1.5 or max_y > 1.5) and min_x >= -1.0 and min_y >= -1.0:
        scale_system = "0_100" 
    else:
        scale_system = "skillcorner_meters"
        
    x_scaled, y_scaled = to_pitch_meters(x, y, source_type=scale_system)
    
    validate_coordinate_bounds(x_scaled, y_scaled)
    
    return x_scaled, y_scaled, scale_system

def validate_coordinate_bounds(x: np.ndarray, y: np.ndarray, tolerance: float = 5.0):
    """
    Post-conversion validation.
    Asserts x in [-58, 58], y in [-38, 38] (Pitch + Runoff).
    Flags warnings if significant out-of-bounds.

    :param x: Array of X-coordinates.
    :param y: Array of Y-coordinates.
    :param tolerance: Tolerance in meters for out-of-bounds check (default: 5.0).
    """
    x_max = np.nanmax(np.abs(x))
    y_max = np.nanmax(np.abs(y))
    
    limit_x = HALF_PITCH_LENGTH + tolerance
    limit_y = HALF_PITCH_WIDTH + tolerance
    
    if x_max > limit_x or y_max > limit_y:
        logger.warning(
            f"Coordinates exceed pitch bounds after scaling! "
            f"Max Abs X: {x_max:.1f} (Limit {limit_x}), Max Abs Y: {y_max:.1f} (Limit {limit_y})"
        )

def standardize_direction(
    x: np.ndarray, 
    y: np.ndarray, 
    period: int, 
    home_attacking_dir_p1: str = 'left_to_right',
    mode: str = 'home_ltr'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Standardize play direction.
    
    :param x: Array of X-coordinates.
    :param y: Array of Y-coordinates.
    :param period: Match period (1 or 2).
    :param home_attacking_dir_p1: Direction home team attacks in P1 (default: 'left_to_right').
    :param mode: 'home_ltr' forces Home team to attack Left->Right in visual output. 'static' leaves as is.
    :return: Tuple of standardized X and Y coordinates.
    """
    if mode == 'static':
        return x, y
        
    should_flip = False
    
    current_attack = home_attacking_dir_p1 
    if period == 2:
        current_attack = 'right_to_left' if home_attacking_dir_p1 == 'left_to_right' else 'left_to_right'
    
    if current_attack == 'right_to_left':
        should_flip = True
        
    if should_flip:
        return -x, -y
        
    return x, y
