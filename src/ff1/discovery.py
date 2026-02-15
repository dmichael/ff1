"""FF1 device discovery — mDNS/ARP scanning + env/config file.

FF1 devices set their Linux hostname to FF1-XXXXXXXX during install
(derived from MAC address). systemd-resolved advertises this via mDNS,
making them reachable as ff1-xxxxxxxx.local on the LAN.

The device does NOT register mDNS service records, so service browsing
won't find it. Instead, discovery works by:
1. FF1_DEVICE env var — optional explicit host override
2. Config file — explicit device list (ff1.json or ~/.config/ff1/config.json)
3. Network scan — broadcast ping to populate ARP table, then match ff1-* hostnames
4. Probe — verify candidates have feral-controld on port 1111
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

from ff1.types import DeviceInfo

FF1_DEFAULT_PORT = 1111
FF1_HOSTNAME_PREFIX = "ff1-"

# ARP table entry: hostname (ip) at mac ...
_ARP_RE = re.compile(r"^(\S+)\s+\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+(\S+)", re.MULTILINE)


def _load_env_device() -> DeviceInfo | None:
    """Load a single device from FF1_DEVICE env var.

    Accepts: host, host:port, or a URL. Optional FF1_API_KEY and FF1_TOPIC_ID.
    """
    raw = os.environ.get("FF1_DEVICE", "").strip()
    if not raw:
        return None

    if "://" not in raw:
        raw = f"http://{raw}"
    try:
        parsed = urlparse(raw)
        host = parsed.hostname
        if not host:
            return None
        port = parsed.port or FF1_DEFAULT_PORT
    except ValueError:
        return None

    return DeviceInfo(
        host=host,
        port=port,
        name=host,
        api_key=os.environ.get("FF1_API_KEY"),
        topic_id=os.environ.get("FF1_TOPIC_ID"),
    )


def _find_config() -> Path | None:
    env_path = os.environ.get("FF1_CONFIG")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    search_paths = [
        Path.cwd() / "ff1.json",
        Path.home() / ".config" / "ff1" / "config.json",
    ]
    for p in search_paths:
        if p.exists():
            return p
    return None


def load_devices() -> list[DeviceInfo]:
    """Load configured devices from FF1_DEVICE env var or config file.

    Config format (compatible with ff1-cli):
    {
      "devices": [
        {"name": "Living Room", "host": "192.168.1.100", "apiKey": "...", "topicID": "..."}
      ]
    }
    """
    env_device = _load_env_device()
    if env_device:
        return [env_device]

    config_path = _find_config()
    if not config_path:
        return []

    data = json.loads(config_path.read_text())
    devices_data = data.get("devices", [])

    devices = []
    for d in devices_data:
        raw_host = str(d.get("host", "")).strip()
        if not raw_host:
            continue
        if "://" not in raw_host:
            raw_host = f"http://{raw_host}"

        try:
            parsed = urlparse(raw_host)
            host = parsed.hostname
            if not host:
                continue
            port = parsed.port or FF1_DEFAULT_PORT
        except ValueError:
            continue

        devices.append(DeviceInfo(
            host=host,
            port=port,
            name=d.get("name", host),
            api_key=d.get("apiKey"),
            topic_id=d.get("topicID"),
        ))

    return devices


def _get_broadcast_address() -> str | None:
    """Get the broadcast address for the primary network interface."""
    try:
        if sys.platform == "darwin":
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True, text=True, timeout=5,
            )
            # Find broadcast on active interface (has inet + broadcast)
            for match in re.finditer(
                r"inet (\d+\.\d+\.\d+\.\d+).*?broadcast (\d+\.\d+\.\d+\.\d+)",
                result.stdout,
            ):
                addr, broadcast = match.groups()
                if not addr.startswith("127."):
                    return broadcast
        else:
            # Linux: ip addr show
            result = subprocess.run(
                ["ip", "-4", "addr", "show"],
                capture_output=True, text=True, timeout=5,
            )
            for match in re.finditer(
                r"inet (\d+\.\d+\.\d+\.\d+)/\d+\s+brd\s+(\d+\.\d+\.\d+\.\d+)",
                result.stdout,
            ):
                addr, broadcast = match.groups()
                if not addr.startswith("127."):
                    return broadcast
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _ping_broadcast():
    """Send a broadcast ping to populate the ARP table with LAN neighbors.

    The ARP table is often stale or empty. A broadcast ping forces the OS
    to ARP-resolve all responding hosts, making mDNS hostnames (like
    ff1-xxxxxxxx.localdomain) visible in the ARP table.
    """
    broadcast = _get_broadcast_address()
    if not broadcast:
        return
    try:
        subprocess.run(
            ["ping", "-c", "1", "-t", "1", broadcast],
            capture_output=True, timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def scan_arp() -> list[DeviceInfo]:
    """Broadcast ping to populate ARP, then match ff1-* hostnames.

    Works on macOS and Linux. The broadcast ping ensures the ARP table
    is fresh — without it, devices may not appear.
    """
    _ping_broadcast()

    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True, text=True, timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    devices = []
    seen = set()
    for hostname, ip, mac in _ARP_RE.findall(result.stdout):
        name_part = hostname.split(".")[0]
        if not name_part.lower().startswith(FF1_HOSTNAME_PREFIX):
            continue
        if ip in seen:
            continue
        seen.add(ip)
        devices.append(DeviceInfo(
            host=ip,
            port=FF1_DEFAULT_PORT,
            name=name_part.upper(),
        ))

    return devices


async def probe_host(host: str, port: int = FF1_DEFAULT_PORT, timeout: float = 2.0) -> DeviceInfo | None:
    """Check if a specific host has feral-controld on the given port."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"http://{host}:{port}/api/cast",
                json={"command": "getDeviceStatus", "request": {}},
                timeout=timeout,
            )
            if resp.status_code == 200:
                return DeviceInfo(host=host, port=port, name=host)
    except (httpx.HTTPError, OSError):
        pass
    return None


async def scan_network(probe_timeout: float = 3.0) -> list[DeviceInfo]:
    """Find FF1 devices via broadcast ping + ARP scan, then verify with probe."""
    candidates = scan_arp()
    if not candidates:
        return []

    tasks = [probe_host(d.host, d.port, timeout=probe_timeout) for d in candidates]
    results = await asyncio.gather(*tasks)

    verified = []
    for candidate, result in zip(candidates, results):
        if result is not None:
            result.name = candidate.name
            verified.append(result)

    return verified


async def discover_devices(timeout: float = 3.0) -> list[DeviceInfo]:
    """Find FF1 devices: env/config first, then network scan as fallback."""
    devices = load_devices()
    if devices:
        return devices
    return await scan_network(probe_timeout=timeout)
