"""MCP server exposing FF1 device tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ff1.client import FF1Client
from ff1.discovery import discover_devices
from ff1.playlist import build_playlist

mcp = FastMCP("ff1", instructions="Control FF1 art computers on the local network.")


async def _get_client(device: str | None = None) -> FF1Client:
    devices = await discover_devices()

    if device:
        for d in devices:
            if d.name.lower() == device.lower():
                return FF1Client(host=d.host, port=d.port, api_key=d.api_key, topic_id=d.topic_id)
        return FF1Client(host=device)

    if not devices:
        raise ValueError("No FF1 devices found. Ensure device is on the network or create ff1.json.")
    if len(devices) > 1:
        names = [f"{d.name} ({d.host})" for d in devices]
        raise ValueError(f"Multiple FF1 devices found: {', '.join(names)}. Specify device parameter.")
    d = devices[0]
    return FF1Client(host=d.host, port=d.port, api_key=d.api_key, topic_id=d.topic_id)


# --- Discovery ---

@mcp.tool()
async def ff1_discover() -> list[dict]:
    """Find FF1 devices on the network (config + ARP scan)."""
    devices = await discover_devices()
    return [d.model_dump() for d in devices]


# --- Device control ---

@mcp.tool()
async def ff1_status(device: str | None = None) -> dict:
    """Get FF1 device status (orientation, wifi, version, volume, etc.)."""
    client = await _get_client(device)
    result = await client.get_device_status()
    return result.model_dump(by_alias=True)


@mcp.tool()
async def ff1_rotate(clockwise: bool = True, device: str | None = None) -> dict:
    """Rotate the FF1 screen. Set clockwise=False for counter-clockwise."""
    client = await _get_client(device)
    return await client.rotate(clockwise=clockwise)


@mcp.tool()
async def ff1_set_volume(percent: int, device: str | None = None) -> dict:
    """Set FF1 volume (0-100)."""
    client = await _get_client(device)
    return await client.set_volume(percent)


@mcp.tool()
async def ff1_toggle_mute(device: str | None = None) -> dict:
    """Toggle mute on the FF1."""
    client = await _get_client(device)
    return await client.toggle_mute()


@mcp.tool()
async def ff1_send_key(code: int, device: str | None = None) -> dict:
    """Send a keyboard event to the FF1. Code is the key code (e.g., 13=Enter)."""
    client = await _get_client(device)
    return await client.send_key(code)


@mcp.tool()
async def ff1_shutdown(device: str | None = None) -> dict:
    """Shutdown the FF1 device."""
    client = await _get_client(device)
    return await client.shutdown()


@mcp.tool()
async def ff1_reboot(device: str | None = None) -> dict:
    """Reboot the FF1 device."""
    client = await _get_client(device)
    return await client.reboot()


@mcp.tool()
async def ff1_update(device: str | None = None) -> dict:
    """Trigger OTA firmware update on the FF1."""
    client = await _get_client(device)
    return await client.update_firmware()


# --- Playback ---

@mcp.tool()
async def ff1_play_url(url: str, duration: int = 300, device: str | None = None) -> dict:
    """Display a single artwork URL on the FF1."""
    client = await _get_client(device)
    pl = build_playlist([url], title="Quick Play", duration=duration)
    return await client.display_playlist(playlist=pl.model_dump(by_alias=True, exclude_none=True))


@mcp.tool()
async def ff1_play_playlist(playlist_url: str, device: str | None = None) -> dict:
    """Play a DP1 playlist from a URL on the FF1."""
    client = await _get_client(device)
    return await client.display_playlist(playlist_url=playlist_url)


@mcp.tool()
async def ff1_player_status(device: str | None = None) -> dict:
    """Get current playback status from the FF1 (via WebSocket)."""
    client = await _get_client(device)
    result = await client.get_player_status()
    return result.model_dump(by_alias=True)


# --- Playlist building ---

@mcp.tool()
def ff1_build_playlist(
    urls: list[str],
    title: str = "Untitled Playlist",
    duration: int = 300,
    scaling: str = "fit",
    background: str = "#000000",
) -> dict:
    """Build a DP1 playlist JSON from artwork URLs (does not send to device)."""
    pl = build_playlist(urls, title=title, duration=duration, scaling=scaling, background=background)
    return pl.model_dump(by_alias=True, exclude_none=True)


def main():
    mcp.run()
