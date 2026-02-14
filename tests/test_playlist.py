"""Tests for playlist builder."""

import uuid

from ff1.playlist import build_playlist


def test_build_single_item():
    pl = build_playlist(["https://example.com/art.html"])
    assert pl.title == "Untitled Playlist"
    assert len(pl.items) == 1
    assert pl.items[0].source == "https://example.com/art.html"
    assert pl.items[0].duration == 300
    assert pl.items[0].license == "open"
    # Valid UUID
    uuid.UUID(pl.id)
    uuid.UUID(pl.items[0].id)


def test_build_multiple_items():
    urls = [
        "https://example.com/a.html",
        "https://example.com/b.html",
        "https://example.com/c.html",
    ]
    pl = build_playlist(urls, title="My Show", duration=60)
    assert pl.title == "My Show"
    assert pl.slug == "my-show"
    assert len(pl.items) == 3
    for item in pl.items:
        assert item.duration == 60


def test_build_custom_options():
    pl = build_playlist(
        ["https://example.com/art.html"],
        title="Custom",
        duration=120,
        scaling="fill",
        background="#ffffff",
        license_type="token",
    )
    assert pl.defaults.display.scaling == "fill"
    assert pl.defaults.display.background == "#ffffff"
    assert pl.defaults.license == "token"
    assert pl.items[0].license == "token"


def test_build_extracts_title_from_url():
    pl = build_playlist(["https://cdn.example.com/works/generative-piece.html"])
    assert pl.items[0].title == "generative-piece.html"


def test_slug_generation():
    pl = build_playlist(["https://x.com/a"], title="Hello World! @#$")
    assert pl.slug == "hello-world"


def test_serialization_roundtrip():
    pl = build_playlist(["https://example.com/art.html"], title="Test")
    d = pl.model_dump(by_alias=True, exclude_none=True)
    assert "dpVersion" in d
    assert d["dpVersion"] == "1.0.0"
    assert "items" in d
    assert "signature" not in d  # None excluded
