"""Pydantic models for the FF1 API."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# --- Command constants (from commands/types.go) ---

class Command(str, Enum):
    CONNECT = "connect"
    SHOW_PAIRING_QR = "showPairingQRCode"
    DEVICE_METRICS = "deviceMetrics"
    KEYBOARD_EVENT = "sendKeyboardEvent"
    DRAG_GESTURE = "dragGesture"
    TAP_GESTURE = "tapGesture"
    ROTATE = "rotate"
    SHUTDOWN = "shutdown"
    REBOOT = "reboot"
    ANALYTICS_TOGGLE = "analyticsToggle"
    BETA_FEATURES_TOGGLE = "betaFeaturesToggle"
    DEVICE_STATUS = "getDeviceStatus"
    UPDATE = "updateToLatestVersion"
    FACTORY_RESET = "factoryReset"
    UPLOAD_LOGS = "uploadLogs"
    SET_VOLUME = "setVolume"
    TOGGLE_MUTE = "toggleMute"
    DISPLAY_PLAYLIST = "displayPlaylist"


# --- Command envelope ---

class CommandEnvelope(BaseModel):
    command: str
    request: dict | None = None


# --- Device status (from status/device_status.go) ---

class MacInfo(BaseModel):
    eth0: str = ""
    wlan0: str = ""


class DeviceStatus(BaseModel):
    screen_rotation: str = Field("", alias="screenRotation")
    connected_wifi: str = Field("", alias="connectedWifi")
    installed_version: str = Field("", alias="installedVersion")
    latest_version: str = Field("", alias="latestVersion")
    analytics_disabled: bool = Field(False, alias="analyticsDisabled")
    beta_features_enabled: bool = Field(False, alias="betaFeaturesEnabled")
    mac_info: MacInfo = Field(default_factory=MacInfo, alias="macInfo")
    volume: int = 0
    is_muted: bool = Field(False, alias="isMuted")

    model_config = {"populate_by_name": True}


# --- Player status (from status/status.go) ---

class DeviceSettings(BaseModel):
    scaling: str = ""
    orientation: str = ""


class PlayerStatusItem(BaseModel):
    id: str = ""
    title: str = ""
    duration: int = 0
    license: str = ""


class PlayerStatus(BaseModel):
    cast_command: str = Field("", alias="castCommand")
    playlist_url: str = Field("", alias="playlistURL")
    playlist: dict | None = None
    index: int = 0
    is_paused: bool = Field(False, alias="isPaused")
    items: list[PlayerStatusItem] = Field(default_factory=list)
    ok: bool = True
    error: str = ""
    device_settings: DeviceSettings = Field(default_factory=DeviceSettings, alias="deviceSettings")

    model_config = {"populate_by_name": True}


# --- DP1 Playlist (from dp1-validator/playlist/playlist.go) ---

class DisplayConfig(BaseModel):
    scaling: str | None = None
    margin: str | int | None = None
    background: str | None = None
    auto_play: bool | None = Field(None, alias="autoPlay")
    loop: bool | None = None

    model_config = {"populate_by_name": True, "by_alias": True}


class PlaylistDefaults(BaseModel):
    display: DisplayConfig | None = None
    license: str | None = None
    duration: int | None = None

    model_config = {"by_alias": True}


class PlaylistItem(BaseModel):
    id: str
    title: str = ""
    source: str
    duration: int
    license: str = "open"
    ref: str | None = None
    override: dict | None = None
    display: DisplayConfig | None = None

    model_config = {"by_alias": True}


class DP1Playlist(BaseModel):
    dp_version: str = Field("1.0.0", alias="dpVersion")
    id: str
    slug: str
    title: str
    created: str
    defaults: PlaylistDefaults | None = None
    items: list[PlaylistItem]
    signature: str | None = None

    model_config = {"populate_by_name": True, "by_alias": True}


# --- Discovery ---

class DeviceInfo(BaseModel):
    host: str
    port: int = 1111
    name: str = ""
    api_key: str | None = None
    topic_id: str | None = None
