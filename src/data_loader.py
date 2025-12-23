"""
Author: Tiago Monteiro
Date: 21-12-2025
Data loading utilities for SkillCorner tracking data.
Implements robust remote loading, caching, and coordinate normalization.
"""

from typing import Optional, Dict, Any, Union
import pandas as pd
import streamlit as st
from kloppy import skillcorner
import logging

from .config import (
    TRACKING_DATA_URL_TEMPLATE,
    MATCH_META_URL_TEMPLATE,
    DYNAMIC_EVENTS_URL_TEMPLATE,
    PHASES_URL_TEMPLATE,
    DATA_VERSION,
    LOCAL_DATA_DIR,
    USE_LOCAL_DATA_FIRST
)
from .utils.coordinates import infer_and_scale_coordinates
from .schema import MatchMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource(show_spinner=False, ttl="4h")
def load_match_data(
    match_id: int,
    sample_rate: float = 1.0,
    limit: Optional[int] = None,
    coordinates: str = "skillcorner",
    to_orientation: str = "STATIC_HOME_AWAY",
    _version: str = DATA_VERSION 
) -> Any:
    """
    Load tracking data for a specific match using Kloppy.
    Using Streamlit cache to prevent re-downloading.

    :param match_id: Match identifier.
    :param sample_rate: 1.0 = 10fps (default), 0.5 = 5fps.
    :param limit: Optional limit on number of frames.
    :param coordinates: Coordinate system to use.
    :param to_orientation: Orientation transformation key.
    :param _version: Cache invalidation key.
    :return: Kloppy Dataset object.
    """
    if USE_LOCAL_DATA_FIRST and LOCAL_DATA_DIR.exists():
        local_tracking = LOCAL_DATA_DIR / str(match_id) / f"{match_id}_tracking_extrapolated.jsonl"
        local_meta = LOCAL_DATA_DIR / str(match_id) / f"{match_id}_match.json"

        if local_tracking.exists() and local_meta.exists():
            logger.info(f"Loading match {match_id} from LOCAL directory")
            try:
                dataset = skillcorner.load(
                    meta_data=str(local_meta),
                    raw_data=str(local_tracking),
                    coordinates=coordinates,
                    sample_rate=sample_rate,
                    limit=limit,
                )

                if to_orientation:
                    dataset = dataset.transform(to_orientation=to_orientation)

                logger.info(f"Successfully loaded match {match_id} from local files")
                return dataset
            except Exception as e:
                logger.warning(f"Local load failed for match {match_id}, falling back to GitHub: {e}")

    tracking_url = TRACKING_DATA_URL_TEMPLATE.format(match_id=match_id)
    meta_url = MATCH_META_URL_TEMPLATE.format(match_id=match_id)

    logger.info(f"Loading match {match_id} from GitHub: {tracking_url}")

    try:
        dataset = skillcorner.load(
            meta_data=meta_url,
            raw_data=tracking_url,
            coordinates=coordinates,
            sample_rate=sample_rate,
            limit=limit,
        )

        if to_orientation:
            dataset = dataset.transform(to_orientation=to_orientation)

        return dataset
    except Exception as e:
        logger.error(f"Failed to load match {match_id} from GitHub: {e}")
        raise e

@st.cache_data(show_spinner=False)
def load_match_to_df(
    match_id: int,
    sample_rate: float = 1.0,
    limit: Optional[int] = None,
    engine: str = "pandas",
    **kwargs
) -> pd.DataFrame:
    """
    Load tracking data directly as a DataFrame (wrapper around Kloppy).

    :param match_id: Match identifier.
    :param sample_rate: Sample rate for loading.
    :param limit: Optional limit on frames.
    :param engine: DataFrame engine (default: pandas).
    :return: DataFrame containing tracking data.
    """
    dataset = load_match_data(
        match_id=match_id,
        sample_rate=sample_rate,
        limit=limit,
        **kwargs
    )
    return dataset.to_df(engine=engine)

@st.cache_data(show_spinner=False)
def load_dynamic_events(match_id: int) -> pd.DataFrame:
    """
    Load dynamic events data for a specific match.

    :param match_id: Match identifier.
    :return: DataFrame containing dynamic events.
    """
    if USE_LOCAL_DATA_FIRST and LOCAL_DATA_DIR.exists():
        local_events = LOCAL_DATA_DIR / str(match_id) / f"{match_id}_dynamic_events.csv"
        if local_events.exists():
            logger.info(f"Loading dynamic events for {match_id} from LOCAL file")
            try:
                df = pd.read_csv(local_events)
                return _process_events_coordinates(df, match_id)
            except Exception as e:
                logger.warning(f"Local events load failed for {match_id}: {e}")

    url = DYNAMIC_EVENTS_URL_TEMPLATE.format(match_id=match_id)
    logger.info(f"Loading dynamic events from {url}")
    
    try:
        df = pd.read_csv(url)
        return _process_events_coordinates(df, match_id)
    except Exception as e:
        logger.error(f"Failed to load dynamic events for {match_id}: {e}")
        return pd.DataFrame()

def _process_events_coordinates(df: pd.DataFrame, match_id: int) -> pd.DataFrame:
    """
    Helper to process and normalize event coordinates.

    :param df: Input DataFrame with raw coordinates.
    :param match_id: Match identifier for logging.
    :return: DataFrame with normalized coordinates.
    """
    if 'location_x' in df.columns and 'location_y' in df.columns:
        x_vals = df['location_x'].values
        y_vals = df['location_y'].values
        
        scaled_x, scaled_y, detected_sys = infer_and_scale_coordinates(x_vals, y_vals)
        
        if detected_sys != 'skillcorner':
            logger.warning(f"Events for match {match_id} detected as {detected_sys}. Scaled to meters.")
        
        df['x'] = scaled_x
        df['y'] = scaled_y
        
        df['x_raw'] = x_vals
        df['y_raw'] = y_vals
        
    return df

@st.cache_data(show_spinner=False)
def load_phases_of_play(match_id: int) -> pd.DataFrame:
    """
    Load phases of play data for a specific match.

    :param match_id: Match identifier.
    :return: DataFrame containing phases of play.
    """
    if USE_LOCAL_DATA_FIRST and LOCAL_DATA_DIR.exists():
        local_phases = LOCAL_DATA_DIR / str(match_id) / f"{match_id}_phases_of_play.csv"
        if local_phases.exists():
            logger.info(f"Loading phases for {match_id} from LOCAL file")
            try:
                return pd.read_csv(local_phases)
            except Exception as e:
                logger.warning(f"Local phases load failed for {match_id}: {e}")

    url = PHASES_URL_TEMPLATE.format(match_id=match_id)
    try:
        return pd.read_csv(url)
    except Exception as e:
        logger.error(f"Error loading phases for {match_id}: {e}")
        return pd.DataFrame()

def get_available_matches() -> Dict[int, str]:
    """
    Get dictionary of available match IDs and descriptions.

    :return: Dictionary mapping match IDs to descriptions.
    """
    return {
        1886347: "Auckland FC vs Newcastle",
        1899585: "Auckland FC vs Wellington P FC",
        1925299: "Brisbane FC vs Perth Glory",
        1953632: "CC Mariners vs Melbourne City",
        1996435: "Sydney FC vs Adelaide United",
        2006229: "Melbourne City vs Macarthur FC",
        2011166: "Wellington P FC vs Melbourne V FC",
        2013725: "Western United vs Sydney FC",
        2015213: "Western United vs Auckland FC",
        2017461: "Melbourne V FC vs Auckland FC",
    }

def get_match_metadata(dataset: Any, match_id: Optional[int] = None) -> Union[Dict[str, Any], MatchMetadata]:
    """
    Extract useful metadata from a loaded dataset.
    Merged with raw metadata if available.

    :param dataset: Loaded Kloppy dataset.
    :param match_id: Optional match ID to fetch enriched metadata.
    :return: Dictionary containing match metadata.
    """
    home_team, away_team = dataset.metadata.teams

    basic_meta = {
        "match_id": match_id if match_id else 0,
        "home_team_id": home_team.team_id,
        "home_team_name": home_team.name,
        "away_team_id": away_team.team_id,
        "away_team_name": away_team.name,
        "home_players": [
            {
                "player_id": int(p.player_id),
                "name": p.name,
                "jersey_no": p.jersey_no,
                "position": str(p.starting_position) if p.starting_position else None,
                "team_id": int(home_team.team_id)
            }
            for p in home_team.players
        ],
        "away_players": [
            {
                "player_id": int(p.player_id),
                "name": p.name,
                "jersey_no": p.jersey_no,
                "position": str(p.starting_position) if p.starting_position else None,
                "team_id": int(away_team.team_id)
            }
            for p in away_team.players
        ],
        "periods": dataset.metadata.periods,
    }
    
    if match_id:
        raw_meta = fetch_enriched_metadata(match_id)
        if raw_meta:
             basic_meta = merge_metadata(basic_meta, raw_meta)
             
    return basic_meta

@st.cache_data(show_spinner=False)
def fetch_enriched_metadata(match_id: int) -> Dict[str, Any]:
    """
    Fetch metadata from remote source.

    :param match_id: Match identifier.
    :return: Dictionary of metadata.
    """
    import requests
    url = MATCH_META_URL_TEMPLATE.format(match_id=match_id)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Could not fetch raw metadata: {e}")
    return {}

def merge_metadata(basic: Dict, raw: Dict) -> Dict:
    """
    Helper to merge enriched stats into basic metadata.

    :param basic: Basic metadata dictionary.
    :param raw: Raw metadata dictionary from remote.
    :return: Merged metadata dictionary.
    """
    if 'periods' in raw:
        basic['periods_extra'] = raw['periods']
        
    valid_players = raw.get('players', [])
    for p_list in [basic['home_players'], basic['away_players']]:
        for p in p_list:
            match = next((rp for rp in valid_players if rp.get('id') == p['player_id']), None)
            if match:
                p['detailed_position'] = match.get('player_role', {}).get('acronym')
                p['start_time'] = match.get('start_time')
                p['end_time'] = match.get('end_time')
    return basic
