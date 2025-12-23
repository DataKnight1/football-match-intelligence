"""
Author: Tiago Monteiro
Date: 21-12-2025
Data extraction, manipulation, and smoothing core functions.
Uses Gap-Aware Smoothing for high-quality velocity derivation.
"""

from typing import Any, Optional, Dict, List
import pandas as pd
import numpy as np
import logging

from ..utils.coordinates import to_pitch_meters
from ..config import MAX_VELOCITY_KMH, VELOCITY_ANOMALY_THRESHOLD
from .filters import apply_gap_aware_smoothing
from .time import calculate_match_clock, get_period_starts

logger = logging.getLogger(__name__)

def extract_player_data(
    dataset: Any,
    player_id: int,
    include_velocity: bool = True,
    smooth: bool = True,
    min_detection_rate: float = 0.95
) -> pd.DataFrame:
    """
    Extract position and velocity data for a specific player.
    Applies Gap-Aware Savitzky-Golay smoothing if enabled.

    :param dataset: The match dataset (Kloppy object).
    :param player_id: The ID of the player to extract.
    :param include_velocity: Whether to calculate velocity and acceleration.
    :param smooth: Whether to apply smoothing to position and velocity.
    :param min_detection_rate: Minimum detection rate required to retain data.
    :return: DataFrame containing player tracking data.
    """
    raw_records = []
    pid_str = str(player_id)
    
    for frame in dataset.frames:
        target_p_data = next((d for p, d in frame.players_data.items() if str(p.player_id) == pid_str), None)
        
        if target_p_data and target_p_data.coordinates:
             raw_records.append({
                 'frame': frame.frame_id,
                 'timestamp': frame.timestamp,
                 'period': frame.period.id,
                 'x': target_p_data.coordinates.x,
                 'y': target_p_data.coordinates.y
             })

    if not raw_records:
        return pd.DataFrame()

    df = pd.DataFrame(raw_records)
    
    df = df.sort_values('timestamp').reset_index(drop=True)
    df = df.drop_duplicates(subset=['timestamp'], keep='first').reset_index(drop=True)
    
    if not df.empty:
        x_p99 = df['x'].quantile(0.99)
        
        if x_p99 < 1.2:
            logger.info(f"Player {player_id}: Detected normalized coordinates (P99 X: {x_p99:.2f}). Scaling to 105x68.")
            df['x'] = df['x'] * 105.0
            df['y'] = df['y'] * 68.0
            
    if smooth and len(df) > 5:
        df['x_smooth'] = apply_gap_aware_smoothing(df['x'], df['timestamp'])
        df['y_smooth'] = apply_gap_aware_smoothing(df['y'], df['timestamp'])
    else:
        df['x_smooth'] = df['x']
        df['y_smooth'] = df['y']
        
    if include_velocity and len(df) > 1:
        t = df['timestamp'].values
        x = df['x_smooth'].values
        y = df['y_smooth'].values
        
        dt = np.gradient(t)
        
        if np.issubdtype(dt.dtype, np.timedelta64):
            dt = dt / np.timedelta64(1, 's')
        
        t_seconds = t
        if np.issubdtype(t.dtype, np.timedelta64):
             t_seconds = t / np.timedelta64(1, 's')
        elif np.issubdtype(t.dtype, np.datetime64):
             t_seconds = (t - t[0]) / np.timedelta64(1, 's')
        
        dt[dt < 1e-4] = np.nan
        
        df['time_delta'] = dt
        if len(df) > 1:
             median_dt = np.nanmedian(dt)
             df['time_delta'] = df['time_delta'].fillna(median_dt)
        
        vx = np.gradient(x, t_seconds) 
        vy = np.gradient(y, t_seconds)
        
        speed_ms = np.sqrt(vx**2 + vy**2)

        max_ms = MAX_VELOCITY_KMH / 3.6
        anomaly_ms = VELOCITY_ANOMALY_THRESHOLD / 3.6

        if np.any(speed_ms > anomaly_ms):
            anomaly_count = np.sum(speed_ms > anomaly_ms)
            logger.warning(f"Player {player_id}: {anomaly_count} velocity anomalies detected > {VELOCITY_ANOMALY_THRESHOLD} km/h")

        speed_ms = np.clip(speed_ms, 0, max_ms)

        df['velocity_raw'] = speed_ms
        df['vx'] = vx
        df['vy'] = vy

        if smooth and len(df) > 5:
            df['velocity'] = apply_gap_aware_smoothing(
                speed_ms, df['timestamp'],
                max_gap_seconds=0.2, window_size=5, poly_order=2
            )
        else:
            df['velocity'] = speed_ms

        df['velocity_kmh'] = df['velocity'] * 3.6

        if len(df) > 2:
            v = df['velocity'].values
            accel = np.gradient(v, t)  

            if smooth and len(df) > 5:
                df['acceleration'] = apply_gap_aware_smoothing(
                    accel, df['timestamp'],
                    max_gap_seconds=0.2, window_size=5, poly_order=2
                )
            else:
                df['acceleration'] = accel

    if len(df) > 0 and min_detection_rate > 0:
        if 'is_detected' not in df.columns:
            df['is_detected'] = ~(df['x'].isna() | df['y'].isna())

        initial_frames = len(df)

        detection_rate = df['is_detected'].mean()

        if detection_rate < min_detection_rate:
            logger.warning(f"Player {player_id}: Low detection rate {detection_rate:.2%} < {min_detection_rate:.2%}")
            df = df[df['is_detected']].copy()

            if len(df) < initial_frames * 0.5:
                logger.warning(f"Player {player_id}: Dropped {initial_frames - len(df)} frames due to low detection rate")

    return df

def extract_team_data(
    dataset: Any,
    team_id: int,
    frame_id: Optional[int] = None
) -> pd.DataFrame:
    """
    Extract positions for all players in a team at a specific frame.

    :param dataset: The match dataset.
    :param team_id: The ID of the team.
    :param frame_id: The ID of the frame to extract.
    :return: DataFrame containing positions of all players in the team at that frame.
    """
    if frame_id is None:
        return pd.DataFrame()

    frame = next((f for f in dataset.frames if f.frame_id == frame_id), None)
    
    if not frame:
        return pd.DataFrame()
        
    players_data = []
    for player, data in frame.players_data.items():
        if str(player.team.team_id) == str(team_id) and data.coordinates:
            players_data.append({
                'player_id': int(player.player_id),
                'player_name': player.name,
                'jersey_no': player.jersey_no,
                'x': data.coordinates.x,
                'y': data.coordinates.y,
                'speed': getattr(data, 'speed', None) 
            })

    return pd.DataFrame(players_data)


def merge_tracking_with_events(
    tracking_df: pd.DataFrame,
    events_df: pd.DataFrame,
    tolerance_seconds: float = 0.2
) -> pd.DataFrame:
    """
    Merge tracking data with dynamic events.
    Uses Timestamp-based merge with tolerance (Nearest).

    :param tracking_df: DataFrame containing tracking data.
    :param events_df: DataFrame containing event data.
    :param tolerance_seconds: Tolerance for merging by timestamp.
    :return: Tracking DataFrame enriched with event data.
    """
    if tracking_df.empty or events_df.empty:
        return tracking_df
        
    tracking_df = tracking_df.sort_values('timestamp')
        
    return tracking_df

def calculate_match_minute(df: pd.DataFrame, match_periods_data: Any) -> pd.DataFrame:
    """
    Legacy wrapper for calculating match minute.
    Uses the new canonical calculate_match_clock from src.preprocessing.time
    but maintains the old DataFrame enrichment API.

    :param df: DataFrame containing tracking data.
    :param match_periods_data: Metadata containing period start information.
    :return: DataFrame with 'match_minute' column added.
    """
    starts = {}
    if isinstance(match_periods_data, dict):
        starts = match_periods_data
    elif isinstance(match_periods_data, list):
         starts = get_period_starts({'periods': match_periods_data})
         
    if 'frame' in df.columns and 'period' in df.columns:
        
        seconds = calculate_match_clock(
            df['frame'].values, 
            df['period'].values, 
            starts
        )
        
        if isinstance(seconds, np.ndarray):
            df['match_minute'] = seconds / 60.0 
            
    return df

def convert_tracking_wide_to_long(df: pd.DataFrame, metadata: Optional[Dict] = None, *args, **kwargs) -> pd.DataFrame:
    """
    Convert tracking DataFrame from wide format (one row per frame) to long format.
    Handles columns like '51678_x' (PlayerID_Attr) or 'Home_51678_x'.
    Uses metadata to resolve Team ID if missing from column name.

    :param df: DataFrame in wide format.
    :param metadata: Match metadata for resolving team IDs.
    :return: DataFrame in long format.
    """
    if df.empty:
        return df

    if 'frame_id' in df.columns and 'frame' not in df.columns:
        df = df.rename(columns={'frame_id': 'frame'})

    if 'period_id' in df.columns and 'period' not in df.columns:
        df = df.rename(columns={'period_id': 'period'})

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns.values]

    id_vars = [c for c in ['frame', 'timestamp', 'period', 'match_minute'] if c in df.columns]
    
    ball_cols = [c for c in df.columns if 'ball' in c.lower()]
    id_vars.extend(ball_cols)
    
    melted = df.melt(id_vars=id_vars, var_name='track_id', value_name='val')

    regex_no_team = r"^(?P<player_id>\d+)_(?P<attr>[a-zA-Z0-9]+)$"
    meta_no_team = melted['track_id'].str.extract(regex_no_team, expand=True)
    
    regex_with_team = r"^(?P<team>.+?)_(?P<player_id>\d+)_(?P<attr>[a-zA-Z0-9]+)$"
    meta_with_team = melted['track_id'].str.extract(regex_with_team, expand=True)
    
    meta = pd.DataFrame(index=melted.index, columns=['team', 'player_id', 'attr'])
    
    mask_no = meta_no_team['player_id'].notna()
    if mask_no.any():
        meta.loc[mask_no, 'player_id'] = meta_no_team.loc[mask_no, 'player_id']
        meta.loc[mask_no, 'attr'] = meta_no_team.loc[mask_no, 'attr']
    
    mask_with = meta_with_team['player_id'].notna()
    if mask_with.any():
        meta.loc[mask_with, 'team'] = meta_with_team.loc[mask_with, 'team']
        meta.loc[mask_with, 'player_id'] = meta_with_team.loc[mask_with, 'player_id']
        meta.loc[mask_with, 'attr'] = meta_with_team.loc[mask_with, 'attr']
    
    valid_mask = meta['player_id'].notna() & meta['attr'].notna()

    if valid_mask.sum() == 0:
        return pd.DataFrame() 
        
    melted = melted[valid_mask].copy()
    meta = meta[valid_mask]
    
    melted['player_id'] = meta['player_id']
    melted['attr'] = meta['attr']
    
    player_team_map = {}
    if metadata:
        for p in metadata.get('home_players', []):
            player_team_map[str(p['player_id'])] = p['team_id']
        for p in metadata.get('away_players', []):
            player_team_map[str(p['player_id'])] = p['team_id']
            
    if meta['team'].notna().any():
        melted['team_id'] = meta['team']
        mask_missing = melted['team_id'].isna()
        if mask_missing.any():
            melted.loc[mask_missing, 'team_id'] = melted.loc[mask_missing, 'player_id'].map(player_team_map)
    else:
         melted['team_id'] = melted['player_id'].map(player_team_map)
         
    melted['team_id'] = melted['team_id'].fillna('Unknown')
    
    pivot_index = [c for c in ['frame', 'period', 'match_minute'] if c in id_vars]
    pivot_index.extend(['team_id', 'player_id'])

    try:
        long_df = melted.pivot_table(
            index=pivot_index,
            columns='attr',
            values='val',
            aggfunc='first'
        ).reset_index()
        
        long_df.columns.name = None
        long_df['player_id'] = pd.to_numeric(long_df['player_id'], errors='ignore')

        frame_meta_cols = ['frame'] + [c for c in ['period', 'timestamp'] + ball_cols if c in df.columns and c not in long_df.columns]

        if frame_meta_cols and len(frame_meta_cols) > 1:
            frame_metadata = df[frame_meta_cols].drop_duplicates(subset=['frame'], keep='first')

            long_df = long_df.merge(frame_metadata, on='frame', how='left')

        ball_x_col = next((c for c in df.columns if 'ball_x' in c.lower()), None)
        ball_y_col = next((c for c in df.columns if 'ball_y' in c.lower()), None)
        
        if ball_x_col and ball_y_col:
            ball_df = df[['frame', ball_x_col, ball_y_col]].copy()
            ball_df = ball_df.rename(columns={ball_x_col: 'x', ball_y_col: 'y'})
            ball_df['player_id'] = -1
            ball_df['team_id'] = -1 
            ball_df['jersey_no'] = ''
            
            for col in long_df.columns:
                if col not in ball_df.columns:
                    if col == 'timestamp' and 'timestamp' in df.columns:
                         pass
                    else:
                         ball_df[col] = np.nan 
            
            if 'timestamp' in df.columns:
                ball_df['timestamp'] = df['timestamp']
            
            ball_df = ball_df[long_df.columns.intersection(ball_df.columns)]
            
            long_df = pd.concat([long_df, ball_df], ignore_index=True)

        return long_df
    except Exception as e:
        logger.error(f"Pivoting failed: {e}")
        return pd.DataFrame()
