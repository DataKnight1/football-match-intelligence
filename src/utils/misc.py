"""
Author: Tiago Monteiro
Date: 21-12-2025
Miscellaneous utility functions for football analytics.
"""

from typing import Optional
from pathlib import Path
from collections import Counter
import base64
import re
import pandas as pd


def time_to_seconds(time_str: str) -> float:
    """
    Convert time string (HH:MM:SS) to seconds.

    :param time_str: Time string.
    :return: Time in seconds.
    """
    if time_str is None:
        return 0.0

    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = map(float, parts)
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m, s = map(float, parts)
        return m * 60 + s
    else:
        return float(parts[0])


def seconds_to_time(seconds: float) -> str:
    """
    Convert seconds to time string (MM:SS).

    :param seconds: Time in seconds.
    :return: Time string.
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def safe_float(value):
    """
    Convert raw value to float when possible, otherwise return None.
    
    :param value: The value to convert.
    :return: Float value or None.
    """
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def truthy(value):
    """
    Determine whether a value from the CSV should be considered True.
    
    :param value: The value to check.
    :return: Boolean result.
    """
    if value is None or pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "success", "successful"}
    return bool(value)


def pick_first(series: pd.Series, *keys):
    """
    Return the first non-null value for the provided keys from a Series.
    
    :param series: The pandas Series.
    :param keys: Keys to check.
    :return: First non-null value or None.
    """
    for key in keys:
        if key in series and not pd.isna(series[key]):
            return series[key]
    return None


def format_event_description(event: pd.Series) -> str:
    """
    Build a human-readable description for an event row shown in the viewer.

    :param event: The event row.
    :return: Event description string.
    """
    event_type_raw = event.get("event_type")
    event_type = str(event_type_raw).lower() if pd.notna(event_type_raw) else ""

    player_name = event.get("player_name")
    if not player_name or pd.isna(player_name):
        player_name = event.get("player_in_possession_name")
    if not player_name or pd.isna(player_name):
        player_id = event.get("player_id")
        player_name = f"Player {player_id}" if pd.notna(player_id) else "Unknown player"
    player_name = str(player_name).strip()

    team = event.get("team_shortname")
    if not team or pd.isna(team):
        team = ""
    identity = f"{player_name} ({team})" if team else player_name

    if event_type == "player_possession":
        end_type_raw = event.get("end_type")
        end_type = str(end_type_raw).lower() if pd.notna(end_type_raw) else ""
        if end_type == "pass":
            target = event.get("player_targeted_name")
            if not target or pd.isna(target):
                target = event.get("player_targeted_id")
            target_text = f" to {target}" if target and not pd.isna(target) else ""
            qualifiers = []
            outcome = event.get("pass_outcome")
            if outcome and not pd.isna(outcome):
                qualifiers.append(str(outcome))
            if truthy(event.get("lead_to_goal")):
                qualifiers.append("leads to goal")
            elif truthy(event.get("lead_to_shot")):
                qualifiers.append("leads to shot")
            qualifier_text = f" ({', '.join(qualifiers)})" if qualifiers else ""
            return f"{identity} plays a pass{target_text}{qualifier_text}"
        if end_type == "shot":
            return f"{identity} scores" if truthy(event.get("lead_to_goal")) else f"{identity} takes a shot"
        if end_type == "clearance":
            return f"{identity} clears the ball"
        if end_type == "foul_suffered":
            return f"{identity} wins a foul"
        if end_type == "possession_loss":
            return f"{identity} loses possession"
        if end_type:
            return f"{identity} ends possession via {end_type}"
        return f"{identity} retains possession"

    if event_type == "passing_option":
        carrier = event.get("player_in_possession_name")
        if not carrier or pd.isna(carrier):
            carrier = event.get("player_in_possession_id")
        carrier_text = str(carrier).strip() if carrier and not pd.isna(carrier) else "the ball carrier"
        qualifiers = []
        if truthy(event.get("dangerous")):
            qualifiers.append("dangerous")
        if truthy(event.get("difficult_pass_target")):
            qualifiers.append("difficult")
        if truthy(event.get("targeted")):
            qualifiers.append("targeted")
        if truthy(event.get("received")):
            qualifiers.append("received")
        qualifier_text = f" ({', '.join(qualifiers)})" if qualifiers else ""
        return f"{identity} is a passing option for {carrier_text}{qualifier_text}"

    if event_type == "on_ball_engagement":
        engagement = event.get("event_subtype")
        engagement_text = str(engagement).replace("_", " ") if engagement and not pd.isna(engagement) else "engagement"
        opponent = event.get("player_in_possession_name")
        target_text = f" on {opponent}" if opponent and not pd.isna(opponent) else ""
        extras = []
        if truthy(event.get("beaten_by_possession")):
            extras.append("beaten on possession")
        if truthy(event.get("force_backward")):
            extras.append("forces play backward")
        if truthy(event.get("reduce_possession_danger")):
            extras.append("reduces danger")
        extras_text = f" ({', '.join(extras)})" if extras else ""
        return f"{identity} applies {engagement_text}{target_text}{extras_text}"

    if event_type == "off_ball_run":
        run_type = event.get("run_type")
        run_text = str(run_type).replace("_", " ") if run_type and not pd.isna(run_type) else "off-ball run"
        qualifiers = []
        if truthy(event.get("is_targeted")):
            qualifiers.append("targeted")
        if truthy(event.get("is_received")):
            qualifiers.append("received")
        qualifier_text = f" ({', '.join(qualifiers)})" if qualifiers else ""
        return f"{identity} makes a {run_text}{qualifier_text}"

    if event_type:
        return f"{identity} action ({event.get('event_type')})"

    return identity


def find_frame_by_id(dataset, target_frame_id):
    """
    Return frame matching target_frame_id or closest available frame.

    :param dataset: The tracking dataset.
    :param target_frame_id: Target frame ID.
    :return: Tuple of (Frame or None, difference).
    """
    closest_frame = None
    closest_diff = None

    for frame in dataset.frames:
        diff = abs(frame.frame_id - target_frame_id)
        if diff == 0:
            return frame, 0
        if closest_diff is None or diff < closest_diff:
            closest_frame = frame
            closest_diff = diff

    return closest_frame, closest_diff


TEAM_NAME_MAP = {
    "CC Mariners": "CC Mariners",
    "Central Coast Mariners Football Club": "CC Mariners",
    "Melb City": "Melbourne City FC",
    "Melbourne City FC": "Melbourne City",
    "Sydney Football Club": "Sydney FC",
    "Adelaide United Football Club": "Adelaide United FC",
    "Wellington P": "Wellington Phoenix FC",
}

def get_team_logo_file(team_name: str, assets_dir: str = "assets/club_logos") -> Optional[Path]:
    """
    Find the SVG logo file for a team.

    :param team_name: Name of the team.
    :param assets_dir: Directory containing assets (default: "assets/club_logos").
    :return: Path to the logo file or None.
    """
    try:
        base_path = Path.cwd()
        logo_dir = base_path / assets_dir
        
        if not logo_dir.exists():
            logo_dir = Path(__file__).parent.parent.parent / assets_dir
            
        if not logo_dir.exists():
            return None

        cleaned_team_name = team_name.strip()
        if cleaned_team_name in TEAM_NAME_MAP:
            target_name = TEAM_NAME_MAP[cleaned_team_name]
        else:
            target_name = cleaned_team_name.replace(" FC", "")
        
        search_term = target_name.lower()
        
        for file_path in logo_dir.glob("*.png"):
            if search_term in file_path.stem.lower():
                return file_path
                
        for file_path in logo_dir.glob("*.svg"):
            if search_term in file_path.stem.lower():
                return file_path
                
        return None
    except Exception:
        return None


TEAM_COLOR_MAP = {
    "Melbourne City FC": "#6CAEE0",
    "Melb City": "#6CAEE0",
    "CC Mariners": "#FFC425",
    "Central Coast Mariners Football Club": "#FFC425",
    "Wellington Phoenix FC": "#FFD700",
    "Wellington P": "#FFD700",
    "Sydney FC": "#87CEEB",
    "Sydney Football Club": "#87CEEB",
    "Adelaide United FC": "#E00000",
    "Adelaide United Football Club": "#E00000",
}

def get_team_color(team_name: str, assets_dir: str = "assets/club_logos", default_color: str = "#808080") -> str:
    """
    Extract the dominant color from a team's SVG logo.

    :param team_name: Name of the team.
    :param assets_dir: Directory containing assets.
    :param default_color: Default color if extraction fails.
    :return: Hex color string.
    """
    if team_name in TEAM_COLOR_MAP:
        return TEAM_COLOR_MAP[team_name]
    if team_name and team_name.strip() in TEAM_NAME_MAP:
         mapped_name = TEAM_NAME_MAP[team_name.strip()]
         if mapped_name in TEAM_COLOR_MAP:
             return TEAM_COLOR_MAP[mapped_name]

    try:
        match_file = get_team_logo_file(team_name, assets_dir)
        
        if not match_file:
            return default_color
            
        with open(match_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        hex_colors = re.findall(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})', content)
        
        if not hex_colors:
            return default_color
            
        normalized_colors = []
        for c in hex_colors:
            if len(c) == 3:
                normalized_colors.append(f"#{c[0]}{c[0]}{c[1]}{c[1]}{c[2]}{c[2]}".upper())
            else:
                normalized_colors.append(f"#{c}".upper())
                
        ignored_colors = {'#FFFFFF', '#000000', '#F0F0F0', '#E0E0E0', '#1A1A1A', '#333333'}
        filtered_colors = [c for c in normalized_colors if c not in ignored_colors]
        
        if not filtered_colors:
            if normalized_colors:
                 return Counter(normalized_colors).most_common(1)[0][0]
            return default_color
            
        return Counter(filtered_colors).most_common(1)[0][0]
        
    except Exception:
        return default_color


def get_team_logo_base64(team_name: str, assets_dir: str = "assets/club_logos") -> Optional[str]:
    """
    Get the base64 encoded string of the team's SVG logo.

    :param team_name: Name of the team.
    :param assets_dir: Directory containing assets.
    :return: Base64 encoded string or None.
    """
    try:
        match_file = get_team_logo_file(team_name, assets_dir)
        
        if not match_file:
            return None
            
        with open(match_file, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
            
        return f"data:image/svg+xml;base64,{encoded}"
        
    except Exception:
        return None
