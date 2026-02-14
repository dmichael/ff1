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

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
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

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.send_command("shutdown")

    call_kwargs = mock_post.call_args
    assert "API-KEY" not in call_kwargs.kwargs["headers"]
    assert call_kwargs.kwargs["params"] == {}


@pytest.mark.asyncio
async def test_send_command_no_request_sends_none():
    """Commands with no args should send request: null, not request: {}."""
    client = FF1Client(host="10.0.0.1")
    mock_response = _ok()

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.send_command("shutdown")

    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["request"] is None


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

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        status = await client.get_device_status()

    assert status.screen_rotation == "portrait"
    assert status.volume == 75
    assert status.is_muted is True


@pytest.mark.asyncio
async def test_rotate(client):
    mock_response = _ok({"orientation": "landscape"})

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        result = await client.rotate(clockwise=False)

    assert result["orientation"] == "landscape"
    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["request"]["clockwise"] is False


@pytest.mark.asyncio
async def test_set_volume(client):
    mock_response = _ok()

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.set_volume(42)

    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["request"]["percent"] == 42


@pytest.mark.asyncio
async def test_display_playlist_by_url(client):
    mock_response = _ok()

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.display_playlist(playlist_url="https://example.com/pl.json")

    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["request"]["playlistUrl"] == "https://example.com/pl.json"


@pytest.mark.asyncio
async def test_display_playlist_by_object(client):
    mock_response = _ok()
    playlist = {"dpVersion": "1.0.0", "items": []}

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await client.display_playlist(playlist=playlist)

    call_kwargs = mock_post.call_args
    req = call_kwargs.kwargs["json"]["request"]
    assert req["dp1_call"] == playlist
    assert req["intent"]["action"] == "now_display"


@pytest.mark.asyncio
async def test_display_playlist_validation_disabled_by_default():
    client = FF1Client(host="10.0.0.1")
    mock_response = _ok()

    with patch.object(client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        # Non-http URL is allowed when feature flag is disabled.
        await client.display_playlist(playlist_url="file:///tmp/playlist.json")


@pytest.mark.asyncio
async def test_display_playlist_validation_enforced_with_env(monkeypatch):
    client = FF1Client(host="10.0.0.1")
    monkeypatch.setenv("FF1_ENABLE_URL_VALIDATION", "1")

    with pytest.raises(ValueError, match="http:// or https://"):
        await client.display_playlist(playlist_url="file:///tmp/playlist.json")


@pytest.mark.asyncio
async def test_display_playlist_payload_validation_enforced_with_env(monkeypatch):
    client = FF1Client(host="10.0.0.1")
    monkeypatch.setenv("FF1_ENABLE_URL_VALIDATION", "1")

    with pytest.raises(ValueError, match="Invalid DP1 playlist payload"):
        await client.display_playlist(playlist={"items": "not-a-list"})


@pytest.mark.asyncio
async def test_display_playlist_requires_arg(client):
    with pytest.raises(ValueError, match="Provide either"):
        await client.display_playlist()


@pytest.mark.asyncio
async def test_client_timeout_configurable():
    """Client timeout propagates to httpx."""
    client = FF1Client(host="10.0.0.1", timeout=5.0)
    assert client.timeout == 5.0
    assert client._http.timeout.connect == 5.0


@pytest.mark.asyncio
async def test_client_context_manager():
    """Client can be used as an async context manager."""
    async with FF1Client(host="10.0.0.1") as client:
        assert client._http is not None
