import asyncio
import logging

from rockbot.chat.ollama_client import OllamaClient
from rockbot.config import get_settings
from rockbot.core.bot import RockBot
from rockbot.core.conversation import ConversationStore
from rockbot.handlers import build_default_router
from rockbot.logging_config import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.rockbot_log_level)

    ollama_client = OllamaClient(
        host=settings.ollama_host,
        model=settings.ollama_model,
        system_prompt=settings.ollama_system_prompt,
    )
    conversation_store = ConversationStore(max_turns=settings.rockbot_history_length)
    router = build_default_router(ollama_client)

    bot = RockBot(
        url=settings.rocketchat_url,
        user_id=settings.rocketchat_user_id,
        token=settings.rocketchat_token,
        trigger=settings.rockbot_trigger,
        router=router,
        conversation_store=conversation_store,
    )

    logger.info("Starting rockbot (model=%s)", settings.ollama_model)
    await bot.run_forever()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
