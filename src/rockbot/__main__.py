import asyncio
import logging

from rockbot.chat.ollama_client import OllamaClient
from rockbot.chat.rocketchat_client import RocketChatClient
from rockbot.config import get_settings
from rockbot.core.bot import RockBot
from rockbot.core.conversation import ConversationStore
from rockbot.core.rooms import parse_room_list
from rockbot.handlers import build_default_router
from rockbot.logging_config import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.rockbot_log_level)

    rc_client = RocketChatClient(
        base_url=settings.rocketchat_url,
        user_id=settings.rocketchat_user_id,
        token=settings.rocketchat_token,
        verify_ssl=settings.rocketchat_verify_ssl,
    )
    ollama_client = OllamaClient(
        host=settings.ollama_host,
        model=settings.ollama_model,
        system_prompt=settings.ollama_system_prompt,
    )
    conversation_store = ConversationStore(max_turns=settings.rockbot_history_length)
    router = build_default_router(ollama_client)

    bot = RockBot(
        client=rc_client,
        trigger=settings.rockbot_trigger,
        poll_interval=settings.rockbot_poll_interval,
        router=router,
        conversation_store=conversation_store,
        watch_rooms=parse_room_list(settings.rockbot_rooms),
    )

    logger.info("Starting rockbot (model=%s)", settings.ollama_model)
    try:
        await bot.run_forever()
    finally:
        await rc_client.aclose()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
