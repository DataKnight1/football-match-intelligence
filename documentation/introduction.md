# System Overview

## Architecture

This is a football match analysis platform built on SkillCorner tracking data. The system processes 10Hz positional data and discrete event metadata to enable tactical analysis, scouting workflows, and performance evaluation.

The platform is designed for analysts, coaches, and researchers requiring programmatic access to match intelligence without proprietary software dependencies.

## Module Organization

The application provides six analytical modules, each addressing distinct analytical requirements:

### Match Overview
Aggregate tactical metrics and spatial visualizations for match-level analysis. Synthesizes event data (passes, shots, possession) with tracking data (player positions) to construct comprehensive tactical summaries.

**Primary outputs:** Scoreboard, pass networks, shot maps, zone control, momentum timelines

### Player Analysis
Multi-dimensional individual performance profiling through four complementary views: tactical positioning (heatmaps, territory polygons), physical output (distance, speed zones), off-ball movement (run classification), and on-ball actions (event timeline).

**Primary outputs:** Phase-filtered heatmaps, speed zone histograms, run type classification, event-synchronized trajectories

### Team Analysis
Collective tactical profiling: spatial organization (convex hull), pressing intensity (field tilt, defensive line metrics), and dangerous sequence identification (possession chains ranked by xG).

**Primary outputs:** Team shape polygons, defensive line box plots, top-10 possession chains, phase-filtered pass networks

### Player Comparison
Head-to-head tactical analysis through complementary lenses: percentile rankings (pizza chart), split-state metrics (in/out of possession), physical benchmarking (scatter plots), and spatial profiling (clash zones, space dominance, threat maps).

**Primary outputs:** 12-metric pizza chart, detailed comparison tables, spatial overlap heatmaps

### Game Flow
Temporal match analysis visualizing dynamics through three complementary metrics: cumulative expected goals (chance accumulation), momentum evolution (weighted moving average), and possession distribution (sequence fragmentation).

**Primary outputs:** Cumulative xG step functions, bidirectional momentum bars, possession timeline blocks

### Event Analysis
Frame-level event reconstruction combining 10Hz tracking data with discrete event metadata. Provides temporal playback (animation player) and static tactical analysis (tactical board with computed overlays) for understanding decision-making context.

**Primary outputs:** Plotly-based animation player, passing option visualization, possession indication

## User Interface

**Navigation:** Sidebar provides module selection. Active module indicated by green accent bar.

**Filtering:** Each module includes standardized filter controls (match selection, player/team selection where applicable).

**Layout:** Three-column responsive layout on wide displays (home team left, shared metrics center, away team right).

## Design System

### Color Encoding

Team colors propagate consistently throughout the application to ensure cognitive continuity:

**Color extraction hierarchy:**
1. Metadata-specified team colors (if present in data source)
2. Logo-derived dominant colors (via k-means clustering on team logo RGB values)
3. Default fallback: Home = `#32FF69` (green), Away = `#3385FF` (blue)

**Text rendering:** Dark green text (`#1A5F3B`) on light backgrounds (`#FAFAFA`) for improved readability versus pure black (#000000).

### Layout Standards

- **Responsive design:** Optimized for displays ≥1920px width
- **Grid system:** Three-column layout (30% | 40% | 30%) for team-vs-team comparisons
- **Whitespace:** 24px vertical spacing between sections, 16px horizontal padding
- **Typography:** Inter font family, 16px base size, 1.5 line height

### Consistency Patterns

- Filter dropdowns positioned identically across all modules (top-left)
- Team color mapping maintained across all visualizations
- Phase terminology standardized (In Possession, Out of Possession, Transition)
- Metric units consistently displayed in parentheses

## Core Capabilities

### Tactical Board (Event Analysis Module)

The tactical board extends raw positional data with computed tactical primitives:

**Passing options:** Multi-gate validation system determines available receivers:
- Gate 1: Line-of-sight clearance (no opponent within 1.0m of pass vector)
- Gate 2: Receiver availability (velocity differential >0.5 m/s from nearest marker)

Passing options rendered as enlarged circles (r=1.2m) with directional arrows. Home team options in green, away team in blue.

**Coordinate alignment:** Automatic detection of attack direction via defensive line centroid analysis. Applies reflection transformation when necessary to maintain consistent orientation.

**Possession indication:** Dual-marker system (dashed circle overlay + filled center dot) ensures possession identification in dense player clusters.

### Phase-Based Analysis

Multiple modules support phase filtering to reveal tactical role differentiation:

**Phase definitions:**
- **In Possession:** Team controls ball (based on possession state machine from event data)
- **Out of Possession:** Opponent controls ball
- **Transition:** Ball control change events

**Applications:**
- Player heatmaps filtered by phase reveal positional adaptability
- Team shape comparison (attacking vs. defending configurations)
- Pass network evolution across build-up, progression, and final third phases

### Pizza Charts (Player Comparison Module)

Percentile-ranked performance visualization using mplsoccer.PyPizza library:

**Baseline dataset:** 450 midfielders/forwards from 2024/2025 competition season
**Normalization:** All metrics normalized per 90 minutes to account for substitution variance
**Rendering:** Polar coordinate projection with overlapping polygons for visual comparison

**Interpretation:** Polygon area indicates overall performance; shape irregularity reveals specialization vs. well-rounded profiles.

### Interactive Visualizations

All visualizations support user interaction:

**Event timelines:** Click events to view synchronized tracking data context
**Frame scrubbing:** Drag slider to navigate animation frames
**Phase filtering:** Toggle buttons to switch between In/Out of Possession views
**Playback controls:** Speed multiplier ([0.5×, 1×, 1.5×, 2×]) for animation player

## Data Processing Architecture

### Data Sources

**Tracking data:** SkillCorner 10Hz positional data (JSONL format)
**Event data:** SkillCorner discrete events (SPADL format)
**Phases of play:** Tactical phase classifications (CSV format)

### Processing Pipeline

1. **Ingestion:** Kloppy library parses SkillCorner formats
2. **Coordinate normalization:** Detect and scale to 105m × 68m standard pitch
3. **Smoothing:** Gap-aware Savitzky-Golay filter (window=11, poly=2) for velocity derivation
4. **Synchronization:** Nearest-neighbor timestamp matching (±0.2s tolerance) merges tracking and events
5. **Phase tagging:** State machine classifies possession state frame-by-frame
6. **Caching:** @st.cache_data decorators prevent redundant computation across page switches

### Performance Optimizations

**Data volume:** 22 players × 10 fps × 90 minutes ≈ 200,000 position updates per match

**Optimization strategies:**
- Detection filtering: Remove frames where >5% of players are extrapolated rather than detected
- Downsampling: 5Hz for team shape calculations (negligible accuracy loss, 50% reduction in computation)
- Vectorized operations: NumPy array operations replace iterative Python loops
- Lazy evaluation: Data loading triggered only when module accessed

**Cache hierarchy:**
1. Match metadata (永久 cache, shared across modules)
2. Tracking data (session cache, ~50MB per match)
3. Derived metrics (module-specific cache, computed on-demand)

## Technical Implementation

### Libraries

**Core data processing:**
- Kloppy: SkillCorner data parsing
- Pandas: DataFrame operations and time series
- NumPy: Numerical computations (velocity, convex hull)
- SciPy: Scientific computing (Savitzky-Golay filters, KDE)

**Visualization:**
- mplsoccer: Soccer-specific visualizations (pitch overlays, pass networks, pizza charts)
- Plotly: Interactive time series and animations
- Matplotlib: Static figure generation

**Application framework:**
- Streamlit: Web application framework with reactive state management

### Coordinate System Handling

SkillCorner uses center-origin coordinate system (0,0 at pitch center) with orientation that may invert between halves. The system automatically detects and normalizes:

1. **Scale detection:** If P99(X) < 1.2, assume normalized coordinates and scale to 105m × 68m
2. **Origin translation:** Convert center-origin to corner-origin if required by visualization
3. **Attack direction:** Compute defensive line centroid to determine attacking direction
4. **Reflection:** Apply coordinate transformation if attack direction contradicts event data orientation

This normalization achieves ~95% accuracy on standard scenarios. Edge cases (set pieces with clustered players) may require manual verification.

## Getting Started

### Recommended Workflow

For users new to the platform:

1. **Match Overview** → Obtain scoreline and aggregate statistics
2. **Pass networks** → Identify team structural patterns
3. **Game Flow** → Locate temporal inflection points (momentum shifts, xG accumulation)
4. **Player Analysis** → Drill into individual contributions
5. **Event Analysis** → Frame-by-frame inspection of key moments

### Documentation

Detailed module documentation available:
- [match_overview.md](match_overview.md) - High-level match intelligence
- [player_analysis.md](player_analysis.md) - Individual performance profiling
- [team_analysis.md](team_analysis.md) - Collective tactical profiling
- [player_comparison.md](player_comparison.md) - Head-to-head analysis
- [game_flow.md](game_flow.md) - Temporal match analysis
- [event_analysis.md](event_analysis.md) - Frame-level reconstruction
- [data.md](data.md) - Complete data dictionary
- [setup.md](setup.md) - Installation and configuration

## Limitations and Known Issues

### Data Quality Dependencies

**Tracking data accuracy:** ~97% player identity accuracy (SkillCorner specification). Remaining 3% are extrapolated positions during camera occlusion.

**Detection filtering:** Frames with <95% detection rate are excluded from velocity calculations to prevent ghost accelerations from extrapolation artifacts.

**Ball tracking:** Degrades during aerial phases (>2m height), affecting ~3-5% of frames.

### Computational Constraints

**Frame processing:** Full 90-minute match at 10Hz requires processing ~200,000 position updates. Initial load may take 10-15 seconds on standard hardware.

**Animation rendering:** Plotly frame-based animations limited to ~1000 frames (100 seconds at 10fps) to prevent browser memory exhaustion.

**Spatial resolution:** KDE heatmaps evaluate on 105×68 grid (1m resolution = 7,140 cells). Higher resolution provides marginal visual improvement at 4× computational cost.

### Browser Compatibility

Tested on Chrome 120+, Firefox 121+, Edge 120+. Safari may exhibit rendering artifacts with Plotly animations due to WebGL implementation differences.

## Support and Troubleshooting

For installation issues, consult [setup.md](setup.md).

For data format questions, refer to [data.md](data.md).

For algorithm implementation details, see individual module documentation files (listed above).
