---
name: ff1-control
description: Control FF1 art computers — discover devices, display artwork, rotate, volume, playlists. Use when the user mentions FF1, art computer, or Feral File device control.
---

You can control FF1 art computers using the `ff1ctl` CLI. All commands output JSON. `--pretty` is a **top-level** flag that goes before the subcommand: `ff1ctl --pretty play <url>`.

## Discovery

FF1 devices are automatically discovered on the local network — no configuration needed. The tool finds devices by scanning the ARP table for hostnames matching `FF1-*` (every FF1 announces itself as `FF1-XXXXXXXX` via mDNS).

```bash
ff1ctl discover              # Find FF1 devices on the network
```

For devices with API keys or topic IDs, create `ff1.json` or `~/.config/ff1/config.json`:
```json
{
  "devices": [
    {"name": "Living Room", "host": "192.168.1.100", "apiKey": "...", "topicID": "..."}
  ]
}
```

You can also target any device directly with `--device HOST`.

## Commands

### Device info
```bash
ff1ctl discover              # Find FF1 devices on the network
ff1ctl status                # Device status (orientation, wifi, version, volume)
ff1ctl player                # Current playback status
```

### Display artwork
```bash
ff1ctl play <url>                          # Display a single artwork
ff1ctl play <url> --duration 60            # Display for 60 seconds
ff1ctl playlist <url>                      # Play a DP1 playlist from URL
ff1ctl playlist <file.json>                # Play a DP1 playlist from file
ff1ctl build <url1> <url2> --title "Show"  # Build a playlist JSON
ff1ctl build <url1> <url2> | ff1ctl playlist -  # Build and play immediately
```

### Device control
```bash
ff1ctl rotate                # Rotate screen clockwise
ff1ctl rotate --ccw          # Rotate counter-clockwise
ff1ctl volume 50             # Set volume to 50%
ff1ctl mute                  # Toggle mute
ff1ctl key 13                # Send keyboard event (13=Enter)
```

### System
```bash
ff1ctl reboot                # Reboot the device
ff1ctl shutdown              # Shutdown the device
ff1ctl update                # Trigger OTA firmware update
```

## Tips
- All commands auto-discover the first FF1 on the network if no config exists
- Use `--device <host>` to target a specific device by IP or hostname
- Pipe `ff1ctl build` output to `ff1ctl playlist -` for build-and-play workflows
- The FF1 API runs on port 1111 via `feral-controld`
