# Data Dictionary

Complete reference for SkillCorner tracking and event data.

---

## 🎯 Tracking Data

### Frame-Level Data

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `frame` | int | Frame number (10 fps) | 100 |
| `timestamp` | string | Match time (MM:SS.decimal) | "01:23.5" |
| `period` | int | Match period (1 or 2) | 1 |
| `possession` | dict | Possession information | `{"player_id": 123, "group": "home"}` |
| `ball_data` | dict | Ball position and status | `{"x": 10.5, "y": -5.2, "z": 0.1}` |
| `player_data` | list | List of player positions | See below |
| `image_corners_projection` | list | Detected field area polygon | Coordinates |

### Player Data (within player_data list)

| Field | Type | Description | Units |
|-------|------|-------------|-------|
| `player_id` | int | Unique player identifier | - |
| `x` | float | X coordinate | meters |
| `y` | float | Y coordinate | meters |
| `is_detected` | bool | True if detected, False if extrapolated | - |

### Ball Data

| Field | Type | Description | Units |
|-------|------|-------------|-------|
| `x` | float | X coordinate | meters |
| `y` | float | Y coordinate | meters |
| `z` | float | Height above ground | meters |
| `is_detected` | bool | Detection status | - |

### Coordinate System

**Origin**: Center of pitch (0, 0)
- **X-axis**: Along length of pitch (-52.5 to +52.5 for 105m pitch)
- **Y-axis**: Along width of pitch (-34 to +34 for 68m pitch)
- **Units**: Meters

**Standard Pitch Dimensions**:
- Length: 105 meters
- Width: 68 meters

---

## 📋 Match Metadata

### Match Information

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique match identifier |
| `date_time` | string | Match date/time (ISO 8601) |
| `home_team_score` | int | Home team goals |
| `away_team_score` | int | Away team goals |
| `status` | string | Match status ("closed", "not_started") |
| `pitch_length` | float | Pitch length in meters |
| `pitch_width` | float | Pitch width in meters |
| `home_team_side` | list | Attack directions by period |

### Team Information

| Field | Type | Description |
|-------|------|-------------|
| `team.id` | int | Unique team identifier |
| `team.name` | string | Full team name |
| `team.short_name` | string | Abbreviated name |
| `team.acronym` | string | Three-letter code |

### Player Information

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique player identifier |
| `first_name` | string | Player first name |
| `last_name` | string | Player last name |
| `short_name` | string | Display name |
| `birthday` | string | Date of birth (YYYY-MM-DD) |
| `number` | int | Jersey number |
| `trackable_object` | int | Tracking system identifier |
| `team_id` | int | Associated team ID |

### Playing Time

| Field | Type | Description | Units |
|-------|------|-------------|-------|
| `start_time` | string | Time entered match | "HH:MM:SS" |
| `end_time` | string | Time left match | "HH:MM:SS" |
| `minutes_played` | float | Total minutes played | minutes |
| `minutes_tip` | float | Minutes team in possession | minutes |
| `minutes_otip` | float | Minutes team out of possession | minutes |

### Player Role

| Field | Type | Description |
|-------|------|-------------|
| `player_role.id` | int | Role identifier |
| `player_role.name` | string | Full position name |
| `player_role.acronym` | string | Position abbreviation |
| `player_role.position_group` | string | General position category |

**Position Categories**:
- `Other`: Goalkeeper, Substitute
- `Central Defender`: Center Back, Left/Right Center Back
- `Full Back`: Left/Right Back, Left/Right Wing Back
- `Midfield`: Defensive/Attacking/Left/Right Midfield
- `Wide Attacker`: Left/Right Winger, Left/Right Forward
- `Center Forward`: Striker, Center Forward

### Match Cards

| Field | Type | Description |
|-------|------|-------------|
| `yellow_card` | int | Number of yellow cards (0 or 1) |
| `red_card` | int | Number of red cards (0 or 1) |
| `injured` | bool | Injury flag |
| `goal` | int | Number of goals scored |
| `own_goal` | int | Number of own goals |

### Match Periods

| Field | Type | Description | Units |
|-------|------|-------------|-------|
| `period` | int | Period number (1, 2) | - |
| `start_frame` | int | Starting frame number | frames |
| `end_frame` | int | Ending frame number | frames |
| `duration_frames` | int | Total frames in period | frames |
| `duration_minutes` | float | Period duration | minutes |

---

## 🎬 Dynamic Events

### Event Types

1. **Off-Ball Runs** (`event_type = "off_ball_run"`)
2. **Line-Breaking Passes** (`event_type = "line_breaking_pass"`)
3. **On-Ball Engagements** (`event_type = "on_ball_engagement"`)
4. **Player Possession** (`event_type = "player_possession"`)

### Common Fields

| Field | Type | Description | Units |
|-------|------|-------------|-------|
| `event_id` | int | Unique event identifier (per match) | - |
| `match_id` | int | Match identifier | - |
| `event_type` | string | Type of event | - |
| `start_frame` | int | Event start frame | frames |
| `end_frame` | int | Event end frame | frames |
| `duration` | float | Event duration | seconds |
| `period` | int | Match period | - |
| `team_id` | int | Team performing action | - |
| `player_id` | int | Player performing action | - |

### Spatial Fields

| Field | Type | Description | Units |
|-------|------|-------------|-------|
| `start_x` | float | Starting X coordinate | meters |
| `start_y` | float | Starting Y coordinate | meters |
| `end_x` | float | Ending X coordinate | meters |
| `end_y` | float | Ending Y coordinate | meters |
| `distance_covered` | float | Total distance | meters |

**Note**: Coordinates are NOT scaled to standard pitch size and require adjustment.

### Phase Information

| Field | Type | Description |
|-------|------|-------------|
| `team_in_possession_phase_type` | string | Phase of possession team |
| `team_out_of_possession_phase_type` | string | Phase of defending team |

**Phase Types**:
- `build_up`: Building from back
- `progress`: Progressing through midfield
- `create`: Creating chances
- `finish`: Final third actions
- `set_piece`: Set piece situations

### Off-Ball Run Specific

| Field | Type | Description |
|-------|------|-------------|
| `run_type` | string | Type of run (e.g., "in_behind", "lateral") |
| `is_targeted` | bool | Run was targeted by pass |
| `is_received` | bool | Run received the ball |
| `average_speed` | float | Average speed during run (km/h) |
| `max_speed` | float | Maximum speed during run (km/h) |

### Line-Breaking Pass Specific

| Field | Type | Description |
|-------|------|-------------|
| `player_in_possession_id` | int | Passer player ID |
| `receiver_player_id` | int | Receiver player ID |
| `pass_outcome` | string | "successful" or "unsuccessful" |
| `opponents_between` | int | Number of opponents bypassed |
| `xpass_completion` | float | Expected pass completion (0-100) |

### On-Ball Engagement Specific

| Field | Type | Description |
|-------|------|-------------|
| `engagement_type` | string | Type (e.g., "tackle", "pressure") |
| `engagement_outcome` | string | "successful" or "unsuccessful" |
| `defending_player_id` | int | Defending player ID |
| `separation_start` | float | Distance at engagement start (m) |
| `separation_end` | float | Distance at engagement end (m) |

**Full Documentation**: [Dynamic Events CSV Specifications](https://26560301.fs1.hubspotusercontent-eu1.net/hubfs/26560301/Guides/Dynamic%20Events/20250216%20-%20Dynamic%20Events%20CSV%20Specifications.pdf)

---

## 🔄 Phases of Play

### Phase Information

| Field | Type | Description |
|-------|------|-------------|
| `match_id` | int | Match identifier |
| `period` | int | Match period (1, 2) |
| `start_frame` | int | Phase start frame |
| `end_frame` | int | Phase end frame |
| `possession_team_id` | int | Team with possession |
| `possession_phase` | string | Attacking phase |
| `non_possession_phase` | string | Defending phase |

### Phase Types

**In Possession (Attacking)**:
- `build_up`: Building play from defensive third
- `progress`: Progressing through midfield
- `create`: Creating scoring opportunities
- `finish`: Final actions toward goal
- `set_piece`: Set piece situations

**Out of Possession (Defending)**:
- `high_press`: Pressing in attacking third
- `mid_press`: Pressing in middle third
- `low_block`: Defending in defensive third
- `transition`: Transitional defending
- `set_piece_defend`: Defending set pieces

**Key Points**:
- Phases only defined when ball is in play
- Each in-possession phase has corresponding out-of-possession phase
- Phases are mutually exclusive (one phase at a time)

**Full Documentation**: [Phases of Play CSV Specifications](https://26560301.fs1.hubspotusercontent-eu1.net/hubfs/26560301/Guides/Phases%20of%20Play/20250216%20-%20Phases%20of%20Play%20CSV%20Specifications.pdf)

---

## 📊 Physical Aggregates (Season-Level)

### Player Physical Metrics

| Metric | Description | Units |
|--------|-------------|-------|
| `total_distance` | Total distance covered | km |
| `sprint_distance` | Distance at sprint speed (>25 km/h) | km |
| `hsr_distance` | High-speed running distance (>20 km/h) | km |
| `accelerations` | Number of accelerations (>3 m/s²) | count |
| `decelerations` | Number of decelerations (<-3 m/s²) | count |
| `sprint_count` | Number of sprints | count |
| `hsr_count` | Number of HSR efforts | count |
| `max_speed` | Maximum speed reached | km/h |
| `avg_speed` | Average speed | km/h |

### Contextual Splits

All metrics available by:
- **Phase**: build_up, progress, create, finish
- **Possession**: In possession (IP) vs out of possession (OOP)
- **Match Context**: Minutes played, starting vs substitute

**Filters Applied**:
- Only performances with >60 minutes played
- Season-level aggregation (not match-level)
- Midfielders only in the open data sample

**Full Documentation**: [Physical Data Glossary](https://skillcorner.crunch.help/en/glossaries/physical-data-glossary)

---

## 🔢 Data Limitations & Considerations

### Tracking Data
- **Accuracy**: ~97% player identity accuracy
- **Extrapolation**: Some positions are extrapolated when player not visible
- **Smoothing**: Raw speed/acceleration may need smoothing
- **Frame Rate**: 10 fps (can be downsampled via `sample_rate`)

### Dynamic Events
- **Match-Specific**: `event_id` is unique only within each match
- **Coordinates**: Not scaled to standard pitch size
- **Coverage**: Not all actions are captured (focus on key events)

### Phases of Play
- **Ball In Play**: Phases only defined during active play
- **Transitions**: Brief gaps during ball out of play
- **Overlaps**: Phases are non-overlapping

### Physical Aggregates
- **Minimum Playtime**: 60+ minutes only
- **Position Filter**: Sample data is midfielders only
- **Aggregation Level**: Season-level, not match-level

---

## 📐 Derived Metrics Examples

### Speed Classification

```python
# Speed thresholds (km/h)
WALKING = 0 - 11
JOGGING = 11 - 14
RUNNING = 14 - 20
HSR = 20 - 25  # High-Speed Running
SPRINT = > 25
```

### Distance Calculations

```python
import numpy as np

def calculate_distance(x1, y1, x2, y2):
    """Euclidean distance in meters"""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def calculate_velocity(x, y, fps=10.0):
    """Velocity in m/s"""
    dx = np.diff(x)
    dy = np.diff(y)
    dt = 1.0 / fps
    return np.sqrt(dx**2 + dy**2) / dt
```

### Spatial Zones

```python
# Pitch zones (assuming 105m x 68m)
DEFENSIVE_THIRD = x < -35
MIDDLE_THIRD = -35 <= x <= 35
ATTACKING_THIRD = x > 35

LEFT_CHANNEL = y < -22.67
CENTER_CHANNEL = -22.67 <= y <= 22.67
RIGHT_CHANNEL = y > 22.67
```

---

## 🔗 External Resources

- **SkillCorner Documentation**: [docs.skillcorner.com](https://docs.skillcorner.com)
- **Kloppy Documentation**: [kloppy.pysport.org](https://kloppy.pysport.org)
- **Dynamic Events PDF**: [Specifications](https://26560301.fs1.hubspotusercontent-eu1.net/hubfs/26560301/Guides/Dynamic%20Events/20250216%20-%20Dynamic%20Events%20CSV%20Specifications.pdf)
- **Phases of Play PDF**: [Specifications](https://26560301.fs1.hubspotusercontent-eu1.net/hubfs/26560301/Guides/Phases%20of%20Play/20250216%20-%20Phases%20of%20Play%20CSV%20Specifications.pdf)
- **Physical Metrics**: [Glossary](https://skillcorner.crunch.help/en/glossaries/physical-data-glossary)

---

**Last Updated**: Competition 2024/2025
