"""Tests for playback URL safety policy."""

import pytest

from ff1.url_policy import is_url_validation_enabled, validate_playback_url, validate_playlist_payload


def test_url_validation_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FF1_ENABLE_URL_VALIDATION", raising=False)
    assert is_url_validation_enabled() is False


def test_validate_playback_url_noops_when_disabled():
    validate_playback_url("file:///tmp/payload.json", enabled=False)
    validate_playback_url("http://127.0.0.1/admin", enabled=False)


def test_validate_playback_url_allows_public_http_and_https_when_enabled():
    validate_playback_url("http://example.com/artwork.html", enabled=True)
    validate_playback_url("https://cdn.example.com/playlist.json", enabled=True)


@pytest.mark.parametrize("url", [
    "file:///tmp/payload.json",
    "ftp://example.com/file",
    "javascript:alert(1)",
])
def test_validate_playback_url_rejects_non_http_schemes(url):
    with pytest.raises(ValueError, match="http:// or https://"):
        validate_playback_url(url, enabled=True)


@pytest.mark.parametrize("url", [
    "http://localhost:8080/internal",
    "http://127.0.0.1/admin",
    "http://192.168.1.10/secret",
    "http://10.0.0.5/config",
    "http://169.254.1.1/meta",
    "http://[::1]/health",
    "http://ff1-abc12345.local/playlist.json",
])
def test_validate_playback_url_rejects_local_and_private_targets(url):
    with pytest.raises(ValueError, match="blocked by default"):
        validate_playback_url(url, enabled=True)


def test_validate_playback_url_rejects_embedded_credentials():
    with pytest.raises(ValueError, match="embedded credentials"):
        validate_playback_url("https://user:pass@example.com/private", enabled=True)


def test_validate_playback_url_allows_local_targets_when_explicitly_enabled():
    validate_playback_url("http://192.168.1.10/playlist.json", enabled=True, allow_local=True)


def test_validate_playback_url_allows_local_targets_from_env(monkeypatch):
    monkeypatch.setenv("FF1_ENABLE_URL_VALIDATION", "1")
    monkeypatch.setenv("FF1_UNSAFE_ALLOW_LOCAL_URLS", "1")
    validate_playback_url("http://127.0.0.1/playlist.json")


def test_validate_playlist_payload_noops_when_disabled():
    playlist = {"items": [{"source": "file:///tmp/local-artwork.html"}]}
    validate_playlist_payload(playlist, enabled=False)


def test_validate_playlist_payload_rejects_bad_item_source_when_enabled():
    playlist = {
        "id": "pl-1",
        "slug": "test",
        "title": "Test",
        "created": "2026-01-01T00:00:00Z",
        "items": [{"id": "item-1", "source": "http://127.0.0.1/admin", "duration": 60}],
    }
    with pytest.raises(ValueError, match="index 0"):
        validate_playlist_payload(playlist, enabled=True)


def test_validate_playlist_payload_rejects_invalid_schema_when_enabled():
    playlist = {"title": "oops", "items": "not-a-list"}
    with pytest.raises(ValueError, match="Invalid DP1 playlist payload"):
        validate_playlist_payload(playlist, enabled=True)
