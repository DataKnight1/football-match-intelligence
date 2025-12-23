"""
Author: Tiago Monteiro
Date: 21-12-2025
Technical metrics calculations (Passing, Shooting, Dribbling, Defense).
"""

import pandas as pd
import numpy as np

def calculate_technical_metrics(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical metrics for all players in the events dataframe.
    
    :param events_df: DataFrame containing match events.
    :return: DataFrame with columns [player_id, player_name, Passing, Shooting, Dribbling, Defense]
    """
    if events_df.empty:
        return pd.DataFrame(columns=['player_id', 'player_name', 'Passing', 'Shooting', 'Dribbling', 'Defense'])
        
    req_cols = ['player_id', 'player_name', 'end_type', 'event_type']
    for c in req_cols:
        if c not in events_df.columns:
             return pd.DataFrame(columns=['player_id', 'player_name', 'Passing', 'Shooting', 'Dribbling', 'Defense'])

    metrics = []
    
    grouped = events_df.groupby(['player_id', 'player_name'])
    
    for (pid, pname), group in grouped:
        if pd.isna(pid):
            continue
            
        passing = len(group[group['end_type'] == 'pass'])
        
        shooting = len(group[group['end_type'] == 'shot'])
        
        dribbling = len(group[group['event_type'].str.lower().str.contains('duel', na=False)])
        
        def_types = ['interception', 'tackle', 'clearance', 'ball recovery']
        defense = len(group[group['event_type'].str.lower().isin(def_types)])
        
        metrics.append({
            'player_id': pid,
            'player_name': pname,
            'Passing': passing,
            'Shooting': shooting,
            'Dribbling': dribbling,
            'Defense': defense
        })
        
    return pd.DataFrame(metrics)
