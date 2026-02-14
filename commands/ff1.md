---
description: Control an FF1 art computer — discover devices, display artwork, rotate screen, adjust volume, build playlists
---

You can control FF1 art computers using the `ff1ctl` CLI. Run `ff1ctl discover` first to find devices on the network, then use the result to run commands.

**User request:** $ARGUMENTS

Use the ff1ctl CLI to fulfill this request. All commands output JSON. Common commands:

- `ff1ctl discover` — find devices
- `ff1ctl status` — device info
- `ff1ctl play <url>` — display artwork
- `ff1ctl playlist <url|file|->` — play a DP1 playlist
- `ff1ctl build <url1> <url2> --title "Name"` — build a playlist
- `ff1ctl rotate [--ccw]` — rotate screen
- `ff1ctl volume <0-100>` — set volume
- `ff1ctl mute` — toggle mute
- `ff1ctl reboot` / `ff1ctl shutdown` — system control

Use `--device HOST` to target a specific device. Use `--pretty` for formatted output.
