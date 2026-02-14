"""CLI entry point for ff1ctl."""

from __future__ import annotations

import asyncio
import json
import sys

import click

from ff1.client import FF1Client
from ff1.discovery import discover_devices
from ff1.playlist import build_playlist


def _run(coro):
    return asyncio.run(coro)


def _output(data, pretty: bool = False):
    if pretty:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(json.dumps(data))


async def _resolve_device(device: str | None) -> FF1Client:
    """Resolve a device to an FF1Client.

    Resolution order:
    1. --device flag (explicit host/IP)
    2. --device flag (device name, matched against discovered devices)
    3. Auto-discover: use the only device if exactly one found
    4. Multiple devices: error with list of available devices
    """
    devices = await discover_devices()

    if device:
        # Try as a name match first
        for d in devices:
            if d.name.lower() == device.lower():
                return FF1Client(host=d.host, port=d.port, api_key=d.api_key, topic_id=d.topic_id)
        # Otherwise treat as a host/IP
        return FF1Client(host=device)

    if not devices:
        click.echo(json.dumps({
            "error": "No FF1 devices found. Ensure device is on the network or create ff1.json."
        }), err=True)
        sys.exit(1)

    if len(devices) == 1:
        d = devices[0]
        click.echo(json.dumps({"using": d.name, "host": d.host}), err=True)
        return FF1Client(host=d.host, port=d.port, api_key=d.api_key, topic_id=d.topic_id)

    # Multiple devices — require explicit selection
    device_list = [{"name": d.name, "host": d.host} for d in devices]
    click.echo(json.dumps({
        "error": "Multiple FF1 devices found. Use --device NAME or --device HOST to select one.",
        "devices": device_list,
    }), err=True)
    sys.exit(1)


@click.group()
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output")
@click.pass_context
def main(ctx, pretty):
    """ff1ctl — control FF1 art computers."""
    ctx.ensure_object(dict)
    ctx.obj["pretty"] = pretty


@main.command()
@click.option("--timeout", default=3.0, help="Discovery timeout in seconds")
@click.pass_context
def discover(ctx, timeout):
    """Find FF1 devices on the network (config + ARP scan)."""
    async def _go():
        devices = await discover_devices(timeout=timeout)
        _output([d.model_dump() for d in devices], ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.option("--device", "-d", default=None, help="Device host (default: first configured)")
@click.pass_context
def status(ctx, device):
    """Get device status."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.get_device_status()
            _output(result.model_dump(by_alias=True), ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.argument("url")
@click.option("--device", "-d", default=None)
@click.option("--duration", default=300, help="Display duration in seconds")
@click.pass_context
def play(ctx, url, device, duration):
    """Display a single artwork URL on the FF1."""
    async def _go():
        async with await _resolve_device(device) as client:
            pl = build_playlist([url], title="Quick Play", duration=duration)
            result = await client.display_playlist(playlist=pl.model_dump(by_alias=True, exclude_none=True))
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.argument("source")
@click.option("--device", "-d", default=None)
@click.pass_context
def playlist(ctx, source, device):
    """Play a DP1 playlist from a URL or local file (use - for stdin)."""
    async def _go():
        async with await _resolve_device(device) as client:
            if source == "-":
                data = json.load(sys.stdin)
                result = await client.display_playlist(playlist=data)
            elif source.startswith("http://") or source.startswith("https://"):
                result = await client.display_playlist(playlist_url=source)
            else:
                with open(source) as f:
                    data = json.load(f)
                result = await client.display_playlist(playlist=data)
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.argument("urls", nargs=-1, required=True)
@click.option("--title", "-t", default="Untitled Playlist")
@click.option("--duration", default=300, help="Duration per item in seconds")
@click.option("--scaling", default="fit", type=click.Choice(["fit", "fill", "stretch", "auto"]))
@click.option("--background", default="#000000")
@click.pass_context
def build(ctx, urls, title, duration, scaling, background):
    """Build a DP1 playlist JSON from artwork URLs."""
    pl = build_playlist(list(urls), title=title, duration=duration, scaling=scaling, background=background)
    _output(pl.model_dump(by_alias=True, exclude_none=True), ctx.obj["pretty"])


@main.command()
@click.option("--ccw", is_flag=True, help="Rotate counter-clockwise")
@click.option("--device", "-d", default=None)
@click.pass_context
def rotate(ctx, ccw, device):
    """Rotate the screen."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.rotate(clockwise=not ccw)
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.argument("percent", type=int)
@click.option("--device", "-d", default=None)
@click.pass_context
def volume(ctx, percent, device):
    """Set volume (0-100)."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.set_volume(percent)
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.option("--device", "-d", default=None)
@click.pass_context
def mute(ctx, device):
    """Toggle mute."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.toggle_mute()
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.argument("code", type=int)
@click.option("--device", "-d", default=None)
@click.pass_context
def key(ctx, code, device):
    """Send a keyboard event."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.send_key(code)
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.option("--device", "-d", default=None)
@click.pass_context
def reboot(ctx, device):
    """Reboot the device."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.reboot()
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.option("--device", "-d", default=None)
@click.pass_context
def shutdown(ctx, device):
    """Shutdown the device."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.shutdown()
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.option("--device", "-d", default=None)
@click.pass_context
def update(ctx, device):
    """Trigger OTA firmware update."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.update_firmware()
            _output(result, ctx.obj["pretty"])
    _run(_go())


@main.command()
@click.option("--device", "-d", default=None)
@click.pass_context
def player(ctx, device):
    """Get current playback status via WebSocket."""
    async def _go():
        async with await _resolve_device(device) as client:
            result = await client.get_player_status()
            _output(result.model_dump(by_alias=True), ctx.obj["pretty"])
    _run(_go())
