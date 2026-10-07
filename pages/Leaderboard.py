"""Championship MVP Leaderboard for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import (
    format_points,
    get_sport_icon,
    get_team_meta,
    load_participants,
    render_points_matrix_table,
    render_top_navigation_bar,
    safe_load,
)

MEDALS = {1: "👑", 2: "🥈", 3: "🥉"}
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


def render_leaderboard_styles() -> None:
    """Inject custom styles for the podium, HUD metrics, and player cards."""
    st.markdown(
        """
        <style>
        /* Ambient Page Accents */
        .leaderboard-hero {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 58, 138, 0.88)), 
                        url('https://images.unsplash.com/photo-1540747737956-3787293a9fc4?q=80&w=1280&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            border-radius: 1.25rem;
            padding: 2.75rem 1.5rem;
            text-align: center;
            border: 2px solid rgba(251, 191, 36, 0.45);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6), 0 0 25px rgba(251, 191, 36, 0.2);
            margin-bottom: 2rem;
        }

        .podium-container {
            display: grid;
            grid-template-columns: 1fr 1.15fr 1fr;
            gap: 1.25rem;
            align-items: flex-end;
            margin: 2rem 0 2.5rem 0;
        }

        .podium-card {
            background: rgba(15, 23, 42, 0.9);
            border-radius: 1.25rem;
            padding: 1.5rem 1rem;
            text-align: center;
            position: relative;
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.5);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        .podium-card:hover {
            transform: translateY(-5px);
        }

        .podium-first {
            border: 2px solid #fbbf24;
            box-shadow: 0 0 35px rgba(251, 191, 36, 0.4);
            transform: scale(1.04);
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        }

        .podium-first:hover {
            transform: scale(1.04) translateY(-5px);
        }

        .podium-second {
            border: 1.5px solid #94a3b8;
            box-shadow: 0 0 20px rgba(148, 163, 184, 0.25);
        }

        .podium-third {
            border: 1.5px solid #b45309;
            box-shadow: 0 0 20px rgba(180, 83, 9, 0.25);
        }

        .hud-metric-box {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.1rem;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        }

        .details-trigger summary::-webkit-details-marker {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_podium(top_three_df: pd.DataFrame) -> None:
    """Render a dynamic Olympic podium that handles ties correctly."""
    if len(top_three_df) < 3:
        return

    # Check ties to format labels
    rank_counts = top_three_df["Rank"].value_counts()

    def get_podium_slot_meta(rank_val: int):
        is_tied = rank_counts.get(rank_val, 0) > 1
        label_rank = f"T-{rank_val}" if is_tied else f"#{rank_val}"

        if rank_val == 1:
            return {
                "icon": "👑",
                "tag": f"LEAGUE MVP ({label_rank})",
                "card_class": "podium-first",
                "color": "#fbbf24",
                "font_size": "2.7rem",
            }
        elif rank_val == 2:
            return {
                "icon": "🥈",
                "tag": f"RANK {label_rank}",
                "card_class": "podium-second",
                "color": "#94a3b8",
                "font_size": "2rem",
            }
        else:
            return {
                "icon": "🥉",
                "tag": f"RANK {label_rank}",
                "card_class": "podium-third",
                "color": "#b45309",
                "font_size": "2rem",
            }

    # Center is index 0, Left is index 1, Right is index 2
    first = top_three_df.iloc[0]
    second = top_three_df.iloc[1]
    third = top_three_df.iloc[2]

    meta_first = get_podium_slot_meta(int(first["Rank"]))
    meta_second = get_podium_slot_meta(int(second["Rank"]))
    meta_third = get_podium_slot_meta(int(third["Rank"]))

    m1 = get_team_meta(first["Team"])
    m2 = get_team_meta(second["Team"])
    m3 = get_team_meta(third["Team"])

    podium_html = (
        f'<div class="podium-container">'
        # Left Slot (Index 1)
        f'<div class="podium-card {meta_second["card_class"]}">'
        f'<div style="font-size: {meta_second["font_size"]};">{meta_second["icon"]}</div>'
        f'<div style="color: {meta_second["color"]}; font-weight: 800; font-size: 0.8rem; letter-spacing: 1.5px; text-transform: uppercase;">{meta_second["tag"]}</div>'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.25rem; margin: 0.4rem 0 0.2rem 0;">{second["Participant"]}</div>'
        f'<div style="color: {m2["color"]}; font-size: 0.8rem; font-weight: 700;">{m2["emoji"]} {m2["short_name"]}</div>'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.6rem; margin-top: 0.5rem;">{format_points(second["TotalPoints"])} <span style="font-size:0.8rem; color:#94a3b8;">PTS</span></div>'
        f'<div style="margin-top:0.6rem; background:rgba(148,163,184,0.1); border-radius:0.4rem; padding:0.25rem; font-size:0.75rem; color:#cbd5e1;">{int(second["Sports_Count"])} Disciplines • {int(second["Wins"])} Wins</div>'
        f'</div>'
        # Center Slot (Index 0 - Highest)
        f'<div class="podium-card {meta_first["card_class"]}">'
        f'<div style="font-size: {meta_first["font_size"]}; filter: drop-shadow(0 0 12px {meta_first["color"]});">{meta_first["icon"]}</div>'
        f'<div style="color: {meta_first["color"]}; font-weight: 900; font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase;">{meta_first["tag"]}</div>'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.5rem; margin: 0.4rem 0 0.2rem 0;">{first["Participant"]}</div>'
        f'<div style="color: {m1["color"]}; font-size: 0.85rem; font-weight: 800;">{m1["emoji"]} {m1["name"]}</div>'
        f'<div style="color: #fbbf24; font-weight: 900; font-size: 2.1rem; margin-top: 0.5rem; text-shadow:0 0 15px rgba(251,191,36,0.4);">{format_points(first["TotalPoints"])} <span style="font-size:0.9rem; color:#cbd5e1;">PTS</span></div>'
        f'<div style="margin-top:0.6rem; background:rgba(251,191,36,0.15); border:1px solid rgba(251,191,36,0.3); border-radius:0.4rem; padding:0.35rem; font-size:0.8rem; color:#fef08a; font-weight:700;">⭐ {int(first["Sports_Count"])} Disciplines • {int(first["Wins"])} Wins ⭐</div>'
        f'</div>'
        # Right Slot (Index 2)
        f'<div class="podium-card {meta_third["card_class"]}">'
        f'<div style="font-size: {meta_third["font_size"]};">{meta_third["icon"]}</div>'
        f'<div style="color: {meta_third["color"]}; font-weight: 800; font-size: 0.8rem; letter-spacing: 1.5px; text-transform: uppercase;">{meta_third["tag"]}</div>'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.25rem; margin: 0.4rem 0 0.2rem 0;">{third["Participant"]}</div>'
        f'<div style="color: {m3["color"]}; font-size: 0.8rem; font-weight: 700;">{m3["emoji"]} {m3["short_name"]}</div>'
        f'<div style="color: #ffffff; font-weight: 900; font-size: 1.6rem; margin-top: 0.5rem;">{format_points(third["TotalPoints"])} <span style="font-size:0.8rem; color:#94a3b8;">PTS</span></div>'
        f'<div style="margin-top:0.6rem; background:rgba(180,83,9,0.1); border-radius:0.4rem; padding:0.25rem; font-size:0.75rem; color:#cbd5e1;">{int(third["Sports_Count"])} Disciplines • {int(third["Wins"])} Wins</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(podium_html, unsafe_allow_html=True)

def render_aggregated_player_card(
    participant_name: str,
    team_name: str,
    group_df: pd.DataFrame,
    rank_val: int,
    rank_label: str,
) -> None:
    """Render an individual athlete card with tie-aware rank badge."""
    medal_symbol = MEDALS.get(rank_val, "")
    team = get_team_meta(team_name)

    total_points = group_df["TotalPoints"].sum()
    sport_count = group_df["Sport"].nunique()
    matches = int(group_df["Matches"].sum())
    wins = int(group_df["Wins"].sum())

    # Styling based on mathematical rank tier
    if rank_val == 1:
        card_border = "border: 2px solid #fbbf24; box-shadow: 0 0 20px rgba(251, 191, 36, 0.35);"
        rank_badge_bg = "background: linear-gradient(90deg, #d97706, #fbbf24); color: #000000;"
    elif rank_val == 2:
        card_border = "border: 1.5px solid #94a3b8; box-shadow: 0 0 16px rgba(148, 163, 184, 0.2);"
        rank_badge_bg = "background: linear-gradient(90deg, #475569, #94a3b8); color: #ffffff;"
    elif rank_val == 3:
        card_border = "border: 1.5px solid #b45309; box-shadow: 0 0 16px rgba(180, 83, 9, 0.2);"
        rank_badge_bg = "background: linear-gradient(90deg, #78350f, #b45309); color: #ffffff;"
    else:
        card_border = "border: 1px solid rgba(255, 255, 255, 0.1);"
        rank_badge_bg = "background: rgba(255, 255, 255, 0.08); color: #94a3b8;"

    sport_rows = []
    for _, row in group_df.sort_values("TotalPoints", ascending=False).iterrows():
        sport_icon = get_sport_icon(row["Sport"])
        item_pts = row["TotalPoints"]
        part_pts = row.get("Participation Points", 0)
        bonus_pts = row.get("Bonus", 0)

        detail_segments = [f"Matches: {int(row.get('Matches', 0))}", f"Wins: {int(row.get('Wins', 0))}"]
        if part_pts > 0:
            detail_segments.append(f"Part. Pts: <strong>{format_points(part_pts)}</strong>")
        if bonus_pts > 0:
            detail_segments.append(f"Bonus: <strong>{format_points(bonus_pts)}</strong>")

        row_html = (
            f'<div style="text-align:left; margin-top:0.45rem; background: rgba(0, 0, 0, 0.35); '
            f'padding: 0.55rem 0.75rem; border-radius: 0.5rem; border-left: 3px solid {team["color"]};">'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<span style="color: #ffffff; font-weight: 700; font-size: 0.82rem;">{sport_icon} {row["Sport"]}</span>'
            f'<strong style="color: #fbbf24; font-size: 0.85rem;">{format_points(item_pts)} pts</strong>'
            f'</div>'
            f'<div style="color: #94a3b8; font-size: 0.73rem; margin-top: 0.2rem;">{" • ".join(detail_segments)}</div>'
            f'</div>'
        )
        sport_rows.append(row_html)

    joined_rows = "".join(sport_rows)

    card_html = (
        f'<div style="background: rgba(15, 23, 42, 0.9); border-radius: 1rem; padding: 1.25rem; '
        f'margin-bottom: 1.15rem; {card_border} border-left: 6px solid {team["color"]};">'
        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
        f'<span style="{rank_badge_bg} font-weight: 900; font-size: 0.78rem; padding: 0.25rem 0.75rem; border-radius: 2rem; letter-spacing: 1px;">'
        f'{medal_symbol} RANK {rank_label}'
        f'</span>'
        f'<span style="color: #cbd5e1; font-size: 0.8rem; font-weight: 700; background: rgba(255,255,255,0.05); padding: 0.2rem 0.6rem; border-radius: 0.5rem;">'
        f'{team["emoji"]} {team["short_name"]}'
        f'</span>'
        f'</div>'
        f'<div style="color: #ffffff; font-size: 1.35rem; font-weight: 900; margin: 0.6rem 0 0.1rem 0; letter-spacing: -0.4px;">'
        f'{participant_name}'
        f'</div>'
        f'<div style="color: #fbbf24; font-size: 1.75rem; font-weight: 900; letter-spacing: -0.5px;">'
        f'{format_points(total_points)} <span style="font-size: 0.85rem; color: #64748b; font-weight: 700;">PTS</span>'
        f'</div>'
        f'<div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.3rem; font-weight: 600;">'
        f'Disciplines: <span style="color:#ffffff;">{sport_count}</span> • Matches: <span style="color:#ffffff;">{matches}</span> • Victories: <span style="color:#ffffff;">{wins}</span>'
        f'</div>'
        f'<details class="details-trigger" style="margin-top: 0.85rem; cursor: pointer; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 0.5rem 0.75rem; border-radius: 0.5rem;">'
        f'<summary style="color: #38bdf8; font-weight: 800; font-size: 0.8rem; outline: none; list-style: none;">'
        f'⚡ VIEW DISCIPLINE BREAKDOWN'
        f'</summary>'
        f'{joined_rows}'
        f'</details>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def main() -> None:
    render_top_navigation_bar("Leaderboard")
    render_leaderboard_styles()

    # --------------------------------------------------
    # 1. CHAMPIONSHIP HERO BANNER
    # --------------------------------------------------
    st.markdown(
        """
        <div class="leaderboard-hero">
            <span style="background: rgba(251, 191, 36, 0.18); border: 1px solid #fbbf24; color: #fbbf24; 
                  padding: 0.35rem 1.1rem; border-radius: 2rem; font-weight: 900; font-size: 0.8rem; letter-spacing: 2px;">
                ⭐ OFFICIAL LEAGUE STANDINGS
            </span>
            <h1 style="color: #ffffff; font-weight: 900; font-size: 2.85rem; margin: 0.6rem 0 0.2rem 0; text-transform: uppercase; text-shadow: 0 4px 20px rgba(0,0,0,0.9);">
                Tournament MVP Leaderboard
            </h1>
            <p style="color: #cbd5e1; font-size: 1.15rem; font-weight: 600; margin: 0;">
                Live franchise matrix, athlete performance scores, and individual MVP stakes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    raw_df = safe_load(load_participants, PARTICIPANT_COLUMNS)

    if raw_df.empty:
        st.info("No leaderboard data available yet.")
        return

    # Clean numeric calculations including Participation Points
    raw_df = raw_df.copy()
    raw_df["Points"] = pd.to_numeric(raw_df.get("Points", 0), errors="coerce").fillna(0.0)
    raw_df["Bonus"] = pd.to_numeric(raw_df.get("Bonus", 0), errors="coerce").fillna(0.0)
    raw_df["Participation Points"] = pd.to_numeric(
        raw_df.get("Participation Points", 0), errors="coerce"
    ).fillna(0.0)
    raw_df["TotalPoints"] = (
        raw_df["Points"] + raw_df["Bonus"] + raw_df["Participation Points"]
    )

    # --------------------------------------------------
    # 2. FRANCHISE BREAKDOWN MATRIX
    # --------------------------------------------------
    render_points_matrix_table(raw_df)
    st.markdown("---")

    # --------------------------------------------------
    # 3. INDIVIDUAL ATHLETE RANKINGS & PODIUM
    # --------------------------------------------------
    st.subheader("👑 League MVP Race")

    # Exclude dummy team-level entries
    athlete_df = raw_df[
        raw_df["Participant"].astype(str).str.strip().str.lower()
        != raw_df["Team"].astype(str).str.strip().str.lower()
    ].copy()

    if athlete_df.empty:
        st.info("Individual athlete records will populate once match results are entered.")
        return

    ## Aggregate total athlete points across all sports
    overall_rankings = (
        athlete_df.groupby(["Participant", "Team"], as_index=False)
        .agg(
            TotalPoints=("TotalPoints", "sum"),
            Wins=("Wins", "sum"),
            Sports_Count=("Sport", "nunique"),
        )
    )

    # 👈 Use true competition min-ranking
    overall_rankings["Rank"] = overall_rankings["TotalPoints"].rank(method="min", ascending=False).astype(int)

    # Sort by Rank (ties ordered by Wins as secondary tie-breaker, then name)
    overall_rankings = overall_rankings.sort_values(
        by=["Rank", "Wins", "Participant"], 
        ascending=[True, False, True]
    ).reset_index(drop=True)

    # Render Top-3 Podium (if at least 3 players exist)
    if len(overall_rankings) >= 3:
        render_podium(overall_rankings.head(3))

    # --------------------------------------------------
    # 4. HUD METRIC TILES
    # --------------------------------------------------
    m1, m2, m3 = st.columns(3)
    metric_template = """
        <div class="hud-metric-box">
            <div style="color: #94a3b8; font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
            <div style="color: {color}; font-size: 2rem; font-weight: 900; margin-top: 0.2rem; letter-spacing: -0.5px;">{value}</div>
        </div>
    """
    m1.markdown(
        metric_template.format(
            label="🏆 Highest MVP Total",
            value=f"{format_points(overall_rankings['TotalPoints'].max())} PTS",
            color="#fbbf24",
        ),
        unsafe_allow_html=True,
    )
    m2.markdown(
        metric_template.format(
            label="📈 Average Athlete Score",
            value=f"{format_points(overall_rankings['TotalPoints'].mean())} PTS",
            color="#10b981",
        ),
        unsafe_allow_html=True,
    )
    m3.markdown(
        metric_template.format(
            label="👥 Total Ranked Athletes",
            value=f"{len(overall_rankings)} PLAYERS",
            color="#38bdf8",
        ),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------
    # 5. ATHLETE FILTER BAY
    # --------------------------------------------------
    with st.container(border=True):
        st.markdown(
            '<div style="color:#fbbf24; font-weight:900; font-size:0.85rem; letter-spacing:1px; margin-bottom:0.5rem;">'
            '🔍 FILTER COMPETITORS'
            '</div>',
            unsafe_allow_html=True,
        )
        col_search, col_team, col_sport = st.columns([2, 1, 1])
        search_query = col_search.text_input(
            "Search Name", placeholder="Type a player name...", label_visibility="collapsed"
        )
        team_options = ["All Franchises"] + sorted(athlete_df["Team"].dropna().unique().tolist())
        sport_options = ["All Disciplines"] + sorted(athlete_df["Sport"].dropna().unique().tolist())
        selected_team = col_team.selectbox("Team", team_options, label_visibility="collapsed")
        selected_sport = col_sport.selectbox("Sport", sport_options, label_visibility="collapsed")

    # Apply Filters
    filtered_df = athlete_df.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Participant"].str.contains(search_query, case=False, na=False)
        ]
    if selected_team != "All Franchises":
        filtered_df = filtered_df[filtered_df["Team"] == selected_team]
    if selected_sport != "All Disciplines":
        filtered_df = filtered_df[filtered_df["Sport"] == selected_sport]

    if filtered_df.empty:
        st.warning("No athletes found matching the active filter criteria.")
        return

    # Recalculate visible ranking based on active filter
    # Recalculate visible ranking based on active filter
    active_totals = (
        filtered_df.groupby(["Participant", "Team"], as_index=False)["TotalPoints"]
        .sum()
    )
    
    # 👈 Assign true competition rank
    active_totals["Filtered_Rank"] = active_totals["TotalPoints"].rank(method="min", ascending=False).astype(int)
    active_totals = active_totals.sort_values(
        by=["Filtered_Rank", "TotalPoints", "Participant"], 
        ascending=[True, False, True]
    ).reset_index(drop=True)

    # Compute tie label (e.g. T-1 vs #1)
    rank_counts = active_totals["Filtered_Rank"].value_counts()
    active_totals["RankLabel"] = active_totals["Filtered_Rank"].apply(
        lambda r: f"T-{r}" if rank_counts[r] > 1 else f"#{r}"
    )

    # --------------------------------------------------
    # 6. ATHLETE SCORECARD GRID (2-COLUMN LAYOUT)
    # --------------------------------------------------
    records = active_totals.to_dict("records")
    for idx in range(0, len(records), 2):
        row_cols = st.columns(2)
        for col, item in zip(row_cols, records[idx : idx + 2]):
            participant_records = filtered_df[
                (filtered_df["Participant"] == item["Participant"])
                & (filtered_df["Team"] == item["Team"])
            ]
            with col:
                render_aggregated_player_card(
                    item["Participant"],
                    item["Team"],
                    participant_records,
                    int(item["Filtered_Rank"]),
                    str(item["RankLabel"]),  # 👈 Passed dynamic label
                )


if __name__ == "__main__":
    main()