"""
Author: Tiago Monteiro
Date: 21-12-2025
Visualization package for football analytics.
"""

from .pitch import plot_player_positions, plot_player_trajectory
from .heatmaps import plot_heatmap, plot_dual_heatmap, plot_proximity_map, plot_delta_heatmap, plot_advanced_heatmap
from .passing import plot_pass_network, plot_vertical_pass_network, plot_phase_pass_network
from .team import plot_team_convex_hull, plot_defensive_line_box, plot_field_tilt_bar, plot_zone_control, plot_convex_hull
from .physical import plot_speed_zones, plot_speed_distribution
from .match import (
    plot_possession_timeline, 
    plot_momentum_chart, 
    plot_cumulative_xg, 
    plot_shot_map, 
    plot_team_shot_map, 
    render_lineup_html,
    plot_team_metric_over_time,
    extract_frame_data,
    plot_frame_with_events
)
from .events import plot_event_sequence, plot_player_event_sequence
from .radars import (
    plot_athletic_style_pizza_chart, 
    plot_energy_expenditure_pizza, 
    plot_run_types_pizza, 
    plot_comparison_pizza
)
from .pizza import plot_pizza_chart
from .animation import create_animation_frame
