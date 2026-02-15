---
description: Control an FF1 art computer — discover devices, display artwork, rotate screen, adjust volume, build playlists
---

Control FF1 art computers using the `ff1_*` MCP tools. Devices are auto-discovered — no setup needed.

**User request:** $ARGUMENTS

Use the appropriate MCP tool to fulfill this request:

- `ff1_discover()` — find devices
- `ff1_status(device?)` — device info
- `ff1_play_url(url, duration?, device?)` — display artwork
- `ff1_play_playlist(playlist_url, device?)` — play a DP1 playlist
- `ff1_build_playlist(urls, title?, duration?, scaling?, background?)` — build a playlist
- `ff1_rotate(clockwise?, device?)` — rotate screen
- `ff1_set_volume(percent, device?)` — set volume (0-100)
- `ff1_toggle_mute(device?)` — toggle mute
- `ff1_player_status(device?)` — playback status
- `ff1_reboot(device?)` / `ff1_shutdown(device?)` — system control

Pass `device` only when multiple FF1s exist on the network.
