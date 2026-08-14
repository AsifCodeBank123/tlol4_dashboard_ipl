"""Application entry point for the TLOL4 Sports League Dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from utils import apply_theme_variables, load_css, refresh_data

CONFIG_PATH = Path("config.json")
CSS_PATH = Path("assets/style.css")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load application settings from config.json."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def initialize_session_state() -> None:
    """Initialize shared Streamlit session state values."""
    st.session_state.setdefault("last_refresh", None)


def render_sidebar(config: dict[str, Any]) -> None:
    """Render sidebar branding, refresh controls, and team links."""
    branding = config["branding"]

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="sidebar-title">{branding['sidebar_title']}</div>
                <div class="sidebar-subtitle">{branding['sidebar_subtitle']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔄 Refresh data", use_container_width=True):
            refresh_data()
            st.rerun()

        st.markdown("---")
        st.caption(config["app"]["footer_text"])


def run_app() -> None:
    """Configure and launch the multipage Streamlit application."""
    config = load_config()
    app_config = config["app"]

    st.set_page_config(
        page_title=app_config["title"],
        page_icon=app_config["page_icon"],
        layout=app_config.get("layout", "wide"),
    )

    initialize_session_state()
    apply_theme_variables(config)
    load_css(CSS_PATH)
    render_sidebar(config)

    team_pages = [
        st.Page(team["page"], title=team["name"], icon=team["emoji"])
        for team in config.get("teams", [])
        if team.get("page")
    ]

    pages = {
        "Dashboard": [
            st.Page("pages/Home.py", title="Home", icon="🏠"),
            st.Page("pages/Fixtures.py", title="Fixtures", icon="📅"),
            st.Page("pages/Leaderboard.py", title="Leaderboard", icon="🏅"),
        ],
        "Teams": team_pages,
    }
    navigation = st.navigation(pages)
    navigation.run()


if __name__ == "__main__":
    run_app()
