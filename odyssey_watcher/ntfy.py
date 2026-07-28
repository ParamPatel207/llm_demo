"""Publish alerts to ntfy.sh (or a self-hosted ntfy server)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from odyssey_watcher.config import Settings

logger = logging.getLogger(__name__)


def ntfy_topic_for_date(month_abbr_lower: str, day: int) -> str:
    return f"odyssey_nyc_{month_abbr_lower}{day}"


def send_ntfy(
    settings: Settings,
    topic: str,
    message: str,
    title: str | None = None,
    click_url: str | None = None,
    priority: str = "high",
) -> bool:
    url = f"{settings.ntfy_base_url}/{topic}"
    headers: dict[str, str] = {}
    if settings.ntfy_token:
        headers["Authorization"] = f"Bearer {settings.ntfy_token}"
    if title:
        headers["Title"] = title
    if click_url:
        headers["Click"] = click_url
    if priority:
        headers["Priority"] = priority

    try:
        response = httpx.post(url, content=message, headers=headers, timeout=20.0)
        if response.status_code >= 400:
            logger.error(
                "ntfy publish failed topic=%s status=%s body=%s",
                topic,
                response.status_code,
                response.text[:300],
            )
            return False
        return True
    except httpx.HTTPError as exc:
        logger.error("ntfy request error topic=%s: %s", topic, exc)
        return False


def publish_seat_alert(
    settings: Settings,
    *,
    showtime_label: str,
    seat_names: list[str],
    showtime_id: int,
    month_abbr_lower: str,
    day: int,
) -> dict[str, Any]:
    seats_text = ", ".join(seat_names)
    click_url = f"{settings.amc_web_base}/showtimes/{showtime_id}/seats"
    message = (
        f"{showtime_label}\n"
        f"Seats: {seats_text}\n"
        f"Book: {click_url}"
    )
    title = "Odyssey IMAX 70mm — seats open"
    day_topic = ntfy_topic_for_date(month_abbr_lower, day)
    results: dict[str, Any] = {}
    for topic in (settings.ntfy_topic_all, day_topic):
        ok = send_ntfy(
            settings,
            topic=topic,
            message=message,
            title=title,
            click_url=click_url,
        )
        results[topic] = ok
    return results
