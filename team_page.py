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
    load_fixtures,
    load_participants,
    render_top_navigation_bar,
    safe_load,
    play_franchise_audio
)

PARTICIPANT_COLUMNS = [
    "Participant",
    "Team",
    "Sport",
    "Points",
    "Matches",
    "Wins",
    "Bonus",
    "Participation Points",
]

FIXTURE_COLUMNS = [
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


def render_franchise_anthem(team_name: str, custom_url: str | None = None) -> None:
    """Render the official franchise anthem player defaulting to Duniya Hila Denge Hum."""
    anthem_title = f"{team_name.upper()} WAR ANTHEM • Duniya Hila Denge Hum"
    video_id = "4pJPj_fkQhc"  # Mumbai Indians / Arena Anthem default

    embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=0&loop=1&playlist={video_id}"

    player_html = f"""
    <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(251, 191, 36, 0.4); 
                border-radius: 0.85rem; padding: 0.6rem 0.9rem; margin-bottom: 1.25rem; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.35);">
        <div style="color: #fbbf24; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.4rem;">
            <span style="width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 6px #10b981; display: inline-block;"></span>
            🔥 OFFICIAL ARENA ANTHEM • {anthem_title}
        </div>
        <iframe width="100%" height="80" src="{embed_url}" title="Franchise Anthem" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border-radius: 0.5rem;"></iframe>
    </div>
    """
    st.markdown(player_html, unsafe_allow_html=True)


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
        [f"{team_name} Athlete 1", f"{team_name} Athlete 2", f"{team_name} Athlete 3"],
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
                "Participation Points": 0.0,
                "TotalPoints": 0.0,
            }
        )
    return pd.DataFrame(rows)


def _get_image_base64(image_path: str) -> str | None:
    """Convert local image file to base64 string for HTML embedding."""
    if image_path and os.path.exists(image_path):
        suffix = Path(image_path).suffix.replace(".", "").lower()
        mime_type = "image/png" if suffix == "png" else f"image/{suffix}"
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:{mime_type};base64,{encoded}"
    return None


def render_team_styles(team_color: str) -> None:
    """Inject dynamic franchise color styling and glassmorphism elements."""
    st.markdown(
        f"""
        <style>
        .franchise-hero {{
            position: relative;
            padding: 2.75rem 2rem;
            border-radius: 1.25rem;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 138, 0.82)),
                        url('https://images.unsplash.com/photo-1540747737956-3787293a9fc4?q=80&w=1280&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            border-left: 8px solid {team_color};
            border-top: 1px solid rgba(255, 255, 255, 0.15);
            border-right: 1px solid rgba(255, 255, 255, 0.15);
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6), 0 0 25px {team_color}33;
            margin-bottom: 1.75rem;
            overflow: hidden;
        }}

        .franchise-hud-card {{
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom: 3px solid {team_color};
            border-radius: 1rem;
            padding: 1.25rem 1rem;
            text-align: center;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35);
            margin-bottom: 1rem;
        }}

        .mvp-honor-card {{
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 4px solid {team_color};
            border-radius: 0.85rem;
            padding: 1rem 1.15rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_team_banner(team_name: str, total_points: float, team_scores: pd.DataFrame) -> None:
    """Render the championship franchise banner with glowing badge and captain tags."""
    team_cfg = get_team_config(team_name)
    meta = get_team_meta(team_name)
    captain = team_cfg.get("captain", "TBD")
    slogan = team_cfg.get("slogan", "One Team. One Target. One Trophy.")
    logo_path = team_cfg.get("logo", "")

    rank_str = "-"
    if not team_scores.empty and team_name in team_scores["Team"].values:
        ranked = team_scores.reset_index(drop=True)
        matched_idx = ranked.index[ranked["Team"].eq(team_name)]
        if not matched_idx.empty:
            rank_str = f"#{int(matched_idx[0]) + 1}"

    img_b64 = _get_image_base64(logo_path)
    if img_b64:
        logo_html = f'<img src="{img_b64}" style="width: 80px; height: 80px; object-fit: contain; filter: drop-shadow(0 0 12px {meta["color"]});" />'
    else:
        logo_html = f'<span style="font-size: 3.8rem; filter: drop-shadow(0 0 15px {meta["color"]});">{meta["emoji"]}</span>'

    banner_html = (
        f'<div class="franchise-hero">'
        f'<div style="display: flex; align-items: center; gap: 1.5rem; margin-bottom: 0.75rem;">'
        f'{logo_html}'
        f'<div>'
        f'<span style="background: rgba(251, 191, 36, 0.16); border: 1px solid #fbbf24; color: #fbbf24; '
        f'font-size: 0.75rem; font-weight: 800; padding: 0.25rem 0.75rem; border-radius: 1rem; letter-spacing: 1.5px; text-transform: uppercase;">'
        f'OFFICIAL FRANCHISE WAR ROOM'
        f'</span>'
        f'<h1 style="margin: 0.4rem 0 0.1rem 0; color: #ffffff !important; font-weight: 900; font-size: 2.75rem; letter-spacing: -0.5px; text-transform: uppercase;">'
        f'{team_name}'
        f'</h1>'
        f'<p style="margin: 0; color: #fbbf24 !important; font-size: 1.05rem; font-weight: 700; font-style: italic;">"{slogan}"</p>'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; gap: 1.5rem; flex-wrap: wrap; margin-top: 1.25rem; padding-top: 0.9rem; border-top: 1px solid rgba(255,255,255,0.12); color: #cbd5e1 !important; font-size: 0.95rem; font-weight: 600;">'
        f'<span>👑 Team Captain: <strong style="color: #ffffff;">{captain}</strong></span>'
        f'<span>📊 Standings Position: <strong style="color: #fbbf24;">{rank_str}</strong></span>'
        f'<span>⚡ Cumulative Score: <strong style="color: #ffffff;">{format_points(total_points)} PTS</strong></span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)


def render_sport_contributions(team_df: pd.DataFrame, team_color: str) -> None:
    """Render sport-wise contribution progress bars across all disciplines and bonuses."""
    played_df = team_df[team_df["Sport"] != "To be assigned"].copy()
    if played_df.empty:
        st.info("Sport contributions will populate once match points are entered.")
        return

    sport_points = (
        played_df.groupby("Sport", as_index=False)["TotalPoints"]
        .sum()
        .sort_values("TotalPoints", ascending=False)
    )
    max_points = float(sport_points["TotalPoints"].max()) if not sport_points.empty else 1.0

    rows = []
    for _, row in sport_points.iterrows():
        width = max(8, int((float(row["TotalPoints"]) / max_points) * 100)) if max_points > 0 else 8
        icon = get_sport_icon(row["Sport"])

        row_html = (
            f'<div style="margin-bottom: 1.1rem;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; color: #ffffff !important; font-weight: 700; font-size: 0.9rem;">'
            f'<span>{icon} {row["Sport"]}</span>'
            f'<span style="color: #fbbf24 !important; font-weight: 800;">{format_points(row["TotalPoints"])} PTS</span>'
            f'</div>'
            f'<div style="width: 100%; height: 9px; background: rgba(255, 255, 255, 0.08); border-radius: 5px; overflow: hidden;">'
            f'<div style="width: {width}%; height: 100%; background: linear-gradient(90deg, {team_color}, #fbbf24); border-radius: 5px; box-shadow: 0 0 8px {team_color};"></div>'
            f'</div>'
            f'</div>'
        )
        rows.append(row_html)

    card_wrapper = (
        f'<div style="background: rgba(15, 23, 42, 0.85) !important; border: 1px solid rgba(255,255,255,0.1) !important; '
        f'border-radius: 1.15rem; padding: 1.4rem; box-shadow: 0 10px 24px rgba(0,0,0,0.35);">'
        f'<div style="color: #fbbf24 !important; font-size: 0.82rem; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1.25rem;">'
        f'⚡ ALL DISCIPLINES & BONUS CONTRIBUTION MATRIX'
        f'</div>'
        f'{"".join(rows)}'
        f'</div>'
    )
    st.markdown(card_wrapper, unsafe_allow_html=True)


def render_team_fixtures(fixtures: pd.DataFrame, team_name: str) -> None:
    """Render the team's fixtures schedule."""
    if fixtures.empty:
        st.info("No fixtures found for this team yet.")
        return

    team_fixtures = fixtures[
        (fixtures["Team 1"].astype(str).str.casefold() == team_name.casefold())
        | (fixtures["Team 2"].astype(str).str.casefold() == team_name.casefold())
    ].copy()

    if team_fixtures.empty:
        st.info("No fixtures scheduled for this franchise yet.")
        return

    display_cols = [
        "Sport",
        "Date",
        "Stage",
        "Participant 1",
        "Team 1",
        "Participant 2",
        "Team 2",
        "Venue",
        "Status",
    ]
    available_cols = [c for c in display_cols if c in team_fixtures.columns]

    st.dataframe(
        team_fixtures[available_cols],
        use_container_width=True,
        hide_index=True,
    )


def render_team_roster(team_df: pd.DataFrame) -> None:
    """Render expandable team roster with individual participant breakdown."""
    if team_df.empty:
        st.info("No roster data available.")
        return

    roster = (
        team_df.groupby("Participant", as_index=False)
        .agg(
            TotalPoints=("TotalPoints", "sum"),
            Matches=("Matches", "sum"),
            Wins=("Wins", "sum"),
            Sports=("Sport", "nunique"),
        )
        .sort_values("TotalPoints", ascending=False)
    )

    for _, player in roster.iterrows():
        p_name = player["Participant"]
        player_rows = team_df[team_df["Participant"] == p_name].copy()

        with st.expander(f"🏅 {p_name} — {format_points(player['TotalPoints'])} PTS ({int(player['Sports'])} Sports)"):
            disp_df = player_rows[
                ["Sport", "Points", "Bonus", "Participation Points", "TotalPoints", "Matches", "Wins"]
            ].copy()

            disp_df["Points"] = disp_df["Points"].apply(format_points)
            disp_df["Bonus"] = disp_df["Bonus"].apply(format_points)
            disp_df["Participation Points"] = disp_df["Participation Points"].apply(format_points)
            disp_df["TotalPoints"] = disp_df["TotalPoints"].apply(format_points)

            st.dataframe(disp_df, use_container_width=True, hide_index=True)


def render_team_page(team_name: str) -> None:
    """Render a standalone franchise command room with full score rollups and anthem."""
    render_top_navigation_bar(team_name)

    meta = get_team_meta(team_name)
    team_cfg = get_team_config(team_name)
    render_team_styles(meta["color"])

    # 🔊 Triggers invisible auto-playing audio based on team
    play_franchise_audio(team_name)

    participants = safe_load(load_participants, PARTICIPANT_COLUMNS)
    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    # Compute TotalPoints safely (Points + Bonus + Participation Points)
    if not participants.empty:
        participants["Points"] = pd.to_numeric(participants.get("Points", 0), errors="coerce").fillna(0.0)
        participants["Bonus"] = pd.to_numeric(participants.get("Bonus", 0), errors="coerce").fillna(0.0)
        participants["Participation Points"] = pd.to_numeric(
            participants.get("Participation Points", 0), errors="coerce"
        ).fillna(0.0)
        participants["TotalPoints"] = (
            participants["Points"] + participants["Bonus"] + participants["Participation Points"]
        )

    team_name_clean = str(team_name).strip().casefold()

    # 1. TOTAL FRANCHISE DATA: Keeps ALL entries (Bowling, Underdog, Participation + Athletes)
    team_all_entries_df = (
        participants[
            participants["Team"].astype(str).str.strip().str.casefold() == team_name_clean
        ].copy()
        if not participants.empty
        else pd.DataFrame(columns=PARTICIPANT_COLUMNS)
    )

    # 2. ATHLETES ONLY: Excludes rows where Participant == Team name (for MVP & Squad roster only)
    athletes_only_df = team_all_entries_df[
        team_all_entries_df["Participant"].astype(str).str.strip().str.casefold() != team_name_clean
    ].copy()

    using_fallback = team_all_entries_df.empty
    if using_fallback:
        team_all_entries_df = build_fallback_team_data(team_name)
        athletes_only_df = team_all_entries_df

    team_scores = get_team_scores(participants)

    # Full franchise total points (e.g. 450 + 200 + 350 + 250 = 1250)
    total_franchise_points = team_all_entries_df["TotalPoints"].sum() if not team_all_entries_df.empty else 0.0

    # 1. Franchise Hero Banner
    render_team_banner(team_name, total_franchise_points, team_scores)

    if using_fallback:
        st.info("Showing placeholder roster until official participant rows are added to the sheet.")

    # 2. Key Telemetry Metrics
    athletes_count = athletes_only_df["Participant"].nunique() if not athletes_only_df.empty else 0
    sports_count = team_all_entries_df["Sport"].nunique() if not team_all_entries_df.empty else 0
    wins_count = int(team_all_entries_df["Wins"].sum()) if not team_all_entries_df.empty else 0

    hud_cols = st.columns(4)
    hud_template = """
        <div class="franchise-hud-card">
            <div style="color: #94a3b8; font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>
            <div style="color: #ffffff; font-size: 1.85rem; font-weight: 900; margin: 0.2rem 0; letter-spacing: -0.5px;">{value}</div>
            <div style="color: {color}; font-size: 0.78rem; font-weight: 700;">{subtext}</div>
        </div>
    """
    hud_cols[0].markdown(hud_template.format(label="Total Points", value=format_points(total_franchise_points), subtext="Franchise Cumulative", color="#fbbf24"), unsafe_allow_html=True)
    hud_cols[1].markdown(hud_template.format(label="Squad Members", value=str(athletes_count), subtext="Registered Athletes", color="#38bdf8"), unsafe_allow_html=True)
    hud_cols[2].markdown(hud_template.format(label="Active Arenas", value=str(sports_count), subtext="Disciplines & Bonus", color="#10b981"), unsafe_allow_html=True)
    hud_cols[3].markdown(hud_template.format(label="Victories", value=str(wins_count), subtext="Total Match Wins", color="#a855f7"), unsafe_allow_html=True)

    st.markdown("---")

    # 3. Sport Breakdown & MVPs
    left_col, right_col = st.columns([1.15, 1])

    with left_col:
        st.subheader("📊 Arena & Bonus Contributions")
        # Uses team_all_entries_df so Bowling, Underdog, and Old School all show
        render_sport_contributions(team_all_entries_df, meta["color"])

    with right_col:
        st.subheader("🥇 Franchise MVPs")
        # Uses athletes_only_df so only individual human players compete for MVP
        top_players = (
            athletes_only_df.groupby("Participant", as_index=False)["TotalPoints"]
            .sum()
            .sort_values("TotalPoints", ascending=False)
            .head(3)
        )
        if not top_players.empty:
            medals = ["👑 FRANCHISE MVP #1", "🥈 FRANCHISE MVP #2", "🥉 FRANCHISE MVP #3"]
            for idx, (_, row) in enumerate(top_players.iterrows()):
                mvp_card_html = (
                    f'<div class="mvp-honor-card">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                    f'<span style="color: #fbbf24; font-size: 0.78rem; font-weight: 800; letter-spacing: 1px;">{medals[idx]}</span>'
                    f'<span style="color: #cbd5e1; font-size: 0.75rem; font-weight: 700;">{team_name}</span>'
                    f'</div>'
                    f'<div style="color: #ffffff; font-size: 1.25rem; font-weight: 900; margin: 0.25rem 0;">{row["Participant"]}</div>'
                    f'<div style="color: #fbbf24; font-size: 1.35rem; font-weight: 900;">{format_points(row["TotalPoints"])} <span style="font-size: 0.8rem; color: #94a3b8;">PTS</span></div>'
                    f'</div>'
                )
                st.markdown(mvp_card_html, unsafe_allow_html=True)
        else:
            st.info("Top MVP players will appear once individual athletes are scored.")

    st.markdown("---")

    # 4. Schedule and Roster
    st.subheader("📅 Franchise Match Schedule")
    render_team_fixtures(fixtures, team_name)

    st.markdown("---")
    st.subheader("👥 Squad Roster & Individual Athlete Contributions")
    render_team_roster(athletes_only_df)