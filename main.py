"""Application entry point for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from utils import apply_theme_variables, load_css

CONFIG_PATH = Path("config.json")
CSS_PATH = Path("assets/style.css")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load application settings from config.json."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def initialize_session_state() -> None:
    """Initialize shared Streamlit session state values."""
    st.session_state.setdefault("last_refresh", None)
    st.session_state.setdefault("team_pages", {})


def run_app() -> None:
    """Configure and launch the flat topbar Streamlit navigation."""
    config = load_config()
    app_config = config["app"]

    st.set_page_config(
        page_title=app_config["title"],
        page_icon=app_config["page_icon"],
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    initialize_session_state()
    apply_theme_variables(config)
    load_css(CSS_PATH)

    # 1. Primary Tournament Hub Pages
    home_page = st.Page("pages/Home.py", title="Home", icon="🏠", default=True)
    fixtures_page = st.Page("pages/Fixtures.py", title="Fixtures", icon="📅")
    leaderboard_page = st.Page("pages/Leaderboard.py", title="Leaderboard", icon="🏅")

    # 2. Individual Team Pages
    team_pages_dict: dict[str, st.Page] = {}
    team_page_list: list[st.Page] = []

    for team in config.get("teams", []):
        page_path = team.get("page")
        if page_path:
            page_obj = st.Page(
                page_path,
                title=team.get("short_name", team["name"]),
                icon=team.get("emoji", "🛡️"),
            )
            team_pages_dict[team["name"]] = page_obj
            team_page_list.append(page_obj)

    st.session_state["team_pages"] = team_pages_dict
    st.session_state["main_pages"] = {
        "Home": home_page,
        "Fixtures": fixtures_page,
        "Leaderboard": leaderboard_page,
    }

    # 3. Flat List creates horizontal tabs in Streamlit topbar
    all_pages = [home_page, fixtures_page, leaderboard_page] + team_page_list

    navigation = st.navigation(all_pages, position="top")
    navigation.run()


if __name__ == "__main__":
    run_app()