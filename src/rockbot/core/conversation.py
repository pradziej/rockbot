from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Turn:
    role: str  # "user" or "assistant"
    content: str


class ConversationStore:
    """Keeps a short rolling history of messages per Rocket.Chat channel."""

    def __init__(self, max_turns: int = 10) -> None:
        self._max_turns = max_turns
        self._history: dict[str, deque[Turn]] = defaultdict(
            lambda: deque(maxlen=max_turns)
        )

    def add(self, channel_id: str, role: str, content: str) -> None:
        self._history[channel_id].append(Turn(role=role, content=content))

    def get(self, channel_id: str) -> list[Turn]:
        return list(self._history[channel_id])

    def clear(self, channel_id: str) -> None:
        self._history.pop(channel_id, None)
