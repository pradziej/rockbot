from rockbot.chat.ollama_client import OllamaClient
from rockbot.core.router import Router
from rockbot.handlers import llm_fallback, ping


def build_default_router(ollama_client: OllamaClient) -> Router:
    """Wires up the built-in handlers.

    Handlers only ever see the text after the trigger (e.g. "/rockbot ping"
    arrives as "ping"). Add new handlers by registering them here, before
    the LLM fallback - e.g. router.register("help", help_handler.handle).
    """
    router = Router()
    router.register("ping", ping.handle)
    router.register("llm_fallback", llm_fallback.build(ollama_client))
    return router
