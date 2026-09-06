"""Shared utilities for styling, Google Sheets access, and data formatting."""

from __future__ import annotations

import functools
import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import gspread
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from google.oauth2.service_account import Credentials

CONFIG_PATH = Path("config.json")
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


@functools.lru_cache(maxsize=1)
def get_config(path: str = str(CONFIG_PATH)) -> dict[str, Any]:
    """Return cached application configuration from config.json."""
    config_file = Path(path)
    with config_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def apply_theme_variables(config: dict[str, Any]) -> None:
    """Inject theme variables from config.json."""
    theme = config.get("theme", {})
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
    """Authorize and establish connection to Google Sheets."""
    cfg = config or get_config()
    sheets_cfg = cfg["google_sheets"]

    try:
        # Streamlit Cloud execution
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
    """Copy a source column to a target column if target does not exist."""
    if target not in df.columns and source in df.columns:
        df[target] = df[source]
    return df


def _clean_participants(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize participant data for all sports including participation points."""
    df = _copy_if_missing(df, "Team", "House")

    expected_columns = [
        "Participant",
        "Team",
        "Sport",
        "Points",
        "Matches",
        "Wins",
        "Bonus",
        "Participation Points",
    ]
    df = df.reindex(columns=expected_columns)

    for col in ["Participant", "Team", "Sport"]:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    for col in ["Points", "Matches", "Wins", "Bonus", "Participation Points"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def _clean_fixtures(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize fixture data."""
    df = _copy_if_missing(df, "Team 1", "House 1")
    df = _copy_if_missing(df, "Team 2", "House 2")
    df = _copy_if_missing(df, "Stage", "Time")

    expected_columns = [
        "Sport",
        "Date",
        "Stage",
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


@cache_data(ttl=get_config()["data"].get("refresh_interval_seconds", 300))
def load_participants() -> pd.DataFrame:
    """Load participant records from the configured worksheet."""
    worksheet_name = get_config()["google_sheets"]["worksheets"]["participants"]
    return _clean_participants(_load_worksheet_records(worksheet_name))


def load_players() -> pd.DataFrame:
    """Backward-compatible alias for older participant loaders."""
    return load_participants()


@cache_data(ttl=get_config()["data"].get("refresh_interval_seconds", 300))
def load_fixtures() -> pd.DataFrame:
    """Load fixture records from the configured worksheet."""
    worksheet_name = get_config()["google_sheets"]["worksheets"]["fixtures"]
    return _clean_fixtures(_load_worksheet_records(worksheet_name))


@cache_data(ttl=get_config()["data"].get("refresh_interval_seconds", 300))
def load_leaderboard() -> pd.DataFrame:
    """Load participant leaderboard with points, bonus, and participation points."""
    participants = load_participants().copy()

    participants["Total_Score"] = (
        participants["Points"]
        + participants["Bonus"]
        + participants["Participation Points"]
    )

    leaderboard = (
        participants.groupby(["Participant", "Team"], as_index=False)
        .agg(
            Points=("Total_Score", "sum"),
            Matches=("Matches", "sum"),
            Wins=("Wins", "sum"),
            Bonus=("Bonus", "sum"),
            Participation_Points=("Participation Points", "sum"),
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
    get_config.cache_clear()
    st.session_state["last_refresh"] = datetime.now().strftime("%d %b %Y, %I:%M %p")


def format_points(points: float | int) -> str:
    """Format points according to configured decimal precision."""
    decimals = int(get_config()["data"].get("points_decimals", 0))
    return f"{float(points):,.{decimals}f}"


def get_status_color(status: str, config: dict[str, Any] | None = None) -> str:
    """Return the configured color for a fixture status."""
    cfg = config or get_config()
    return cfg["data"].get("status_colors", {}).get(status, cfg["theme"]["muted_color"])


def get_team_meta(team_name: str | None) -> dict[str, str]:
    """Config-driven fuzzy and alias lookup for team metadata."""
    config = get_config()
    default_meta = {
        "name": str(team_name) if team_name else "Unknown",
        "color": "#fbbf24",
        "emoji": "🛡️",
        "short_name": "TBD",
    }

    if not team_name or pd.isna(team_name):
        return default_meta

    clean_input = str(team_name).strip().casefold()

    for team in config.get("teams", []):
        t_name = team["name"].strip().casefold()
        t_short = team.get("short_name", "").strip().casefold()
        aliases = [str(a).strip().casefold() for a in team.get("aliases", [])]

        if clean_input in (t_name, t_short) or any(alias in clean_input for alias in aliases):
            return team

        # Default fallback keyword heuristics
        if any(kw in clean_input for kw in ["bhagyashree", "rcb"]) and "bhagyashree" in t_name:
            return team
        if any(kw in clean_input for kw in ["gayatri", "gi"]) and "gayatri" in t_name:
            return team
        if any(kw in clean_input for kw in ["pooja", "psk"]) and "pooja" in t_name:
            return team
        if any(kw in clean_input for kw in ["komal", "kkr"]) and "komal" in t_name:
            return team

    return default_meta


def get_house_meta(house_name: str, config: dict[str, Any] | None = None) -> dict[str, str]:
    """Backward-compatible alias for house metadata."""
    return get_team_meta(house_name)


def get_team_scores(participants_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate cumulative scores per team including match points, bonuses, and team entries."""
    if participants_df.empty:
        return pd.DataFrame(columns=["Team", "Points"])

    df = participants_df.copy()
    pts = pd.to_numeric(df.get("Points", 0), errors="coerce").fillna(0.0)
    bonus = pd.to_numeric(df.get("Bonus", 0), errors="coerce").fillna(0.0)
    part_pts = pd.to_numeric(df.get("Participation Points", 0), errors="coerce").fillna(0.0)

    # Sum ALL columns for each row
    df["TotalScore"] = pts + bonus + part_pts

    # Group by Team across ALL rows (both individual players and team awards)
    team_scores = (
        df.groupby("Team", as_index=False)["TotalScore"]
        .sum()
        .rename(columns={"TotalScore": "Points"})
        .sort_values(by="Points", ascending=False)
    )
    return team_scores


def render_points_matrix_table(participants_df: pd.DataFrame) -> None:
    """Generates the multi-sport breakdown matrix including all team awards and individual sports."""
    if participants_df.empty:
        return

    df = participants_df.copy()
    pts = pd.to_numeric(df.get("Points", 0), errors="coerce").fillna(0.0)
    bonus = pd.to_numeric(df.get("Bonus", 0), errors="coerce").fillna(0.0)
    part_pts = pd.to_numeric(df.get("Participation Points", 0), errors="coerce").fillna(0.0)

    df["OverallPoints"] = pts + bonus + part_pts

    # Pivot all rows: sums all participant points under each Sport per Team
    matrix = df.pivot_table(
        index="Sport",
        columns="Team",
        values="OverallPoints",
        aggfunc="sum",
        fill_value=0,
    )

    config = get_config()
    team_order = [t["name"] for t in config.get("teams", []) if t["name"] in matrix.columns]
    if team_order:
        remaining = [c for c in matrix.columns if c not in team_order]
        matrix = matrix[team_order + remaining]

    # Calculate overall total sum per team
    totals = matrix.sum(axis=0)
    matrix.loc["Total Points till now"] = totals

    # Format 0 as blank for visual clarity
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


def get_house_scores(participants: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible alias for team scores."""
    return get_team_scores(participants).rename(columns={"Team": "House"})


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


def is_team_bonus_entry(row: pd.Series | dict) -> bool:
    """Detect if a row represents team-level bonus points rather than a human player."""
    participant = str(row.get("Participant", "")).strip().casefold()
    team = str(row.get("Team", "")).strip().casefold()
    sport = str(row.get("Sport", "")).strip().casefold()
    bonus_keywords = ["points", "bonus", "participation", "underdog", "female"]
    return participant == team or any(kw in sport for kw in bonus_keywords)

import streamlit.components.v1 as components


def render_arena_anthem(
    video_id: str = "yq3SedbPF08",
    title: str = "TLOL4 ARENA • IPL Stadium EDM Theme",
) -> None:
    """Renders a pure audio controller with YouTube completely hidden off-screen."""
    player_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            body {{
                background: transparent;
                overflow: hidden;
            }}
            .arena-controller {{
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 58, 138, 0.92));
                border: 1.5px solid #fbbf24;
                border-radius: 0.85rem;
                padding: 0.6rem 1.1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5), 0 0 15px rgba(251, 191, 36, 0.25);
            }}
            .stream-meta {{
                display: flex;
                align-items: center;
                gap: 0.65rem;
            }}
            .live-dot {{
                width: 9px;
                height: 9px;
                background-color: #10b981;
                border-radius: 50%;
                box-shadow: 0 0 8px #10b981;
                animation: liveBlink 1.4s infinite ease-in-out;
            }}
            @keyframes liveBlink {{
                0%, 100% {{ transform: scale(0.9); opacity: 0.75; }}
                50% {{ transform: scale(1.3); opacity: 1; }}
            }}
            .title-text {{
                color: #fbbf24;
                font-size: 0.85rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .sub-text {{
                color: #94a3b8;
                font-size: 0.72rem;
                font-weight: 600;
            }}
            .play-btn {{
                background: linear-gradient(135deg, #d97706, #fbbf24);
                color: #0f172a;
                border: none;
                border-radius: 2rem;
                padding: 0.4rem 1.1rem;
                font-size: 0.78rem;
                font-weight: 900;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 0.45rem;
                box-shadow: 0 0 12px rgba(251, 191, 36, 0.45);
                transition: transform 0.15s ease, box-shadow 0.15s ease;
                white-space: nowrap;
            }}
            .play-btn:hover {{
                transform: scale(1.04);
                box-shadow: 0 0 16px rgba(251, 191, 36, 0.65);
            }}
            /* Completely offscreen - never visible to users, yet active for browser audio */
            #offscreen-audio-pod {{
                position: fixed;
                left: -9999px;
                top: -9999px;
                width: 250px;
                height: 200px;
                visibility: hidden;
            }}
        </style>
    </head>
    <body>
        <div class="arena-controller">
            <div class="stream-meta">
                <div class="live-dot"></div>
                <div>
                    <div class="title-text">🎺 {title}</div>
                    <div class="sub-text">TLOL Stadium Audio Broadcast</div>
                </div>
            </div>
            <div>
                <button id="toggle-btn" class="play-btn" onclick="togglePlayback()">
                    <span id="btn-icon">▶</span> <span id="btn-label">PLAY ANTHEM</span>
                </button>
            </div>
        </div>

        <div id="offscreen-audio-pod">
            <div id="yt-audio-anchor"></div>
        </div>

        <script src="https://www.youtube.com/iframe_api"></script>
        <script>
            let player;
            let active = false;
            const btn = document.getElementById('toggle-btn');
            const icon = document.getElementById('btn-icon');
            const label = document.getElementById('btn-label');

            function onYouTubeIframeAPIReady() {{
                player = new YT.Player('yt-audio-anchor', {{
                    height: '200',
                    width: '250',
                    videoId: '{video_id}',
                    playerVars: {{
                        'autoplay': 1,
                        'controls': 0,
                        'playsinline': 1,
                        'disablekb': 1
                    }},
                    events: {{
                        'onReady': (e) => {{
                            e.target.playVideo();
                        }},
                        'onStateChange': onPlayerStateChange
                    }}
                }});
            }}

            function onPlayerStateChange(e) {{
                // YT.PlayerState.ENDED is 0: loop automatically
                if (e.data === 0) {{
                    player.seekTo(0);
                    player.playVideo();
                }}
                // Playing
                if (e.data === 1) {{
                    active = true;
                    icon.textContent = "⏸";
                    label.textContent = "PAUSE";
                }}
                // Paused
                if (e.data === 2) {{
                    active = false;
                    icon.textContent = "▶";
                    label.textContent = "PLAY ANTHEM";
                }}
            }}

            function togglePlayback() {{
                if (!player) return;
                if (!active) {{
                    player.playVideo();
                }} else {{
                    player.pauseVideo();
                }}
            }}
        </script>
    </body>
    </html>
    """

    components.html(player_html, height=65)

def play_franchise_audio(team_name: str) -> None:
    """Plays pure background anthem automatically across all 4 franchises."""
    clean_team = str(team_name).lower()

    # 4-Team Anthem Mapping
    if any(kw in clean_team for kw in ["gayatri", "gi"]):
        video_id = "4pJPj_fkQhc"  # Mumbai Indians - Duniya Hila Denge Hum
        track_label = "Duniya Hila Denge Hum • Gayatri Indians"
    elif any(kw in clean_team for kw in ["pooja", "psk"]):
        video_id = "ozVfeBqJnbs"  # CSK Whistle Podu
        track_label = "Whistle Podu • Pooja Super Kings"
    elif any(kw in clean_team for kw in ["komal", "kkr"]):
        video_id = "GkQprQygqk4"  # KKR Korbo Lorbo Jeetbo
        track_label = "Korbo Lorbo Jeetbo • Komal Knight Riders"
    elif any(kw in clean_team for kw in ["bhagyashree", "rcb"]):
        video_id = "WOZSI2_m-3o"  # Alan Walker, Sofiloud - Team Side feat. RCB
        track_label = "Team Side (Play Bold) • Royal Challengers of Bhagyashree"
    else:
        return

    # Visual HUD status badge
    st.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(251, 191, 36, 0.4); 
                    border-radius: 0.75rem; padding: 0.45rem 0.85rem; margin-bottom: 1rem; 
                    display: flex; align-items: center; justify-content: space-between;">
            <div style="color: #fbbf24; font-size: 0.8rem; font-weight: 800; display: flex; align-items: center; gap: 0.45rem;">
                <span style="width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 6px #10b981; display: inline-block;"></span>
                🎵 PLAYING LIVE ARENA AUDIO: <strong style="color:#ffffff;">{track_label}</strong>
            </div>
            <span style="color: #94a3b8; font-size: 0.75rem; font-style: italic;">Auto-Playing</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1x1 zero-dimension iframe with autoplay enabled
    components.html(
        f"""
        <iframe 
            width="1" 
            height="1" 
            src="https://www.youtube.com/embed/{video_id}?autoplay=1&loop=1&playlist={video_id}&enablejsapi=1" 
            allow="autoplay" 
            style="display:none; border:0;">
        </iframe>
        """,
        height=1,
    )

def render_top_navigation_bar(current_page: str = "Home") -> None:
    """Render a clean status & sync bar without duplicate page links."""
    col_brand, col_sync, col_ref = st.columns([3.5, 1.8, 0.9])

    with col_brand:
        st.markdown(
            '<div style="color:#fbbf24; font-weight:900; font-size:1.05rem; padding-top:0.25rem;">'
            '🏆 TLOL4 ARENA <span style="color:#64748b; font-size:0.85rem; font-weight:600;">| 2026 LIVE DASHBOARD</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_sync:
        st.markdown(
            f'<div style="color:#94a3b8; font-size:0.85rem; text-align:right; padding-top:0.35rem;">'
            f'🔄 Sync: <strong style="color:#ffffff;">{get_last_refresh_label()}</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_ref:
        if st.button("⚡ Sync", key=f"top_sync_{current_page.lower()}", use_container_width=True):
            refresh_data()
            st.rerun()


def render_tournament_bracket_for_sport(sport: str, fixtures_df: pd.DataFrame) -> None:
    """Renders sport-specific tournament progression (Knockout Tree or Group + Knockout)."""
    if fixtures_df.empty:
        st.info(f"No match fixtures recorded for {sport}.")
        return

    sport_matches = fixtures_df[
        fixtures_df["Sport"].astype(str).str.strip().str.lower() == str(sport).strip().lower()
    ].copy()

    if sport_matches.empty:
        st.info(f"No scheduled matches found for {sport}.")
        return

    def get_stage_str(row: pd.Series) -> str:
        val = row.get("Stage")
        if pd.isna(val) or not str(val).strip():
            val = row.get("Time", "")
        return str(val).strip()

    def render_team_slot(participant: str, team_name: str) -> str:
        meta = get_team_meta(team_name)
        p_label = participant if str(participant).strip() else "TBD"
        return (
            f'<div style="display: flex; align-items: center; justify-content: space-between; '
            f'padding: 0.35rem 0.55rem; border-radius: 0.4rem; margin: 0.2rem 0; '
            f'background: rgba(255, 255, 255, 0.04); border-left: 4px solid {meta["color"]};">'
            f'<div>'
            f'<div style="color: #ffffff; font-weight: 800; font-size: 0.85rem;">{p_label}</div>'
            f'<div style="color: #94a3b8; font-size: 0.7rem;">{meta["emoji"]} {meta["short_name"]}</div>'
            f'</div>'
            f'</div>'
        )

    def render_match_box(match_row: pd.Series, is_championship: bool = False) -> str:
        border_style = (
            "2px solid #fbbf24; box-shadow: 0 0 15px rgba(251,191,36,0.3);"
            if is_championship
            else "1px solid rgba(255,255,255,0.12);"
        )
        bg_style = (
            "linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,58,138,0.85));"
            if is_championship
            else "rgba(15,23,42,0.88);"
        )

        return (
            f'<div style="background: {bg_style} border: {border_style} border-radius: 0.65rem; '
            f'padding: 0.65rem; margin-bottom: 0.6rem; min-width: 220px;">'
            f'<div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #fbbf24; font-weight: 700; margin-bottom: 0.25rem;">'
            f'<span>{match_row.get("Match", "Match")}</span>'
            f'<span style="color: #94a3b8;">📍 {match_row.get("Venue", "Arena")}</span>'
            f'</div>'
            f'{render_team_slot(str(match_row.get("Participant 1", "TBD")), str(match_row.get("Team 1", "TBD")))}'
            f'{render_team_slot(str(match_row.get("Participant 2", "TBD")), str(match_row.get("Team 2", "TBD")))}'
            f'</div>'
        )

    # -------------------------------------------------------------
    # FORMAT 1: TABLE TENNIS (4 Groups -> Quarters -> Semis -> Final)
    # -------------------------------------------------------------
    if "table tennis" in str(sport).strip().lower():
        st.markdown(
            '<div style="background: rgba(15,23,42,0.9); border: 1px solid rgba(251,191,36,0.3); '
            'border-radius: 0.75rem; padding: 0.75rem 1rem; margin-bottom: 1rem; color: #fbbf24; font-weight: 800;">'
            '🏓 Table Tennis Championship Progression (4 Groups • Top 2 Qualify for Quarters)'
            '</div>',
            unsafe_allow_html=True,
        )

        tt_tabs = st.tabs(["📊 Group Stage (A, B, C, D)", "🏆 Knockout Finals (QF ➔ SF ➔ F01)"])

        with tt_tabs[0]:
            g_cols = st.columns(4)
            group_codes = [("Group A", "GA"), ("Group B", "GB"), ("Group C", "GC"), ("Group D", "GD")]
            for idx, (g_title, g_prefix) in enumerate(group_codes):
                with g_cols[idx]:
                    st.markdown(f"**{g_title}**")
                    g_matches = sport_matches[sport_matches["Match"].astype(str).str.startswith(g_prefix)]
                    if not g_matches.empty:
                        for _, m in g_matches.iterrows():
                            st.markdown(render_match_box(m), unsafe_allow_html=True)
                    else:
                        st.caption(f"No {g_prefix} matches found.")

        with tt_tabs[1]:
            qf_matches = sport_matches[sport_matches["Match"].astype(str).str.startswith("QF")]
            sf_matches = sport_matches[sport_matches["Match"].astype(str).str.startswith("SF")]
            f_matches = sport_matches[sport_matches["Match"].astype(str).str.startswith("F")]

            k_col1, k_col2, k_col3 = st.columns([1.2, 1.2, 1.3])
            with k_col1:
                st.markdown("**⚔️ Quarter Finals (QF01-04)**")
                for _, m in qf_matches.iterrows():
                    st.markdown(render_match_box(m), unsafe_allow_html=True)

            with k_col2:
                st.markdown("**🔥 Semi Finals (SF01-02)**")
                for _, m in sf_matches.iterrows():
                    st.markdown(render_match_box(m), unsafe_allow_html=True)

            with k_col3:
                st.markdown("**🏆 Grand Final (F01)**")
                for _, m in f_matches.iterrows():
                    st.markdown(render_match_box(m, is_championship=True), unsafe_allow_html=True)
        return

    # -------------------------------------------------------------
    # FORMAT 2: 5-STAGE KNOCKOUT (Carrom, Foosball, Badminton)
    # Round 1 -> Round 2 -> Quarter Final -> Semi Final -> Final
    # -------------------------------------------------------------
    r1 = sport_matches[sport_matches.apply(get_stage_str, axis=1).str.contains("Round 1|R1", case=False, na=False)]
    r2 = sport_matches[sport_matches.apply(get_stage_str, axis=1).str.contains("Round 2|R2", case=False, na=False)]
    qf = sport_matches[sport_matches.apply(get_stage_str, axis=1).str.contains("Quarter|QF", case=False, na=False)]
    sf = sport_matches[sport_matches.apply(get_stage_str, axis=1).str.contains("Semi|SF", case=False, na=False)]
    fn = sport_matches[
        sport_matches.apply(get_stage_str, axis=1).str.contains("Final|1st|Gold", case=False, na=False)
        & ~sport_matches.apply(get_stage_str, axis=1).str.contains("Semi|Quarter|3rd", case=False, na=False)
    ]

    cols = st.columns(5)
    stages_data = [
        ("Round 1", r1),
        ("Round 2", r2),
        ("Quarter Final", qf),
        ("Semi Final", sf),
        ("🏆 Final", fn),
    ]

    for idx, (stage_label, stage_df) in enumerate(stages_data):
        with cols[idx]:
            st.markdown(
                f'<div style="text-align:center; font-size:0.75rem; font-weight:800; color:#fbbf24; '
                f'background:rgba(251,191,36,0.1); border:1px solid rgba(251,191,36,0.25); '
                f'border-radius:0.4rem; padding:0.25rem; margin-bottom:0.5rem; text-transform:uppercase;">'
                f'{stage_label}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if not stage_df.empty:
                for _, m in stage_df.iterrows():
                    is_champ = (stage_label == "🏆 Final")
                    st.markdown(render_match_box(m, is_championship=is_champ), unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div style="color:#64748b; font-size:0.75rem; text-align:center; padding:0.75rem; '
                    'background:rgba(255,255,255,0.02); border-radius:0.5rem;">Awaiting Lineup</div>',
                    unsafe_allow_html=True,
                )