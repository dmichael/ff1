"""Tests for Pydantic models."""

from ff1.types import (
    Command,
    CommandEnvelope,
    DeviceStatus,
    DisplayConfig,
    DP1Playlist,
    PlayerStatus,
    PlaylistDefaults,
    PlaylistItem,
)


def test_command_enum_values():
    assert Command.DEVICE_STATUS == "getDeviceStatus"
    assert Command.ROTATE == "rotate"
    assert Command.DISPLAY_PLAYLIST == "displayPlaylist"
    assert Command.SET_VOLUME == "setVolume"


def test_command_envelope():
    env = CommandEnvelope(command="rotate", request={"clockwise": True})
    d = env.model_dump()
    assert d == {"command": "rotate", "request": {"clockwise": True}}


def test_command_envelope_no_request():
    env = CommandEnvelope(command="shutdown")
    d = env.model_dump()
    assert d == {"command": "shutdown", "request": None}


def test_device_status_from_api():
    raw = {
        "screenRotation": "portrait",
        "connectedWifi": "MyWifi",
        "installedVersion": "1.0.7",
        "latestVersion": "1.0.7",
        "analyticsDisabled": False,
        "betaFeaturesEnabled": False,
        "macInfo": {"eth0": "", "wlan0": ""},
        "volume": 50,
        "isMuted": False,
    }
    status = DeviceStatus.model_validate(raw)
    assert status.screen_rotation == "portrait"
    assert status.connected_wifi == "MyWifi"
    assert status.volume == 50
    assert status.is_muted is False

    # Round-trip back to API format
    out = status.model_dump(by_alias=True)
    assert out["screenRotation"] == "portrait"
    assert out["isMuted"] is False


def test_player_status_defaults():
    ps = PlayerStatus()
    assert ps.ok is True
    assert ps.index == 0
    assert ps.items == []


def test_playlist_item_serialization():
    item = PlaylistItem(
        id="abc-123",
        title="Test Art",
        source="https://example.com/art.html",
        duration=60,
        license="open",
    )
    d = item.model_dump(by_alias=True, exclude_none=True)
    assert d["source"] == "https://example.com/art.html"
    assert "ref" not in d  # None excluded
    assert "override" not in d


def test_dp1_playlist_structure():
    pl = DP1Playlist(
        id="pl-1",
        slug="test",
        title="Test",
        created="2026-01-01T00:00:00Z",
        defaults=PlaylistDefaults(
            display=DisplayConfig(scaling="fit", background="#000"),
            duration=300,
        ),
        items=[
            PlaylistItem(
                id="item-1",
                source="https://example.com/a.html",
                duration=300,
                license="open",
            )
        ],
    )
    d = pl.model_dump(by_alias=True, exclude_none=True)
    assert d["dpVersion"] == "1.0.0"
    assert d["slug"] == "test"
    assert len(d["items"]) == 1
    assert d["defaults"]["display"]["scaling"] == "fit"
