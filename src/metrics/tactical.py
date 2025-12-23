"""
Author: Tiago Monteiro
Date: 21-12-2025
Tactical metrics calculations.
"""

from typing import Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from scipy.spatial import distance


def calculate_pitch_control(
    attacking_positions: np.ndarray,
    defending_positions: np.ndarray,
    ball_position: Tuple[float, float],
    pitch_length: float = 105,
    pitch_width: float = 68,
    grid_resolution: int = 50
) -> np.ndarray:
    """
    Calculate pitch control surface using Voronoi-based model.

    :param attacking_positions: Array of attacking player positions.
    :param defending_positions: Array of defending player positions.
    :param ball_position: Tuple of ball coordinates (x, y).
    :param pitch_length: Length of the pitch (default: 105).
    :param pitch_width: Width of the pitch (default: 68).
    :param grid_resolution: Resolution of the grid (default: 50).
    :return: Pitch control matrix.
    """
    x_grid = np.linspace(-pitch_length/2, pitch_length/2, grid_resolution)
    y_grid = np.linspace(-pitch_width/2, pitch_width/2, grid_resolution)
    X, Y = np.meshgrid(x_grid, y_grid)

    grid_points = np.column_stack([X.flatten(), Y.flatten()])

    attack_distances = distance.cdist(grid_points, attacking_positions)
    defend_distances = distance.cdist(grid_points, defending_positions)

    min_attack_dist = np.min(attack_distances, axis=1)
    min_defend_dist = np.min(defend_distances, axis=1)

    control = (min_attack_dist < min_defend_dist).astype(float)

    return control.reshape(X.shape)


def calculate_pressing_intensity(
    defending_positions: np.ndarray,
    ball_position: Tuple[float, float],
    radius: float = 10.0
) -> Dict[str, Any]:
    """
    Calculate pressing intensity around the ball.

    :param defending_positions: Array of defending player positions.
    :param ball_position: Tuple of ball coordinates (x, y).
    :param radius: Radius to consider for pressing (default: 10.0).
    :return: Dictionary containing pressing intensity metrics.
    """
    ball_pos = np.array(ball_position)
    distances = np.linalg.norm(defending_positions - ball_pos, axis=1)

    pressers = distances <= radius

    return {
        'n_pressers': np.sum(pressers),
        'avg_distance': np.mean(distances),
        'min_distance': np.min(distances),
        'pressers_within_5m': np.sum(distances <= 5.0),
        'pressers_within_10m': np.sum(distances <= 10.0),
    }


def calculate_pass_availability(
    passer_position: Tuple[float, float],
    teammate_positions: np.ndarray,
    opponent_positions: np.ndarray,
    max_distance: float = 30.0
) -> pd.DataFrame:
    """
    Calculate passing options with interception risk.

    :param passer_position: Tuple of passer coordinates (x, y).
    :param teammate_positions: Array of teammate positions.
    :param opponent_positions: Array of opponent positions.
    :param max_distance: Maximum pass distance (default: 30.0).
    :return: DataFrame containing pass availability metrics.
    """
    passer_pos = np.array(passer_position)
    results = []

    for i, teammate_pos in enumerate(teammate_positions):
        pass_distance = np.linalg.norm(teammate_pos - passer_pos)

        if pass_distance > max_distance or pass_distance < 1.0:
            continue

        pass_vector = teammate_pos - passer_pos
        pass_length = np.linalg.norm(pass_vector)
        pass_direction = pass_vector / pass_length

        risk_count = 0
        min_opponent_dist = float('inf')

        for opp_pos in opponent_positions:
            to_opp = opp_pos - passer_pos
            projection = np.dot(to_opp, pass_direction)

            if 0 < projection < pass_length:
                perp_dist = np.linalg.norm(to_opp - projection * pass_direction)

                if perp_dist < 5.0:
                    risk_count += 1

                min_opponent_dist = min(min_opponent_dist, perp_dist)

        results.append({
            'teammate_idx': i,
            'distance': pass_distance,
            'risk_count': risk_count,
            'min_opponent_distance': min_opponent_dist,
            'angle': np.degrees(np.arctan2(pass_vector[1], pass_vector[0])),
        })

    return pd.DataFrame(results)


def calculate_high_press_triggers(
    events_df: pd.DataFrame,
    pressure_events: Optional[pd.DataFrame] = None,
    height_threshold: float = 35.0
) -> pd.DataFrame:
    """
    Identify high press trigger events.

    :param events_df: DataFrame containing match events.
    :param pressure_events: Optional DataFrame containing pressure events.
    :param height_threshold: X-coordinate threshold for high press (default: 35.0).
    :return: DataFrame containing high press trigger events.
    """
    if pressure_events is None:
        pressure_events = events_df[
            events_df['event_type'] == 'on_ball_engagement'
        ].copy()

    triggers = pressure_events[pressure_events['start_x'] > height_threshold].copy()
    return triggers


def calculate_ppda(
    defensive_actions: pd.DataFrame,
    opponent_passes: pd.DataFrame,
    attacking_third_x: float = 35.0
) -> float:
    """
    Calculate PPDA (Passes Allowed Per Defensive Action).

    :param defensive_actions: DataFrame containing defensive actions.
    :param opponent_passes: DataFrame containing opponent passes.
    :param attacking_third_x: X-coordinate threshold for attacking third (default: 35.0).
    :return: The PPDA value.
    """
    def_actions_attacking = defensive_actions[
        defensive_actions['start_x'] > attacking_third_x
    ]
    passes_attacking = opponent_passes[
        opponent_passes['start_x'] > attacking_third_x
    ]

    n_defensive_actions = len(def_actions_attacking)
    n_passes = len(passes_attacking)

    if n_defensive_actions == 0:
        return float('inf')

    return n_passes / n_defensive_actions


def calculate_penetration_index(
    team_positions: np.ndarray,
    ball_position: Tuple[float, float],
    opponent_defensive_line: float
) -> float:
    """
    Calculate how penetrative team's position is.

    :param team_positions: Array of player positions for the team.
    :param ball_position: Tuple of ball coordinates (x, y).
    :param opponent_defensive_line: X-coordinate of the opponent's defensive line.
    :return: The penetration index (0 to 1).
    """
    ball_x = ball_position[0]

    players_ahead = np.sum(team_positions[:, 0] > opponent_defensive_line)
    total_players = len(team_positions)

    ball_penetration = max(0, (ball_x - opponent_defensive_line) / 52.5)

    player_penetration = players_ahead / total_players
    penetration_index = 0.6 * ball_penetration + 0.4 * player_penetration

    return np.clip(penetration_index, 0, 1)


def find_player_encounters(
    player1_df: pd.DataFrame,
    player2_df: pd.DataFrame,
    distance_threshold: float = 5.0
) -> pd.DataFrame:
    """
    Find frames where two players are within a certain distance of each other.

    :param player1_df: DataFrame containing tracking data for player 1.
    :param player2_df: DataFrame containing tracking data for player 2.
    :param distance_threshold: Maximum distance to consider an encounter (default: 5.0).
    :return: DataFrame containing encounter frames.
    """
    merged_df = pd.merge(player1_df, player2_df, on='frame', suffixes=('_p1', '_p2'))

    merged_df['distance'] = np.sqrt(
        (merged_df['x_p1'] - merged_df['x_p2'])**2 +
        (merged_df['y_p1'] - merged_df['y_p2'])**2
    )

    encounters_df = merged_df[merged_df['distance'] <= distance_threshold].copy()

    return encounters_df


def calculate_field_tilt(
    tracking_df: pd.DataFrame,
    team_id: int,
    pitch_length: float = 105.0
) -> Dict[str, float]:
    """
    Calculate territory dominance (field tilt) for a team.

    :param tracking_df: DataFrame containing tracking data.
    :param team_id: The ID of the team.
    :param pitch_length: The length of the pitch (default: 105.0).
    :return: Dictionary containing field tilt metrics.
    """
    if tracking_df.empty:
        return {'percentage': 0.0, 'frames_in_opp_half': 0, 'total_frames': 0}
    
    team_data = tracking_df[tracking_df['team_id'] == team_id] if 'team_id' in tracking_df.columns else tracking_df
    
    if team_data.empty:
        return {'percentage': 0.0, 'frames_in_opp_half': 0, 'total_frames': 0}
    
    if 'frame' in team_data.columns and 'x' in team_data.columns:
        centroids = team_data.groupby('frame')['x'].mean()
        
        min_x = team_data['x'].min()
        if min_x < 0:
            midline = 0.0
        else:
            midline = pitch_length / 2.0
            
        frames_in_opp_half = (centroids > midline).sum()
        total_frames = len(centroids)
        
        percentage = (frames_in_opp_half / total_frames * 100) if total_frames > 0 else 0.0
        
        return {
            'percentage': percentage,
            'frames_in_opp_half': int(frames_in_opp_half),
            'total_frames': int(total_frames)
        }
    
    return {'percentage': 0.0, 'frames_in_opp_half': 0, 'total_frames': 0}
