"""
Author: Tiago Monteiro
Date: 21-12-2025
Time manipulation and match clock utilities.
Canonicalizes how 'Match Minute' is calculated across the app.
"""

from typing import Dict, Any, Union, Optional
import numpy as np
import pandas as pd

def calculate_match_clock(
    frame: Union[int, np.ndarray, pd.Series],
    period: Union[int, np.ndarray, pd.Series],
    period_start_frames: Dict[int, int],
    fps: float = 10.0
) -> Union[str, pd.Series]:
    """
    Calculate the display match clock (MM:SS) from frame/period data.
    
    :param frame: Current frame number(s)
    :param period: Current period number(s) (1 or 2)
    :param period_start_frames: Dict mapping period ID to start frame {1: 123, 2: 20000}
    :param fps: Frames per second
    :return: Formatted clock string (e.g. "45:02") or Series of strings
    """
    if isinstance(frame, (pd.Series, np.ndarray)):
        p1_mask = (period == 1)
        p2_mask = (period == 2)
        
        start_frames = np.zeros_like(frame)
        base_minutes = np.zeros_like(frame, dtype=float)
        
        p1_start = period_start_frames.get(1, 0)
        p2_start = period_start_frames.get(2, 0)
        
        start_frames[p1_mask] = p1_start
        start_frames[p2_mask] = p2_start
        
        base_minutes[p1_mask] = 0.0
        base_minutes[p2_mask] = 45.0
        
        seconds_elapsed = (frame - start_frames) / fps
        total_seconds = (base_minutes * 60) + seconds_elapsed
        
        return total_seconds
        
    else:
        start = period_start_frames.get(period, 0)
        base = 0 if period == 1 else 45
        
        seconds_elapsed = max(0, (frame - start) / fps)
        total_minutes = base + (seconds_elapsed // 60)
        rem_seconds = int(seconds_elapsed % 60)
        
        return f"{int(total_minutes):02d}:{rem_seconds:02d}"

def get_period_starts(metadata: Dict[str, Any]) -> Dict[int, int]:
    """
    Safely extract period start frames from various metadata structures.

    :param metadata: Match metadata.
    :return: Dictionary mapping period IDs to start frames.
    """
    starts = {}
    periods = metadata.get('periods_extra', metadata.get('periods', []))
    
    for p in periods:
        if isinstance(p, dict):
            pid = p.get('period', p.get('id'))
            start = p.get('start_frame')
        else:
            pid = getattr(p, 'id', None)
            start = getattr(p, 'start_frame', None)
            
        if pid and start is not None:
             starts[int(pid)] = int(start)
             
    return starts
