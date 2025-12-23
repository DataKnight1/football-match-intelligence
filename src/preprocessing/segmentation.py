"""
Author: Tiago Monteiro
Date: 21-12-2025
Functions for segmentation and phase analysis.
"""

from typing import List, Dict, Optional
import pandas as pd


def create_time_windows(
    df: pd.DataFrame,
    window_size: int = 100,
    overlap: int = 50
) -> List[pd.DataFrame]:
    """
    Split DataFrame into overlapping time windows.

    :param df: DataFrame containing tracking data.
    :param window_size: Size of the window in frames (default: 100).
    :param overlap: Overlap between windows in frames (default: 50).
    :return: List of DataFrame windows.
    """
    windows = []
    step = window_size - overlap

    for start_idx in range(0, len(df) - window_size + 1, step):
        end_idx = start_idx + window_size
        windows.append(df.iloc[start_idx:end_idx].copy())

    return windows


def aggregate_by_phase(
    df: pd.DataFrame,
    phases_df: pd.DataFrame,
    agg_func: Dict[str, str] = None
) -> pd.DataFrame:
    """
    Aggregate tracking data by phases of play.

    :param df: DataFrame containing tracking data.
    :param phases_df: DataFrame containing phase information.
    :param agg_func: Aggregation functions map (default: None).
    :return: Aggregated phase data.
    """
    if agg_func is None:
        agg_func = {
            'velocity': 'mean',
            'velocity_kmh': 'mean',
            'x': 'mean',
            'y': 'mean',
        }

    phase_data = []

    for _, phase in phases_df.iterrows():
        phase_frames = df[
            (df['frame'] >= phase['start_frame']) &
            (df['frame'] <= phase['end_frame'])
        ]

        if len(phase_frames) > 0:
            agg_values = phase_frames.agg(agg_func).to_dict()
            agg_values['possession_phase'] = phase['possession_phase']
            agg_values['start_frame'] = phase['start_frame']
            agg_values['end_frame'] = phase['end_frame']
            phase_data.append(agg_values)

    return pd.DataFrame(phase_data)


def build_event_sequences(
    events_df: pd.DataFrame,
    phases_df: pd.DataFrame,
    target_event_type: Optional[str] = None,
    team_id: Optional[int] = None
) -> pd.DataFrame:
    """
    Link events into chronological sequences within possession phases.

    :param events_df: DataFrame containing match events.
    :param phases_df: DataFrame containing phase information.
    :param target_event_type: Optional target event type to filter sequences.
    :param team_id: Optional team ID to filter events.
    :return: DataFrame containing event sequences.
    """
    sequences = []
    
    if 'phase_index' not in events_df.columns:
        return pd.DataFrame()
    
    if team_id is not None and 'team_id' in events_df.columns:
        events_df = events_df[events_df['team_id'] == team_id].copy()
    
    for phase_idx in events_df['phase_index'].dropna().unique():
        phase_events = events_df[events_df['phase_index'] == phase_idx].copy()
        
        frame_col = 'frame_start' if 'frame_start' in phase_events.columns else 'frame'
        phase_events = phase_events.sort_values(frame_col)
        
        if target_event_type is not None:
            has_target = False
            
            if 'event_type' in phase_events.columns:
                has_target = (phase_events['event_type'].str.lower() == target_event_type.lower()).any()
            
            if not has_target and 'end_type' in phase_events.columns:
                has_target = (phase_events['end_type'].str.lower() == target_event_type.lower()).any()
            
            if not has_target:
                lead_to_col = f'lead_to_{target_event_type.lower()}'
                if lead_to_col in phase_events.columns:
                    has_target = (phase_events[lead_to_col] == True).any()
                
            if not has_target:
                continue
        
        start_frame = int(phase_events[frame_col].iloc[0])
        end_frame = int(phase_events[frame_col].iloc[-1])
        
        key_outcome = "Ends"
        if 'end_type' in phase_events.columns:
            final_end_type = phase_events.iloc[-1]['end_type']
            if isinstance(final_end_type, str):
                key_outcome = final_end_type.replace('_', ' ').title()
                
        start_type = phase_events.iloc[0]['event_type'].replace('_', ' ').title()
        
        match_minute = ""
        if 'match_minute' in phase_events.columns:
             match_minute = f"({phase_events['match_minute'].iloc[0]}')"
             
        description = f"{start_type} → {key_outcome} {match_minute}"
        
        if len(description) < 20: 
             description = f"Sequence: {description}"
        
        sequences.append({
            'sequence_id': len(sequences),
            'phase_index': phase_idx,
            'events_list': phase_events.to_dict('records'),
            'start_frame': start_frame,
            'end_frame': end_frame,
            'description': description,
            'num_events': len(phase_events)
        })
    
    return pd.DataFrame(sequences)
