"""
Author: Tiago Monteiro
Date: 21-12-2025
Match Analysis Engine. Encapsulates data and performs complex aggregations.
"""

from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np
from . import data_loader, preprocessing, metrics

class MatchAnalyzer:
    """
    Class to analyze match data.
    """
    def __init__(self, match_id: int, dataset: Any, events: pd.DataFrame, phases: pd.DataFrame):
        """
        Initialize the MatchAnalyzer.

        :param match_id: The ID of the match.
        :param dataset: The tracking dataset.
        :param events: The DataFrame of match events.
        :param phases: The DataFrame of match phases.
        """
        self.match_id = match_id
        self.dataset = dataset
        self.events = events
        self.phases = phases
        self.metadata = data_loader.get_match_metadata(dataset)
        
        self._tracking_df = None
        self._home_players = None
        self._away_players = None
    
    @property
    def tracking_df(self) -> pd.DataFrame:
        """
        Returns the tracking DataFrame, cached.

        :return: The tracking DataFrame.
        """
        if self._tracking_df is None:
            self._tracking_df = self.dataset.to_df(engine='pandas')
        return self._tracking_df

    def get_team_stats(self) -> pd.DataFrame:
        """
        Calculate high-level physical stats for both teams.

        :return: A DataFrame containing team statistics.
        """
        players = []
        
        all_players = self.metadata['home_players'] + self.metadata['away_players']
        
        for p in all_players:
            pid = p['player_id']
            try:
                df = preprocessing.extract_player_data(self.dataset, pid)
                if df.empty:
                    continue
                
                dist_metrics = preprocessing.calculate_distance_metrics(
                    df['x'].values, df['y'].values
                )
                
                players.append({
                    'player_id': pid,
                    'name': p['name'],
                    'team': self.metadata['home_team_name'] if p in self.metadata['home_players'] else self.metadata['away_team_name'],
                    'total_distance_km': dist_metrics['total_distance'] / 1000,
                    'sprint_distance_m': dist_metrics['sprint_distance'],
                    'max_speed_kmh': dist_metrics['max_speed'],
                    'minutes_played': len(df) / (10 * 60)
                })
            except Exception:
                continue
                
        return pd.DataFrame(players)

    def get_player_profile(self, player_id: int) -> Dict[str, Any]:
        """
        Generate a complete profile for a specific player.

        :param player_id: The ID of the player.
        :return: A dictionary containing the player's profile data.
        """
        df = preprocessing.extract_player_data(self.dataset, player_id)
        if df.empty:
            return {}

        phys = preprocessing.calculate_distance_metrics(df['x'].values, df['y'].values)
        
        player_events = self.events[self.events['player_id'] == player_id]
        
        avg_x = df['x'].mean()
        avg_y = df['y'].mean()
        
        return {
            'physical': phys,
            'events': player_events['event_type'].value_counts().to_dict(),
            'avg_position': (avg_x, avg_y),
            'minutes': len(df) / 600
        }

    def calculate_pitch_control_at_event(self, event_id: int):
        """
        Calculate pitch control frame for a specific event.

        :param event_id: The ID of the event.
        :return: The pitch control matrix.
        """
        event = self.events[self.events['event_id'] == event_id].iloc[0]
        frame_id = int(event['start_frame']) if 'start_frame' in event else int(event['frame'])
        
        frame = [f for f in self.dataset.frames if f.frame_id == frame_id][0]
        
        home_pos = []
        away_pos = []
        
        home_id = self.metadata['home_team_id']
        
        for player in frame.players_data:
            if not player.coordinates: continue
            
            pos = [player.coordinates.x, player.coordinates.y]
            if player.player.team.team_id == home_id:
                home_pos.append(pos)
            else:
                away_pos.append(pos)
                
        return metrics.calculate_pitch_control(
            np.array(home_pos), 
            np.array(away_pos), 
            (frame.ball_coordinates.x, frame.ball_coordinates.y)
        )

    def get_player_summary_stats(self, player_id: int) -> Dict[str, Any]:
        """
        Generate a summary of stats for a specific player.

        :param player_id: The ID of the player.
        :return: A dictionary containing summary statistics.
        """
        df = preprocessing.extract_player_data(self.dataset, player_id)
        if df.empty:
            return {}

        phys = preprocessing.calculate_distance_metrics(df['x'].values, df['y'].values)
        
        player_events = self.events[self.events['player_id'] == player_id]
        
        stats = {
            "Max Speed": phys.get('max_speed', 0),
            "Total Distance (km)": phys.get('total_distance', 0) / 1000,
            "Sprint Distance (m)": phys.get('sprint_distance', 0),
            "Off-ball-runs": len(player_events[player_events['event_type'] == 'off_ball_run']),
            "Pressures": len(player_events[player_events['event_type'] == 'on_ball_engagement']),
        }
        
        return stats