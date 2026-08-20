"""Fixtures page for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import (
    get_config,
    get_sport_icon,
    get_status_color,
    get_team_meta,
    inject_stadium_audio,
    load_fixtures,
    safe_load,
)

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


def render_sport_rules(sport: str, config: dict) -> None:
    """Render rules and card details dynamically based on config definition."""
    rules_cfg = config.get("sports_rules", {}).get(sport, {})
    icon = get_sport_icon(sport)
    rules = rules_cfg.get("rules", ["Rules will be updated by the organisers."])
    card_details = rules_cfg.get(
        "card_details",
        ["Fixture cards show participants, teams, venue, match number, and status."],
    )

    rules_html = "".join(
        f"<li style='color: rgba(255,255,255,0.85); margin-bottom: 0.3rem;'>{rule}</li>"
        for rule in rules
    )
    card_html = "".join(
        f"<li style='color: rgba(255,255,255,0.85); margin-bottom: 0.3rem;'>{detail}</li>"
        for detail in card_details
    )

    st.markdown(
        f"""
        <div class="rules-card" style="
            background: rgba(15, 23, 42, 0.85); 
            border: 1px solid rgba(251, 191, 36, 0.25); 
            border-radius: 1rem; 
            padding: 1.5rem; 
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        ">
            <div class="card-value" style="color: #fbbf24 !important; font-size: 1.3rem; font-weight: 800; margin-bottom: 1rem;">
                {icon} {sport} Arena Rules & Match Protocol
            </div>
            <div class="card-label" style="color: #94a3b8 !important; font-weight: 700; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px; margin-top: 0.75rem;">
                📜 Official Rules
            </div>
            <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">{rules_html}</ul>
            <div class="card-label" style="color: #94a3b8 !important; font-weight: 700; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px; margin-top: 0.75rem;">
                📋 Card & Scoring Details
            </div>
            <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">{card_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_fixture_card(row, config) -> None:
    """Render one sheet-driven fixture as a high-contrast IPL match card."""
    status = str(row.get("Status", "Upcoming")).strip()
    status_bg = get_status_color(status, config)

    participant1 = str(row.get("Participant 1", "TBD")).strip()
    participant2 = str(row.get("Participant 2", "TBD")).strip()

    # Supports both 'Team 1/2' and fallback 'House 1/2' without throwing Unknown
    t1_val = str(row.get("Team 1") or row.get("House 1") or "Unknown").strip()
    t2_val = str(row.get("Team 2") or row.get("House 2") or "Unknown").strip()

    team1_meta = get_team_meta(t1_val)
    team2_meta = get_team_meta(t2_val)

    sport = str(row.get("Sport", "Sport")).strip()
    date = str(row.get("Date", "TBD")).strip()
    time = str(row.get("Time", "TBD")).strip()
    venue = str(row.get("Venue", "Arena")).strip()
    match_no = str(row.get("Match", "")).strip()

    icon = get_sport_icon(sport)

    # Flattened HTML string structure
    html = (
        f'<div class="fixture-card dynamic-pulse" style="background: rgba(15, 23, 42, 0.85) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.12) !important; border-radius: 1rem; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4) !important;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">'
        f'<span class="sport-badge" style="color: #ffffff !important; font-weight: 800; background: linear-gradient(90deg, #1e40af, #3b82f6); padding: 0.35rem 0.85rem; border-radius: 2rem; font-size: 0.8rem; border: 1px solid #60a5fa;">⚡ {icon} {sport}</span>'
        f'<span class="match-badge" style="color: #fbbf24 !important; font-size: 0.85rem; font-weight: 700; text-shadow: 0 0 8px rgba(251,191,36,0.3);">{match_no}</span>'
        f'</div>'
        f'<div class="card-label" style="color: #94a3b8 !important; font-size: 0.9rem; font-weight: 600; margin-bottom: 1rem;">📅 {date} • 🕒 {time}</div>'
        f'<div class="participant-section" style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin: 1rem 0;">'
        f'<div class="participant-card" style="flex: 1; padding: 0.85rem; border-radius: 0.6rem; background: rgba(255,255,255,0.03); border-left: 5px solid {team1_meta["color"]};">'
        f'<div class="participant-name" style="color: #ffffff !important; font-weight: 800; font-size: 1.1rem;">{participant1}</div>'
        f'<div class="participant-house" style="color: #94a3b8 !important; font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem;">{team1_meta["emoji"]} {team1_meta["name"]}</div>'
        f'</div>'
        f'<div class="vs-section" style="color: #fbbf24 !important; font-weight: 900; font-size: 1.1rem; font-style: italic; text-shadow: 0 0 10px rgba(251,191,36,0.4);">VS</div>'
        f'<div class="participant-card" style="flex: 1; padding: 0.85rem; border-radius: 0.6rem; background: rgba(255,255,255,0.03); border-left: 5px solid {team2_meta["color"]};">'
        f'<div class="participant-name" style="color: #ffffff !important; font-weight: 800; font-size: 1.1rem;">{participant2}</div>'
        f'<div class="participant-house" style="color: #94a3b8 !important; font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem;">{team2_meta["emoji"]} {team2_meta["name"]}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(255,255,255,0.08);">'
        f'<div class="card-subtle" style="color: #64748b !important; font-size: 0.85rem; font-weight: 600;">📍 {venue}</div>'
        f'<span class="status-badge" style="background:{status_bg}; color: #ffffff !important; padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">{status}</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_fixture_list(fixtures: pd.DataFrame, config: dict) -> None:
    """Render rows seamlessly straight out of the parsed sheet data matrix."""
    for _, row in fixtures.iterrows():
        render_fixture_card(row, config)


def main() -> None:
    """Render the fixtures page."""
    inject_stadium_audio()
    config = get_config()

    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    st.title("📅 Match Center & Fixtures Schedule")
    st.caption("Live sport-wise fixtures, tournament rules, arena venues, and match progress.")

    if fixtures.empty:
        st.info("No fixtures available yet in the spreadsheet matrix.")
        return

    # Strip whitespace across dataframe
    fixtures = fixtures.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    # Dynamic status filter
    statuses = ["All"] + sorted(fixtures["Status"].dropna().unique().tolist())
    selected_status = st.selectbox("Filter by match status", statuses)

    filtered = fixtures.copy()
    if selected_status != "All":
        filtered = filtered[filtered["Status"] == selected_status]

    if filtered.empty:
        st.warning("No live records match the active filter criteria.")
        return

    # Dynamic sport tabs
    available_sports = sorted(filtered["Sport"].dropna().unique().tolist())
    tab_names = ["🏆 All Disciplines"] + [f"{get_sport_icon(sport)} {sport}" for sport in available_sports]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        st.subheader("🏆 All Scheduled Matches")
        render_fixture_list(filtered, config)

    for tab, sport in zip(tabs[1:], available_sports):
        with tab:
            sport_df = filtered[filtered["Sport"] == sport]
            render_sport_rules(sport, config)
            render_fixture_list(sport_df, config)


if __name__ == "__main__":
    main()