from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from rockbot.core.conversation import Turn


@dataclass
class MessageContext:
    """Everything a handler needs to decide how to respond."""

    channel_id: str
    sender_id: str
    text: str
    history: list[Turn] = field(default_factory=list)


Handler = Callable[[MessageContext], Awaitable[str | None]]


class Router:
    """Tries registered handlers in order; the first non-None reply wins.

    Register specific handlers (commands) before generic/fallback ones,
    since the first handler that returns a reply short-circuits the rest.
    """

    def __init__(self) -> None:
        self._handlers: list[tuple[str, Handler]] = []

    def register(self, name: str, handler: Handler) -> None:
        self._handlers.append((name, handler))

    async def dispatch(self, ctx: MessageContext) -> str | None:
        for name, handler in self._handlers:
            reply = await handler(ctx)
            if reply is not None:
                return reply
        return None
