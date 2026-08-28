import asyncio
import logging
import random

from rocketchat_async import RocketChat

from rockbot.core.conversation import ConversationStore
from rockbot.core.router import MessageContext, Router
from rockbot.core.trigger import extract_query

logger = logging.getLogger(__name__)


class RockBot:
    """Connects to Rocket.Chat, listens for messages and routes them.

    The Rocket.Chat realtime API invokes message callbacks synchronously,
    so `_on_message` only schedules an asyncio task; the actual work
    (calling the router, talking to Ollama, replying) happens in
    `_handle_message`.

    Only messages addressed to the bot via `trigger` (e.g. "/rockbot how's
    it going?") are answered; everything else is ignored so the bot doesn't
    talk over every message in a channel.
    """

    def __init__(
        self,
        url: str,
        user_id: str,
        token: str,
        trigger: str,
        router: Router,
        conversation_store: ConversationStore,
    ) -> None:
        self._url = url
        self._user_id = user_id
        self._token = token
        self._trigger = trigger
        self._router = router
        self._conversations = conversation_store
        self._rc = RocketChat()

    async def run_forever(self) -> None:
        while True:
            try:
                await self._connect_and_serve()
            except (RocketChat.ConnectionClosed, RocketChat.ConnectCallFailed) as exc:
                delay = random.uniform(4, 8)
                logger.warning("Connection lost (%s), reconnecting in %.1fs", exc, delay)
                await asyncio.sleep(delay)

    async def _connect_and_serve(self) -> None:
        self._rc = RocketChat()
        # `resume` logs in via a token (a Rocket.Chat Personal Access Token
        # works here). The second argument is only used as the display name
        # for typing-indicator events, so the configured user id doubles for
        # it; the actual user id comes back from the server in the response.
        await self._rc.resume(self._url, self._user_id, self._token)
        if self._rc.user_id != self._user_id:
            logger.warning(
                "Authenticated user id (%s) does not match ROCKETCHAT_USER_ID (%s)",
                self._rc.user_id,
                self._user_id,
            )
        logger.info("Connected to Rocket.Chat as user %s", self._rc.user_id)

        for channel_id, _channel_type in await self._rc.get_channels():
            await self._rc.subscribe_to_channel_messages(channel_id, self._on_message)
        logger.info("Subscribed to channel messages")

        await self._rc.run_forever()

    def _on_message(
        self,
        channel_id: str,
        sender_id: str,
        msg_id: str,
        thread_id: str | None,
        msg: str,
        qualifier: str | None,
        unread: bool,
        repeated: bool,
    ) -> None:
        if qualifier is not None:
            return  # Not a plain text message (e.g. user joined/left).
        if sender_id == self._rc.user_id:
            return  # Ignore the bot's own messages.
        query = extract_query(msg, self._trigger)
        if query is None:
            return  # Not addressed to the bot.
        asyncio.create_task(self._handle_message(channel_id, sender_id, query))

    async def _handle_message(self, channel_id: str, sender_id: str, text: str) -> None:
        if not text:
            await self._rc.send_message(
                f"Yes? Ask me something, e.g. `{self._trigger} what's the weather like?`",
                channel_id,
            )
            return

        ctx = MessageContext(
            channel_id=channel_id,
            sender_id=sender_id,
            text=text,
            history=self._conversations.get(channel_id),
        )
        try:
            reply = await self._router.dispatch(ctx)
        except Exception:
            logger.exception("Unhandled error while routing message in %s", channel_id)
            return

        if reply is None:
            return

        self._conversations.add(channel_id, "user", text)
        self._conversations.add(channel_id, "assistant", reply)
        await self._rc.send_message(reply, channel_id)
