---
name: ff1-control
description: Control FF1 art computers — discover devices, display artwork, rotate, volume, playlists. Use when the user mentions FF1, art computer, or Feral File device control.
---

Control FF1 art computers using the `ff1_*` MCP tools. Devices are auto-discovered on the local network — no configuration needed.

## MCP Tools

### Discovery & status
- `ff1_discover()` — find FF1 devices on the network
- `ff1_status(device?)` — device info (orientation, wifi, version, volume)
- `ff1_player_status(device?)` — current playback status

### Display artwork
- `ff1_play_url(url, duration=300, device?)` — display a single artwork URL
- `ff1_play_playlist(playlist_url, device?)` — play a DP1 playlist from URL
- `ff1_build_playlist(urls, title?, duration?, scaling?, background?)` — build a DP1 playlist JSON (does not send to device)

### Device control
- `ff1_rotate(clockwise=True, device?)` — rotate screen
- `ff1_set_volume(percent, device?)` — set volume (0-100)
- `ff1_toggle_mute(device?)` — toggle mute
- `ff1_send_key(code, device?)` — send keyboard event (e.g. 13=Enter)

### System
- `ff1_reboot(device?)` — reboot the device
- `ff1_shutdown(device?)` — shutdown the device
- `ff1_update(device?)` — trigger OTA firmware update

## Tips
- All tools auto-discover the device if only one FF1 is on the network
- Pass `device` (name or IP) only when multiple devices exist
- `ff1_build_playlist` returns JSON — pass its output URL to `ff1_play_playlist` or use `ff1_play_url` for single artworks
- Artwork URLs are typically IPFS/Arweave links or any web-accessible media
