# Odyssey IMAX 70mm seat watcher

Monitors **The Odyssey** IMAX **70mm** showtimes at **AMC Lincoln Square 13** and pushes **ntfy** alerts when seats open (cancellations / new inventory).

This mirrors the Reddit setup (`odyssey_nyc_all` plus per-day topics like `odyssey_nyc_jul28`).

## Important

AMC uses Queue-it and Cloudflare. Run this on your **home computer** (or a residential IP), not a typical cloud VPS. Datacenter IPs are often blocked.

## Phone setup (30 seconds)

1. Install [ntfy](https://ntfy.sh/) (App Store / Play Store) or use https://ntfy.sh in a browser.
2. Add subscription → topic: `odyssey_nyc_all` (or your custom topic from `.env`).
3. Optional: subscribe only to one day, e.g. `odyssey_nyc_jul31` or `odyssey_nyc_aug1`.

## Run the watcher

```bash
cd odyssey_watcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env if you want a private topic name instead of odyssey_nyc_all
python -m odyssey_watcher --once -v
python -m odyssey_watcher
```

From the repo root (after `pip install -r odyssey_watcher/requirements.txt`):

```bash
PYTHONPATH=. python -m odyssey_watcher
```

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `NTFY_TOPIC_ALL` | `odyssey_nyc_all` | ntfy topic for all showtimes |
| `NTFY_BASE_URL` | `https://ntfy.sh` | ntfy server |
| `NTFY_TOKEN` | (empty) | Bearer token for protected topics |
| `POLL_INTERVAL_SECONDS` | `45` | Poll frequency |
| `LOOKAHEAD_DAYS` | `25` | Days ahead to scan |

Per-day topics are always `odyssey_nyc_{mon}{day}` (e.g. `odyssey_nyc_jul28`, `odyssey_nyc_aug1`).

## What you get in each alert

- Showtime date and time
- Exact available seat numbers
- Tap-to-open link to the AMC seat map

## Keep it running

**macOS (launchd):** create `~/Library/LaunchAgents/com.odyssey.watcher.plist` pointing to your venv Python and repo path, then `launchctl load` it.

**Linux:** use `systemd` user service or `cron` with `@reboot`.

## Or use the public Reddit channel

If you only want alerts without running anything, subscribe to `odyssey_nyc_all` in ntfy (when the original poster’s service is up). This project is for running your **own** watcher with your own topic.
