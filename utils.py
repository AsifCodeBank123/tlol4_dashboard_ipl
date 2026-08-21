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


def get_team_meta(team_name: str | None) -> dict:
    """Fuzzy and case-insensitive lookup for team metadata to avoid 'Unknown'."""
    config = get_config()
    default_meta = {
        "name": str(team_name) if team_name else "Unknown",
        "color": "#fbbf24",
        "emoji": "🛡️",
        "short_name": "TBD"
    }

    if not team_name or pd.isna(team_name):
        return default_meta

    clean_input = str(team_name).strip().casefold()

    for team in config.get("teams", []):
        t_name = team["name"].strip().casefold()
        t_short = team.get("short_name", "").strip().casefold()

        # Exact match, short name match, or partial fuzzy match
        if clean_input == t_name or clean_input == t_short:
            return team
        
        # Handle "Royal Challengers of Bhagyashree" vs "Royal Challengers Bhagyashree"
        if "bhagyashree" in clean_input and "bhagyashree" in t_name:
            return team
        if "gayatri" in clean_input and "gayatri" in t_name:
            return team
        if "pooja" in clean_input and "pooja" in t_name:
            return team
        if "komal" in clean_input and "komal" in t_name:
            return team

    return default_meta

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


def is_team_bonus_entry(row) -> bool:
    """Detect if a row represents team-level bonus points rather than a human player."""
    participant = str(row.get("Participant", "")).strip().casefold()
    team = str(row.get("Team", "")).strip().casefold()
    sport = str(row.get("Sport", "")).strip().casefold()
    
    bonus_keywords = ["points", "bonus", "participation", "underdog", "female"]
    return participant == team or any(kw in sport for kw in bonus_keywords)


def render_points_matrix_table(participants_df: pd.DataFrame) -> None:
    """Generates the exact team breakdown matrix table from the sheet."""
    if participants_df.empty:
        return

    # Pivot all rows (both player points and team bonuses) across Sport/Category vs Team
    matrix = participants_df.pivot_table(
        index="Sport",
        columns="Team",
        values="Points",
        aggfunc="sum",
        fill_value=0,
    )

    config = get_config()
    team_order = [t["name"] for t in config.get("teams", []) if t["name"] in matrix.columns]
    if team_order:
        # Keep non-matching team columns as well if any
        remaining = [c for c in matrix.columns if c not in team_order]
        matrix = matrix[team_order + remaining]

    # Calculate total sum per team
    totals = matrix.sum(axis=0)
    matrix.loc["Total Points till now"] = totals

    # Format 0 as blank for visual clarity matching the spreadsheet screenshot
    display_matrix = matrix.astype(int).astype(str).replace("0", "")

    st.markdown(
        """
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(251, 191, 36, 0.3); 
            border-radius: 1rem; padding: 1.25rem; margin: 1.5rem 0 1rem 0; box-shadow: 0 10px 25px rgba(0,0,0,0.4);">
                <div style="color: #fbbf24; font-size: 1.1rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
                📋 Multi-Sport Points Breakdown Matrix
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(display_matrix, use_container_width=True)


def inject_stadium_audio(
    anthem_url: str | None = None,
    anthem_title: str = "STADIUM BROADCAST",
    subtitle: str = "Live Track",
) -> None:
    """Inject a slim, compact top audio bar without claiming sidebar width."""
    import streamlit as st

    if isinstance(anthem_url, str) and anthem_url.strip():
        audio_source = anthem_url.strip()
    else:
        audio_source = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

    audio_html = (
        f'<div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(251, 191, 36, 0.4); '
        f'border-radius: 0.75rem; padding: 0.5rem 1rem; margin-bottom: 1rem; display: flex; '
        f'align-items: center; justify-content: space-between; gap: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">'
        f'<div style="display: flex; align-items: center; gap: 0.6rem; min-width: 220px;">'
        f'<span style="width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 6px #10b981; display: inline-block;"></span>'
        f'<div>'
        f'<div style="color: #fbbf24; font-size: 0.8rem; font-weight: 800; text-transform: uppercase;">🏟️ {anthem_title}</div>'
        f'<div style="color: #94a3b8; font-size: 0.7rem;">{subtitle}</div>'
        f'</div>'
        f'</div>'
        f'<div style="flex: 1; max-width: 320px;">'
        f'<audio autoplay loop controls style="width: 100%; height: 26px; outline: none;">'
        f'<source src="{audio_source}" type="audio/mpeg">'
        f'</audio>'
        f'</div>'
        f'</div>'
    )
    # Render in main container instead of sidebar
    st.markdown(audio_html, unsafe_allow_html=True)

import urllib.parse
import streamlit as st
import streamlit.components.v1 as components

def render_soundcloud_player(
    track_url: str,
    title: str = "ARENA AUDIO BROADCAST",
    auto_play: bool = False,
    compact: bool = True,
) -> None:
    """Renders an embedded SoundCloud HTML5 player widget."""
    encoded_url = urllib.parse.quote(track_url, safe="")
    height = 80 if compact else 166
    
    embed_url = (
        f"https://w.soundcloud.com/player/?url={encoded_url}"
        f"&color=%23fbbf24"
        f"&auto_play={'true' if auto_play else 'false'}"
        f"&hide_related=true"
        f"&show_comments=false"
        f"&show_user=true"
        f"&show_reposts=false"
        f"&show_teaser=false"
        f"&visual={'false' if compact else 'true'}"
    )

    st.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(251, 191, 36, 0.4); 
                    border-radius: 0.75rem; padding: 0.5rem 0.85rem; margin-bottom: 1rem; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            <div style="color: #fbbf24; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.4rem;">
                <span style="width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 6px #10b981; display: inline-block;"></span>
                🎵 {title}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        f'<iframe width="100%" height="{height}" scrolling="no" frameborder="no" allow="autoplay" src="{embed_url}"></iframe>',
        height=height + 10,
    )

def render_top_navigation_bar(current_page: str = "Home") -> None:
    """Render a horizontal topbar with Home, Fixtures, and Leaderboard switchers."""
    import streamlit as st
    from utils import get_last_refresh_label, refresh_data

    main_pages = st.session_state.get("main_pages", {})

    st.markdown(
        """
        <style>
        .top-nav-container {
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-radius: 0.85rem;
            padding: 0.5rem 1rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        col_brand, col_nav1, col_nav2, col_nav3, col_sync, col_ref = st.columns(
            [2.2, 1.1, 1.1, 1.3, 1.4, 0.9]
        )

        with col_brand:
            st.markdown(
                '<div style="color:#fbbf24; font-weight:900; font-size:1.05rem; padding-top:0.35rem;">'
                '🏆 TLOL4 ARENA <span style="color:#64748b; font-size:0.8rem;">| 2026</span>'
                '</div>',
                unsafe_allow_html=True,
            )

        with col_nav1:
            if "Home" in main_pages:
                st.page_link(main_pages["Home"], label="🏠 Home", use_container_width=True)
            else:
                st.page_link("pages/Home.py", label="🏠 Home", use_container_width=True)

        with col_nav2:
            if "Fixtures" in main_pages:
                st.page_link(main_pages["Fixtures"], label="📅 Fixtures", use_container_width=True)
            else:
                st.page_link("pages/Fixtures.py", label="📅 Fixtures", use_container_width=True)

        with col_nav3:
            if "Leaderboard" in main_pages:
                st.page_link(main_pages["Leaderboard"], label="🏅 Leaderboard", use_container_width=True)
            else:
                st.page_link("pages/Leaderboard.py", label="🏅 Leaderboard", use_container_width=True)

        with col_sync:
            st.markdown(
                f'<div style="color:#94a3b8; font-size:0.75rem; text-align:right; padding-top:0.45rem;">'
                f'🔄 Sync: <strong style="color:#ffffff;">{get_last_refresh_label()}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_ref:
            if st.button("⚡ Sync", key=f"top_sync_{current_page.lower()}", use_container_width=True):
                refresh_data()
                st.rerun()