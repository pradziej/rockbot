import logging

from ollama import AsyncClient

from rockbot.core.conversation import Turn

logger = logging.getLogger(__name__)


class OllamaClient:
    """Thin wrapper around the local Ollama server's chat API."""

    def __init__(self, host: str, model: str, system_prompt: str) -> None:
        self._client = AsyncClient(host=host)
        self._model = model
        self._system_prompt = system_prompt

    async def reply(self, history: list[Turn], user_message: str) -> str:
        messages = [{"role": "system", "content": self._system_prompt}]
        messages += [{"role": turn.role, "content": turn.content} for turn in history]
        messages.append({"role": "user", "content": user_message})

        logger.debug("Sending %d messages to model %s", len(messages), self._model)
        response = await self._client.chat(
            model=self._model,
            messages=messages,
            stream=False,
        )
        return response.message.content
