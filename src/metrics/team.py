"""
Author: Tiago Monteiro
Date: 21-12-2025
Team-level metrics calculations.
"""

from typing import Tuple, Any, List, Optional
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull


def calculate_team_compactness(
    x: np.ndarray,
    y: np.ndarray,
    method: str = 'area'
) -> float:
    """
    Calculate team compactness (spread).

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param method: Method to calculation compactness ('area', 'std', 'centroid').
    :return: The compactness value.
    """
    positions = np.column_stack([x, y])

    if method == 'area':
        if len(positions) < 3:
            return 0.0
        try:
            hull = ConvexHull(positions)
            return hull.volume 
        except Exception:
            return 0.0

    elif method == 'std':
        return np.std(x) * np.std(y)

    elif method == 'centroid':
        centroid = np.mean(positions, axis=0)
        distances = np.linalg.norm(positions - centroid, axis=1)
        return np.mean(distances)

    else:
        raise ValueError(f"Unknown method: {method}")


def calculate_team_length(
    x: np.ndarray,
    y: np.ndarray,
    direction: str = 'longitudinal'
) -> float:
    """
    Calculate team length (longitudinal or lateral).

    :param x: Array of x-coordinates.
    :param y: Array of y-coordinates.
    :param direction: Direction of calculation ('longitudinal' or 'lateral').
    :return: The team length.
    """
    if direction == 'longitudinal':
        return np.max(x) - np.min(x)
    elif direction == 'lateral':
        return np.max(y) - np.min(y)
    else:
        raise ValueError(f"Unknown direction: {direction}")


def calculate_space_occupation(
    team_positions: np.ndarray,
    pitch_length: float = 105,
    pitch_width: float = 68,
    n_zones: Tuple[int, int] = (3, 3)
) -> np.ndarray:
    """
    Calculate which pitch zones are occupied by team.

    :param team_positions: Array of team positions.
    :param pitch_length: Length of the pitch (default: 105).
    :param pitch_width: Width of the pitch (default: 68).
    :param n_zones: Tuple representing grid dimensions (default: (3, 3)).
    :return: Occupation matrix.
    """
    n_long, n_lat = n_zones

    x_bins = np.linspace(-pitch_length/2, pitch_length/2, n_long + 1)
    y_bins = np.linspace(-pitch_width/2, pitch_width/2, n_lat + 1)

    occupation = np.zeros((n_long, n_lat))

    for x, y in team_positions:
        x_zone = np.digitize(x, x_bins) - 1
        y_zone = np.digitize(y, y_bins) - 1

        x_zone = np.clip(x_zone, 0, n_long - 1)
        y_zone = np.clip(y_zone, 0, n_lat - 1)

        occupation[x_zone, y_zone] = 1

    return occupation


def calculate_defensive_line_height(
    defending_positions: np.ndarray,
    n_players: int = 4
) -> float:
    """
    Calculate defensive line height (average x-position of deepest defenders).

    :param defending_positions: Array of defending player positions.
    :param n_players: Number of deepest defenders to consider (default: 4).
    :return: The defensive line height.
    """
    x_positions = defending_positions[:, 0]
    deepest_x = np.partition(x_positions, n_players)[:n_players]
    return np.mean(deepest_x)


def calculate_attacking_width(
    attacking_positions: np.ndarray,
    percentile: int = 90
) -> float:
    """
    Calculate attacking width (lateral spread).

    :param attacking_positions: Array of attacking player positions.
    :param percentile: Percentile for spread calculation (default: 90).
    :return: The attacking width.
    """
    def q(x, p): return np.percentile(x, p)
    y_positions = attacking_positions[:, 1]
    return q(y_positions, percentile) - q(y_positions, 100 - percentile)


def calculate_team_metrics_over_time(
    dataset: Any,
    team_id: int
) -> pd.DataFrame:
    """
    Calculate team metrics for each frame of a match.

    :param dataset: The match dataset.
    :param team_id: The ID of the team.
    :return: DataFrame containing team metrics over time.
    """
    team_metrics = []
    for frame in dataset.frames:
        team_players = [
            data for player, data in frame.players_data.items()
            if player.team.team_id == team_id and data.coordinates
        ]
        
        if len(team_players) > 0:
            x_coords = np.array([p.coordinates.x for p in team_players])
            y_coords = np.array([p.coordinates.y for p in team_players])
            
            compactness = calculate_team_compactness(x_coords, y_coords)
            def_line = calculate_defensive_line_height(np.column_stack([x_coords, y_coords]))
            team_width = float(np.ptp(y_coords))
            team_length = float(np.ptp(x_coords))
            centroid_x = float(np.mean(x_coords))
            centroid_y = float(np.mean(y_coords))
            
            team_metrics.append({
                'frame': frame.frame_id,
                'timestamp': frame.timestamp,
                'compactness': compactness,
                'defensive_line_height': def_line,
                'team_width': team_width,
                'team_length': team_length,
                'centroid_x': centroid_x,
                'centroid_y': centroid_y
            })
            
    return pd.DataFrame(team_metrics)


def calculate_defensive_line_heights(
    tracking_df: pd.DataFrame,
    team_id: int,
    defensive_positions: Optional[List[str]] = None
) -> pd.Series:
    """
    Calculate defensive line heights (X-coordinates) for box plot analysis.
    Uses X coordinate to represent how high up the pitch the line is.

    :param tracking_df: DataFrame containing tracking data.
    :param team_id: The ID of the team.
    :param defensive_positions: List of position names to consider as defenders.
    :return: Series of line heights indexed by frame.
    """
    if defensive_positions is None:
        defensive_positions = ['CB', 'RB', 'LB', 'RWB', 'LWB', 'LCB', 'RCB']
    
    team_data = tracking_df[tracking_df['team_id'] == team_id] if 'team_id' in tracking_df.columns else tracking_df
    
    if team_data.empty:
        return pd.Series([], dtype=float)
    
    if 'player_position' in team_data.columns:
        def_data = team_data[
            (team_data['player_position'].isin(defensive_positions)) &
            (team_data['player_position'] != 'GK')
        ]
        if def_data.empty:
             def_data = team_data[team_data['player_position'] != 'GK']
    else:
        def_data = team_data
    
    if 'x' in def_data.columns and 'frame' in def_data.columns:
        line_heights = def_data.groupby('frame')['x'].mean()
        return line_heights
    
    return pd.Series([], dtype=float)
