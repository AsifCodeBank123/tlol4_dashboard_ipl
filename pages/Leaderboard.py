"""Leaderboard page for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import format_points, get_sport_icon, get_team_meta, load_participants, safe_load, inject_stadium_audio

# inject_stadium_audio()

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
PARTICIPANT_COLUMNS = ["Participant", "Team", "Sport", "Points", "Matches", "Wins", "Bonus"]


def render_aggregated_player_card(participant_name: str, team_name: str, group_df: pd.DataFrame, rank: int) -> None:
    """Render a consolidated participant card with collapsible sport breakdown."""
    medal = MEDALS.get(rank, f"#{rank}")
    team = get_team_meta(team_name)
    card_class = "leader-card top-rank" if rank <= 3 else "leader-card"

    total_points = group_df["Points"].sum()
    sport_count = group_df["Sport"].nunique()
    matches = int(group_df["Matches"].sum())
    wins = int(group_df["Wins"].sum())

    sport_rows = []
    for _, row in group_df.sort_values("Points", ascending=False).iterrows():
        sport_icon = get_sport_icon(row["Sport"])
        sport_rows.append(
            f"""
            <div class="participant-card" style="--team-color:{team['color']}; text-align:left; margin-top:0.55rem;">
                <div style="display:flex; justify-content:space-between; gap:1rem; align-items:center;">
                    <span class="sport-badge">{sport_icon} {row['Sport']}</span>
                    <strong>{format_points(row['Points'])} pts</strong>
                </div>
                <div class="card-subtle">Matches: {int(row['Matches'])} • Wins: {int(row['Wins'])} • Bonus: {format_points(row['Bonus'])}</div>
            </div>
            """
        )

    html = f"""
    <div class="{card_class}" style="border-left:0.45rem solid {team['color']};">
        <div class="card-label"><span class="medal">{medal}</span>Rank {rank}</div>
        <div class="card-value">{participant_name}</div>
        <div class="card-subtle">{team['emoji']} {team_name}</div>
        <br>
        <div class="card-value">{format_points(total_points)} pts</div>
        <div class="card-subtle">Sports: {sport_count} • Matches: {matches} • Wins: {wins}</div>
        <details>
            <summary>📋 Show sports breakdown</summary>
            {''.join(sport_rows)}
        </details>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def main() -> None:
    """Render the leaderboard page with multi-sport breakdown."""
    raw_df = safe_load(load_participants, PARTICIPANT_COLUMNS)

    st.title("🏅 Leaderboard")
    st.caption("Participants are ranked by total points across all sports, with sport-wise breakdown.")

    if raw_df.empty:
        st.info("No leaderboard data available yet.")
        return

    raw_df = raw_df.copy()
    raw_df["Points"] = pd.to_numeric(raw_df["Points"], errors="coerce").fillna(0.0)
    raw_df["Bonus"] = pd.to_numeric(raw_df["Bonus"], errors="coerce").fillna(0.0)

    filter_cols = st.columns([2, 1, 1])
    search_text = filter_cols[0].text_input("Search participant", placeholder="Type a participant name...")
    teams = ["All"] + sorted(raw_df["Team"].dropna().unique().tolist())
    sports = ["All"] + sorted(raw_df["Sport"].dropna().unique().tolist())
    selected_team = filter_cols[1].selectbox("Filter by team", teams)
    selected_sport = filter_cols[2].selectbox("Filter by sport", sports)

    filtered = raw_df.copy()
    if search_text:
        filtered = filtered[filtered["Participant"].str.contains(search_text, case=False, na=False)]
    if selected_team != "All":
        filtered = filtered[filtered["Team"] == selected_team]
    if selected_sport != "All":
        filtered = filtered[filtered["Sport"] == selected_sport]

    if filtered.empty:
        st.warning("No participants match the selected filters.")
        return

    totals = (
        filtered.groupby(["Participant", "Team"], as_index=False)["Points"]
        .sum()
        .sort_values("Points", ascending=False)
        .reset_index(drop=True)
    )
    totals["Rank"] = totals.index + 1

    metrics_cols = st.columns(3)
    metrics_cols[0].metric("Highest Total Score", format_points(totals["Points"].max()))
    metrics_cols[1].metric("Average Total Score", format_points(totals["Points"].mean()))
    metrics_cols[2].metric("Lowest Total Score", format_points(totals["Points"].min()))

    records = totals.to_dict("records")
    for index in range(0, len(records), 2):
        grid_cols = st.columns(2)
        for col, item in zip(grid_cols, records[index:index + 2]):
            participant_df = filtered[
                (filtered["Participant"] == item["Participant"])
                & (filtered["Team"] == item["Team"])
            ]
            with col:
                render_aggregated_player_card(
                    item["Participant"],
                    item["Team"],
                    participant_df,
                    int(item["Rank"]),
                )


if __name__ == "__main__":
    main()
