"""Shared utilities for styling, Google Sheets access, and data formatting."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

CONFIG_PATH = Path("config.json")
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Return application configuration from config.json."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def apply_theme_variables(config: dict[str, Any]) -> None:
    """Inject theme variables from config.json."""
    theme = config["theme"]
    variables = [f"--{key.replace('_', '-')}: {value};" for key, value in theme.items()]
    st.markdown(f"<style>:root {{{' '.join(variables)}}}</style>", unsafe_allow_html=True)


def load_css(css_path: Path) -> None:
    """Load custom CSS into the current Streamlit page."""
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def cache_data(ttl: int | None = None) -> Callable:
    """Return a configured Streamlit cache decorator."""
    return st.cache_data(ttl=ttl, show_spinner=False)


def connect_google_sheet(config: dict[str, Any] | None = None) -> gspread.Spreadsheet:
    cfg = config or get_config()
    sheets_cfg = cfg["google_sheets"]

    try:
        # Streamlit Cloud
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=GOOGLE_SCOPES,
        )
    except Exception:
        # Local execution
        credentials_path = Path(sheets_cfg["credentials_file"])

        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Google service account file not found: {credentials_path}"
            )

        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=GOOGLE_SCOPES,
        )

    client = gspread.authorize(credentials)
    return client.open_by_key(sheets_cfg["sheet_id"])


def _load_worksheet_records(worksheet_name: str) -> pd.DataFrame:
    """Load one worksheet from Google Sheets as a DataFrame."""
    config = get_config()
    sheet = connect_google_sheet(config)
    worksheet = sheet.worksheet(worksheet_name)
    return pd.DataFrame(worksheet.get_all_records())


def _copy_if_missing(df: pd.DataFrame, target: str, source: str) -> pd.DataFrame:
    """Copy a source column to a target column if the target column does not exist."""
    if target not in df.columns and source in df.columns:
        df[target] = df[source]
    return df


def _clean_participants(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize participant data for all sports.

    Supports both old `House` column and new `Team` column.
    """
    df = _copy_if_missing(df, "Team", "House")

    expected_columns = ["Participant", "Team", "Sport", "Points", "Matches", "Wins", "Bonus"]
    df = df.reindex(columns=expected_columns)

    text_columns = ["Participant", "Team", "Sport"]
    numeric_columns = ["Points", "Matches", "Wins", "Bonus"]

    for column in text_columns:
        df[column] = df[column].fillna("Unknown").astype(str).str.strip()

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    return df


def _clean_fixtures(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize fixture data.

    Supports both old `House 1/House 2` columns and new `Team 1/Team 2` columns.
    """
    df = _copy_if_missing(df, "Team 1", "House 1")
    df = _copy_if_missing(df, "Team 2", "House 2")

    expected_columns = [
        "Sport",
        "Date",
        "Time",
        "Participant 1",
        "Team 1",
        "Participant 2",
        "Team 2",
        "Match",
        "Venue",
        "Status",
    ]
    df = df.reindex(columns=expected_columns)

    for column in expected_columns:
        df[column] = df[column].fillna("TBD").astype(str).str.strip()

    return df


@cache_data(ttl=get_config()["data"]["refresh_interval_seconds"])
def load_participants() -> pd.DataFrame:
    """Load participant records from the configured worksheet."""
    worksheet_name = get_config()["google_sheets"]["worksheets"]["participants"]
    return _clean_participants(_load_worksheet_records(worksheet_name))


def load_players() -> pd.DataFrame:
    """Backward-compatible alias for older cricket-specific code."""
    return load_participants()


@cache_data(ttl=get_config()["data"]["refresh_interval_seconds"])
def load_fixtures() -> pd.DataFrame:
    """Load fixture records from the configured worksheet."""
    worksheet_name = get_config()["google_sheets"]["worksheets"]["fixtures"]
    return _clean_fixtures(_load_worksheet_records(worksheet_name))


@cache_data(ttl=get_config()["data"]["refresh_interval_seconds"])
def load_leaderboard() -> pd.DataFrame:
    """Load participant leaderboard with merged points across sports."""
    participants = load_participants().copy()

    leaderboard = (
        participants.groupby(["Participant", "Team"], as_index=False)
        .agg(
            Points=("Points", "sum"),
            Matches=("Matches", "sum"),
            Wins=("Wins", "sum"),
            Bonus=("Bonus", "sum"),
            Sports_Played=("Sport", "nunique"),
        )
        .sort_values("Points", ascending=False)
        .reset_index(drop=True)
    )
    leaderboard.insert(0, "Rank", leaderboard.index + 1)
    return leaderboard


def refresh_data() -> None:
    """Clear cached data and update the last refresh timestamp."""
    st.cache_data.clear()
    st.session_state["last_refresh"] = datetime.now().strftime("%d %b %Y, %I:%M %p")


def format_points(points: float | int) -> str:
    """Format points according to configured decimal precision."""
    decimals = int(get_config()["data"].get("points_decimals", 0))
    return f"{float(points):,.{decimals}f}"


def get_status_color(status: str, config: dict[str, Any] | None = None) -> str:
    """Return the configured color for a fixture status."""
    cfg = config or get_config()
    return cfg["data"].get("status_colors", {}).get(status, cfg["theme"]["muted_color"])


def get_team_meta(team_name: str, config: dict[str, Any] | None = None) -> dict[str, str]:
    """Return emoji and colors for a team."""
    cfg = config or get_config()
    for team in cfg["teams"]:
        if team["name"].casefold() == str(team_name).casefold():
            return team
    return {"name": str(team_name), "emoji": "🏳️", "color": cfg["theme"]["muted_color"], "accent": "#ffffff"}


def get_house_meta(house_name: str, config: dict[str, Any] | None = None) -> dict[str, str]:
    """Backward-compatible alias for old house terminology."""
    return get_team_meta(house_name, config)


def get_team_scores(participants: pd.DataFrame) -> pd.DataFrame:
    """Calculate total points by team."""
    if participants.empty:
        return pd.DataFrame(columns=["Team", "Points"])
    return participants.groupby("Team", as_index=False)["Points"].sum().sort_values("Points", ascending=False)


def get_house_scores(participants: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible alias for old house terminology."""
    scores = get_team_scores(participants)
    return scores.rename(columns={"Team": "House"})


def get_sport_icon(sport: str, config: dict[str, Any] | None = None) -> str:
    """Return configured sport icon."""
    cfg = config or get_config()
    return cfg.get("sports_rules", {}).get(str(sport), {}).get("icon", "🏅")


def get_last_refresh_label() -> str:
    """Return a user-friendly last refresh label."""
    return st.session_state.get("last_refresh") or "Not refreshed in this session"


def safe_load(loader: Callable[[], pd.DataFrame], empty_columns: list[str]) -> pd.DataFrame:
    """Load data safely and show setup issues in the UI."""
    try:
        return loader()
    except Exception as exc:
        st.warning(str(exc))
        return pd.DataFrame(columns=empty_columns)

def inject_stadium_audio() -> None:
    """Injects a high-voltage, flattened HTML5 stadium sound engine with autoplay."""
    import streamlit as st
    
    # Flattened string architecture to prevent Streamlit markdown parser escaping
    audio_html = (
        '<div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 58, 138, 0.4)); border: 2px solid #fbbf24; border-radius: 1rem; padding: 1.25rem; text-align: center; margin-bottom: 1.5rem; box-shadow: 0 0 20px rgba(251, 191, 36, 0.3); position: relative; overflow: hidden;">'
        '<div style="position: absolute; top: 8px; right: 12px; width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981;"></div>'
        '<p style="margin: 0 0 0.25rem 0; color: #fbbf24 !important; font-size: 0.85rem; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">🏟️ STADIUM BROADCAST LIVE</p>'
        '<p style="margin: 0 0 0.75rem 0; color: #94a3b8 !important; font-size: 0.75rem; font-weight: 600;">Theme Anthem Streaming Autoplay</p>'
        '<div style="display: flex; justify-content: center; align-items: center; width: 100%; overflow: hidden; border-radius: 0.5rem; background: rgba(255,255,255,0.05); padding: 0.4rem;">'
        '<audio autoplay loop controls style="width: 100%; height: 32px; outline: none;">'
        '<source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" type="audio/mpeg">'
        'Your browser does not support the audio element.'
        '</audio>'
        '</div>'
        '<div style="margin-top: 0.5rem; color: #64748b !important; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">⚡ Arena Atmosphere Active ⚡</div>'
        '</div>'
    )
    
    st.sidebar.markdown(audio_html, unsafe_allow_html=True)