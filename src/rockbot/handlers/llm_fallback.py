import logging

from rockbot.chat.ollama_client import OllamaClient
from rockbot.core.router import Handler, MessageContext

logger = logging.getLogger(__name__)


def build(ollama_client: OllamaClient) -> Handler:
    """Fallback handler: answers anything not caught by an earlier handler.

    Register this one last so specific commands get a chance to run first.
    """

    async def handle(ctx: MessageContext) -> str | None:
        try:
            return await ollama_client.reply(ctx.history, ctx.text)
        except Exception:
            logger.exception("Ollama request failed for channel %s", ctx.channel_id)
            return "Sorry, I couldn't reach the language model just now."

    return handle
