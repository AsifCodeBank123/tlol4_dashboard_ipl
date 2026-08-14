"""Reusable team profile page renderer for TLOL4 Sports League."""

from __future__ import annotations

import base64
import os
from pathlib import Path
import pandas as pd
import streamlit as st

from utils import (
    format_points,
    get_config,
    get_sport_icon,
    get_team_meta,
    get_team_scores,
    inject_stadium_audio,
    load_fixtures,
    load_participants,
    safe_load,
)

PARTICIPANT_COLUMNS = ["Participant", "Team", "Sport", "Points", "Matches", "Wins", "Bonus"]
FIXTURE_COLUMNS = [
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


def get_team_config(team_name: str) -> dict:
    """Return team configuration from config.json."""
    config = get_config()
    for team in config.get("teams", []):
        if team["name"].casefold() == team_name.casefold():
            return team
    return {}


def build_fallback_team_data(team_name: str) -> pd.DataFrame:
    """Create fallback roster rows when the Google Sheet has no team records."""
    team_cfg = get_team_config(team_name)
    fallback_members = team_cfg.get(
        "fallback_members",
        [f"{team_name} Player 1", f"{team_name} Player 2", f"{team_name} Player 3"],
    )
    rows = []
    for member in fallback_members:
        rows.append(
            {
                "Participant": member,
                "Team": team_name,
                "Sport": "To be assigned",
                "Points": 0.0,
                "Matches": 0,
                "Wins": 0,
                "Bonus": 0.0,
            }
        )
    return pd.DataFrame(rows)


def render_card(label: str, value: str, detail: str = "") -> None:
    """Render a reusable IPL-themed dashboard card with glassmorphism."""
    html = (
        f'<div class="dashboard-card" style="background: rgba(15, 23, 42, 0.75) !important; backdrop-filter: blur(12px); border: 1px solid rgba(251, 191, 36, 0.25) !important; border-radius: 1rem; padding: 1.25rem; margin-bottom: 0.5rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);">'
        f'<div class="card-label" style="color: #94a3b8 !important; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>'
        f'<div class="card-value" style="color: #ffffff !important; font-size: 1.8rem; font-weight: 900; margin: 0.25rem 0; text-shadow: 0 0 10px rgba(255,255,255,0.2);">{value}</div>'
        f'<div class="card-subtle" style="color: #fbbf24 !important; font-size: 0.8rem; font-weight: 600;">{detail}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _get_image_base64(image_path: str) -> str | None:
    """Convert local image file to base64 string for direct HTML embedding."""
    if image_path and os.path.exists(image_path):
        suffix = Path(image_path).suffix.replace(".", "").lower()
        mime_type = "image/png" if suffix == "png" else f"image/{suffix}"
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:{mime_type};base64,{encoded}"
    return None


def render_team_banner(team_name: str, team_df: pd.DataFrame, team_scores: pd.DataFrame) -> None:
    """Render the high-voltage IPL Franchise Banner with custom Logo support."""
    team_cfg = get_team_config(team_name)
    meta = get_team_meta(team_name)
    total_points = team_df["Points"].sum() if not team_df.empty else 0
    captain = team_cfg.get("captain", "TBD")
    slogan = team_cfg.get("slogan", "One team. One target. One trophy.")
    logo_path = team_cfg.get("logo", "")

    rank = "-"
    if not team_scores.empty and team_name in team_scores["Team"].values:
        ranked = team_scores.reset_index(drop=True)
        rank = int(ranked.index[ranked["Team"].eq(team_name)][0]) + 1

    # Encode logo to base64 or fallback to emoji with glowing drop shadow
    img_b64 = _get_image_base64(logo_path)
    if img_b64:
        logo_html = f'<img src="{img_b64}" style="width: 75px; height: 75px; object-fit: contain; filter: drop-shadow(0 0 10px {meta["color"]});" />'
    else:
        logo_html = f'<span style="font-size: 3.5rem; filter: drop-shadow(0 0 12px {meta["color"]});">{meta["emoji"]}</span>'

    banner_html = (
        f'<div class="team-explorer-banner" style="position: relative; padding: 2.5rem 2rem; border-radius: 1.25rem; background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 138, 0.85)); border-left: 8px solid {meta["color"]}; border-top: 1px solid rgba(255,255,255,0.15); border-right: 1px solid rgba(255,255,255,0.15); border-bottom: 1px solid rgba(255,255,255,0.15); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); margin-bottom: 2rem; overflow: hidden;">'
        f'<div style="display: flex; align-items: center; gap: 1.25rem; margin-bottom: 0.5rem;">'
        f'{logo_html}'
        f'<div>'
        f'<h2 style="margin: 0; color: #ffffff !important; font-weight: 900; font-size: 2.6rem; letter-spacing: -0.5px; text-transform: uppercase;">{team_name}</h2>'
        f'<p style="margin: 0.25rem 0 0 0; color: #fbbf24 !important; font-size: 1.1rem; font-weight: 700; font-style: italic;">"{slogan}"</p>'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; gap: 1.5rem; flex-wrap: wrap; margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(255,255,255,0.1); color: #cbd5e1 !important; font-size: 0.95rem; font-weight: 600;">'
        f'<span>👑 Captain: <strong style="color: white;">{captain}</strong></span>'
        f'<span>📊 Points Table Rank: <strong style="color: #fbbf24;">#{rank}</strong></span>'
        f'<span>⚡ Cumulative Score: <strong style="color: white;">{format_points(total_points)} PTS</strong></span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)


def render_sport_contributions(team_df: pd.DataFrame, team_color: str) -> None:
    """Render sport-wise contribution bars without multiline markdown indent leaks."""
    played_df = team_df[team_df["Sport"] != "To be assigned"].copy()
    if played_df.empty:
        st.info("Sport contribution will appear once points are added in the sheet.")
        return

    sport_points = (
        played_df.groupby("Sport", as_index=False)["Points"]
        .sum()
        .sort_values("Points", ascending=False)
    )
    max_points = float(sport_points["Points"].max()) if not sport_points.empty else 1.0

    rows = []
    for _, row in sport_points.iterrows():
        width = max(6, int((float(row["Points"]) / max_points) * 100)) if max_points else 0
        icon = get_sport_icon(row["Sport"])

        row_html = (
            f'<div style="margin-bottom: 1.2rem;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; color: #ffffff !important; font-weight: 700; font-size: 0.95rem;">'
            f'<span>{icon} {row["Sport"]}</span>'
            f'<span style="color: #fbbf24 !important; font-weight: 800;">{format_points(row["Points"])} PTS</span>'
            f'</div>'
            f'<div style="width: 100%; height: 10px; background: rgba(255, 255, 255, 0.1); border-radius: 5px; overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.5);">'
            f'<div style="width: {width}%; height: 100%; background: linear-gradient(90deg, {team_color}, #fbbf24); border-radius: 5px; transition: width 0.8s ease-in-out; box-shadow: 0 0 10px {team_color};"></div>'
            f'</div>'
            f'</div>'
        )
        rows.append(row_html)

    card_wrapper = (
        f'<div class="sport-contribution-card" style="background: rgba(15, 23, 42, 0.8) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 1.25rem; padding: 1.5rem; box-shadow: 0 10px 20px rgba(0,0,0,0.3);">'
        f'<div class="card-label" style="color: #94a3b8 !important; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1.25rem;">⚡ SPORT CONTRIBUTION BREAKDOWN</div>'
        f'{"".join(rows)}'
        f'</div>'
    )
    st.markdown(card_wrapper, unsafe_allow_html=True)


def render_team_fixtures(fixtures: pd.DataFrame, team_name: str) -> None:
    """Render the team's fixtures table."""
    if fixtures.empty:
        st.info("No fixtures found for this team yet.")
        return

    team_fixtures = fixtures[
        (fixtures["Team 1"].str.casefold() == team_name.casefold())
        | (fixtures["Team 2"].str.casefold() == team_name.casefold())
    ].copy()

    if team_fixtures.empty:
        st.info("No fixtures found for this team yet.")
        return

    st.dataframe(
        team_fixtures[
            ["Sport", "Date", "Time", "Participant 1", "Team 1", "Participant 2", "Team 2", "Venue", "Status"]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_team_roster(team_df: pd.DataFrame) -> None:
    """Render expandable team roster with player-wise sport breakdown."""
    if team_df.empty:
        st.info("No roster data available.")
        return

    roster = (
        team_df.groupby("Participant", as_index=False)
        .agg(
            Points=("Points", "sum"),
            Matches=("Matches", "sum"),
            Wins=("Wins", "sum"),
            Sports=("Sport", "nunique"),
        )
        .sort_values("Points", ascending=False)
    )

    for _, player in roster.iterrows():
        player_rows = team_df[team_df["Participant"] == player["Participant"]].copy()
        with st.expander(f"🏅 {player['Participant']} — {format_points(player['Points'])} PTS"):
            display_df = player_rows[["Sport", "Points", "Matches", "Wins", "Bonus"]].copy()
            display_df["Points"] = display_df["Points"].apply(format_points)
            display_df["Bonus"] = display_df["Bonus"].apply(format_points)
            st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_team_page(team_name: str) -> None:
    
    """Render a standalone team profile page with its own franchise anthem."""
    team_cfg = get_team_config(team_name)
    team_anthem = team_cfg.get("anthem")
    
    # Trigger the team's custom anthem in sidebar console
    inject_stadium_audio(
        anthem_url=team_anthem,
        anthem_title=f"{team_name.upper()} ANTHEM",
        subtitle=f"Official Franchise Anthem • {team_cfg.get('slogan', '')}"
    )
    participants = safe_load(load_participants, PARTICIPANT_COLUMNS)
    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    live_team_df = (
        participants[participants["Team"].str.casefold() == team_name.casefold()].copy()
        if not participants.empty
        else pd.DataFrame(columns=PARTICIPANT_COLUMNS)
    )

    using_fallback = live_team_df.empty
    team_df = build_fallback_team_data(team_name) if using_fallback else live_team_df
    team_scores = get_team_scores(participants)

    render_team_banner(team_name, team_df, team_scores)

    if using_fallback:
        st.info("Showing fallback team members because no live sheet rows were found for this team.")

    total_points = team_df["Points"].sum() if not team_df.empty else 0
    participants_count = team_df["Participant"].nunique() if not team_df.empty else 0
    sports_count = team_df[team_df["Sport"] != "To be assigned"]["Sport"].nunique() if not team_df.empty else 0
    wins_count = int(team_df["Wins"].sum()) if not team_df.empty else 0

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_card("Total Points", format_points(total_points), "Franchise total")
    with metric_cols[1]:
        render_card("Squad Members", str(participants_count), "Registered athletes")
    with metric_cols[2]:
        render_card("Active Arenas", str(sports_count), "Sports represented")
    with metric_cols[3]:
        render_card("Total Victories", str(wins_count), "Wins recorded")

    st.markdown("---")

    left_col, right_col = st.columns([1.15, 1])
    with left_col:
        st.subheader("📊 Sport Contribution")
        meta = get_team_meta(team_name)
        render_sport_contributions(team_df, meta["color"])

    with right_col:
        st.subheader("🥇 Franchise MVPs")
        top_players = (
            team_df.groupby("Participant", as_index=False)["Points"]
            .sum()
            .sort_values("Points", ascending=False)
            .head(3)
        )
        medals = ["👑 MVP #1", "🥈 MVP #2", "🥉 MVP #3"]
        for idx, (_, row) in enumerate(top_players.iterrows()):
            render_card(f"{medals[idx]} {row['Participant']}", f"{format_points(row['Points'])} PTS", team_name)
            st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📅 Franchise Fixture Schedule")
    render_team_fixtures(fixtures, team_name)

    st.markdown("---")
    st.subheader("👥 Squad Roster & Performance Breakdown")
    render_team_roster(team_df)