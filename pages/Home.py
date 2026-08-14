"""Home page for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

import streamlit as st

from utils import (
    format_points,
    get_config,
    get_last_refresh_label,
    get_sport_icon,
    get_team_meta,
    get_team_scores,
    load_fixtures,
    load_participants,
    safe_load,
    inject_stadium_audio,
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


def render_card(label: str, value: str, detail: str = "") -> None:
    """Render a reusable dashboard card with neon glow effects."""
    st.markdown(
        f"""
        <div class="dashboard-card" style="
            background: rgba(11, 19, 43, 0.7) !important;
            backdrop-filter: blur(16px);
            border: 1px solid rgba(59, 130, 246, 0.4) !important;
            border-radius: 1.25rem;
            padding: 1.5rem;
            margin-bottom: 0.5rem;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        ">
            <div style="color: #94a3b8 !important; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
            <div style="color: #ffffff !important; font-size: 2.2rem; font-weight: 900; margin: 0.4rem 0; text-shadow: 0 0 10px rgba(255,255,255,0.3);">{value}</div>
            <div style="color: #fbbf24 !important; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_team_card(team: str, points: float, rank: int | None = None) -> None:
    """Render one premium team standings badge card with stadium pulse overlay."""
    meta = get_team_meta(team)
    rank_text = f"RANK #{rank}" if rank else "TEAM POINTS"
    
    st.markdown(
        f"""
        <div class="team-card dynamic-pulse" style="
            background: rgba(11, 19, 43, 0.8) !important;
            backdrop-filter: blur(16px);
            border-left: 6px solid {meta['color']} !important;
            border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        ">
            <div style="color: #ffffff !important; font-size: 1.3rem; font-weight: 800; display: flex; align-items: center; gap: 0.6rem;">
                <span style="filter: drop-shadow(0 0 4px {meta['color']});">{meta['emoji']}</span> {team}
            </div>
            <div style="color: #ffffff !important; font-size: 1.8rem; font-weight: 900; margin-top: 0.5rem; letter-spacing: -0.5px;">
                {format_points(points)} <span style="font-size: 1rem; color: #64748b; font-weight: 500;">PTS</span>
            </div>
            <div style="color: {meta['color']} !important; font-size: 0.8rem; font-weight: 800; letter-spacing: 1px; margin-top: 0.5rem; text-transform: uppercase;">{rank_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upcoming_card(row) -> None:
    """Render a flat, code-bleed proof match day card layout."""
    icon = get_sport_icon(row["Sport"])
    team1 = get_team_meta(row["Team 1"])
    team2 = get_team_meta(row["Team 2"])
    
    html = (
        f'<div class="upcoming-card dynamic-pulse" style="background: rgba(15, 23, 42, 0.85) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 1.25rem; padding: 1.5rem; box-shadow: 0 20px 40px rgba(0,0,0,0.4); margin-bottom: 1rem; transition: all 0.3s ease;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">'
        f'<span class="sport-badge" style="color: #ffffff !important; font-weight: 800; background: linear-gradient(90deg, #1e40af, #3b82f6); padding: 0.4rem 1rem; border-radius: 2rem; font-size: 0.8rem; border: 1px solid #60a5fa; box-shadow: 0 0 10px rgba(59,130,246,0.4);">⚡ {icon} {row["Sport"]}</span>'
        f'<span style="color: #fbbf24 !important; font-size: 0.85rem; font-weight: 800; letter-spacing: 1px; text-shadow: 0 0 8px rgba(251,191,36,0.3);">MATCH {row["Match"]}</span>'
        f'</div>'
        f'<div style="color: #94a3b8 !important; font-size: 0.95rem; font-weight: 600; margin-bottom: 1.25rem;">📅 {row["Date"]} • 🕒 {row["Time"]}</div>'
        f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin: 1rem 0;">'
        f'<div style="flex: 1; padding: 1rem; border-radius: 0.75rem; background: rgba(255,255,255,0.03); border-left: 5px solid {team1["color"]}; box-shadow: inset 0 1px 2px rgba(255,255,255,0.05);">'
        f'<div style="color: #ffffff !important; font-weight: 800; font-size: 1.2rem;">{row["Participant 1"]}</div>'
        f'<div style="color: #94a3b8 !important; font-size: 0.85rem; margin-top: 0.25rem; font-weight: 600;">{team1["emoji"]} {row["Team 1"]}</div>'
        f'</div>'
        f'<div style="color: #fbbf24 !important; font-weight: 900; font-size: 1.2rem; font-style: italic; animation: neonBlink 2s infinite alternate; text-shadow: 0 0 10px #fbbf24;">VS</div>'
        f'<div style="flex: 1; padding: 1rem; border-radius: 0.75rem; background: rgba(255,255,255,0.03); border-left: 5px solid {team2["color"]}; box-shadow: inset 0 1px 2px rgba(255,255,255,0.05);">'
        f'<div style="color: #ffffff !important; font-weight: 800; font-size: 1.2rem;">{row["Participant 2"]}</div>'
        f'<div style="color: #94a3b8 !important; font-size: 0.85rem; margin-top: 0.25rem; font-weight: 600;">{team2["emoji"]} {row["Team 2"]}</div>'
        f'</div>'
        f'</div>'
        f'<div style="color: #64748b !important; font-size: 0.85rem; font-weight: 600; margin-top: 1rem; display: flex; align-items: center; gap: 0.3rem;">📍 Stadium Venue: {row["Venue"]}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

# --------------------------------------------------
    # HIGH-VOLTAGE GRAPHICS & FLOODLIGHT ENGINE
    # --------------------------------------------------
    st.markdown(
        """
        <style>
        /* Immersive Dark Arena Backdrop */
        .stApp {
            background-image: linear-gradient(rgba(6, 9, 22, 0.85), rgba(4, 6, 14, 0.98)), 
                              url('https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2560&auto=format&fit=crop');
            background-size: cover;
            background-attachment: fixed;
            background-position: center top;
        }

        /* Keyframe 1: High-Speed Stadium Strobe / Flashing Lights */
        @keyframes floodlightFlash {
            0%, 100% { opacity: 0.3; transform: scale(1) rotate(0deg); }
            20% { opacity: 0.95; transform: scale(1.1) rotate(2deg); }
            40% { opacity: 0.4; transform: scale(0.98) rotate(-1deg); }
            60% { opacity: 1; transform: scale(1.15) rotate(3deg); }
            80% { opacity: 0.5; transform: scale(1.02) rotate(-2deg); }
        }

        /* Keyframe 2: Sweeping Stadium Beam Scan */
        @keyframes lightSweep {
            0% { transform: translateX(-100%) rotate(25deg); }
            50% { transform: translateX(100%) rotate(25deg); }
            100% { transform: translateX(-100%) rotate(25deg); }
        }

        /* Keyframe 3: Pulsing Neon Golden Border Glow */
        @keyframes neonPulse {
            0% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.4), inset 0 0 15px rgba(251, 191, 36, 0.2); }
            50% { box-shadow: 0 0 45px rgba(251, 191, 36, 0.7), inset 0 0 30px rgba(59, 130, 246, 0.4); }
            100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.4), inset 0 0 15px rgba(251, 191, 36, 0.2); }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def main() -> None:
    """Render the high-voltage interactive home page."""
    inject_stadium_audio()
    config = get_config()
    participants = safe_load(load_participants, PARTICIPANT_COLUMNS)
    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    # --------------------------------------------------
    # HIGH-VOLTAGE GRAPHICS ENGINE (CSS INJECTION)
    # --------------------------------------------------
    st.markdown(
        """
        <style>
        /* Immersive High-Res Stadium Backdrop */
        .stApp {
            background-image: linear-gradient(rgba(6, 9, 22, 0.82), rgba(4, 6, 14, 0.97)), 
                              url('https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2560&auto=format&fit=crop');
            background-size: cover;
            background-attachment: fixed;
            background-position: center top;
        }
        
        /* Global Typography Shimmers */
        h1, h2, h3, span, p, label {
            color: #ffffff !important;
            font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
        }

        /* Card Hover Animations & Scale Matrix */
        .dashboard-card:hover, .team-card:hover, .upcoming-card:hover {
            transform: translateY(-6px) scale(1.02);
            border-color: #fbbf24 !important;
            box-shadow: 0 20px 30px rgba(251, 191, 36, 0.15) !important;
        }

        /* Global Widget Custom Navigation Overrides (Fancy Links) */
        .stPageLink a {
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 0.75rem !important;
            padding: 0.75rem 1.2rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(59,130,246,0.2) !important;
        }
        .stPageLink a:hover {
            transform: scale(1.04) !important;
            border-color: #fbbf24 !important;
            box-shadow: 0 0 15px rgba(251, 191, 36, 0.4) !important;
        }

        /* Custom Keyframe Effects Matrices */
        @keyframes sweep {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes neonBlink {
            0% { opacity: 0.6; text-shadow: 0 0 5px #fbbf24; }
            100% { opacity: 1; text-shadow: 0 0 15px #fbbf24, 0 0 25px #f59e0b; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------
    # BROADCAST HERO AREA (FLATTENED TO PREVENT TEXT BLEED)
    # --------------------------------------------------
    # Combined into a strict concatenated string format with zero inner lines or tabs to prevent markdown parser leaks
    # --------------------------------------------------
    # BROADCAST HERO AREA (WITH DYNAMIC FLOODLIGHT ENGINE)
    # --------------------------------------------------
    hero_html = (
        f'<div class="hero-banner" style="position: relative; padding: 4.5rem 2.5rem; border-radius: 1.5rem; background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 138, 0.9)), url(\'https://images.unsplash.com/photo-1540747737956-3787293a9fc4?q=80&w=2560&auto=format&fit=crop\'); background-size: cover; background-position: center; color: white; margin-bottom: 2.5rem; border: 2px solid #fbbf24; overflow: hidden; animation: neonPulse 4s infinite ease-in-out;">'
        # Left Floodlight Tower (Flashing Beam)
        f'<div style="position: absolute; top: -30px; left: -30px; width: 250px; height: 250px; background: radial-gradient(circle, rgba(255,255,255,0.95) 0%, rgba(59,130,246,0.6) 35%, rgba(0,0,0,0) 70%); border-radius: 50%; pointer-events: none; animation: floodlightFlash 2.5s infinite alternate ease-in-out; filter: blur(10px); z-index: 1;"></div>'
        # Right Floodlight Tower (Flashing Beam)
        f'<div style="position: absolute; top: -30px; right: -30px; width: 250px; height: 250px; background: radial-gradient(circle, rgba(255,255,255,0.95) 0%, rgba(251,191,36,0.6) 35%, rgba(0,0,0,0) 70%); border-radius: 50%; pointer-events: none; animation: floodlightFlash 3.2s infinite alternate ease-in-out; filter: blur(10px); z-index: 1;"></div>'
        # Sweeping Light Beam overlay across the banner
        f'<div style="position: absolute; top: -100%; left: 0; width: 50%; height: 300%; background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.25) 50%, rgba(255,255,255,0) 100%); pointer-events: none; animation: lightSweep 7s infinite ease-in-out; z-index: 1;"></div>'
        # Foreground Content Container
        f'<div style="position: relative; z-index: 2; text-align: center;">'
        f'<span style="background: linear-gradient(90deg, #fbbf24, #f59e0b); color: #0f172a !important; font-size: 0.85rem; font-weight: 900; padding: 0.4rem 1.25rem; border-radius: 2rem; text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 15px rgba(251,191,36,0.6);">🏟️ WELCOME TO THE ARENA</span>'
        f'<h1 style="margin: 1rem 0 0.25rem 0; color: #ffffff !important; font-weight: 900; font-size: 3.2rem; letter-spacing: -1px; text-shadow: 0 0 20px rgba(0,0,0,0.9), 0 0 10px rgba(255,255,255,0.5); text-transform: uppercase;">🏆 {config["app"]["tournament_name"].upper()}</h1>'
        f'<p style="margin: 0.5rem 0 0 0; color: #cbd5e1 !important; font-size: 1.3rem; font-weight: 600; letter-spacing: 0.5px; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">{config["app"]["tagline"]}</p>'
        f'</div>'
        f'</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)
    

    # --------------------------------------------------
    # PERFORMANCE TILES
    # --------------------------------------------------
    total_participants = len(participants)
    total_fixtures = len(fixtures)
    total_sports = participants["Sport"].nunique() if not participants.empty else 0
    completed_count = 0 if fixtures.empty else len(fixtures[fixtures["Status"].str.lower() == "completed"])

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_card("Squad Size", str(total_participants), "Registered Athletes")
    with metric_cols[1]:
        render_card("Match Count", str(total_fixtures), f"{completed_count} Fixtures Done")
    with metric_cols[2]:
        render_card("Tournaments", str(total_sports), "Active Disciplines")
    with metric_cols[3]:
        render_card("Sync Engine", get_last_refresh_label(), "Google Sheets Live")

    st.markdown("---")

    # --------------------------------------------------
    # STANDINGS BOARD
    # --------------------------------------------------
    st.subheader("🏏 IPL Official Points Table")
    team_scores = get_team_scores(participants)

    if team_scores.empty:
        st.info("No team scores available yet.")
    else:
        team_cols = st.columns(4)
        for rank, (col, (_, row)) in enumerate(zip(team_cols, team_scores.iterrows()), start=1):
            with col:
                render_team_card(row["Team"], row["Points"], rank)

    st.markdown("---")

    # --------------------------------------------------
    # CAP LEADERS
    # --------------------------------------------------
    st.subheader("🥇 MVP Cap Standings (Orange & Purple Caps)")
    leaderboard = (
        participants.groupby(["Participant", "Team"], as_index=False)["Points"]
        .sum()
        .sort_values("Points", ascending=False)
        .head(3)
    )

    if leaderboard.empty:
        st.info("No participant scores available yet.")
    else:
        participant_cols = st.columns(3)
        medals = ["🔥 ORANGE CAP #1", "💎 PURPLE CAP #2", "✨ CAP LEADER #3"]
        for idx, (_, row) in enumerate(leaderboard.iterrows()):
            with participant_cols[idx]:
                meta = get_team_meta(row["Team"])
                render_card(
                    f"{medals[idx]} {row['Participant']}",
                    f"{format_points(row['Points'])} PTS",
                    f"{meta['emoji']} {row['Team']}",
                )

    st.markdown("---")

    # --------------------------------------------------
    # UPCOMING LINEUPS
    # --------------------------------------------------
    st.subheader("📅 Live Match Day Arenas")
    upcoming = fixtures[fixtures["Status"].str.lower() == "upcoming"].head(3)

    if upcoming.empty:
        st.info("No upcoming fixtures on the spreadsheet roster.")
    else:
        for _, row in upcoming.iterrows():
            render_upcoming_card(row)

    st.markdown("---")

    # --------------------------------------------------
    # DYNAMIC PODIUM BLOCKS
    # --------------------------------------------------
    podium_cols = st.columns(2)
    
    with podium_cols[0]:
        st.subheader("👑 Orange Cap (MVP Leader)")
        if leaderboard.empty:
            st.info("Awaiting tournament registration metrics.")
        else:
            champion = leaderboard.iloc[0]
            meta = get_team_meta(champion["Team"])
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1.75rem; border-radius: 1rem; border: 1px solid #fbbf24; box-shadow: 0 15px 30px rgba(245,158,11,0.25); position: relative; overflow: hidden;">
                    <h2 style="margin:0; color: #0f172a !important; font-weight:900; font-size:1.8rem;">{champion['Participant']}</h2>
                    <p style="margin:0.25rem 0; color: #1e293b !important; font-weight:700; font-size:1.1rem;">{meta['emoji']} Franchise: {champion['Team']}</p>
                    <div style="margin-top: 0.75rem; background: #0f172a; display: inline-block; padding: 0.4rem 0.8rem; border-radius: 0.5rem; font-weight: 900; color: #fbbf24 !important; font-size: 0.9rem; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">{format_points(champion['Points'])} TOTAL MATCH POINTS</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with podium_cols[1]:
        st.subheader("🏆 Leaderboard Toppers")
        if team_scores.empty:
            st.info("Awaiting league metrics.")
        else:
            winner = team_scores.iloc[0]
            meta = get_team_meta(winner["Team"])
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 1.75rem; border-radius: 1rem; border: 1px solid #60a5fa; box-shadow: 0 15px 30px rgba(37,99,235,0.25);">
                    <h2 style="margin:0; color: white !important; font-weight:900; font-size:1.8rem;">{meta['emoji']} {winner['Team']}</h2>
                    <p style="margin:0.25rem 0; color: #bfdbfe !important; font-weight:600; font-size:1.05rem;">Tournament Seed #1</p>
                    <div style="margin-top: 0.75rem; background: white; display: inline-block; padding: 0.4rem 0.8rem; border-radius: 0.5rem; font-weight: 900; color: #1e3a8a !important; font-size: 0.9rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">{format_points(winner['Points'])} TEAM POINTS</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # --------------------------------------------------
    # MATCH CENTER BUTTON LINKS
    # --------------------------------------------------
    st.subheader("🚀 Match Center Arenas")
    nav_cols = st.columns(2)
    with nav_cols[0]:
        st.page_link("pages/Fixtures.py", label="📅 View Full Schedule")
    with nav_cols[1]:
        st.page_link("pages/Leaderboard.py", label="🏅 View Detailed Leaderboard")


if __name__ == "__main__":
    main()