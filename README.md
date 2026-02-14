<img src="https://feralfile.com/assets/feralfile-og.png" width="200" alt="Feral File" />

# ff1ctl

**CLI and agent toolkit for the [Feral File](https://feralfile.com) FF1 art computer.**
Zero-config discovery. Full device control. Agent-ready.

---

## Quickstart — Claude Code Plugin

The fastest way to get started. Install as a Claude Code plugin and get MCP tools, skills, and the `/ff1` slash command in one step:

```bash
claude plugin install github.com/dmichael/ff1
```

Then just ask Claude:

> "Discover my FF1 and show its status"
> "Play this artwork on my FF1: https://example.com/art.html"
> "Rotate the screen and set volume to 30%"

Or use the slash command:

```
/ff1 build a playlist from these URLs and display it
```

## Install

### As a Python package

```bash
pip install ff1ctl          # CLI + Python library
pip install ff1ctl[mcp]     # + MCP server
```

Or run without installing:

```bash
uvx ff1ctl discover
```

### As an MCP server (manual)

Add to your Claude Code or Claude Desktop config:

```json
{
  "mcpServers": {
    "ff1": {
      "command": "uvx",
      "args": ["ff1ctl[mcp]", "ff1-mcp"]
    }
  }
}
```

**Available MCP tools:** `ff1_discover`, `ff1_status`, `ff1_rotate`, `ff1_set_volume`, `ff1_toggle_mute`, `ff1_send_key`, `ff1_shutdown`, `ff1_reboot`, `ff1_update`, `ff1_play_url`, `ff1_play_playlist`, `ff1_player_status`, `ff1_build_playlist`

## Features

- **Zero-config discovery** — finds FF1 devices on your network automatically (ARP + mDNS hostname matching)
- **Full device control** — rotate, volume, mute, reboot, shutdown, firmware update
- **DP1 playlist builder** — create valid playlists from artwork URLs, pipe them to the device
- **JSON output** — every command returns structured JSON, perfect for scripting and agents
- **MCP server** — expose all tools to Claude Code, Claude Desktop, or any MCP client
- **Claude Code plugin** — one-command install bundles MCP tools, skills, and slash commands
- **Python async client** — `await client.rotate()` from your own code
- **Multi-device aware** — explicit selection when multiple FF1s are on the network

## Python Library

```python
from ff1 import FF1Client

client = FF1Client(host="192.168.1.42")

status = await client.get_device_status()
print(status.volume, status.screen_rotation)

await client.rotate(clockwise=True)
await client.set_volume(75)
await client.display_playlist(playlist_url="https://example.com/playlist.json")
```

## Configuration

**ff1ctl works without any configuration.** It discovers devices automatically by scanning the ARP table for hostnames matching `FF1-*`.

For devices with API keys or when you want to name your devices, create `ff1.json` (or `~/.config/ff1/config.json`):

```json
{
  "devices": [
    {
      "name": "Living Room",
      "host": "192.168.1.42",
      "apiKey": "optional-api-key",
      "topicID": "optional-topic-id"
    }
  ]
}
```

## Architecture

```
Humans / Scripts ──► ff1ctl CLI ──┐
AI Agents (Skill) ──► ff1ctl CLI ──┤──► FF1Client ──► HTTP :1111 ──► feral-controld
AI Agents (MCP)   ──► MCP Server ──┘
```

Three layers, one codebase:
1. **Client library** (`ff1.client`) — async Python, talks HTTP/WS to the device
2. **CLI** (`ff1ctl`) — structured JSON output for humans and scripts
3. **MCP server** (`ff1-mcp`) — tool interface for AI agents

## CLI Reference

```bash
# Discovery & Status
ff1ctl discover                    # Find FF1 devices on the network
ff1ctl status                      # Device info (orientation, wifi, version, volume)
ff1ctl player                      # Current playback status

# Display Artwork
ff1ctl play <url>                  # Display a single artwork
ff1ctl play <url> --duration 60    # Set display duration (seconds)
ff1ctl playlist <url>              # Play a DP1 playlist from URL
ff1ctl playlist <file.json>        # Play from local file
ff1ctl playlist -                  # Play from stdin

# Build Playlists
ff1ctl build <url1> <url2> --title "My Show" --duration 120
ff1ctl build <url1> <url2> | ff1ctl playlist -    # Build and play

# Device Control
ff1ctl rotate                      # Rotate clockwise
ff1ctl rotate --ccw                # Rotate counter-clockwise
ff1ctl volume 50                   # Set volume (0-100)
ff1ctl mute                        # Toggle mute
ff1ctl key 13                      # Send keyboard event

# System
ff1ctl reboot                      # Reboot
ff1ctl shutdown                    # Shutdown
ff1ctl update                      # OTA firmware update
```

All commands accept `--device HOST` to target a specific device and `--pretty` for formatted output.

## Development

```bash
git clone https://github.com/dmichael/ff1.git && cd ff1
python -m venv .venv && source .venv/bin/activate
pip install -e ".[mcp]"
pytest
```

## License

MIT
