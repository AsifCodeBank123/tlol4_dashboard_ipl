"""Fixtures page for the Hogwarts Office Sports Dashboard."""

from __future__ import annotations

import streamlit as st

from utils import get_config, get_sport_icon, get_status_color, get_house_meta, load_fixtures, safe_load, inject_stadium_audio

# inject_stadium_audio()
# The exact column headers coming from your live Google Sheet layout
FIXTURE_COLUMNS = [
    "Sport",
    "Date",
    "Time",
    "Participant 1",
    "House 1",
    "Participant 2",
    "House 2",
    "Match",
    "Venue",
    "Status",
]


def render_sport_rules(sport: str, config: dict) -> None:
    """Render rules and card details dynamically based on config definition."""
    rules_cfg = config.get("sports_rules", {}).get(sport, {})
    icon = rules_cfg.get("icon", "🏅")
    rules = rules_cfg.get("rules", ["Rules will be updated by the organisers."])
    card_details = rules_cfg.get("card_details", ["Fixture cards show participants, houses, venue, match number, and status."])

    rules_html = "".join(f"<li style='color: rgba(255,255,255,0.85); margin-bottom: 0.3rem;'>{rule}</li>" for rule in rules)
    card_html = "".join(f"<li style='color: rgba(255,255,255,0.85); margin-bottom: 0.3rem;'>{detail}</li>" for detail in card_details)

    st.markdown(
        f"""
        <div class="rules-card" style="
            background: rgba(30, 41, 59, 0.85); 
            border: 1px solid rgba(255,255,255,0.12); 
            border-radius: 1rem; 
            padding: 1.5rem; 
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        ">
            <div class="card-value" style="color: #ffffff !important; font-size: 1.3rem; font-weight: 700; margin-bottom: 1rem;">
                {icon} {sport} Rules & Card Details
            </div>
            <div class="card-label" style="color: rgba(255, 255, 255, 0.6) !important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px; margin-top: 0.75rem;">
                Rules
            </div>
            <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">{rules_html}</ul>
            <div class="card-label" style="color: rgba(255, 255, 255, 0.6) !important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.5px; margin-top: 0.75rem;">
                Card Details
            </div>
            <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">{card_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_fixture_card(row, config) -> None:
    """Render one sheet-driven fixture as a modern card with flat HTML string format."""
    status = str(row.get("Status", "TBD")).strip()
    status_bg = get_status_color(status, config)

    participant1 = str(row.get("Participant 1", "TBD"))
    participant2 = str(row.get("Participant 2", "TBD"))
    
    # FIXED: pulling correctly from "House 1" and "House 2" instead of "Team"
    house1 = str(row.get("House 1", "Unknown")).strip()
    house2 = str(row.get("House 2", "Unknown")).strip()
    
    sport = str(row.get("Sport", "Sport"))
    date = str(row.get("Date", "TBD"))
    time = str(row.get("Time", "TBD"))
    venue = str(row.get("Venue", "TBD"))
    match_no = str(row.get("Match", ""))

    house1_meta = get_house_meta(house1)
    house2_meta = get_house_meta(house2)
    icon = get_sport_icon(sport, config)

    # Completely flat string structure prevents Streamlit from rendering raw text blocks
    html = (
        f'<div class="fixture-card" style="background: rgba(30, 41, 59, 0.8) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.12) !important; border-radius: 1rem; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">'
        f'<span class="sport-badge" style="color: #ffffff !important; font-weight: 600; background: rgba(255,255,255,0.08); padding: 0.25rem 0.6rem; border-radius: 0.5rem; font-size: 0.85rem;">⚡ {icon} {sport}</span>'
        f'<span class="match-badge" style="color: rgba(255,255,255,0.7) !important; font-size: 0.85rem; font-weight: 500;">Match {match_no}</span>'
        f'</div>'
        f'<div class="card-label" style="color: rgba(255, 255, 255, 0.65) !important; font-size: 0.9rem; margin-bottom: 1rem;">📅 {date} • 🕒 {time}</div>'
        f'<div class="participant-section" style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin: 1rem 0;">'
        f'<div class="participant-card" style="flex: 1; padding: 0.75rem; border-radius: 0.5rem; background: rgba(255,255,255,0.03); border-left: 4px solid {house1_meta["color"]};">'
        f'<div class="participant-name" style="color: #ffffff !important; font-weight: 700; font-size: 1.05rem;">{participant1}</div>'
        f'<div class="participant-house" style="color: rgba(255,255,255,0.6) !important; font-size: 0.85rem; margin-top: 0.15rem;">{house1_meta["emoji"]} {house1}</div>'
        f'</div>'
        f'<div class="vs-section" style="color: rgba(255,255,255,0.4) !important; font-weight: 800; font-size: 0.9rem; letter-spacing: 1px;">VS</div>'
        f'<div class="participant-card" style="flex: 1; padding: 0.75rem; border-radius: 0.5rem; background: rgba(255,255,255,0.03); border-left: 4px solid {house2_meta["color"]};">'
        f'<div class="participant-name" style="color: #ffffff !important; font-weight: 700; font-size: 1.05rem;">{participant2}</div>'
        f'<div class="participant-house" style="color: rgba(255,255,255,0.6) !important; font-size: 0.85rem; margin-top: 0.15rem;">{house2_meta["emoji"]} {house2}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(255,255,255,0.06);">'
        f'<div class="card-subtle" style="color: rgba(255, 255, 255, 0.55) !important; font-size: 0.85rem;">📍 {venue}</div>'
        f'<span class="status-badge" style="background:{status_bg}; color: #ffffff !important; padding: 0.2rem 0.6rem; border-radius: 0.4rem; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{status}</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_fixture_list(fixtures, config) -> None:
    """Render rows seamlessly straight out of the parsed sheet data matrix."""
    for _, row in fixtures.iterrows():
        render_fixture_card(row, config)


def main() -> None:
    """Render the fixtures page."""
    config = get_config()
    
    # Loads live dataframe entries from the connected Google Sheets backend pipeline securely
    fixtures = safe_load(load_fixtures, FIXTURE_COLUMNS)

    st.title("📅 Fixtures")
    st.caption("Live sport-wise fixtures with rules, match cards, house profiles, and progress tracking.")

    if fixtures.empty:
        st.info("No fixtures available yet in the spreadsheet matrix.")
        return

    # Dynamic status population built instantly from spreadsheet column rows
    statuses = ["All"] + sorted(fixtures["Status"].dropna().unique().tolist())
    selected_status = st.selectbox("Filter by status", statuses)

    filtered = fixtures.copy()
    if selected_status != "All":
        filtered = filtered[filtered["Status"] == selected_status]

    if filtered.empty:
        st.warning("No live records match the active filter criteria.")
        return

    # Dynamically separate incoming values based on Sheet classifications discovered
    available_sports = sorted(filtered["Sport"].dropna().unique().tolist())
    tab_names = ["🏆 All"] + [f"{get_sport_icon(sport, config)} {sport}" for sport in available_sports]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        st.subheader("🏆 All Fixtures")
        render_fixture_list(filtered, config)

    for tab, sport in zip(tabs[1:], available_sports):
        with tab:
            sport_df = filtered[filtered["Sport"] == sport]
            render_sport_rules(sport, config)
            render_fixture_list(sport_df, config)


if __name__ == "__main__":
    main()