"""URL validation policy for remote playback requests."""

from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse

_ALLOWED_SCHEMES = {"http", "https"}
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


def is_url_validation_enabled() -> bool:
    """Whether strict playback URL validation is enforced."""
    return _env_flag("FF1_ENABLE_URL_VALIDATION", default=False)


def allow_local_urls_from_env() -> bool:
    """Opt-out switch for trusted deployments that need local URLs."""
    return _env_flag("FF1_UNSAFE_ALLOW_LOCAL_URLS", default=False)


def validate_playback_url(
    url: str,
    *,
    enabled: bool | None = None,
    allow_local: bool | None = None,
) -> None:
    """Validate a URL intended for device-side fetch.

    Validation is feature-flagged and disabled by default to avoid breaking
    trusted local workflows while the project is under development.
    """
    if enabled is None:
        enabled = is_url_validation_enabled()
    if not enabled:
        return

    if allow_local is None:
        allow_local = allow_local_urls_from_env()

    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError("URL must use http:// or https://")
    if not parsed.hostname:
        raise ValueError("URL must include a host")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")

    if allow_local:
        return

    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        raise ValueError("Local hosts are blocked by default for safety")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if host.endswith(".local") or host.endswith(".localdomain"):
            raise ValueError("mDNS/local-domain hosts are blocked by default for safety")
        return

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise ValueError("Private or local IP ranges are blocked by default for safety")


def validate_playlist_payload(
    playlist: dict,
    *,
    enabled: bool | None = None,
    allow_local: bool | None = None,
) -> None:
    """Validate DP1 playlist shape and source URLs."""
    if enabled is None:
        enabled = is_url_validation_enabled()
    if not enabled:
        return

    if not isinstance(playlist, dict):
        raise ValueError("Playlist payload must be a JSON object")

    from pydantic import ValidationError

    from ff1.types import DP1Playlist

    try:
        parsed = DP1Playlist.model_validate(playlist)
    except ValidationError as exc:
        raise ValueError(f"Invalid DP1 playlist payload: {exc}") from exc

    for idx, item in enumerate(parsed.items):
        try:
            validate_playback_url(item.source, enabled=True, allow_local=allow_local)
        except ValueError as exc:
            raise ValueError(f"Playlist item at index {idx} has invalid source URL: {exc}") from exc
