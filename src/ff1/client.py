"""Async HTTP/WS client for feral-controld on FF1 devices."""

from __future__ import annotations

import asyncio
import json

import httpx
import websockets

from ff1.types import Command, CommandEnvelope, DeviceStatus, PlayerStatus
from ff1.url_policy import validate_playback_url, validate_playlist_payload

_DEFAULT_TIMEOUT = 30.0
_DEFAULT_WS_TIMEOUT = 10.0


class FF1Client:
    """Talks to a single FF1 device via its local HTTP API."""

    def __init__(
        self,
        host: str,
        port: int = 1111,
        api_key: str | None = None,
        topic_id: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.topic_id = topic_id
        self.timeout = timeout
        self._base_url = f"http://{host}:{port}"
        self._http = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def close(self):
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

    # --- Low-level ---

    async def send_command(self, command: str, request: dict | None = None) -> dict:
        envelope = CommandEnvelope(command=command, request=request)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["API-KEY"] = self.api_key

        params = {}
        if self.topic_id:
            params["topicID"] = self.topic_id

        resp = await self._http.post(
            "/api/cast",
            json=envelope.model_dump(),
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    # --- Device control ---

    async def get_device_status(self) -> DeviceStatus:
        data = await self.send_command(Command.DEVICE_STATUS)
        return DeviceStatus.model_validate(data)

    async def rotate(self, clockwise: bool = True) -> dict:
        return await self.send_command(Command.ROTATE, {"clockwise": clockwise})

    async def set_volume(self, percent: int) -> dict:
        return await self.send_command(Command.SET_VOLUME, {"percent": percent})

    async def toggle_mute(self) -> dict:
        return await self.send_command(Command.TOGGLE_MUTE)

    async def send_key(self, code: int) -> dict:
        return await self.send_command(Command.KEYBOARD_EVENT, {"code": code})

    async def shutdown(self) -> dict:
        return await self.send_command(Command.SHUTDOWN)

    async def reboot(self) -> dict:
        return await self.send_command(Command.REBOOT)

    async def update_firmware(self) -> dict:
        return await self.send_command(Command.UPDATE)

    # --- Playback ---

    async def display_playlist(self, playlist: dict | None = None, playlist_url: str | None = None) -> dict:
        if playlist and playlist_url:
            raise ValueError("Provide playlist or playlist_url, not both")
        if playlist_url:
            validate_playback_url(playlist_url)
            return await self.send_command(Command.DISPLAY_PLAYLIST, {"playlistUrl": playlist_url})
        if playlist:
            validate_playlist_payload(playlist)
            return await self.send_command(Command.DISPLAY_PLAYLIST, {
                "dp1_call": playlist,
                "intent": {"action": "now_display"},
            })
        raise ValueError("Provide either playlist or playlist_url")

    async def get_player_status(self) -> PlayerStatus:
        ws_url = f"ws://{self.host}:{self.port}/api/notification"
        async with websockets.connect(ws_url, open_timeout=self.timeout, close_timeout=self.timeout) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=_DEFAULT_WS_TIMEOUT)
            data = json.loads(msg)
            return PlayerStatus.model_validate(data)
