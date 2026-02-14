"""Tests for device discovery."""

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

from ff1.discovery import FF1_DEFAULT_PORT, load_devices, scan_arp


def test_load_devices_from_config(tmp_path):
    config = tmp_path / "ff1.json"
    config.write_text(json.dumps({
        "devices": [
            {"name": "Living Room", "host": "192.168.1.100", "apiKey": "key1", "topicID": "topic1"},
            {"name": "Bedroom", "host": "192.168.1.101"},
        ]
    }))

    with patch("ff1.discovery._find_config", return_value=config):
        devices = load_devices()

    assert len(devices) == 2
    assert devices[0].name == "Living Room"
    assert devices[0].host == "192.168.1.100"
    assert devices[0].api_key == "key1"
    assert devices[0].topic_id == "topic1"
    assert devices[1].name == "Bedroom"
    assert devices[1].api_key is None


def test_load_devices_strips_protocol(tmp_path):
    config = tmp_path / "ff1.json"
    config.write_text(json.dumps({
        "devices": [
            {"name": "Test", "host": "http://192.168.1.100:1111/api"},
        ]
    }))

    with patch("ff1.discovery._find_config", return_value=config):
        devices = load_devices()

    assert devices[0].host == "192.168.1.100"
    assert devices[0].port == 1111


def test_load_devices_no_config():
    with patch("ff1.discovery._find_config", return_value=None):
        devices = load_devices()
    assert devices == []


def test_load_devices_skips_invalid_port(tmp_path):
    config = tmp_path / "ff1.json"
    config.write_text(json.dumps({
        "devices": [
            {"name": "Bad", "host": "192.168.1.100:not-a-port"},
            {"name": "Good", "host": "192.168.1.101:1111"},
        ]
    }))

    with patch("ff1.discovery._find_config", return_value=config):
        devices = load_devices()

    assert len(devices) == 1
    assert devices[0].name == "Good"
    assert devices[0].host == "192.168.1.101"
    assert devices[0].port == 1111


def test_load_devices_supports_ipv6_brackets(tmp_path):
    config = tmp_path / "ff1.json"
    config.write_text(json.dumps({
        "devices": [
            {"name": "IPv6 Device", "host": "http://[2001:db8::1]:1212/api"},
        ]
    }))

    with patch("ff1.discovery._find_config", return_value=config):
        devices = load_devices()

    assert len(devices) == 1
    assert devices[0].host == "2001:db8::1"
    assert devices[0].port == 1212


def test_scan_arp_finds_ff1():
    arp_output = textwrap.dedent("""\
        ? (192.168.1.1) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]
        ff1-abc12345.localdomain (192.168.1.42) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]
        ff1-abc12345.localdomain (192.168.1.42) at aa:bb:cc:dd:ee:ff on en7 ifscope [ethernet]
        somehost (192.168.1.50) at 11:22:33:44:55:66 on en0 ifscope [ethernet]
    """)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = arp_output
        devices = scan_arp()

    assert len(devices) == 1
    assert devices[0].host == "192.168.1.42"
    assert devices[0].name == "FF1-ABC12345"
    assert devices[0].port == FF1_DEFAULT_PORT


def test_scan_arp_multiple_devices():
    arp_output = textwrap.dedent("""\
        ff1-abc12345.local (10.0.0.10) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]
        ff1-def67890.local (10.0.0.11) at 11:22:33:44:55:66 on en0 ifscope [ethernet]
    """)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = arp_output
        devices = scan_arp()

    assert len(devices) == 2
    assert {d.host for d in devices} == {"10.0.0.10", "10.0.0.11"}


def test_scan_arp_no_ff1():
    arp_output = "somehost (192.168.1.50) at 11:22:33:44:55:66 on en0\n"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = arp_output
        devices = scan_arp()

    assert devices == []
