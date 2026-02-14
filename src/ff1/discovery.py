"""FF1 device discovery — ARP/hostname scanning + config file.

FF1 devices set their Linux hostname to FF1-XXXXXXXX during install
(derived from MAC address). systemd-resolved advertises this via mDNS,
making them reachable as ff1-xxxxxxxx.local on the LAN.

The device does NOT register mDNS service records, so service browsing
won't find it. Instead, discovery works by:
1. Config file — explicit device list
2. ARP table scan — parse `arp -a` for hostnames matching ff1-*
3. Probe — verify a candidate host has feral-controld on port 1111
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from pathlib import Path

import httpx

from ff1.types import DeviceInfo

FF1_DEFAULT_PORT = 1111
FF1_HOSTNAME_PREFIX = "ff1-"

# ARP table entry: hostname (ip) at mac ...
_ARP_RE = re.compile(r"^(\S+)\s+\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+(\S+)", re.MULTILINE)


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
    """Load configured devices from config file.

    Config format (compatible with ff1-cli):
    {
      "devices": [
        {"name": "Living Room", "host": "192.168.1.100", "apiKey": "...", "topicID": "..."}
      ]
    }
    """
    config_path = _find_config()
    if not config_path:
        return []

    data = json.loads(config_path.read_text())
    devices_data = data.get("devices", [])

    devices = []
    for d in devices_data:
        host = d.get("host", "")
        if not host:
            continue
        host = host.removeprefix("http://").removeprefix("https://")
        if "/" in host:
            host = host.split("/")[0]
        if ":" in host:
            parts = host.rsplit(":", 1)
            host = parts[0]
            port = int(parts[1])
        else:
            port = FF1_DEFAULT_PORT

        devices.append(DeviceInfo(
            host=host,
            port=port,
            name=d.get("name", host),
            api_key=d.get("apiKey"),
            topic_id=d.get("topicID"),
        ))

    return devices


def scan_arp() -> list[DeviceInfo]:
    """Parse the system ARP table for hostnames matching ff1-*.

    Works on macOS and Linux. The ARP table is populated by normal
    network activity — no special scanning needed.
    """
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
        # Match ff1-* hostnames (may have .localdomain or .local suffix)
        name_part = hostname.split(".")[0]
        if not name_part.lower().startswith(FF1_HOSTNAME_PREFIX):
            continue
        if ip in seen:
            continue
        seen.add(ip)
        devices.append(DeviceInfo(
            host=ip,
            port=FF1_DEFAULT_PORT,
            name=name_part.upper(),  # Normalize to FF1-XXXXXXXX
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
    """Find FF1 devices on the network via ARP table, then verify with probe.

    The ARP table contains hostnames from DHCP/mDNS. FF1 devices always
    have hostnames matching FF1-XXXXXXXX. Each candidate is verified by
    hitting its feral-controld API on port 1111.
    """
    candidates = scan_arp()
    if not candidates:
        return []

    # Verify all candidates concurrently
    tasks = [probe_host(d.host, d.port, timeout=probe_timeout) for d in candidates]
    results = await asyncio.gather(*tasks)

    verified = []
    for candidate, result in zip(candidates, results):
        if result is not None:
            # Keep the nice hostname from ARP, not just the IP
            result.name = candidate.name
            verified.append(result)

    return verified


async def discover_devices(timeout: float = 3.0) -> list[DeviceInfo]:
    """Find FF1 devices: config first, then network scan as fallback."""
    devices = load_devices()
    if devices:
        return devices
    return await scan_network(probe_timeout=timeout)
