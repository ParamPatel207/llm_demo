# Blender MCP Setup

This workspace includes project-scoped Cursor MCP configuration for
[BlenderMCP](https://github.com/ahujasid/blender-mcp), which lets Cursor
control a live Blender session via natural language.

Blender MCP has two parts:

1. **Blender addon** — runs inside Blender and listens on a TCP socket
   (default `localhost:9876`)
2. **MCP server** — launched by Cursor via `uvx blender-mcp` and relays
   tool calls to the addon

## Prerequisites

- Blender 3.0 or newer
- Python 3.10 or newer (managed by `uv`)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

## Step 1: Install uv

**Linux / macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new shell so `~/.local/bin` is on your PATH, then verify:

```bash
uv --version
uvx --version
```

**macOS (Homebrew):**

```bash
brew install uv
```

**Windows (PowerShell):**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Add `%USERPROFILE%\.local\bin` to your user PATH if needed, then restart
Cursor.

## Step 2: Install the Blender addon

1. Open Blender
2. Go to **Edit → Preferences → Add-ons**
3. Click **Install...** and select `blender/addon.py` from this repo
4. Enable the addon by checking **Interface: Blender MCP**

## Step 3: Start the Blender connection

1. In the 3D Viewport, press `N` to open the sidebar
2. Open the **BlenderMCP** tab
3. Optionally enable **Poly Haven** for asset downloads
4. Click **Connect to Claude**

The addon must show an active connection before Cursor tools will work.

## Step 4: Enable MCP in Cursor

This repo ships [`.cursor/mcp.json`](../.cursor/mcp.json) with the
`blender` server preconfigured. After cloning:

1. Fully quit and relaunch Cursor (Cmd-Q on macOS, quit from tray on
   Windows)
2. Open **Settings → MCP**
3. Confirm `blender` appears with a green status indicator

### Windows configuration

If you are on Windows, update `.cursor/mcp.json` to use `cmd`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "cmd",
      "args": ["/c", "uvx", "--python", "3.11", "blender-mcp"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876",
        "UV_PYTHON_PREFERENCE": "only-managed",
        "DISABLE_TELEMETRY": "true"
      }
    }
  }
}
```

## Step 5: Verify the setup

1. Confirm the MCP server binary resolves:

   ```bash
   uvx --python 3.11 blender-mcp --help
   ```

2. In Cursor chat, check that Blender tools appear (hammer icon)
3. Try a prompt such as: `List all objects in the current Blender scene`

## Remote Blender host

If Blender runs on another machine, set `BLENDER_HOST` and `BLENDER_PORT`
in `.cursor/mcp.json` (or in your environment) to point at that host.

## Troubleshooting

### `spawn uvx ENOENT` in Cursor

GUI apps do not inherit your shell PATH. Use the absolute path to `uvx`:

```bash
which uvx   # macOS / Linux
where uvx   # Windows
```

Set that path as the `"command"` value in `.cursor/mcp.json`.

### Connection refused

- Blender must be running with the addon enabled
- Click **Connect to Claude** in the BlenderMCP sidebar panel
- Confirm host/port match (`localhost:9876` by default)
- Check that nothing else is using port 9876

### Client closed / server won't start

- Fully quit and relaunch Cursor after editing MCP config
- Pin Python 3.11 (already set in this repo's config)
- Clear a stale cache: `uv cache clean blender-mcp && uvx --refresh blender-mcp`

### Only one MCP server instance

Run the Blender MCP server from **either** Cursor **or** Claude Desktop,
not both at the same time.

### Security note

Blender MCP can execute LLM-generated Python inside Blender without
sandboxing. Save your work before using it, and avoid running it on
machines with sensitive data.

## References

- [BlenderMCP GitHub](https://github.com/ahujasid/blender-mcp)
- [Cursor MCP documentation](https://cursor.com/help/customization/mcp)
- [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

## Cloud environment (Cursor Cloud Agent VM)

Blender MCP **can** run in a headless Linux cloud VM using a virtual display.
This was verified on the Cursor Cloud Agent VM: Blender 4.0 + `xvfb-run` +
the MCP addon listening on `localhost:9876`, with `uvx blender-mcp` connecting
successfully.

### Limitations

- **Cloud Agent MCP tools**: Cursor Cloud Agents may not expose the `blender`
  MCP server from `.cursor/mcp.json` as callable tools in the agent session
  (only internal tools like `cursor-cloud` may appear). The stack runs on the
  VM, but the agent may not be able to invoke it directly yet.
- **Ephemeral VM**: Blender must be started on each new cloud agent run unless
  you add the setup scripts to a [Cursor environment](https://cursor.com/docs)
  build.
- **No real GUI**: Rendering/viewport screenshots work, but there is no
  interactive Blender window — use `xvfb-run`, not `blender -b` (background mode
  blocks the addon server).

### Cloud quick start

From the repo root on a Linux cloud VM:

```bash
./scripts/cloud-blender-mcp-setup.sh   # once: install Blender, uv, enable addon
./scripts/cloud-blender-mcp-start.sh   # start Blender + MCP addon on :9876
./scripts/cloud-blender-mcp-verify.sh  # confirm addon + blender-mcp connect
```

The addon auto-starts its TCP server when Blender loads (default port `9876`).
Test manually:

```bash
uvx --python 3.11 blender-mcp --help
```

For day-to-day use, **local setup** (Blender on your machine + Cursor MCP) is
still the recommended path — lower latency, persistent GUI, and full MCP tool
integration in the Cursor desktop app.
