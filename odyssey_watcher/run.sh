#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
if [[ ! -d odyssey_watcher/.venv ]]; then
  python3 -m venv odyssey_watcher/.venv
  odyssey_watcher/.venv/bin/pip install -r odyssey_watcher/requirements.txt
fi
# shellcheck source=/dev/null
source odyssey_watcher/.venv/bin/activate
if [[ ! -f odyssey_watcher/.env ]]; then
  cp odyssey_watcher/.env.example odyssey_watcher/.env
  echo "Created odyssey_watcher/.env — set NTFY_TOPIC_ALL to your ntfy subscription topic."
fi
exec python -m odyssey_watcher "$@"
