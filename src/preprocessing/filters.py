"""
Author: Tiago Monteiro
Date: 21-12-2025
Data filtering and normalization functions.
Includes Gap-Aware Savitzky-Golay smoothing.
"""

from typing import Tuple, Optional, List, Union
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from ..config import SMOOTHING_WINDOW_SIZE, SMOOTHING_POLY_ORDER

def apply_gap_aware_smoothing(
    series: Union[pd.Series, np.ndarray],
    timestamps: Union[pd.Series, np.ndarray],
    max_gap_seconds: float = 0.2, 
    window_size: int = SMOOTHING_WINDOW_SIZE,
    poly_order: int = SMOOTHING_POLY_ORDER
) -> np.ndarray:
    """
    Apply Savitzky-Golay smoothing while respecting time gaps.
    If a gap > max_gap_seconds exists, smoothing is broken (reset) across the gap.
    
    :param series: Data to smooth (Position X or Y).
    :param timestamps: Corresponding timestamps (in seconds).
    :param max_gap_seconds: Gaps larger than this trigger a segment break.
    :param window_size: Smoothing window size.
    :param poly_order: Polynomial order for smoothing.
    :return: Smoothed array.
    """
    vals = np.asarray(series)
    ts = np.asarray(timestamps)
    
    if len(vals) < window_size:
        return vals 
        
    dt = np.diff(ts, prepend=ts[0])
    
    if np.issubdtype(dt.dtype, np.timedelta64):
        dt = dt / np.timedelta64(1, 's')
        
    split_indices = np.where(dt > max_gap_seconds)[0]
    
    if len(split_indices) == 0:
        return _safe_savgol(vals, window_size, poly_order)
        
    smoothed = np.empty_like(vals)
    start_idx = 0
    
    boundaries = np.concatenate([split_indices, [len(vals)]])
    
    for end_idx in boundaries:
        segment = vals[start_idx:end_idx]
        
        if len(segment) > window_size:
            smoothed[start_idx:end_idx] = _safe_savgol(segment, window_size, poly_order)
        else:
            if len(segment) > poly_order + 2:
                 w = len(segment) | 1 
                 if w == len(segment) + 1: w -= 2 
                 
                 if w > poly_order:
                    smoothed[start_idx:end_idx] = _safe_savgol(segment, w, poly_order)
                 else:
                    smoothed[start_idx:end_idx] = segment
            else:
                 smoothed[start_idx:end_idx] = segment
            
        start_idx = end_idx
        
    return smoothed

def _safe_savgol(data, window, order):
    """
    Helper to apply savgol and handle edge cases or NaNs.

    :param data: Input data array.
    :param window: Window size.
    :param order: Polynomial order.
    :return: Smoothed data array.
    """
    if np.isnan(data).any():
        df = pd.Series(data)
        data = df.interpolate(limit_direction='both').to_numpy()
        
    try:
        if window % 2 == 0: window += 1 
        return savgol_filter(data, window, order)
    except Exception:
        return data

def filter_detected_positions(
    df: pd.DataFrame,
    min_detection_rate: float = 0.95
) -> pd.DataFrame:
    """
    Filter out players with low detection rates.

    :param df: Input DataFrame.
    :param min_detection_rate: Minimum required detection rate.
    :return: Filtered DataFrame.
    """
    if 'is_detected' not in df.columns:
        return df

    detection_rate = df.groupby('player_id')['is_detected'].mean()
    valid_players = detection_rate[detection_rate >= min_detection_rate].index
    return df[df['player_id'].isin(valid_players)].copy()


def interpolate_missing_positions(
    x: np.ndarray,
    y: np.ndarray,
    method: str = 'linear',
    limit: Optional[int] = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interpolate missing position data (NaN values).

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param method: Interpolation method (default: 'linear').
    :param limit: Maximum number of consecutive NaNs to fill.
    :return: Tuple containing interpolated x and y arrays.
    """
    s_x = pd.Series(x)
    s_y = pd.Series(y)

    x_interp = s_x.interpolate(method=method, limit=limit, limit_direction='both').values
    y_interp = s_y.interpolate(method=method, limit=limit, limit_direction='both').values

    return x_interp, y_interp

from ..utils.coordinates import standardize_direction

def normalize_to_attacking_direction(
    x: np.ndarray,
    y: np.ndarray,
    period: int,
    home_team_attack_direction: List[str]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Wrapper for canonical standardize_direction.
    Maintains legacy API signature with list input.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param period: Current period.
    :param home_team_attack_direction: List indicating home team attack direction.
    :return: Tuple containing normalized x and y arrays.
    """
    p1_dir = 'left_to_right' if home_team_attack_direction[0] == 'left' else 'right_to_left'
    
    return standardize_direction(
        x, y, period, 
        home_attacking_dir_p1=p1_dir,
        mode='home_ltr' 
    )

def resample_trajectory(
    x: np.ndarray,
    y: np.ndarray,
    timestamps: np.ndarray,
    target_fps: float = 5.0,
    original_fps: float = 10.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Resample trajectory to different frame rate.

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param timestamps: Array of timestamps.
    :param target_fps: Target frames per second (default: 5.0).
    :param original_fps: Original frames per second (default: 10.0).
    :return: Tuple containing resampled x, y, and timestamps arrays.
    """
    step = int(original_fps / target_fps)
    step = max(1, step)
    return x[::step], y[::step], timestamps[::step]
