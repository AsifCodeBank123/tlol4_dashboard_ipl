"""Championship Arena Home page for the TLOL4 Sports League Dashboard."""

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
    render_arena_anthem,
    render_top_navigation_bar,
    render_tournament_bracket_for_sport,
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


def render_home_styles() -> None:
    """Inject high-energy EDM laser festival and strobe lighting CSS."""
    st.markdown(
        """
        <style>
        /* 1. Fast EDM Bass Strobe & Border Rhythm */
        @keyframes edmBassStrobe {
            0% {
                border-color: #fbbf24;
                box-shadow: 0 0 25px rgba(251, 191, 36, 0.6), inset 0 0 20px rgba(59, 130, 246, 0.35);
            }
            25% {
                border-color: #3b82f6;
                box-shadow: 0 0 35px rgba(59, 130, 246, 0.7), inset 0 0 30px rgba(251, 191, 36, 0.4);
            }
            50% {
                border-color: #ec4899;
                box-shadow: 0 0 40px rgba(236, 72, 153, 0.6), inset 0 0 25px rgba(59, 130, 246, 0.4);
            }
            75% {
                border-color: #10b981;
                box-shadow: 0 0 35px rgba(16, 185, 129, 0.6), inset 0 0 20px rgba(251, 191, 36, 0.35);
            }
            100% {
                border-color: #fbbf24;
                box-shadow: 0 0 25px rgba(251, 191, 36, 0.6), inset 0 0 20px rgba(59, 130, 246, 0.35);
            }
        }

        /* 2. Criss-Cross EDM Laser Beams */
        @keyframes laserSweepLeft {
            0% { transform: translateX(-100%) rotate(35deg); opacity: 0; }
            20% { opacity: 0.65; }
            50% { transform: translateX(100%) rotate(35deg); opacity: 0.7; }
            80% { opacity: 0.65; }
            100% { transform: translateX(200%) rotate(35deg); opacity: 0; }
        }

        @keyframes laserSweepRight {
            0% { transform: translateX(200%) rotate(-35deg); opacity: 0; }
            20% { opacity: 0.65; }
            50% { transform: translateX(0%) rotate(-35deg); opacity: 0.7; }
            80% { opacity: 0.65; }
            100% { transform: translateX(-150%) rotate(-35deg); opacity: 0; }
        }

        /* 3. Fast Subwoofer Bass Orb Pumps */
        @keyframes edmSubOrb {
            0%, 100% { transform: scale(0.85); opacity: 0.3; filter: blur(12px); }
            50% { transform: scale(1.35); opacity: 0.85; filter: blur(6px); }
        }

        /* 4. Neon Equalizer Visualizer Bars */
        @keyframes eqBounce1 { 0%, 100% { height: 12px; } 50% { height: 48px; } }
        @keyframes eqBounce2 { 0%, 100% { height: 36px; } 50% { height: 14px; } }
        @keyframes eqBounce3 { 0%, 100% { height: 22px; } 50% { height: 55px; } }
        @keyframes eqBounce4 { 0%, 100% { height: 46px; } 50% { height: 18px; } }

        .edm-arena-hero {
            position: relative;
            padding: 3.5rem 2rem;
            border-radius: 1.5rem;
            background: radial-gradient(circle at center, rgba(30, 58, 138, 0.45) 0%, rgba(15, 23, 42, 0.96) 80%),
                        url('https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=1280&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            text-align: center;
            margin-bottom: 2rem;
            border: 2.5px solid #fbbf24;
            overflow: hidden;
            animation: edmBassStrobe 1.87s infinite cubic-bezier(0.4, 0, 0.2, 1);
        }

        .laser-beam-1 {
            position: absolute;
            top: -100%;
            left: 0;
            width: 30%;
            height: 300%;
            background: linear-gradient(90deg, transparent 0%, rgba(59, 130, 246, 0.4) 50%, rgba(251, 191, 36, 0.6) 55%, transparent 100%);
            pointer-events: none;
            animation: laserSweepLeft 3.2s infinite ease-in-out;
            filter: blur(8px);
            z-index: 1;
        }

        .laser-beam-2 {
            position: absolute;
            top: -100%;
            right: 0;
            width: 30%;
            height: 300%;
            background: linear-gradient(90deg, transparent 0%, rgba(236, 72, 153, 0.45) 50%, rgba(59, 130, 246, 0.6) 55%, transparent 100%);
            pointer-events: none;
            animation: laserSweepRight 2.6s infinite ease-in-out 0.4s;
            filter: blur(8px);
            z-index: 1;
        }

        .sub-orb-cyan {
            position: absolute;
            top: -40px;
            left: -40px;
            width: 230px;
            height: 230px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.8) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            animation: edmSubOrb 0.94s infinite ease-in-out;
            z-index: 1;
        }

        .sub-orb-gold {
            position: absolute;
            top: -40px;
            right: -40px;
            width: 230px;
            height: 230px;
            background: radial-gradient(circle, rgba(251, 191, 36, 0.8) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            animation: edmSubOrb 0.94s infinite ease-in-out 0.47s;
            z-index: 1;
        }

        .eq-container {
            display: flex;
            align-items: flex-end;
            justify-content: center;
            gap: 6px;
            height: 55px;
            margin-top: 1.2rem;
            position: relative;
            z-index: 2;
        }

        .eq-bar {
            width: 6px;
            border-radius: 3px;
            background: linear-gradient(180deg, #fbbf24 0%, #3b82f6 100%);
            box-shadow: 0 0 10px rgba(251, 191, 36, 0.8);
        }

        .team-hub-card {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(14px);
            border-radius: 1rem;
            padding: 1.15rem 1rem;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            margin-bottom: 0.5rem;
        }
        .team-hub-card:hover { transform: translateY(-4px); }

        .standings-deck-card {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(16px);
            border-radius: 1.15rem;
            padding: 1.35rem 1rem;
            text-align: center;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
            margin-bottom: 1.25rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.25s ease;
        }
        .standings-deck-card:hover { transform: translateY(-4px); }

        .match-plate-container {
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 1.15rem;
            padding: 1.3rem;
            margin-bottom: 1.15rem;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .match-plate-container:hover {
            border-color: rgba(251, 191, 36, 0.5);
            transform: translateY(-3px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

import textwrap

def render_compact_home_podium(participants_df: pd.DataFrame) -> None:
    """Render a space-efficient Top-3 MVP Podium without markdown indent leaks."""
    if participants_df.empty:
        return

    df = participants_df.copy()
    pts = pd.to_numeric(df.get("Points", 0), errors="coerce").fillna(0.0)
    bonus = pd.to_numeric(df.get("Bonus", 0), errors="coerce").fillna(0.0)
    part_pts = pd.to_numeric(df.get("Participation Points", 0), errors="coerce").fillna(0.0)
    df["TotalScore"] = pts + bonus + part_pts

    # Filter out franchise bonus rows (where Participant == Team)
    athletes = df[
        df["Participant"].astype(str).str.strip().str.casefold()
        != df["Team"].astype(str).str.strip().str.casefold()
    ].copy()

    if athletes.empty:
        return

    top3 = (
        athletes.groupby(["Participant", "Team"], as_index=False)["TotalScore"]
        .sum()
        .sort_values(by="TotalScore", ascending=False)
        .head(3)
        .reset_index(drop=True)
    )

    if len(top3) < 3:
        return

    first = top3.iloc[0]
    second = top3.iloc[1]
    third = top3.iloc[2]

    m1 = get_team_meta(first["Team"])
    m2 = get_team_meta(second["Team"])
    m3 = get_team_meta(third["Team"])

    # Using textwrap.dedent and zero indentation prevents the 4-space code block bug
    podium_html = textwrap.dedent(f"""
<style>
.mini-podium-shelf {{
    display: grid;
    grid-template-columns: 1fr 1.08fr 1fr;
    gap: 0.75rem;
    align-items: flex-end;
    margin: 0.5rem 0 1.25rem 0;
}}
.mini-pedestal {{
    background: rgba(15, 23, 42, 0.9);
    border-radius: 0.85rem;
    padding: 0.85rem 0.6rem;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}}
.pedestal-first {{
    border: 1.5px solid #fbbf24;
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
    box-shadow: 0 0 20px rgba(251, 191, 36, 0.35);
    padding: 1.1rem 0.6rem;
}}
.pedestal-second {{
    border: 1px solid #94a3b8;
}}
.pedestal-third {{
    border: 1px solid #b45309;
}}
</style>
<div class="mini-podium-shelf">
<div class="mini-pedestal pedestal-second">
<div style="font-size: 1.4rem;">🥈</div>
<div style="color: #94a3b8; font-size: 0.65rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;">RANK #2</div>
<div style="color: #ffffff; font-weight: 900; font-size: 1.05rem; margin: 0.15rem 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{second["Participant"]}</div>
<div style="color: {m2['color']}; font-size: 0.72rem; font-weight: 700;">{m2['emoji']} {m2['short_name']}</div>
<div style="color: #ffffff; font-weight: 900; font-size: 1.35rem; margin-top: 0.3rem;">{format_points(second["TotalScore"])} <span style="font-size: 0.7rem; color: #94a3b8;">PTS</span></div>
</div>
<div class="mini-pedestal pedestal-first">
<div style="font-size: 1.8rem; filter: drop-shadow(0 0 8px #fbbf24);">👑</div>
<div style="color: #fbbf24; font-size: 0.7rem; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase;">LEAGUE MVP</div>
<div style="color: #ffffff; font-weight: 900; font-size: 1.25rem; margin: 0.2rem 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{first["Participant"]}</div>
<div style="color: {m1['color']}; font-size: 0.75rem; font-weight: 800;">{m1['emoji']} {m1['short_name']}</div>
<div style="color: #fbbf24; font-weight: 900; font-size: 1.65rem; margin-top: 0.35rem; text-shadow: 0 0 10px rgba(251,191,36,0.4);">{format_points(first["TotalScore"])} <span style="font-size: 0.75rem; color: #cbd5e1;">PTS</span></div>
</div>
<div class="mini-pedestal pedestal-third">
<div style="font-size: 1.4rem;">🥉</div>
<div style="color: #b45309; font-size: 0.65rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;">RANK #3</div>
<div style="color: #ffffff; font-weight: 900; font-size: 1.05rem; margin: 0.15rem 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{third["Participant"]}</div>
<div style="color: {m3['color']}; font-size: 0.72rem; font-weight: 700;">{m3['emoji']} {m3['short_name']}</div>
<div style="color: #ffffff; font-weight: 900; font-size: 1.35rem; margin-top: 0.3rem;">{format_points(third["TotalScore"])} <span style="font-size: 0.7rem; color: #94a3b8;">PTS</span></div>
</div>
</div>
""").strip()

    st.subheader("🥇 Top Individual MVPs")
    st.markdown(podium_html, unsafe_allow_html=True)

def render_standings_card(team_name: str, points: float, rank: int) -> None:
    """Render an IPL-styled championship standings card."""
    meta = get_team_meta(team_name)
    is_leader = rank == 1

    if is_leader:
        border_style = "border: 2px solid #fbbf24; border-top: 6px solid #fbbf24; box-shadow: 0 0 25px rgba(251, 191, 36, 0.4);"
        badge_html = '<span style="background: linear-gradient(90deg, #d97706, #fbbf24); color: #000000; font-weight: 900; font-size: 0.75rem; padding: 0.25rem 0.8rem; border-radius: 1rem; letter-spacing: 1px;">👑 LEAGUE LEADER</span>'
    else:
        border_style = f"border: 1px solid rgba(255, 255, 255, 0.12); border-top: 5px solid {meta['color']};"
        badge_html = f'<span style="background: rgba(255, 255, 255, 0.08); color: #cbd5e1; font-weight: 800; font-size: 0.75rem; padding: 0.25rem 0.75rem; border-radius: 1rem; letter-spacing: 1px;">RANK #{rank}</span>'

    card_html = (
        f'<div class="standings-deck-card" style="{border_style}">'
        f'<div style="font-size: 2.35rem; margin-bottom: 0.3rem; filter: drop-shadow(0 0 10px {meta["color"]});">{meta["emoji"]}</div>'
        f'<div style="color: #ffffff; font-size: 1.15rem; font-weight: 900; letter-spacing: -0.3px;">{team_name}</div>'
        f'<div style="color: #fbbf24; font-size: 1.95rem; font-weight: 900; margin: 0.25rem 0; letter-spacing: -0.5px;">'
        f'{format_points(points)} <span style="font-size: 0.85rem; color: #64748b; font-weight: 700;">PTS</span>'
        f'</div>'
        f'<div style="margin-top: 0.6rem;">{badge_html}</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_match_card(row: pd.Series) -> None:
    """Render a television broadcast-style head-to-head encounter card."""
    sport_label = str(row.get("Sport", "Match")).strip()
    icon = get_sport_icon(sport_label)

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

    plate_html = (
        f'<div class="match-plate-container">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">'
        f'<span style="color: #ffffff; font-weight: 800; font-size: 0.8rem; background: linear-gradient(90deg, #1e40af, #3b82f6); padding: 0.3rem 0.85rem; border-radius: 1rem; letter-spacing: 0.5px;">'
        f'⚡ {icon} {sport_label}'
        f'</span>'
        f'<span style="color: #fbbf24; font-size: 0.82rem; font-weight: 800; letter-spacing: 0.5px;">{match_label}</span>'
        f'</div>'
        f'<div style="color: #94a3b8; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.85rem;">'
        f'📅 {date_str} &nbsp;•&nbsp; 🏆 {stage_str} &nbsp;•&nbsp; 📍 {venue}'
        f'</div>'
        f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;">'
        # Player 1 Plate
        f'<div style="flex: 1; padding: 0.85rem; border-radius: 0.6rem; background: rgba(255, 255, 255, 0.03); border-left: 4px solid {team1["color"]};">'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.05rem;">{p1}</div>'
        f'<div style="color: #94a3b8; font-size: 0.78rem; margin-top: 0.2rem; font-weight: 600;">{team1["emoji"]} {team1["short_name"]}</div>'
        f'</div>'
        # VS Badge
        f'<div style="color: #fbbf24; font-weight: 900; font-size: 1.15rem; font-style: italic; text-shadow: 0 0 10px rgba(251, 191, 36, 0.4);">VS</div>'
        # Player 2 Plate
        f'<div style="flex: 1; padding: 0.85rem; border-radius: 0.6rem; background: rgba(255, 255, 255, 0.03); border-left: 4px solid {team2["color"]};">'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.05rem;">{p2}</div>'
        f'<div style="color: #94a3b8; font-size: 0.78rem; margin-top: 0.2rem; font-weight: 600;">{team2["emoji"]} {team2["short_name"]}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(plate_html, unsafe_allow_html=True)


def main() -> None:
    render_top_navigation_bar("Home")
    render_home_styles()

    # 🎺 Official IPL Arena Background Anthem
    render_arena_anthem(
        video_id="yq3SedbPF08",
        title="TLOL4 ARENA • IPL Stadium Theme Anthem",
    )

    config = get_config()
    participants = safe_load(load_participants, PARTICIPANT_COLUMNS)
    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    # --------------------------------------------------
    # 1. 2-TONE STADIUM DISCO HERO BANNER
    # --------------------------------------------------
    # --------------------------------------------------
    # EDM LASER STROBE HERO BANNER
    # --------------------------------------------------
    banner_html = (
        f'<div class="edm-arena-hero">'
        f'<div class="laser-beam-1"></div>'
        f'<div class="laser-beam-2"></div>'
        f'<div class="sub-orb-cyan"></div>'
        f'<div class="sub-orb-gold"></div>'
        f'<div style="position: relative; z-index: 2;">'
        f'<span style="background: rgba(251, 191, 36, 0.2); border: 1.5px solid #fbbf24; color: #fbbf24 !important; '
        f'font-size: 0.82rem; font-weight: 900; padding: 0.4rem 1.3rem; border-radius: 2rem; '
        f'text-transform: uppercase; letter-spacing: 2.5px; box-shadow: 0 0 18px rgba(251, 191, 36, 0.6);">'
        f'⚡ LIVE EDM STADIUM FESTIVAL'
        f'</span>'
        f'<h1 style="color: #ffffff; font-weight: 900; font-size: 3rem; margin: 0.85rem 0 0.3rem 0; '
        f'text-transform: uppercase; letter-spacing: -0.5px; text-shadow: 0 0 25px rgba(251, 191, 36, 0.55), 0 3px 12px rgba(0,0,0,0.9);">'
        f'🏆 {config["app"]["tournament_name"].upper()}'
        f'</h1>'
        f'<p style="color: #e2e8f0; font-size: 1.15rem; font-weight: 700; margin: 0; letter-spacing: 0.5px; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">'
        f'{config["app"]["tagline"]}'
        f'</p>'
        # Animated Audio Equalizer Bars matching the EDM Beat
        f'<div class="eq-container">'
        f'<div class="eq-bar" style="animation: eqBounce1 0.45s infinite ease-in-out;"></div>'
        f'<div class="eq-bar" style="animation: eqBounce3 0.6s infinite ease-in-out 0.1s;"></div>'
        f'<div class="eq-bar" style="animation: eqBounce2 0.38s infinite ease-in-out 0.2s;"></div>'
        f'<div class="eq-bar" style="animation: eqBounce4 0.52s infinite ease-in-out 0.05s;"></div>'
        f'<div class="eq-bar" style="animation: eqBounce1 0.48s infinite ease-in-out 0.15s;"></div>'
        f'<div class="eq-bar" style="animation: eqBounce3 0.42s infinite ease-in-out 0.25s;"></div>'
        f'<div class="eq-bar" style="animation: eqBounce2 0.55s infinite ease-in-out 0.3s;"></div>'
        f'<div class="eq-bar" style="animation: eqBounce4 0.39s infinite ease-in-out 0.12s;"></div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # --------------------------------------------------
    # 2. FRANCHISE SQUAD COMMAND ROOMS
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
                    f'<div class="team-hub-card" style="border-top: 4px solid {meta["color"]};">'
                    f'<div style="font-size: 2.1rem; margin-bottom: 0.2rem; filter: drop-shadow(0 0 10px {meta["color"]});">{meta["emoji"]}</div>'
                    f'<div style="color: #ffffff; font-size: 1.05rem; font-weight: 900;">{team_name}</div>'
                    f'<div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.3rem;">👑 Capt: <strong style="color: #ffffff;">{team.get("captain", "TBD")}</strong></div>'
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
    # 3. CUMULATIVE TEAM STANDINGS DECK
    # --------------------------------------------------
    st.subheader("🏆 Championship Standings Deck")
    team_scores = get_team_scores(participants)

    if not team_scores.empty:
        standings_cols = st.columns(len(team_scores))
        for rank, (col, (_, row)) in enumerate(zip(standings_cols, team_scores.iterrows()), start=1):
            with col:
                render_standings_card(row["Team"], row["Points"], rank)

    st.markdown("---")
    
    # --------------------------------------------------
    # 4. COMPACT TOP-3 MVP PODIUM (NEW SECTION)
    # --------------------------------------------------
    render_compact_home_podium(participants)

    st.markdown("---")

    # --------------------------------------------------
    # 5. MULTI-SPORT POINTS BREAKDOWN MATRIX
    # --------------------------------------------------
    if not participants.empty:
        render_points_matrix_table(participants)
    # --------------------------------------------------

    st.markdown("---")

    # --------------------------------------------------
    # 6. SPORT-WISE PLAYOFF & FINALS BRACKET (COLLAPSIBLE)
    # --------------------------------------------------
    TARGET_BRACKET_SPORTS = ["Carrom", "Foosball", "Badminton", "Table Tennis"]

    with st.expander("🎮 Live Tournament Progression & Brackets (Click to Inspect)", expanded=False):
        st.caption("Select a sport below to review stage-by-stage progression or group stage ladders.")

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
            st.info("No fixture records found to construct championship brackets.")

    st.markdown("---")

    # --------------------------------------------------
    # 7. UPCOMING ARENA FIXTURES
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
    # 8. QUICK DISPATCH FOOTER NAVIGATION
    # --------------------------------------------------
    nav_cols = st.columns(2)
    with nav_cols[0]:
        st.page_link("pages/Fixtures.py", label="📅 View Complete Match Schedule", use_container_width=True)
    with nav_cols[1]:
        st.page_link("pages/Leaderboard.py", label="🏅 View Detailed MVP Leaderboard", use_container_width=True)


if __name__ == "__main__":
    main()