<img src="https://feralfile.com/assets/feralfile-og.png" width="200" alt="Feral File" />

# `ff1ctl`

**Agent toolkit and CLI for the [Feral File](https://feralfile.com) [FF1](https://feralfile.substack.com/p/meet-ff1-the-art-computer-by-feral) art computer.**
Talk to your FF1 through Claude, the command line, or Python.

---

## Quickstart — Claude Code

```bash
claude plugin marketplace add dmichael/ff1
claude plugin install ff1@ff1
```

Then just ask:

> "Display this on my FF1: https://arweave.net/AqQfOQHzAGOa2ko16SwIuqQI4XpjDULEOSY6_6ssLnY"

Claude discovers the device and displays the artwork — no configuration needed:

```json
{"message": {"ok": true}}
{"using": "FF1-KZD1O1F7", "host": "192.168.1.79"}
```

That's it. You're displaying art.

More things you can say:

> "Rotate the screen and set volume to 30%"
> "Build a playlist from these URLs and display it"

Or use the slash command: `/ff1 discover my devices`

### MCP Server (without plugin)

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

> **Note:** `ff1ctl` is not yet on PyPI. Until then, [install from source](#development) and use `"command": "ff1-mcp"` instead.

**MCP tools:** `ff1_discover`, `ff1_status`, `ff1_rotate`, `ff1_set_volume`, `ff1_toggle_mute`, `ff1_send_key`, `ff1_shutdown`, `ff1_reboot`, `ff1_update`, `ff1_play_url`, `ff1_play_playlist`, `ff1_player_status`, `ff1_build_playlist`

---

## CLI

For humans and scripts. Every command outputs JSON.

### Install

```bash
git clone https://github.com/dmichael/ff1.git && cd ff1
pip install -e ".[mcp]"
```

### Usage

```bash
# Discover & display
ff1ctl discover                                  # Find FF1 devices on the network
ff1ctl play <url>                                # Display a single artwork
ff1ctl play <url> --duration 60                  # Display for 60 seconds

# Playlists
ff1ctl build <url1> <url2> --title "My Show"     # Build a playlist
ff1ctl build <url1> <url2> | ff1ctl playlist -   # Build and play immediately
ff1ctl playlist <file.json>                       # Play from file or URL

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

---

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
AI Agents (Plugin) ──► ff1ctl CLI ──┐
AI Agents (MCP)    ──► MCP Server ──┤──► FF1Client ──► HTTP :1111 ──► feral-controld
Humans / Scripts   ──► ff1ctl CLI ──┘
```

## Development

```bash
git clone https://github.com/dmichael/ff1.git && cd ff1
pip install -e ".[mcp]"
pytest
```

## Support

If you find this useful: `davidmichael.eth`

## License

MIT
