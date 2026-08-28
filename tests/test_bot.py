import pytest

from rockbot.chat.rocketchat_client import Room
from rockbot.core.bot import RockBot
from rockbot.core.conversation import ConversationStore
from rockbot.core.router import Router


class FakeClient:
    def __init__(self, rooms):
        self.user_id = "bot-id"
        self._rooms = rooms
        self.polled_room_ids = []

    async def whoami(self):
        return "rockbot"

    async def get_rooms(self):
        return self._rooms

    async def get_new_messages(self, room, oldest):
        self.polled_room_ids.append(room.id)
        return []

    async def send_message(self, room_id, text):
        pass


def _bot(client, watch_rooms=None) -> RockBot:
    return RockBot(
        client=client,
        trigger="/rockbot",
        poll_interval=1.0,
        router=Router(),
        conversation_store=ConversationStore(max_turns=5),
        watch_rooms=watch_rooms,
    )


@pytest.mark.asyncio
async def test_watch_rooms_restricts_polling_to_matching_rooms():
    rooms = [
        Room(id="general-id", type="c", name="general"),
        Room(id="random-id", type="c", name="random"),
    ]
    client = FakeClient(rooms)
    bot = _bot(client, watch_rooms=["general"])

    await bot._poll_once()  # establishes the baseline for "general" only
    await bot._poll_once()  # actually polls it

    assert client.polled_room_ids == ["general-id"]


@pytest.mark.asyncio
async def test_no_watch_rooms_polls_everything():
    rooms = [
        Room(id="general-id", type="c", name="general"),
        Room(id="random-id", type="c", name="random"),
    ]
    client = FakeClient(rooms)
    bot = _bot(client)

    await bot._poll_once()
    await bot._poll_once()

    assert set(client.polled_room_ids) == {"general-id", "random-id"}


@pytest.mark.asyncio
async def test_unresolved_room_warns_once(caplog):
    client = FakeClient([Room(id="general-id", type="c", name="general")])
    bot = _bot(client, watch_rooms=["nonexistent"])

    with caplog.at_level("WARNING"):
        await bot._poll_once()
        await bot._poll_once()

    warnings = [r for r in caplog.records if "nonexistent" in r.getMessage()]
    assert len(warnings) == 1
    assert client.polled_room_ids == []
