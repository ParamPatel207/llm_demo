#!/usr/bin/env bash
# Install Blender + uv and enable the BlenderMCP addon for headless cloud use.
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"

echo "==> Installing Blender..."
sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y blender xvfb

echo "==> Installing uv..."
if ! command -v uvx >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
	export PATH="${HOME}/.local/bin:${PATH}"
fi

BL_VER="$(blender --version | head -1 | awk '{print $2}' | cut -d. -f1,2)"
ADDON_DIR="${HOME}/.config/blender/${BL_VER}/scripts/addons"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "${ADDON_DIR}"
cp "${REPO_ROOT}/blender/addon.py" "${ADDON_DIR}/blender_mcp.py"

echo "==> Enabling BlenderMCP addon..."
blender --background --python-expr "
import bpy, addon_utils
addon_utils.enable('blender_mcp', default_set=True, persistent=True)
bpy.ops.wm.save_userpref()
print('BlenderMCP addon enabled')
" 2>&1 | tail -5

echo "==> Setup complete. Start Blender with: ./scripts/cloud-blender-mcp-start.sh"
