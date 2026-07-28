"""Poll AMC and send ntfy alerts when Odyssey IMAX 70mm seats open."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from curl_cffi import requests as curl_requests

from odyssey_watcher.amc import (
    discover_imax_70mm_showtimes,
    snapshot_showtime,
)
from odyssey_watcher.config import Settings
from odyssey_watcher.ntfy import publish_seat_alert, send_ntfy

logger = logging.getLogger(__name__)


@dataclass
class WatcherState:
    last_available: dict[str, list[str]]
    last_alert_at: dict[str, str]

    @classmethod
    def empty(cls) -> WatcherState:
        return WatcherState(last_available={}, last_alert_at={})

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_available": self.last_available,
            "last_alert_at": self.last_alert_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatcherState:
        return WatcherState(
            last_available={
                str(k): list(v) for k, v in data.get("last_available", {}).items()
            },
            last_alert_at={
                str(k): str(v) for k, v in data.get("last_alert_at", {}).items()
            },
        )


def load_state(path: Path) -> WatcherState:
    if not path.exists():
        return WatcherState.empty()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return WatcherState.from_dict(raw)
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("could not load state %s: %s", path, exc)
        return WatcherState.empty()


def save_state(path: Path, state: WatcherState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def run_poll(settings: Settings) -> dict[str, Any]:
    session = curl_requests.Session(impersonate="chrome131")
    state = load_state(settings.state_path)
    summary: dict[str, Any] = {
        "discovered": 0,
        "alerts_sent": 0,
        "new_seats": [],
    }

    showtimes = discover_imax_70mm_showtimes(settings, session)
    summary["discovered"] = len(showtimes)

    for discovered in showtimes:
        snapshot = snapshot_showtime(settings, discovered, session)
        if snapshot is None:
            continue

        key = str(snapshot.showtime_id)
        previous = frozenset(state.last_available.get(key, []))
        current = snapshot.available_seats
        new_seats = sorted(current - previous)

        state.last_available[key] = sorted(current)

        if not new_seats:
            continue

        month_abbr = discovered.show_date.strftime("%b").lower()
        day = discovered.show_date.day
        publish_seat_alert(
            settings,
            showtime_label=snapshot.label,
            seat_names=new_seats,
            showtime_id=snapshot.showtime_id,
            month_abbr_lower=month_abbr,
            day=day,
        )
        state.last_alert_at[key] = datetime.utcnow().isoformat()
        summary["alerts_sent"] += 1
        summary["new_seats"].append(
            {
                "showtime_id": snapshot.showtime_id,
                "seats": new_seats,
                "label": snapshot.label,
            }
        )
        logger.info(
            "alert showtime=%s new_seats=%s",
            snapshot.showtime_id,
            ", ".join(new_seats),
        )

    save_state(settings.state_path, state)
    return summary


def send_startup_ping(settings: Settings) -> None:
    message = (
        "Odyssey IMAX 70mm watcher is running. "
        f"Polling every {settings.poll_interval_seconds}s. "
        f"Topic (all days): {settings.ntfy_topic_all}"
    )
    send_ntfy(
        settings,
        topic=settings.ntfy_topic_all,
        message=message,
        title="Watcher started",
        priority="default",
    )
