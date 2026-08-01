#!/usr/bin/env bash
# Start Blender with a virtual display so the MCP addon can listen on :9876.
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"
LOG_FILE="${LOG_FILE:-/tmp/blender-mcp.log}"
SESSION_NAME="${SESSION_NAME:-blender-mcp-server}"

if ss -tlnp 2>/dev/null | grep -q ':9876 '; then
	echo "Blender MCP already listening on port 9876"
	exit 0
fi

if tmux -f /exec-daemon/tmux.portal.conf has-session -t "=${SESSION_NAME}" 2>/dev/null; then
	echo "Stopping existing Blender tmux session..."
	tmux -f /exec-daemon/tmux.portal.conf kill-session -t "${SESSION_NAME}" 2>/dev/null || true
	sleep 2
fi

tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "${SESSION_NAME}" -c "$(pwd)" -- "${SHELL:-bash}" -l
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "${SESSION_NAME}:0.0" \
	"export PATH=\"\${HOME}/.local/bin:\${PATH}\"; xvfb-run -a blender 2>&1 | tee ${LOG_FILE}" C-m

echo "Waiting for Blender MCP on port 9876..."
for _ in $(seq 1 30); do
	if ss -tlnp 2>/dev/null | grep -q ':9876 '; then
		echo "Blender MCP server is running on localhost:9876"
		echo "Log: ${LOG_FILE}"
		exit 0
	fi
	sleep 2
done

echo "Timed out waiting for port 9876. Check ${LOG_FILE}"
exit 1
