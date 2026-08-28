import asyncio
import datetime as dt
import logging

import httpx

from rockbot.chat.rocketchat_client import RocketChatClient, Room
from rockbot.core.conversation import ConversationStore
from rockbot.core.rooms import resolve_rooms
from rockbot.core.router import MessageContext, Router
from rockbot.core.trigger import extract_query

logger = logging.getLogger(__name__)


class RockBot:
    """Polls Rocket.Chat's REST API for new messages and routes them.

    No websocket/realtime API is involved - `poll_interval` controls how
    often each room's history is checked. Only messages addressed to the
    bot via `trigger` (e.g. "/rockbot how's it going?") are answered;
    everything else is ignored so the bot doesn't talk over every message
    in a channel.

    If `watch_rooms` is given, only those rooms are polled (each entry may
    be a room ID or a name, resolved against the bot's subscriptions on
    every poll cycle - see `core/rooms.py`). Otherwise every room the bot
    is a member of is polled.
    """

    def __init__(
        self,
        client: RocketChatClient,
        trigger: str,
        poll_interval: float,
        router: Router,
        conversation_store: ConversationStore,
        watch_rooms: list[str] | None = None,
    ) -> None:
        self._client = client
        self._trigger = trigger
        self._poll_interval = poll_interval
        self._router = router
        self._conversations = conversation_store
        self._watch_rooms = watch_rooms or []
        self._last_seen: dict[str, dt.datetime] = {}
        self._background_tasks: set[asyncio.Task] = set()
        self._identified = False
        self._warned_unresolved: set[str] = set()

    async def run_forever(self) -> None:
        logger.info("Polling Rocket.Chat every %.1fs", self._poll_interval)
        while True:
            try:
                if not self._identified:
                    username = await self._client.whoami()
                    logger.info("Connected to Rocket.Chat as %s", username)
                    self._identified = True
                await self._poll_once()
            except httpx.HTTPError as exc:
                logger.warning("Rocket.Chat request failed (%s), retrying next cycle", exc)
            await asyncio.sleep(self._poll_interval)

    async def _poll_once(self) -> None:
        subscriptions = await self._client.get_rooms()
        rooms = self._select_rooms(subscriptions)
        now = dt.datetime.now(dt.timezone.utc)
        for room in rooms:
            if room.id not in self._last_seen:
                # Newly-seen room: start watching from now, don't replay history.
                self._last_seen[room.id] = now
                continue
            await self._poll_room(room)

    def _select_rooms(self, subscriptions: list[Room]) -> list[Room]:
        if not self._watch_rooms:
            return subscriptions

        rooms, unresolved = resolve_rooms(subscriptions, self._watch_rooms)
        for entry in unresolved:
            if entry in self._warned_unresolved:
                continue
            self._warned_unresolved.add(entry)
            logger.warning(
                "Configured room '%s' not found among the bot's subscriptions "
                "(check the ID/name, and that the bot has been invited)",
                entry,
            )
        return rooms

    async def _poll_room(self, room: Room) -> None:
        oldest = self._last_seen[room.id]
        messages = await self._client.get_new_messages(room, oldest)
        for message in messages:
            self._last_seen[room.id] = message.ts

            if message.qualifier is not None:
                continue  # Not a plain text message (e.g. user joined/left).
            #Do not ignore my own messages... while the API key is issued by myself
            #if message.sender_id == self._client.user_id:
            #    continue  # Ignore the bot's own messages.

            query = extract_query(message.text, self._trigger)
            if query is None:
                continue  # Not addressed to the bot.

            self._spawn(self._handle_message(room.id, message.sender_id, query))

    def _spawn(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _handle_message(self, room_id: str, sender_id: str, text: str) -> None:
        if not text:
            await self._client.send_message(
                room_id,
                f"Yes? Ask me something, e.g. `{self._trigger} what's the weather like?`",
            )
            return

        ctx = MessageContext(
            channel_id=room_id,
            sender_id=sender_id,
            text=text,
            history=self._conversations.get(room_id),
        )
        try:
            reply = await self._router.dispatch(ctx)
        except Exception:
            logger.exception("Unhandled error while routing message in %s", room_id)
            return

        if reply is None:
            return

        self._conversations.add(room_id, "user", text)
        self._conversations.add(room_id, "assistant", reply)
        await self._client.send_message(room_id, reply)
