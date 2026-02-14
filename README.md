<img src="https://feralfile.com/assets/feralfile-og.png" width="200" alt="Feral File" />

# `ff1ctl`

**CLI and agent toolkit for the [Feral File](https://feralfile.com) FF1 art computer.**
Zero-config discovery. Full device control. Agent-ready.

---

## 1. Install

```bash
pip install ff1ctl
```

Or run without installing:

```bash
uvx ff1ctl discover
```

## 2. Discover

```bash
ff1ctl discover
```

The FF1 announces itself as `FF1-XXXXXXXX` via mDNS. No configuration needed — `ff1ctl` finds it automatically by scanning the ARP table.

## 3. Display

```bash
ff1ctl play https://arweave.net/AqQfOQHzAGOa2ko16SwIuqQI4XpjDULEOSY6_6ssLnY
```

Any publicly accessible URL works — web pages, images, NFT artwork on Arweave or IPFS. The above displays *Nothing Silent* by David Michael (from [Foundation](https://foundation.app/@davidmichael)):

```json
{"message": {"ok": true}}
{"using": "FF1-KZD1O1F7", "host": "192.168.1.79"}
```

That's it. You're displaying art.

---

## More Commands

```bash
# Playlists
ff1ctl build <url1> <url2> --title "My Show"   # Build a playlist
ff1ctl build <url1> <url2> | ff1ctl playlist -  # Build and play immediately
ff1ctl playlist <file.json>                      # Play from file or URL

# Device control
ff1ctl status                      # Device info (orientation, wifi, version, volume)
ff1ctl player                      # Current playback status
ff1ctl rotate                      # Rotate clockwise (--ccw for counter)
ff1ctl volume 50                   # Set volume (0-100)
ff1ctl mute                        # Toggle mute

# System
ff1ctl reboot
ff1ctl shutdown
ff1ctl update                      # OTA firmware update
```

`--device HOST` targets a specific device. `--pretty` goes before the subcommand: `ff1ctl --pretty status`.

## AI Agent Integration

### Claude Code Plugin (recommended)

```bash
claude plugin marketplace add dmichael/ff1
claude plugin install ff1@ff1
```

Then just ask Claude:

> "Play this artwork on my FF1: https://example.com/art.html"
> "Rotate the screen and set volume to 30%"

Or use the slash command: `/ff1 build a playlist from these URLs and display it`

The plugin provides MCP tools (self-contained) and a CLI skill. The skill requires `ff1ctl` in your PATH; MCP tools work without it.

### MCP Server (manual)

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

**MCP tools:** `ff1_discover`, `ff1_status`, `ff1_rotate`, `ff1_set_volume`, `ff1_toggle_mute`, `ff1_send_key`, `ff1_shutdown`, `ff1_reboot`, `ff1_update`, `ff1_play_url`, `ff1_play_playlist`, `ff1_player_status`, `ff1_build_playlist`

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

**ff1ctl works without any configuration.** For devices with API keys or when you want to name your devices, create `ff1.json` (or `~/.config/ff1/config.json`):

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

## Development

```bash
git clone https://github.com/dmichael/ff1.git && cd ff1
python -m venv .venv && source .venv/bin/activate
pip install -e ".[mcp]"
pytest
```

## License

MIT
