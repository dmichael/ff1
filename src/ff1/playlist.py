"""DP1 playlist builder for FF1 devices."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from ff1.types import DP1Playlist, DisplayConfig, PlaylistDefaults, PlaylistItem


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", text.lower().strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:64]


def build_playlist(
    sources: list[str],
    title: str = "Untitled Playlist",
    duration: int = 300,
    scaling: str = "fit",
    background: str = "#000000",
    license_type: str = "open",
) -> DP1Playlist:
    """Build a valid DP1 playlist from a list of artwork URLs."""
    now = datetime.now(timezone.utc).isoformat()

    items = []
    for source in sources:
        item_title = urlparse(source).path.split("/")[-1] or "Untitled"
        items.append(PlaylistItem(
            id=str(uuid.uuid4()),
            title=item_title,
            source=source,
            duration=duration,
            license=license_type,
        ))

    return DP1Playlist(
        id=str(uuid.uuid4()),
        slug=_slugify(title),
        title=title,
        created=now,
        defaults=PlaylistDefaults(
            display=DisplayConfig(scaling=scaling, background=background),
            license=license_type,
            duration=duration,
        ),
        items=items,
    )
