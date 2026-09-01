"""Home page for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

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
    render_points_matrix_table,
    render_soundcloud_player,
    render_top_navigation_bar,
    render_tournament_bracket_for_sport,
    safe_load,
)

PARTICIPANT_COLUMNS = ["Participant", "Team", "Sport", "Points", "Matches", "Wins", "Bonus"]
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


def render_standings_card(team_name: str, points: float, rank: int) -> None:
    """Render an IPL-styled standings card with franchise branding."""
    meta = get_team_meta(team_name)
    rank_badge = f"RANK #{rank}" if rank > 1 else "👑 LEAGUE LEADER"
    border_accent = meta["color"] if rank > 1 else "#fbbf24"

    html = (
        f'<div class="team-card" style="background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); '
        f'border-top: 4px solid {border_accent}; border-left: 1px solid rgba(255,255,255,0.1); '
        f'border-right: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); '
        f'border-radius: 1rem; padding: 1.25rem; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.4); '
        f'margin-bottom: 1rem; transition: transform 0.3s ease;">'
        f'<div style="font-size: 2.2rem; filter: drop-shadow(0 0 10px {meta["color"]});">{meta["emoji"]}</div>'
        f'<div style="color: #ffffff; font-size: 1.1rem; font-weight: 800; margin: 0.25rem 0;">{team_name}</div>'
        f'<div style="color: #ffffff; font-size: 1.8rem; font-weight: 900; margin-top: 0.2rem;">'
        f'{format_points(points)} <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 600;">PTS</span>'
        f'</div>'
        f'<div style="color: {border_accent}; font-size: 0.8rem; font-weight: 800; letter-spacing: 1px; margin-top: 0.4rem; text-transform: uppercase;">'
        f'{rank_badge}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_match_card(row: pd.Series) -> None:
    """Render an upcoming match card with clean participant cards."""
    icon = get_sport_icon(row.get("Sport", "Sport"))
    t1_name = str(row.get("Team 1") or row.get("House 1") or "Unknown").strip()
    t2_name = str(row.get("Team 2") or row.get("House 2") or "Unknown").strip()

    team1 = get_team_meta(t1_name)
    team2 = get_team_meta(t2_name)

    p1 = str(row.get("Participant 1", "TBD")).strip()
    p2 = str(row.get("Participant 2", "TBD")).strip()
    match_label = str(row.get("Match", "Match")).strip()
    venue = str(row.get("Venue", "Arena")).strip()
    date_str = str(row.get("Date", "TBD")).strip()
    stage_str = str(row.get("Stage") or row.get("Time") or "TBD").strip()

    html = (
        f'<div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); '
        f'border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 8px 20px rgba(0,0,0,0.3);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">'
        f'<span style="color: #ffffff; font-weight: 800; font-size: 0.8rem; background: linear-gradient(90deg, #1e40af, #3b82f6); padding: 0.3rem 0.8rem; border-radius: 1rem;">⚡ {icon} {row.get("Sport", "Match")}</span>'
        f'<span style="color: #fbbf24; font-size: 0.8rem; font-weight: 800;">{match_label}</span>'
        f'</div>'
        f'<div style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.75rem;">📅 {date_str} • 🏆 {stage_str} • 📍 {venue}</div>'
        f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;">'
        f'<div style="flex: 1; padding: 0.75rem; border-radius: 0.5rem; background: rgba(255,255,255,0.03); border-left: 4px solid {team1["color"]};">'
        f'<div style="color: #ffffff; font-weight: 800; font-size: 1.05rem;">{p1}</div>'
        f'<div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.15rem;">{team1["emoji"]} {team1["name"]}</div>'
        f'</div>'
        f'<div style="color: #fbbf24; font-weight: 900; font-size: 1rem; font-style: italic;">VS</div>'
        f'<div style="flex: 1; padding: 0.75rem; border-radius: 0.5rem; background: rgba(255,255,255,0.03); border-left: 4px solid {team2["color"]};">'
        f'<div style="color: #ffffff; font-weight: 800; font-size: 1.05rem;">{p2}</div>'
        f'<div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.15rem;">{team2["emoji"]} {team2["name"]}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def main() -> None:
    """Render the streamlined championship home arena."""
    render_top_navigation_bar("Home")

    render_soundcloud_player(
        track_url="https://soundcloud.com/mak-division/the-antidote",
        title="TLOL4 ARENA ANTHEM • The Antidote",
        auto_play=True,
        compact=True,
    )

    config = get_config()
    participants = safe_load(load_participants, PARTICIPANT_COLUMNS)
    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    # --------------------------------------------------
    # MINIMAL 2-TONE STADIUM DISCO HERO BANNER
    # --------------------------------------------------
    st.markdown(
        """
        <style>
        @keyframes discoGoldBlue {
            0% {
                border-color: #fbbf24;
                box-shadow: 0 0 20px rgba(251, 191, 36, 0.45), inset 0 0 15px rgba(59, 130, 246, 0.2);
            }
            50% {
                border-color: #3b82f6;
                box-shadow: 0 0 25px rgba(59, 130, 246, 0.5), inset 0 0 20px rgba(251, 191, 36, 0.25);
            }
            100% {
                border-color: #fbbf24;
                box-shadow: 0 0 20px rgba(251, 191, 36, 0.45), inset 0 0 15px rgba(59, 130, 246, 0.2);
            }
        }

        @keyframes discoFloodlight {
            0% { transform: translateX(-100%) rotate(25deg); opacity: 0; }
            30% { opacity: 0.35; }
            70% { opacity: 0.35; }
            100% { transform: translateX(100%) rotate(25deg); opacity: 0; }
        }

        @keyframes beatGlowOrb {
            0%, 100% { transform: scale(0.9); opacity: 0.3; }
            50% { transform: scale(1.18); opacity: 0.75; }
        }

        .disco-banner {
            position: relative;
            padding: 3.25rem 2rem;
            border-radius: 1.25rem;
            background: linear-gradient(135deg, rgba(11, 19, 43, 0.94), rgba(15, 23, 42, 0.92)), 
                        url('https://images.unsplash.com/photo-1540747737956-3787293a9fc4?q=80&w=2560&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            text-align: center;
            margin-bottom: 1.5rem;
            border: 2px solid #fbbf24;
            overflow: hidden;
            animation: discoGoldBlue 3.2s infinite ease-in-out;
        }

        .disco-sweep-light {
            position: absolute;
            top: -50%;
            left: 0;
            width: 45%;
            height: 200%;
            background: linear-gradient(90deg, transparent 0%, rgba(251, 191, 36, 0.25) 50%, transparent 100%);
            pointer-events: none;
            animation: discoFloodlight 6s infinite ease-in-out;
            filter: blur(10px);
            z-index: 1;
        }

        .disco-orb-left {
            position: absolute;
            top: -30px;
            left: -30px;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.7) 0%, rgba(59, 130, 246, 0) 70%);
            border-radius: 50%;
            pointer-events: none;
            animation: beatGlowOrb 2.8s infinite ease-in-out;
            filter: blur(8px);
            z-index: 1;
        }

        .disco-orb-right {
            position: absolute;
            top: -30px;
            right: -30px;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(251, 191, 36, 0.7) 0%, rgba(251, 191, 36, 0) 70%);
            border-radius: 50%;
            pointer-events: none;
            animation: beatGlowOrb 2.8s infinite ease-in-out 1.4s;
            filter: blur(8px);
            z-index: 1;
        }

        .disco-title {
            margin: 0.8rem 0 0.25rem 0;
            font-weight: 900;
            font-size: 2.85rem;
            letter-spacing: -0.5px;
            text-transform: uppercase;
            color: #ffffff !important;
            text-shadow: 0 0 16px rgba(251, 191, 36, 0.4), 0 2px 8px rgba(0, 0, 0, 0.9);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    banner_html = (
        f'<div class="disco-banner">'
        f'<div class="disco-sweep-light"></div>'
        f'<div class="disco-orb-left"></div>'
        f'<div class="disco-orb-right"></div>'
        f'<div style="position: relative; z-index: 2;">'
        f'<span style="background: rgba(251, 191, 36, 0.15); border: 1px solid #fbbf24; color: #fbbf24 !important; '
        f'font-size: 0.8rem; font-weight: 800; padding: 0.35rem 1.1rem; border-radius: 2rem; '
        f'text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 12px rgba(251, 191, 36, 0.3);">'
        f'🪩 LIVE STADIUM ARENA'
        f'</span>'
        f'<h1 class="disco-title">🏆 {config["app"]["tournament_name"].upper()}</h1>'
        f'<p style="margin: 0.35rem 0 0 0; color: #cbd5e1 !important; font-size: 1.15rem; font-weight: 600; '
        f'letter-spacing: 0.5px; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">'
        f'{config["app"]["tagline"]}'
        f'</p>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # --------------------------------------------------
    # FRANCHISE QUICK ACCESS SQUAD ROOMS
    # --------------------------------------------------
    team_pages_dict = st.session_state.get("team_pages", {})
    teams = config.get("teams", [])

    if teams:
        team_cols = st.columns(len(teams))
        for idx, team in enumerate(teams):
            team_name = team["name"]
            meta = get_team_meta(team_name)
            target_page = team_pages_dict.get(team_name)

            with team_cols[idx]:
                card_html = (
                    f'<div style="background: rgba(15, 23, 42, 0.85); border-top: 4px solid {meta["color"]}; '
                    f'border-left: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1); '
                    f'border-bottom: 1px solid rgba(255,255,255,0.1); border-radius: 0.75rem; padding: 1rem; '
                    f'text-align: center; margin-bottom: 0.4rem; box-shadow: 0 10px 20px rgba(0,0,0,0.3);">'
                    f'<div style="font-size: 2rem; margin-bottom: 0.2rem; filter: drop-shadow(0 0 8px {meta["color"]});">{meta["emoji"]}</div>'
                    f'<div style="color: #ffffff; font-size: 1rem; font-weight: 800;">{team_name}</div>'
                    f'<div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;">👑 Capt: <strong style="color: #ffffff;">{team.get("captain", "TBD")}</strong></div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

                if target_page:
                    st.page_link(
                        target_page,
                        label=f"{team.get('short_name', team_name)} Hub ➔",
                        use_container_width=True,
                    )

    st.markdown("---")

    # --------------------------------------------------
    # STANDINGS BOARD
    # --------------------------------------------------
    st.subheader("🏆 Team Cumulative Standings")
    team_scores = get_team_scores(participants)

    if not team_scores.empty:
        standings_cols = st.columns(len(team_scores))
        for rank, (col, (_, row)) in enumerate(zip(standings_cols, team_scores.iterrows()), start=1):
            with col:
                render_standings_card(row["Team"], row["Points"], rank)

    # --------------------------------------------------
    # BREAKDOWN MATRIX (LIVE SPREADSHEET TABLE)
    # --------------------------------------------------
    if not participants.empty:
        render_points_matrix_table(participants)

    st.markdown("---")

    # --------------------------------------------------
    # SPORT-WISE PLAYOFF & FINALS BRACKET (COLLAPSIBLE)
    # --------------------------------------------------
    TARGET_BRACKET_SPORTS = ["Carrom", "Foosball", "Badminton", "Table Tennis"]

    with st.expander("🎮 Live Sport Knockout Brackets (Click to Expand)", expanded=False):
        st.caption("Select a sport below to inspect its tournament bracket and playoff progression.")

        if not fixtures.empty and "Sport" in fixtures.columns:
            available_target_sports = [
                s for s in TARGET_BRACKET_SPORTS
                if any(fixtures["Sport"].astype(str).str.strip().str.lower() == s.lower())
            ]

            display_sports = available_target_sports if available_target_sports else TARGET_BRACKET_SPORTS

            tab_labels = [f"{get_sport_icon(sport)} {sport}" for sport in display_sports]
            sport_tabs = st.tabs(tab_labels)

            for tab, sport in zip(sport_tabs, display_sports):
                with tab:
                    render_tournament_bracket_for_sport(sport, fixtures)
        else:
            st.info("No fixtures data available to generate brackets.")

    st.markdown("---")

    # --------------------------------------------------
    # UPCOMING ARENA FIXTURES
    # --------------------------------------------------
    st.subheader("⚡ Next Arena Showdowns")
    upcoming = fixtures[fixtures["Status"].astype(str).str.strip().str.lower() == "upcoming"].head(4)

    if upcoming.empty:
        st.info("No upcoming fixtures on the match schedule.")
    else:
        fix_cols = st.columns(2)
        for idx, (_, row) in enumerate(upcoming.iterrows()):
            with fix_cols[idx % 2]:
                render_match_card(row)

    st.markdown("---")

    # --------------------------------------------------
    # FOOTER NAVIGATION
    # --------------------------------------------------
    nav_cols = st.columns(2)
    with nav_cols[0]:
        st.page_link("pages/Fixtures.py", label="📅 View Complete Fixture Schedule", use_container_width=True)
    with nav_cols[1]:
        st.page_link("pages/Leaderboard.py", label="🏅 View Detailed MVP Leaderboard", use_container_width=True)


if __name__ == "__main__":
    main()