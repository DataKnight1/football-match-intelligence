"""
Author: Tiago Monteiro
Date: 21-12-2025
Schema definitions for data validation and type hinting.
Uses Pydantic for metadata and lightweight TypedDict/Dataclasses for high-frequency tracking frames.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel
from dataclasses import dataclass



class PlayerMetadata(BaseModel):
    player_id: int
    name: str = "Unknown"
    jersey_no: int = 99
    position: Optional[str] = None
    detailed_position: Optional[str] = None
    team_id: int

class TeamMetadata(BaseModel):
    team_id: int
    name: str
    players: List[PlayerMetadata] = []

class MatchMetadata(BaseModel):
    match_id: int
    home_team: TeamMetadata
    away_team: TeamMetadata
    pitch_length: float = 105.0
    pitch_width: float = 68.0





@dataclass(slots=True)
class BallData:
    x: float
    y: float
    z: float = 0.0
    is_detected: bool = False

@dataclass(slots=True)
class PlayerTrackingData:
    player_id: int
    x: float
    y: float
    speed: Optional[float] = None
    direction: Optional[float] = None
    
@dataclass(slots=True)
class FrameData:
    frame_id: int
    timestamp: float
    period: int
    ball: Optional[BallData]
    players: List[PlayerTrackingData]
    possession_team_id: Optional[int] = None
    in_possession: bool = False
