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
    inject_stadium_audio,
    render_soundcloud_player,
    load_fixtures,
    load_participants,
    render_points_matrix_table,
    safe_load,
    render_top_navigation_bar
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
    time_str = str(row.get("Time", "TBD")).strip()

    html = (
        f'<div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); '
        f'border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 8px 20px rgba(0,0,0,0.3);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">'
        f'<span style="color: #ffffff; font-weight: 800; font-size: 0.8rem; background: linear-gradient(90deg, #1e40af, #3b82f6); padding: 0.3rem 0.8rem; border-radius: 1rem;">⚡ {icon} {row.get("Sport", "Match")}</span>'
        f'<span style="color: #fbbf24; font-size: 0.8rem; font-weight: 800;">{match_label}</span>'
        f'</div>'
        f'<div style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.75rem;">📅 {date_str} • 🕒 {time_str} • 📍 {venue}</div>'
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
    #inject_stadium_audio()

    # Embed your SoundCloud track
    render_soundcloud_player(
        track_url="https://soundcloud.com/mak-division/the-antidote",
        title="TLOL4 ARENA ANTHEM • The Antidote",
        auto_play=True,  # Set to True if you want it to trigger on load
        compact=True,     # Compact slim player (80px)
    )

    config = get_config()
    participants = safe_load(load_participants, PARTICIPANT_COLUMNS)
    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    # --------------------------------------------------
    # STADIUM DISCO & LASER HERO BANNER
    # --------------------------------------------------
    st.markdown(
        """
        <style>
        @keyframes discoAura {
            0% {
                border-color: #fbbf24;
                box-shadow: 0 0 25px rgba(251, 191, 36, 0.6), inset 0 0 20px rgba(59, 130, 246, 0.4);
            }
            25% {
                border-color: #ec4899;
                box-shadow: 0 0 35px rgba(236, 72, 153, 0.8), inset 0 0 25px rgba(251, 191, 36, 0.4);
            }
            50% {
                border-color: #8b5cf6;
                box-shadow: 0 0 45px rgba(139, 92, 246, 0.9), inset 0 0 30px rgba(16, 185, 129, 0.5);
            }
            75% {
                border-color: #06b6d4;
                box-shadow: 0 0 35px rgba(6, 182, 212, 0.8), inset 0 0 25px rgba(236, 72, 153, 0.4);
            }
            100% {
                border-color: #fbbf24;
                box-shadow: 0 0 25px rgba(251, 191, 36, 0.6), inset 0 0 20px rgba(59, 130, 246, 0.4);
            }
        }

        @keyframes laserSweep1 {
            0% { transform: rotate(-35deg) translateX(-120%); opacity: 0.2; }
            50% { transform: rotate(15deg) translateX(120%); opacity: 0.85; }
            100% { transform: rotate(-35deg) translateX(-120%); opacity: 0.2; }
        }

        @keyframes laserSweep2 {
            0% { transform: rotate(35deg) translateX(120%); opacity: 0.3; }
            50% { transform: rotate(-20deg) translateX(-120%); opacity: 0.9; }
            100% { transform: rotate(35deg) translateX(120%); opacity: 0.3; }
        }

        @keyframes strobePulse {
            0%, 100% { opacity: 0.3; transform: scale(0.9); }
            20% { opacity: 1; transform: scale(1.35) rotate(15deg); }
            40% { opacity: 0.4; transform: scale(0.95); }
            60% { opacity: 0.95; transform: scale(1.25) rotate(-10deg); }
            80% { opacity: 0.2; transform: scale(0.85); }
        }

        @keyframes discoTextShine {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .disco-banner-container {
            position: relative;
            padding: 3.5rem 2rem;
            border-radius: 1.5rem;
            background: linear-gradient(135deg, rgba(10, 15, 30, 0.95), rgba(20, 10, 40, 0.92)), 
                        url('https://images.unsplash.com/photo-1540747737956-3787293a9fc4?q=80&w=2560&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            text-align: center;
            margin-bottom: 1.5rem;
            border: 2.5px solid #fbbf24;
            overflow: hidden;
            animation: discoAura 3s infinite ease-in-out;
        }

        .laser-beam-1 {
            position: absolute;
            top: -50%;
            left: -20%;
            width: 40%;
            height: 200%;
            background: linear-gradient(90deg, rgba(236,72,153,0) 0%, rgba(236,72,153,0.4) 50%, rgba(251,191,36,0.6) 100%);
            pointer-events: none;
            animation: laserSweep1 4.5s infinite ease-in-out;
            filter: blur(12px);
            z-index: 1;
        }

        .laser-beam-2 {
            position: absolute;
            top: -50%;
            right: -20%;
            width: 35%;
            height: 200%;
            background: linear-gradient(90deg, rgba(6,182,212,0.6) 0%, rgba(139,92,246,0.4) 50%, rgba(6,182,212,0) 100%);
            pointer-events: none;
            animation: laserSweep2 5.2s infinite ease-in-out;
            filter: blur(14px);
            z-index: 1;
        }

        .strobe-orb-left {
            position: absolute;
            top: -40px;
            left: -40px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(236,72,153,0.7) 40%, rgba(0,0,0,0) 75%);
            border-radius: 50%;
            pointer-events: none;
            animation: strobePulse 1.8s infinite ease-in-out;
            filter: blur(8px);
            z-index: 1;
        }

        .strobe-orb-right {
            position: absolute;
            top: -40px;
            right: -40px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(6,182,212,0.8) 40%, rgba(0,0,0,0) 75%);
            border-radius: 50%;
            pointer-events: none;
            animation: strobePulse 2.3s infinite ease-in-out;
            filter: blur(8px);
            z-index: 1;
        }

        .disco-title {
            margin: 0.85rem 0 0.25rem 0;
            font-weight: 900;
            font-size: 3rem;
            letter-spacing: -1px;
            text-transform: uppercase;
            background: linear-gradient(90deg, #ffffff, #fbbf24, #ec4899, #60a5fa, #ffffff);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: discoTextShine 4s linear infinite;
            filter: drop-shadow(0 0 15px rgba(251,191,36,0.5));
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    banner_html = (
        f'<div class="disco-banner-container">'
        f'<div class="laser-beam-1"></div>'
        f'<div class="laser-beam-2"></div>'
        f'<div class="strobe-orb-left"></div>'
        f'<div class="strobe-orb-right"></div>'
        f'<div style="position: relative; z-index: 2;">'
        f'<span style="background: linear-gradient(90deg, #ec4899, #fbbf24, #06b6d4); color: #0f172a !important; '
        f'font-size: 0.85rem; font-weight: 900; padding: 0.4rem 1.4rem; border-radius: 2rem; '
        f'text-transform: uppercase; letter-spacing: 2.5px; box-shadow: 0 0 20px rgba(236,72,153,0.7);">'
        f'🏟️ OFFICIAL TOURNAMENT HUB'
        f'</span>'
        f'<h1 class="disco-title">🏆 {config["app"]["tournament_name"].upper()}</h1>'
        f'<p style="margin: 0.4rem 0 0 0; color: #e2e8f0 !important; font-size: 1.2rem; font-weight: 700; '
        f'letter-spacing: 0.5px; text-shadow: 0 2px 10px rgba(0,0,0,0.9);">'
        f'✨ {config["app"]["tagline"]}'
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

    # # --------------------------------------------------
    # # LIVE KNOCKOUT FINALS ARENA BRACKET (BLEED-PROOF)
    # # --------------------------------------------------
    # finals_bracket_html = (
    #     '<div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 138, 0.7)); '
    #     'border: 2px solid #fbbf24; border-radius: 1.25rem; padding: 1.5rem; margin-bottom: 2rem; '
    #     'box-shadow: 0 10px 30px rgba(0,0,0,0.5);">'
    #     '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">'
    #     '<span style="color: #fbbf24; font-size: 1.05rem; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;">'
    #     '🎮 OLD SCHOOL GAMES: FINALS BRACKET & STAKES'
    #     '</span>'
    #     '<span style="background: #dc2626; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 800;">'
    #     'LIVE ROUND 2'
    #     '</span>'
    #     '</div>'
    #     '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem;">'
    #     '<div style="background: rgba(255,255,255,0.03); border: 1px solid #fbbf24; border-radius: 0.85rem; padding: 1rem; text-align: center;">'
    #     '<div style="color: #fbbf24; font-size: 0.85rem; font-weight: 900; margin-bottom: 0.25rem;">'
    #     '🏆 GRAND CHAMPIONSHIP FINAL'
    #     '</div>'
    #     '<div style="color: #ffffff; font-size: 1.1rem; font-weight: 800; margin: 0.4rem 0;">'
    #     '👑 Royal Challengers of Bhagyashree <br>'
    #     '<span style="color: #fbbf24; font-size: 0.85rem; font-style: italic;">VS</span><br>'
    #     '⚔️ Komal Knight Riders'
    #     '</div>'
    #     '<div style="background: rgba(251, 191, 36, 0.15); border-radius: 0.4rem; padding: 0.35rem; color: #fde68a; font-size: 0.75rem; font-weight: 700; margin-top: 0.5rem;">'
    #     '🥇 Winner: 1000 PTS • 🥈 Runner-Up: 500 PTS'
    #     '</div>'
    #     '</div>'
    #     '<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.15); border-radius: 0.85rem; padding: 1rem; text-align: center;">'
    #     '<div style="color: #94a3b8; font-size: 0.85rem; font-weight: 900; margin-bottom: 0.25rem;">'
    #     '🥉 3RD PLACE PLAYOFF'
    #     '</div>'
    #     '<div style="color: #ffffff; font-size: 1.1rem; font-weight: 800; margin: 0.4rem 0;">'
    #     '🌀 Gayatri Indians <br>'
    #     '<span style="color: #94a3b8; font-size: 0.85rem; font-style: italic;">VS</span><br>'
    #     '🦁 Pooja Super Kings'
    #     '</div>'
    #     '<div style="background: rgba(255, 255, 255, 0.05); border-radius: 0.4rem; padding: 0.35rem; color: #cbd5e1; font-size: 0.75rem; font-weight: 700; margin-top: 0.5rem;">'
    #     '🥉 Winner: 250 PTS • 4th Place: 0 PTS'
    #     '</div>'
    #     '</div>'
    #     '</div>'
    #     '</div>'
    # )
    # st.markdown(finals_bracket_html, unsafe_allow_html=True)

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