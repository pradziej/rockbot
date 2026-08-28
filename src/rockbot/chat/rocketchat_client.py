import datetime as dt
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Room type -> REST history endpoint. Anything else (livechat, etc.) is
# skipped since it needs a different API.
_HISTORY_ENDPOINT = {
    "c": "channels.history",
    "p": "groups.history",
    "d": "im.history",
}


@dataclass(frozen=True)
class Room:
    id: str
    type: str


@dataclass(frozen=True)
class IncomingMessage:
    room_id: str
    msg_id: str
    sender_id: str
    text: str
    ts: dt.datetime
    thread_id: str | None
    qualifier: str | None


def parse_ts(value: str) -> dt.datetime:
    """Parse a Rocket.Chat timestamp (e.g. "2016-12-09T12:50:51.555Z").

    Python's `datetime.fromisoformat` only accepts a "Z" suffix from 3.11
    onwards, so it's normalized to an explicit UTC offset first.
    """
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


class RocketChatClient:
    """Thin async wrapper around the Rocket.Chat REST API (no websockets).

    Authenticates the same way as any REST API client: an X-Auth-Token /
    X-User-Id header pair, which a Rocket.Chat Personal Access Token
    satisfies directly.
    """

    def __init__(
        self,
        base_url: str,
        user_id: str,
        token: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.user_id = user_id
        self._http = httpx.AsyncClient(
            base_url=f"{base_url.rstrip('/')}/api/v1/",
            headers={"X-Auth-Token": token, "X-User-Id": user_id},
            timeout=10.0,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def whoami(self) -> str:
        """Verify credentials and return the bot's username."""
        response = await self._http.get("me")
        response.raise_for_status()
        return response.json()["username"]

    async def get_rooms(self) -> list[Room]:
        """List the rooms the bot currently belongs to."""
        response = await self._http.get("subscriptions.get")
        response.raise_for_status()
        subscriptions = response.json().get("update", [])
        rooms = []
        for sub in subscriptions:
            if sub.get("t") not in _HISTORY_ENDPOINT:
                continue
            rooms.append(Room(id=sub["rid"], type=sub["t"]))
        return rooms

    async def get_new_messages(self, room: Room, oldest: dt.datetime) -> list[IncomingMessage]:
        """Fetch messages posted in `room` strictly after `oldest`, oldest first."""
        endpoint = _HISTORY_ENDPOINT[room.type]
        response = await self._http.get(
            endpoint,
            params={"roomId": room.id, "oldest": oldest.isoformat()},
        )
        if response.status_code == 429:
            logger.warning("Rate limited while polling room %s", room.id)
            return []
        response.raise_for_status()

        messages = [
            IncomingMessage(
                room_id=room.id,
                msg_id=raw["_id"],
                sender_id=raw["u"]["_id"],
                text=raw.get("msg", ""),
                ts=parse_ts(raw["ts"]),
                thread_id=raw.get("tmid"),
                qualifier=raw.get("t"),
            )
            for raw in response.json().get("messages", [])
        ]
        messages = [m for m in messages if m.ts > oldest]
        messages.sort(key=lambda m: m.ts)
        return messages

    async def send_message(self, room_id: str, text: str) -> None:
        response = await self._http.post("chat.postMessage", json={"roomId": room_id, "text": text})
        response.raise_for_status()
