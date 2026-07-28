"""CLI entrypoint for the Odyssey seat watcher."""

from __future__ import annotations

import argparse
import logging
import time

from odyssey_watcher.config import load_settings
from odyssey_watcher.watcher import run_poll, send_startup_ping


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch AMC Lincoln Square Odyssey IMAX 70mm seats and alert via ntfy."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll cycle instead of looping.",
    )
    parser.add_argument(
        "--no-startup-ping",
        action="store_true",
        help="Skip the startup notification on launch.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    settings = load_settings()

    if not args.no_startup_ping:
        send_startup_ping(settings)

    if args.once:
        summary = run_poll(settings)
        logging.info("poll complete: %s", summary)
        return

    while True:
        try:
            summary = run_poll(settings)
            logging.info("poll complete: %s", summary)
        except Exception:
            logging.exception("poll failed")
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
