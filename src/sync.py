"""
Author: Tiago Monteiro
Date: 21-12-2025
Synchronization utilities for aligning Event data with Tracking data.
Centralizes timestamp matching and sequence window extraction.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Union, Any
from dataclasses import dataclass

@dataclass
class SequenceContext:
    event_id: Union[str, int]
    event_type: str
    tracking_frame_idx: int
    match_time_str: str
    window_frames: pd.DataFrame
    diagnostics: Dict[str, Any]

def find_nearest_frame(
    target_timestamp: float,
    tracking_timestamps: np.ndarray,
    tracking_indices: np.ndarray,
    tolerance: float = 0.2
) -> Optional[int]:
    """
    Find the frame index nearest to the target timestamp within tolerance.
    
    :param target_timestamp: Event time in seconds.
    :param tracking_timestamps: Array of tracking timestamps.
    :param tracking_indices: Array of corresponding frame IDs/indices.
    :param tolerance: Max allowed difference in seconds.
    :return: Frame index or None.
    """
    idx = np.searchsorted(tracking_timestamps, target_timestamp)
    
    candidates = []
    
    if idx < len(tracking_timestamps):
        candidates.append(idx)
    if idx > 0:
        candidates.append(idx - 1)
        
    if not candidates:
        return None
        
    best_idx = None
    min_diff = float('inf')
    
    for c in candidates:
        diff = abs(tracking_timestamps[c] - target_timestamp)
        if diff < min_diff and diff <= tolerance:
            min_diff = diff
            best_idx = tracking_indices[c]
            
    return best_idx

def get_sequence_window(
    tracking_df: pd.DataFrame,
    center_frame_id: int,
    pre_seconds: float = 5.0,
    post_seconds: float = 5.0,
    fps: float = 10.0
) -> pd.DataFrame:
    """
    Extract a window of frames around a center frame.
    
    :param tracking_df: DataFrame containing tracking data.
    :param center_frame_id: Central frame ID.
    :param pre_seconds: Seconds before center.
    :param post_seconds: Seconds after center.
    :param fps: Frames per second.
    :return: Slice of tracking_df.
    """
    n_pre = int(pre_seconds * fps)
    n_post = int(post_seconds * fps)
    
    if 'frame' not in tracking_df.columns:
        return pd.DataFrame()
        
    start_f = center_frame_id - n_pre
    end_f = center_frame_id + n_post
    
    window = tracking_df[
        (tracking_df['frame'] >= start_f) &
        (tracking_df['frame'] <= end_f)
    ].copy()
    
    return window

def build_sequence_context(
    event_row: pd.Series,
    tracking_df: pd.DataFrame,
    pre_seconds: float = 4.0,
    post_seconds: float = 3.0
) -> Optional[SequenceContext]:
    """
    Build context for a specific event sequence.

    :param event_row: Series containing event data.
    :param tracking_df: DataFrame containing tracking data.
    :param pre_seconds: Seconds before event.
    :param post_seconds: Seconds after event.
    :return: SequenceContext object.
    """
    ts = None
    if 'timestamp' in event_row:
        ts = float(event_row['timestamp'])
    elif 'time' in event_row:
         pass
         
    frame_ref = None
    
    for col in ['start_frame', 'frame', 'frame_start', 'start_frame_id']:
        if col in event_row and pd.notna(event_row[col]):
            try:
                frame_ref = int(event_row[col])
                break
            except Exception:
                continue

    matched_frame = None
    
    if frame_ref is not None:
        if frame_ref in tracking_df['frame'].values:
            matched_frame = frame_ref
        else:
            frames = tracking_df['frame'].values
            if len(frames) > 0:
                idx = (np.abs(frames - frame_ref)).argmin()
                closest_frame = frames[idx]
                
                if abs(closest_frame - frame_ref) <= 5:
                    matched_frame = closest_frame

    elif ts is not None and not tracking_df.empty:
        t_stamps = tracking_df['timestamp'].values
        t_frames = tracking_df['frame'].values
        matched_frame = find_nearest_frame(ts, t_stamps, t_frames)
        
    if matched_frame is None:
        return None
        
    window = get_sequence_window(tracking_df, matched_frame, pre_seconds, post_seconds)
    
    return SequenceContext(
        event_id=event_row.get('event_id', 'unknown'),
        event_type=event_row.get('event_type', 'unknown'),
        tracking_frame_idx=matched_frame,
        match_time_str=str(event_row.get('match_time', '')),
        window_frames=window,
        diagnostics={
            'found_by': 'frame' if frame_ref else 'timestamp',
            'window_size': len(window)
        }
    )
