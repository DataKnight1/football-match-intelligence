"""
Author: Tiago Monteiro
Date: 21-12-2025
Configuration parameters and constants for the SkillCorner Analytics application.
Includes explicit semantic versioning/commit pinning and direction modes.
"""

from pathlib import Path

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
HALF_PITCH_LENGTH = PITCH_LENGTH / 2.0
HALF_PITCH_WIDTH = PITCH_WIDTH / 2.0

DATA_VERSION = "master" 

GITHUB_BASE_URL = f"https://raw.githubusercontent.com/SkillCorner/opendata/{DATA_VERSION}/data/matches"
MEDIA_BASE_URL = f"https://media.githubusercontent.com/media/SkillCorner/opendata/{DATA_VERSION}/data/matches"

TRACKING_DATA_URL_TEMPLATE = f"{MEDIA_BASE_URL}/{{match_id}}/{{match_id}}_tracking_extrapolated.jsonl"
MATCH_META_URL_TEMPLATE = f"{GITHUB_BASE_URL}/{{match_id}}/{{match_id}}_match.json"
DYNAMIC_EVENTS_URL_TEMPLATE = f"{GITHUB_BASE_URL}/{{match_id}}/{{match_id}}_dynamic_events.csv"
PHASES_URL_TEMPLATE = f"{GITHUB_BASE_URL}/{{match_id}}/{{match_id}}_phases_of_play.csv"

ATTACKING_DIRECTION_MODE = "home_ltr"

SMOOTHING_WINDOW_SIZE = 7 
SMOOTHING_POLY_ORDER = 2
MAX_VELOCITY_KMH = 42.0  
VELOCITY_ANOMALY_THRESHOLD = 45.0  

LOCAL_DATA_DIR = Path(__file__).parent.parent / "opendata-master" / "data" / "matches"
USE_LOCAL_DATA_FIRST = True  

TEAM_COLORS = {
    "Home": "#32FF69",
    "Away": "#3385FF"
}
