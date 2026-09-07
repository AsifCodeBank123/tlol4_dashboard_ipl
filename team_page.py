"""Comprehensive championship franchise war room module for TLOL4 Sports League."""

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
    play_franchise_audio,
    render_top_navigation_bar,
    safe_load,
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


def get_team_config(team_name: str) -> dict:
    """Return franchise metadata and configuration from config.json."""
    config = get_config()
    for team in config.get("teams", []):
        if team.get("name", "").casefold() == team_name.casefold():
            return team
    return {}


def _get_image_base64(image_path: str) -> str | None:
    """Convert local asset file to base64 string for clean HTML rendering."""
    if image_path and os.path.exists(image_path):
        suffix = Path(image_path).suffix.replace(".", "").lower()
        mime_type = "image/png" if suffix == "png" else f"image/{suffix}"
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:{mime_type};base64,{encoded}"
    return None


def render_war_room_styles(team_color: str) -> None:
    """Inject specialized franchise CSS classes and theme tokens."""
    st.markdown(
        f"""
        <style>
        .franchise-hero {{
            position: relative;
            padding: 2.75rem 2rem;
            border-radius: 1.25rem;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 58, 138, 0.85)),
                        url('https://images.unsplash.com/photo-1540747737956-3787293a9fc4?q=80&w=1280&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            border-left: 8px solid {team_color};
            border-top: 1px solid rgba(255, 255, 255, 0.15);
            border-right: 1px solid rgba(255, 255, 255, 0.15);
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6), 0 0 25px {team_color}33;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }}

        .tactical-box {{
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.15rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
            margin-bottom: 1rem;
        }}

        .spotlight-card {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 58, 138, 0.9));
            border: 1.5px solid #fbbf24;
            border-radius: 1.15rem;
            padding: 1.35rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4), 0 0 20px rgba(251, 191, 36, 0.25);
        }}

        .badge-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            margin: 0.25rem 0.25rem 0.25rem 0;
        }}

        .h2h-card {{
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 0.85rem;
            padding: 0.9rem;
            margin-bottom: 0.75rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_franchise_hero(team_name: str, total_points: float, team_scores: pd.DataFrame) -> None:
    """Render the official command room banner with captain and standings position."""
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
        f'<span>👑 Captain: <strong style="color: #ffffff;">{captain}</strong></span>'
        f'<span>📊 Table Position: <strong style="color: #fbbf24;">{rank_str}</strong></span>'
        f'<span>⚡ Cumulative Points: <strong style="color: #ffffff;">{format_points(total_points)} PTS</strong></span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)


def render_captain_orders(team_name: str, team_color: str) -> None:
    """Feature 4: Captain's Tactical Orders & War Cry Dispatch."""
    team_cfg = get_team_config(team_name)
    captain = team_cfg.get("captain", "Squad Captain")
    slogan = team_cfg.get("slogan", "All for victory.")

    brief_html = (
        f'<div class="tactical-box" style="border-left: 5px solid {team_color};">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">'
        f'<span style="color: #fbbf24; font-size: 0.8rem; font-weight: 900; letter-spacing: 1px; text-transform: uppercase;">'
        f'⚔️ CAPTAIN\'S STRATEGIC DISPATCH'
        f'</span>'
        f'<span style="color: #94a3b8; font-size: 0.75rem; font-weight: 700;">COMMS DIRECT: {captain.upper()}</span>'
        f'</div>'
        f'<div style="color: #f1f5f9; font-size: 0.95rem; font-weight: 600; line-height: 1.5; font-style: italic;">'
        f'"{slogan} Maintain discipline across every table, secure all bowling bonus thresholds, and lock in qualification."'
        f'</div>'
        f'</div>'
    )
    st.markdown(brief_html, unsafe_allow_html=True)


def render_power_gauges(team_all_df: pd.DataFrame, athletes_df: pd.DataFrame, team_color: str) -> None:
    """Feature 2: Tactical Power Ranking & Win Probability Gauges."""
    total_pts = float(team_all_df["TotalPoints"].sum()) if not team_all_df.empty else 0.0
    matches = int(team_all_df["Matches"].sum()) if not team_all_df.empty else 0
    wins = int(team_all_df["Wins"].sum()) if not team_all_df.empty else 0
    bonus_pts = float(team_all_df["Bonus"].sum()) if not team_all_df.empty else 0.0

    win_rate = int((wins / matches) * 100) if matches > 0 else 0
    bonus_pct = int((bonus_pts / total_pts) * 100) if total_pts > 0 else 0
    clinch_status = "PLAYOFF CLINCH SECURED" if total_pts >= 1000 else "IN ACTIVE HUNT"

    cols = st.columns(4)
    metric_template = """
        <div class="tactical-box" style="text-align: center; border-bottom: 3px solid {color};">
            <div style="color: #94a3b8; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>
            <div style="color: #ffffff; font-size: 1.7rem; font-weight: 900; margin: 0.2rem 0; letter-spacing: -0.5px;">{value}</div>
            <div style="color: {color}; font-size: 0.75rem; font-weight: 700;">{subtext}</div>
        </div>
    """
    cols[0].markdown(metric_template.format(label="Franchise Score", value=format_points(total_pts), subtext=clinch_status, color="#fbbf24"), unsafe_allow_html=True)
    cols[1].markdown(metric_template.format(label="Win Efficiency", value=f"{win_rate}%", subtext=f"{wins} Wins of {matches} Matches", color=team_color), unsafe_allow_html=True)
    cols[2].markdown(metric_template.format(label="Bonus Impact", value=f"{bonus_pct}%", subtext=f"{format_points(bonus_pts)} Bonus PTS", color="#10b981"), unsafe_allow_html=True)
    cols[3].markdown(metric_template.format(label="Squad Depth", value=str(athletes_df["Participant"].nunique()), subtext="Active Roster", color="#38bdf8"), unsafe_allow_html=True)


def render_achievement_badges(team_all_df: pd.DataFrame, athletes_df: pd.DataFrame) -> None:
    """Feature 3: Franchise Milestone & Achievement Badges."""
    total_pts = float(team_all_df["TotalPoints"].sum()) if not team_all_df.empty else 0.0
    wins = int(team_all_df["Wins"].sum()) if not team_all_df.empty else 0
    has_centurion = False
    if not athletes_df.empty:
        p_sums = athletes_df.groupby("Participant")["TotalPoints"].sum()
        has_centurion = any(p_sums >= 100)

    badges = [
        ("👑 FRANCHISE TITAN", "Crossed 1,000 Total Points", total_pts >= 1000, "#fbbf24"),
        ("⚡ CENTURION SQUAD", "Athlete scored 100+ points", has_centurion, "#38bdf8"),
        ("🎯 UNDERDOG EXECUTIONER", "Captured Underdog Bonus", "underdog" in str(team_all_df["Sport"].values).lower(), "#ec4899"),
        ("🛡️ CLEAN SHEET DEFENDER", "Achieved 3+ tournament wins", wins >= 3, "#10b981"),
    ]

    badge_html_items = []
    for title, desc, unlocked, color in badges:
        if unlocked:
            badge_html_items.append(
                f'<span class="badge-pill" style="background: rgba(255,255,255,0.06); border: 1px solid {color}; color: {color};" title="{desc}">'
                f'{title} &nbsp;✔'
                f'</span>'
            )
        else:
            badge_html_items.append(
                f'<span class="badge-pill" style="background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.15); color: #64748b;" title="Locked: {desc}">'
                f'{title} (Locked)'
                f'</span>'
            )

    st.markdown(
        f"""
        <div class="tactical-box">
            <div style="color: #fbbf24; font-size: 0.8rem; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.5rem;">
                🏆 UNLOCKED FRANCHISE MILESTONES
            </div>
            <div>{''.join(badge_html_items)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_next_battle_spotlight(fixtures: pd.DataFrame, team_name: str) -> None:
    """Feature 5: Next Battle Spotlight Card (Upcoming Imminent Clash)."""
    if fixtures.empty:
        return

    team_clean = team_name.strip().casefold()
    upcoming = fixtures[
        fixtures["Status"].astype(str).str.strip().str.lower() == "upcoming"
    ].copy()

    team_upcoming = upcoming[
        (upcoming["Team 1"].astype(str).str.strip().str.casefold() == team_clean)
        | (upcoming["Team 2"].astype(str).str.strip().str.casefold() == team_clean)
    ]

    if team_upcoming.empty:
        return

    next_match = team_upcoming.iloc[0]
    sport = next_match.get("Sport", "Arena Showdown")
    icon = get_sport_icon(sport)
    match_num = next_match.get("Match", "Match")
    venue = next_match.get("Venue", "Main Arena")
    date_str = next_match.get("Date", "TBD")
    stage = next_match.get("Stage") or next_match.get("Time") or "Tournament"

    p1 = next_match.get("Participant 1", "TBD")
    t1 = next_match.get("Team 1", "TBD")
    p2 = next_match.get("Participant 2", "TBD")
    t2 = next_match.get("Team 2", "TBD")

    m1 = get_team_meta(t1)
    m2 = get_team_meta(t2)

    spotlight_html = (
        f'<div class="spotlight-card">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">'
        f'<span style="background: #fbbf24; color: #000000; font-size: 0.75rem; font-weight: 900; padding: 0.25rem 0.75rem; border-radius: 1rem; letter-spacing: 1px;">'
        f'⚔️ NEXT BATTLE SPOTLIGHT'
        f'</span>'
        f'<span style="color: #fbbf24; font-size: 0.8rem; font-weight: 800;">{match_num} • {stage}</span>'
        f'</div>'
        f'<div style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 0.75rem;">📅 {date_str} &nbsp;•&nbsp; 📍 {venue} &nbsp;•&nbsp; ⚡ {icon} {sport}</div>'
        f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;">'
        f'<div style="flex: 1; padding: 0.75rem; border-radius: 0.5rem; background: rgba(255,255,255,0.03); border-left: 4px solid {m1["color"]};">'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.1rem;">{p1}</div>'
        f'<div style="color: #94a3b8; font-size: 0.75rem;">{m1["emoji"]} {m1["name"]}</div>'
        f'</div>'
        f'<div style="color: #fbbf24; font-weight: 900; font-size: 1.2rem; font-style: italic;">VS</div>'
        f'<div style="flex: 1; padding: 0.75rem; border-radius: 0.5rem; background: rgba(255,255,255,0.03); border-left: 4px solid {m2["color"]};">'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.1rem;">{p2}</div>'
        f'<div style="color: #94a3b8; font-size: 0.75rem;">{m2["emoji"]} {m2["name"]}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(spotlight_html, unsafe_allow_html=True)


def render_h2h_matrix(fixtures: pd.DataFrame, team_name: str) -> None:
    """Feature 1: Head-to-Head (H2H) Rivalry Matrix against all 3 opponents."""
    config = get_config()
    all_teams = [t["name"] for t in config.get("teams", []) if t["name"].casefold() != team_name.casefold()]

    st.markdown(
        """
        <div style="color: #fbbf24; font-size: 0.85rem; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.5rem;">
            ⚔️ HEAD-TO-HEAD RIVALRY MATRIX
        </div>
        """,
        unsafe_allow_html=True,
    )

    if fixtures.empty:
        st.info("Match records will populate head-to-head statistics.")
        return

    team_clean = team_name.casefold()
    cols = st.columns(len(all_teams))

    for idx, opponent in enumerate(all_teams):
        opp_clean = opponent.casefold()
        opp_meta = get_team_meta(opponent)

        clashes = fixtures[
            ((fixtures["Team 1"].astype(str).str.casefold() == team_clean) & (fixtures["Team 2"].astype(str).str.casefold() == opp_clean))
            | ((fixtures["Team 2"].astype(str).str.casefold() == team_clean) & (fixtures["Team 1"].astype(str).str.casefold() == opp_clean))
        ]

        total_clashes = len(clashes)
        completed = len(clashes[clashes["Status"].astype(str).str.casefold() == "completed"])
        upcoming = len(clashes[clashes["Status"].astype(str).str.casefold() == "upcoming"])

        with cols[idx]:
            card_html = (
                f'<div class="h2h-card" style="border-top: 3px solid {opp_meta["color"]}; text-align: center;">'
                f'<div style="font-size: 1.75rem;">{opp_meta["emoji"]}</div>'
                f'<div style="color: #ffffff; font-weight: 800; font-size: 0.85rem; margin: 0.2rem 0;">vs {opp_meta["short_name"]}</div>'
                f'<div style="color: #fbbf24; font-size: 1.15rem; font-weight: 900;">{total_clashes} Encounters</div>'
                f'<div style="color: #94a3b8; font-size: 0.72rem; margin-top: 0.3rem;">'
                f'Finished: <strong style="color: #ffffff;">{completed}</strong> • Pending: <strong style="color: #ffffff;">{upcoming}</strong>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)


def render_athlete_roster_with_form(athletes_df: pd.DataFrame, total_franchise_pts: float) -> None:
    """Feature 6: Athlete Form Guide & MVP Contribution Share."""
    if athletes_df.empty:
        st.info("No individual athlete records available.")
        return

    roster = (
        athletes_df.groupby("Participant", as_index=False)
        .agg(
            TotalPoints=("TotalPoints", "sum"),
            Matches=("Matches", "sum"),
            Wins=("Wins", "sum"),
            Bonus=("Bonus", "sum"),
            Sports=("Sport", "nunique"),
        )
        .sort_values("TotalPoints", ascending=False)
    )

    for _, player in roster.iterrows():
        p_name = player["Participant"]
        p_pts = float(player["TotalPoints"])
        share_pct = int((p_pts / total_franchise_pts) * 100) if total_franchise_pts > 0 else 0
        matches = int(player["Matches"])
        wins = int(player["Wins"])
        win_pct = int((wins / matches) * 100) if matches > 0 else 0

        # Form Pill
        if win_pct >= 70:
            form_pill = '<span style="background: rgba(16,185,129,0.2); color: #10b981; padding: 0.2rem 0.5rem; border-radius: 1rem; font-size: 0.7rem; font-weight: 800;">🔥 ON FIRE</span>'
        elif win_pct >= 40:
            form_pill = '<span style="background: rgba(56,189,248,0.2); color: #38bdf8; padding: 0.2rem 0.5rem; border-radius: 1rem; font-size: 0.7rem; font-weight: 800;">⚖️ IN RHYTHM</span>'
        else:
            form_pill = '<span style="background: rgba(148,163,184,0.15); color: #94a3b8; padding: 0.2rem 0.5rem; border-radius: 1rem; font-size: 0.7rem; font-weight: 800;">WARMUP</span>'

        player_rows = athletes_df[athletes_df["Participant"] == p_name].copy()

        expander_title = (
            f"🏅 {p_name} — {format_points(p_pts)} PTS ({share_pct}% Team Share) • {int(player['Sports'])} Sports"
        )
        with st.expander(expander_title):
            st.markdown(
                f"<div style='margin-bottom: 0.5rem; display: flex; gap: 0.5rem; align-items: center;'>"
                f"{form_pill} <span style='color: #94a3b8; font-size: 0.8rem;'>Win Ratio: <strong>{win_pct}%</strong> ({wins}W - {matches - wins}L)</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            disp_df = player_rows[
                ["Sport", "Points", "Bonus", "Participation Points", "TotalPoints", "Matches", "Wins"]
            ].copy()
            for c in ["Points", "Bonus", "Participation Points", "TotalPoints"]:
                disp_df[c] = disp_df[c].apply(format_points)
            st.dataframe(disp_df, use_container_width=True, hide_index=True)


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
        f'<div class="tactical-box">'
        f'<div style="color: #fbbf24 !important; font-size: 0.82rem; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1.25rem;">'
        f'⚡ ALL DISCIPLINES & BONUS CONTRIBUTION MATRIX'
        f'</div>'
        f'{"".join(rows)}'
        f'</div>'
    )
    st.markdown(card_wrapper, unsafe_allow_html=True)


def render_team_page(team_name: str) -> None:
    """Master orchestrator for the complete franchise war room experience."""
    render_top_navigation_bar(team_name)

    meta = get_team_meta(team_name)
    render_war_room_styles(meta["color"])

    # 🔊 Continuous Background Audio (Duniya Hila Denge Hum, Whistle Podu, etc.)
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

    team_clean = str(team_name).strip().casefold()

    # 1. TOTAL TEAM DATA (Includes Bowling, Underdog, and Athlete rows)
    team_all_entries_df = (
        participants[
            participants["Team"].astype(str).str.strip().str.casefold() == team_clean
        ].copy()
        if not participants.empty
        else pd.DataFrame(columns=PARTICIPANT_COLUMNS)
    )

    # 2. ATHLETES ONLY (For MVP ranking and Squad Roster)
    athletes_only_df = team_all_entries_df[
        team_all_entries_df["Participant"].astype(str).str.strip().str.casefold() != team_clean
    ].copy()

    team_scores = get_team_scores(participants)
    total_franchise_points = float(team_all_entries_df["TotalPoints"].sum()) if not team_all_entries_df.empty else 0.0

    # Section 1: Hero Banner & Captain's Dispatch
    render_franchise_hero(team_name, total_franchise_points, team_scores)
    render_captain_orders(team_name, meta["color"])

    # Section 2: Tactical Power Gauges
    render_power_gauges(team_all_entries_df, athletes_only_df, meta["color"])

    # Section 3: Next Battle Spotlight
    render_next_battle_spotlight(fixtures, team_name)

    # Section 4: Milestone Badges
    render_achievement_badges(team_all_entries_df, athletes_only_df)

    # Section 5: Head-to-Head Rivalry Dossier
    render_h2h_matrix(fixtures, team_name)

    st.markdown("---")

    # Section 6: Arena Contributions & MVPs
    left_col, right_col = st.columns([1.15, 1])

    with left_col:
        st.subheader("📊 Arena & Bonus Contributions")
        render_sport_contributions(team_all_entries_df, meta["color"])

    with right_col:
        st.subheader("🥇 Franchise MVPs")
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
                    f'<div class="tactical-box" style="border-left: 4px solid {meta["color"]}; margin-bottom: 0.65rem;">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                    f'<span style="color: #fbbf24; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px;">{medals[idx]}</span>'
                    f'<span style="color: #cbd5e1; font-size: 0.72rem; font-weight: 700;">{team_name}</span>'
                    f'</div>'
                    f'<div style="color: #ffffff; font-size: 1.25rem; font-weight: 900; margin: 0.2rem 0;">{row["Participant"]}</div>'
                    f'<div style="color: #fbbf24; font-size: 1.35rem; font-weight: 900;">{format_points(row["TotalPoints"])} <span style="font-size: 0.8rem; color: #94a3b8;">PTS</span></div>'
                    f'</div>'
                )
                st.markdown(mvp_card_html, unsafe_allow_html=True)
        else:
            st.info("Athlete MVP honors will populate as match points are scored.")

    st.markdown("---")

    # Section 7: Squad Roster & Individual Form Guide
    st.subheader("👥 Squad Roster & Individual Form Guide")
    render_athlete_roster_with_form(athletes_only_df, total_franchise_points)