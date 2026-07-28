"""AMC GraphQL + showtime page scraping for Odyssey IMAX 70mm."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

from odyssey_watcher.config import Settings

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.amctheatres.com",
    "Referer": "https://www.amctheatres.com/",
}

SEAT_QUERY = """
query TicketSelection($showtimeId: Int!, $hasToken: Boolean!) {
  viewer {
    showtime(id: $showtimeId) {
      showtimeId
      display { date time amPm }
      movie { name }
      seatingLayout {
        seats {
          name
          available
          seatStatus
          type
        }
      }
    }
  }
}
"""

RESERVABLE_TYPES = frozenset(
    {"CanReserve", "Premium", "Recliner", "LoveSeatLeft", "LoveSeatRight"}
)


@dataclass(frozen=True)
class DiscoveredShowtime:
    showtime_id: int
    show_date: date
    time_label: str
    booking_url: str


@dataclass(frozen=True)
class SeatSnapshot:
    showtime_id: int
    label: str
    available_seats: frozenset[str]
    booking_url: str
    show_date: date


def _session() -> curl_requests.Session:
    session = curl_requests.Session(impersonate="chrome131")
    session.headers.update(BROWSER_HEADERS)
    return session


def showtimes_page_url(settings: Settings, show_date: date) -> str:
    datestr = show_date.isoformat()
    return (
        f"{settings.amc_web_base}/movie-theatres/"
        f"{settings.theatre_location}/{settings.theatre_key}/showtimes/all/"
        f"{datestr}/{settings.theatre_key}/{settings.premium_offering}"
    )


def _is_imax_70mm_header(text: str) -> bool:
    normalized = " ".join(text.split()).upper()
    if "IMAX" not in normalized or "70" not in normalized:
        return False
    if "GREATER DETAIL" in normalized:
        return False
    return True


def _parse_imax_showtimes_from_html(
    html: str,
    settings: Settings,
    show_date: date,
) -> list[DiscoveredShowtime]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[DiscoveredShowtime] = []

    film_blocks = soup.select(".ShowtimesByTheatre-film")
    if not film_blocks:
        film_blocks = soup.select("[class*='ShowtimesByTheatre-film']")

    for film in film_blocks:
        title_el = film.select_one(".MovieTitleHeader-title h2")
        if title_el is None:
            title_el = film.find("h2")
        if title_el is None:
            continue
        title = title_el.get_text(strip=True)
        if title.lower() != settings.movie_title.lower():
            continue

        for header in film.find_all(["h2", "h3", "h4", "p", "span", "div"]):
            header_text = header.get_text(" ", strip=True)
            if not _is_imax_70mm_header(header_text):
                continue

            container = header
            links: list[Any] = []
            for _ in range(8):
                if container is None:
                    break
                links = container.select("a[href*='/showtimes/']")
                if links:
                    break
                container = container.parent

            for link in links:
                href = link.get("href", "")
                match = re.search(r"/showtimes/(\d+)", href)
                if not match:
                    continue
                showtime_id = int(match.group(1))
                time_label = link.get_text(" ", strip=True) or "unknown time"
                booking_url = (
                    href
                    if href.startswith("http")
                    else f"{settings.amc_web_base}{href}"
                )
                results.append(
                    DiscoveredShowtime(
                        showtime_id=showtime_id,
                        show_date=show_date,
                        time_label=time_label,
                        booking_url=booking_url,
                    )
                )

    deduped: dict[int, DiscoveredShowtime] = {s.showtime_id: s for s in results}
    return list(deduped.values())


def discover_imax_70mm_showtimes(
    settings: Settings,
    session: curl_requests.Session | None = None,
) -> list[DiscoveredShowtime]:
    session = session or _session()
    today = date.today()
    discovered: list[DiscoveredShowtime] = []

    for offset in range(settings.lookahead_days):
        show_date = today + timedelta(days=offset)
        url = showtimes_page_url(settings, show_date)
        try:
            response = session.get(url, timeout=45)
        except curl_requests.RequestsError as exc:
            logger.warning("showtimes fetch failed %s: %s", url, exc)
            continue

        if response.status_code >= 400:
            logger.warning(
                "showtimes HTTP %s for %s", response.status_code, show_date
            )
            continue

        day_showtimes = _parse_imax_showtimes_from_html(
            response.text, settings, show_date
        )
        logger.info(
            "discovered %d IMAX 70mm showtimes for %s",
            len(day_showtimes),
            show_date,
        )
        discovered.extend(day_showtimes)

    deduped: dict[int, DiscoveredShowtime] = {s.showtime_id: s for s in discovered}
    return list(deduped.values())


def fetch_available_seats(
    settings: Settings,
    showtime_id: int,
    session: curl_requests.Session | None = None,
) -> dict[str, Any] | None:
    session = session or _session()
    payload = {
        "operationName": "TicketSelection",
        "variables": {"showtimeId": showtime_id, "hasToken": False},
        "query": SEAT_QUERY,
    }
    try:
        response = session.post(
            settings.amc_graph_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45,
        )
    except curl_requests.RequestsError as exc:
        logger.warning("GraphQL failed showtime=%s: %s", showtime_id, exc)
        return None

    if response.status_code >= 400:
        logger.warning(
            "GraphQL HTTP %s showtime=%s", response.status_code, showtime_id
        )
        return None

    try:
        return response.json()
    except ValueError:
        logger.warning("GraphQL invalid JSON showtime=%s", showtime_id)
        return None


def _available_seat_names(seats: list[dict[str, Any]]) -> frozenset[str]:
    available: set[str] = set()
    for seat in seats:
        if not seat.get("available"):
            continue
        if seat.get("seatStatus") == "Sold":
            continue
        seat_type = seat.get("type")
        if seat_type in {"NotASeat", "Wheelchair", "Companion"}:
            continue
        if seat_type not in RESERVABLE_TYPES:
            continue
        name = seat.get("name")
        if name:
            available.add(str(name))
    return frozenset(available)


def snapshot_showtime(
    settings: Settings,
    discovered: DiscoveredShowtime,
    session: curl_requests.Session | None = None,
) -> SeatSnapshot | None:
    data = fetch_available_seats(settings, discovered.showtime_id, session)
    if not data:
        return None

    showtime = (
        data.get("data", {})
        .get("viewer", {})
        .get("showtime")
    )
    if not showtime:
        return None

    seats = showtime.get("seatingLayout", {}).get("seats", [])
    available = _available_seat_names(seats)
    display = showtime.get("display", {})
    movie_name = showtime.get("movie", {}).get("name", settings.movie_title)
    label = (
        f"{movie_name} — {display.get('date', discovered.show_date.isoformat())} "
        f"{display.get('time', discovered.time_label)}"
        f"{display.get('amPm', '')}"
    )
    return SeatSnapshot(
        showtime_id=discovered.showtime_id,
        label=label.strip(),
        available_seats=available,
        booking_url=f"{settings.amc_web_base}/showtimes/{discovered.showtime_id}/seats",
        show_date=discovered.show_date,
    )
