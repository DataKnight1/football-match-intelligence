"""
Author: Tiago Monteiro
Date: 21-12-2025
Feature extraction functions (metrics, stats).
"""

from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from ..utils import calculate_velocity, calculate_covered_distance


def calculate_distance_metrics(
    x: np.ndarray,
    y: np.ndarray,
    fps: float = 10.0
) -> Dict[str, float]:
    """
    Calculate distance-based metrics from trajectory.

    :param x: Array of x-coordinates (should be smoothed to avoid artifacts).
    :param y: Array of y-coordinates (should be smoothed to avoid artifacts).
    :param fps: Frames per second (default: 10.0).
    :return: Dictionary containing distance metrics.
    """
    velocity_kmh = calculate_velocity(x, y, fps=fps, unit='km/h')
    
    dx = np.diff(x)
    dy = np.diff(y)
    segment_distances = np.sqrt(dx**2 + dy**2)
    
    MAX_STEP_DISTANCE = 5.0
    valid_mask = segment_distances <= MAX_STEP_DISTANCE
    filtered_distances = segment_distances.copy()
    filtered_distances[~valid_mask] = 0
    
    total_dist = np.sum(filtered_distances)

    sprint_mask = (velocity_kmh > 25.0) & valid_mask
    hsr_mask = (velocity_kmh > 20.0) & valid_mask

    sprint_distance = np.sum(filtered_distances[sprint_mask])
    hsr_distance = np.sum(filtered_distances[hsr_mask])

    valid_velocities = velocity_kmh[velocity_kmh <= 38.0]

    if len(valid_velocities) > 0:
        robust_max_speed = np.max(valid_velocities)
        avg_speed = np.mean(valid_velocities)
    else:
        robust_max_speed = 0.0
        avg_speed = 0.0

    return {
        'total_distance': total_dist,
        'sprint_distance': sprint_distance,
        'hsr_distance': hsr_distance,
        'max_speed': robust_max_speed,
        'avg_speed': avg_speed,
    }


def calculate_proximity_stats(
    tracking_df: pd.DataFrame,
    p1_id: int,
    p2_id: int,
    threshold: float = 8.0,
    fps: int = 10
) -> Tuple[float, pd.DataFrame]:
    """
    Calculate time spent head-to-head (distance < threshold) and return clash frames.

    :param tracking_df: DataFrame containing tracking data.
    :param p1_id: ID of player 1.
    :param p2_id: ID of player 2.
    :param threshold: Distance threshold for proximity (default: 8.0).
    :param fps: Frames per second (default: 10).
    :return: Tuple containing (minutes spent, plot DataFrame).
    """
    cols = [f"{p1_id}_x", f"{p1_id}_y", f"{p2_id}_x", f"{p2_id}_y"]
    
    if not all(col in tracking_df.columns for col in cols):
        return 0.0, pd.DataFrame()
        
    df = tracking_df.dropna(subset=cols).copy()
    if df.empty:
        return 0.0, pd.DataFrame()
        
    dx = df[f"{p1_id}_x"] - df[f"{p2_id}_x"]
    dy = df[f"{p1_id}_y"] - df[f"{p2_id}_y"]
    df['distance'] = np.sqrt(dx**2 + dy**2)
    
    clash_df = df[df['distance'] <= threshold].copy()
    
    if clash_df.empty:
        return 0.0, pd.DataFrame()

    minutes = len(clash_df) / fps / 60
    
    plot_df = pd.DataFrame({
        'x': (clash_df[f"{p1_id}_x"] + clash_df[f"{p2_id}_x"]) / 2, 
        'y': (clash_df[f"{p1_id}_y"] + clash_df[f"{p2_id}_y"]) / 2,
        'distance': clash_df['distance']
    })
    
    return minutes, plot_df


def calculate_split_physical_stats(
    tracking_df: pd.DataFrame,
    player_id: int,
    team_id: int,
    fps: int = 10
) -> Dict[str, float]:
    """
    Calculate physical stats split by In/Out of Possession.

    :param tracking_df: DataFrame containing tracking data.
    :param player_id: The ID of the player.
    :param team_id: The ID of the team.
    :param fps: Frames per second (default: 10).
    :return: Dictionary containing split physical stats.
    """
    cols = [f"{player_id}_x", f"{player_id}_y", 'ball_owning_team_id']
    if not all(col in tracking_df.columns for col in cols):
        return {'in_poss_dist': 0, 'out_poss_dist': 0, 'in_poss_sprint': 0, 'out_poss_sprint': 0}
        
    df = tracking_df.dropna(subset=[f"{player_id}_x", f"{player_id}_y"]).copy()
    
    if df.empty:
         return {'in_poss_dist': 0, 'out_poss_dist': 0, 'in_poss_sprint': 0, 'out_poss_sprint': 0}

    df['x_diff'] = df[f"{player_id}_x"].diff().abs()
    df['y_diff'] = df[f"{player_id}_y"].diff().abs()
    
    dist = np.sqrt(df['x_diff']**2 + df['y_diff']**2)
    dist[dist > 1.2] = 0 
    df['step_dist'] = dist.fillna(0)
    
    df['speed'] = df['step_dist'] * fps
    
    mask_in = df['ball_owning_team_id'] == team_id
    mask_out = (df['ball_owning_team_id'] != team_id) & (df['ball_owning_team_id'].notna()) & (df['ball_owning_team_id'] != -1)
    
    stats = {}
    
    stats['in_poss_dist'] = df.loc[mask_in, 'step_dist'].sum() / 1000
    stats['out_poss_dist'] = df.loc[mask_out, 'step_dist'].sum() / 1000
    
    stats['in_poss_sprint'] = df.loc[mask_in & (df['speed'] > 5.5), 'step_dist'].sum()
    stats['out_poss_sprint'] = df.loc[mask_out & (df['speed'] > 5.5), 'step_dist'].sum()
    
    return stats


def calculate_tactical_events(events_df: pd.DataFrame, player_id: int) -> Dict[str, int]:
    """
    Calculate tactical event metrics (Passes, Shots, Dribbles, etc.).

    :param events_df: DataFrame containing match events.
    :param player_id: The ID of the player.
    :return: Dictionary containing counts of tactical events.
    """
    defaults = {
        'passes': 0, 'prog_passes': 0, 'off_ball_runs': 0,
        'dribbles': 0, 'shots': 0, 'crosses': 0,
        'interceptions': 0, 'tackles': 0, 'recoveries': 0,
        'clearances': 0
    }
    
    if events_df.empty:
         return defaults
         
    p_events = events_df[events_df['player_id'] == player_id]
    if p_events.empty:
        return defaults
    
    def count_type(df, terms):
        if isinstance(terms, str): terms = [terms]
        valid_df = df[df['event_type'] != 'passing_option']
        if valid_df.empty: return 0
        
        mask = pd.Series(False, index=valid_df.index)
        for term in terms:
            e_match = valid_df['event_type'].str.contains(term, case=False, na=False)
            e_end = valid_df['end_type'].str.contains(term, case=False, na=False) if 'end_type' in valid_df.columns else False
            e_sub = valid_df['event_subtype'].str.contains(term, case=False, na=False) if 'event_subtype' in valid_df.columns else False
            mask = mask | e_match | e_end | e_sub
            
        return len(valid_df[mask])

    active_events = p_events[p_events['event_type'] != 'passing_option']
    passes = active_events[active_events['end_type'].str.contains('pass', case=False, na=False)] if 'end_type' in active_events.columns else pd.DataFrame()
    pass_prog_count = 0
    if not passes.empty:
        dists = np.sqrt((passes['x_end']-passes['x_start'])**2 + (passes['y_end']-passes['y_start'])**2)
        pass_prog_count = len(dists[dists > 15])
        

    metrics = {
        'passes': len(passes), 
        'prog_passes': pass_prog_count,
        'off_ball_runs': len(p_events[p_events['event_type'] == 'off_ball_run']),
        'dribbles': len(p_events[p_events['event_type'] == 'player_possession']),
        'shots': count_type(p_events, ['shot', 'goal', 'save', 'post']),
        'crosses': count_type(p_events, 'cross'),
        'interceptions': count_type(p_events, 'interception'),
        'tackles': count_type(p_events, 'tackle'),
        'recoveries': count_type(p_events, 'recovery'),
        'clearances': count_type(p_events, 'clearance')
    }
    
    return metrics
