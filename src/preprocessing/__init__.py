"""
Author: Tiago Monteiro
Date: 21-12-2025
Initialization info for preprocessing module.
"""

from .data import (
    extract_player_data, 
    extract_team_data, 
    merge_tracking_with_events,
    calculate_match_minute,
    convert_tracking_wide_to_long
)

from .filters import (
    filter_detected_positions, 
    interpolate_missing_positions, 
    normalize_to_attacking_direction, 
    resample_trajectory
)

from .time import (
    calculate_match_clock
)

from .segmentation import (
    create_time_windows, 
    aggregate_by_phase, 
    build_event_sequences
)

from .features import (
    calculate_distance_metrics, 
    calculate_proximity_stats, 
    calculate_split_physical_stats, 
    calculate_tactical_events
)
