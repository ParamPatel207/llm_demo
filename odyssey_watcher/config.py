"""Configuration for the Odyssey IMAX 70mm seat watcher."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PACKAGE_DIR = Path(__file__).resolve().parent
load_dotenv(_PACKAGE_DIR / ".env")
load_dotenv()


@dataclass(frozen=True)
class Settings:
    ntfy_base_url: str
    ntfy_topic_all: str
    ntfy_token: str | None
    poll_interval_seconds: int
    lookahead_days: int
    theatre_location: str
    theatre_key: str
    movie_title: str
    premium_offering: str
    state_path: Path
    amc_graph_url: str
    amc_web_base: str


def load_settings() -> Settings:
    state_path = Path(
        os.getenv("STATE_PATH", str(_PACKAGE_DIR / "data" / "state.json"))
    )
    return Settings(
        ntfy_base_url=os.getenv("NTFY_BASE_URL", "https://ntfy.sh").rstrip("/"),
        ntfy_topic_all=os.getenv("NTFY_TOPIC_ALL", "odyssey_nyc_my_alerts"),
        ntfy_token=os.getenv("NTFY_TOKEN"),
        poll_interval_seconds=max(15, int(os.getenv("POLL_INTERVAL_SECONDS", "45"))),
        lookahead_days=max(1, int(os.getenv("LOOKAHEAD_DAYS", "25"))),
        theatre_location=os.getenv("THEATRE_LOCATION", "new-york-city"),
        theatre_key=os.getenv("THEATRE_KEY", "amc-lincoln-square-13"),
        movie_title=os.getenv("MOVIE_TITLE", "The Odyssey"),
        premium_offering=os.getenv("PREMIUM_OFFERING", "70mm"),
        state_path=state_path,
        amc_graph_url=os.getenv(
            "AMC_GRAPH_URL", "https://graph.amctheatres.com"
        ),
        amc_web_base=os.getenv("AMC_WEB_BASE", "https://www.amctheatres.com"),
    )
