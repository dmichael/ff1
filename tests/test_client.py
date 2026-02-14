"""Tests for the FF1 client (using mocked HTTP)."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from ff1.client import FF1Client
from ff1.types import Command

_FAKE_REQUEST = httpx.Request("POST", "http://fake/api/cast")


def _ok(json_data: dict | None = None) -> httpx.Response:
    return httpx.Response(200, json=json_data or {"ok": True}, request=_FAKE_REQUEST)


@pytest.fixture
def client():
    return FF1Client(host="192.168.1.42", api_key="test-key", topic_id="test-topic")


@pytest.mark.asyncio
async def test_send_command_envelope(client):
    """Verify the correct envelope is sent to the API."""
    mock_response = _ok()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        result = await client.send_command("rotate", {"clockwise": True})

    assert result == {"ok": True}
    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"] == {
        "command": "rotate",
        "request": {"clockwise": True},
    }
    assert call_kwargs.kwargs["headers"]["API-KEY"] == "test-key"
    assert call_kwargs.kwargs["params"]["topicID"] == "test-topic"


@pytest.mark.asyncio
async def test_send_command_no_auth():
    """Client without api_key/topic_id omits those headers/params."""
    client = FF1Client(host="10.0.0.1")
    mock_response = _ok()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.send_command("shutdown")

    call_kwargs = mock_post.call_args
    assert "API-KEY" not in call_kwargs.kwargs["headers"]
    assert call_kwargs.kwargs["params"] == {}


@pytest.mark.asyncio
async def test_get_device_status(client):
    status_data = {
        "screenRotation": "portrait",
        "connectedWifi": "TestWifi",
        "installedVersion": "1.0.0",
        "latestVersion": "1.0.0",
        "analyticsDisabled": False,
        "betaFeaturesEnabled": False,
        "macInfo": {"eth0": "", "wlan0": ""},
        "volume": 75,
        "isMuted": True,
    }
    mock_response = _ok(status_data)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        status = await client.get_device_status()

    assert status.screen_rotation == "portrait"
    assert status.volume == 75
    assert status.is_muted is True


@pytest.mark.asyncio
async def test_rotate(client):
    mock_response = _ok({"orientation": "landscape"})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        result = await client.rotate(clockwise=False)

    assert result["orientation"] == "landscape"
    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["request"]["clockwise"] is False


@pytest.mark.asyncio
async def test_set_volume(client):
    mock_response = _ok()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.set_volume(42)

    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["request"]["percent"] == 42


@pytest.mark.asyncio
async def test_display_playlist_by_url(client):
    mock_response = _ok()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.display_playlist(playlist_url="https://example.com/pl.json")

    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["request"]["playlistUrl"] == "https://example.com/pl.json"


@pytest.mark.asyncio
async def test_display_playlist_by_object(client):
    mock_response = _ok()
    playlist = {"dpVersion": "1.0.0", "items": []}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.display_playlist(playlist=playlist)

    call_kwargs = mock_post.call_args
    req = call_kwargs.kwargs["json"]["request"]
    assert req["dp1_call"] == playlist
    assert req["intent"]["action"] == "now_display"


@pytest.mark.asyncio
async def test_display_playlist_requires_arg(client):
    with pytest.raises(ValueError, match="Provide either"):
        await client.display_playlist()
