"""Leaderboard page for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import (
    format_points,
    get_sport_icon,
    get_team_meta,
    inject_stadium_audio,
    load_participants,
    render_points_matrix_table,
    safe_load,
)

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
PARTICIPANT_COLUMNS = ["Participant", "Team", "Sport", "Points", "Matches", "Wins", "Bonus"]


def render_aggregated_player_card(
    participant_name: str, team_name: str, group_df: pd.DataFrame, rank: int
) -> None:
    """Render a consolidated individual participant card."""
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
            <div class="participant-card" style="text-align:left; margin-top:0.55rem; background: rgba(255,255,255,0.03); padding: 0.5rem; border-radius: 0.5rem; border-left: 3px solid {team['color']};">
                <div style="display:flex; justify-content:space-between; gap:1rem; align-items:center;">
                    <span class="sport-badge" style="color: #ffffff; font-weight: 700;">{sport_icon} {row['Sport']}</span>
                    <strong style="color: #fbbf24;">{format_points(row['Points'])} pts</strong>
                </div>
                <div class="card-subtle" style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.2rem;">Matches: {int(row['Matches'])} • Wins: {int(row['Wins'])} • Bonus: {format_points(row['Bonus'])}</div>
            </div>
            """
        )

    html = f"""
    <div class="{card_class}" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255,255,255,0.12); border-left: 0.45rem solid {team['color']}; border-radius: 1rem; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#fbbf24; font-weight:800; font-size:0.9rem;"><span class="medal">{medal}</span> RANK #{rank}</span>
            <span style="color:#94a3b8; font-size:0.85rem; font-weight:600;">{team['emoji']} {team_name}</span>
        </div>
        <div style="color:#ffffff; font-size:1.4rem; font-weight:800; margin:0.3rem 0;">{participant_name}</div>
        <div style="color:#ffffff; font-size:1.6rem; font-weight:900; letter-spacing:-0.5px;">{format_points(total_points)} <span style="font-size:0.9rem; color:#64748b;">PTS</span></div>
        <div style="color:#94a3b8; font-size:0.85rem; margin-top:0.25rem;">Disciplines: {sport_count} • Matches: {matches} • Victories: {wins}</div>
        <details style="margin-top:0.75rem; cursor:pointer;">
            <summary style="color:#fbbf24; font-weight:700; font-size:0.85rem;">📋 View Discipline Breakdown</summary>
            {''.join(sport_rows)}
        </details>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def main() -> None:
    inject_stadium_audio()
    raw_df = safe_load(load_participants, PARTICIPANT_COLUMNS)

    st.title("🏅 Tournament Standings & Leaderboard")
    st.caption("Official franchise points matrix, bonus categories, and athlete standings.")

    if raw_df.empty:
        st.info("No leaderboard data available yet.")
        return

    raw_df = raw_df.copy()
    raw_df["Points"] = pd.to_numeric(raw_df["Points"], errors="coerce").fillna(0.0)
    raw_df["Bonus"] = pd.to_numeric(raw_df["Bonus"], errors="coerce").fillna(0.0)

    # --------------------------------------------------
    # 1. TEAM BREAKDOWN MATRIX (INCLUDES TEAM BONUSES)
    # --------------------------------------------------
    render_points_matrix_table(raw_df)

    st.markdown("---")

    # --------------------------------------------------
    # 2. INDIVIDUAL ATHLETE RANKINGS (EXCLUDES TEAM ROWS)
    # --------------------------------------------------
    st.subheader("🥇 MVP Athlete Standings")

    # Safe comparison using .str.lower()
    athlete_df = raw_df[
        raw_df["Participant"].astype(str).str.strip().str.lower()
        != raw_df["Team"].astype(str).str.strip().str.lower()
    ].copy()

    if athlete_df.empty:
        st.info("Individual athlete points will appear as single-player matches are scored.")
        return

    filter_cols = st.columns([2, 1, 1])
    search_text = filter_cols[0].text_input("Search athlete", placeholder="Type a player name...")
    teams = ["All"] + sorted(athlete_df["Team"].dropna().unique().tolist())
    sports = ["All"] + sorted(athlete_df["Sport"].dropna().unique().tolist())
    selected_team = filter_cols[1].selectbox("Filter by team", teams)
    selected_sport = filter_cols[2].selectbox("Filter by discipline", sports)

    filtered = athlete_df.copy()
    if search_text:
        filtered = filtered[filtered["Participant"].str.contains(search_text, case=False, na=False)]
    if selected_team != "All":
        filtered = filtered[filtered["Team"] == selected_team]
    if selected_sport != "All":
        filtered = filtered[filtered["Sport"] == selected_sport]

    if filtered.empty:
        st.warning("No individual athletes match the selected filter criteria.")
        return

    totals = (
        filtered.groupby(["Participant", "Team"], as_index=False)["Points"]
        .sum()
        .sort_values("Points", ascending=False)
        .reset_index(drop=True)
    )
    totals["Rank"] = totals.index + 1

    metrics_cols = st.columns(3)
    metrics_cols[0].metric("Highest Individual Total", f"{format_points(totals['Points'].max())} PTS")
    metrics_cols[1].metric("Average Athlete Total", f"{format_points(totals['Points'].mean())} PTS")
    metrics_cols[2].metric("Total Ranked Athletes", f"{len(totals)}")

    records = totals.to_dict("records")
    for index in range(0, len(records), 2):
        grid_cols = st.columns(2)
        for col, item in zip(grid_cols, records[index : index + 2]):
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