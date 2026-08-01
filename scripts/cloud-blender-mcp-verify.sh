#!/usr/bin/env bash
# Verify Blender addon and blender-mcp server can communicate.
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"

if ! ss -tlnp 2>/dev/null | grep -q ':9876 '; then
	echo "Blender MCP is not running. Start it first:"
	echo "  ./scripts/cloud-blender-mcp-start.sh"
	exit 1
fi

echo "==> Probing Blender addon on :9876..."
python3 -c "
import json, socket
s = socket.socket()
s.settimeout(5)
s.connect(('127.0.0.1', 9876))
s.send(json.dumps({'type': 'get_scene_info'}).encode() + b'\n')
print(s.recv(4096).decode())
s.close()
"

echo "==> Probing blender-mcp package..."
timeout 8 uvx --python 3.11 blender-mcp --help 2>&1 | grep -E 'Connected to Blender|BlenderMCP' || true
echo "Verification complete."
