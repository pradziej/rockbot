import datetime as dt

import httpx
import pytest

from rockbot.chat.rocketchat_client import RocketChatClient, parse_ts


def test_parse_ts_handles_zulu_suffix():
    assert parse_ts("2016-12-09T12:50:51.555Z") == dt.datetime(
        2016, 12, 9, 12, 50, 51, 555000, tzinfo=dt.timezone.utc
    )


def _client_with(handler) -> RocketChatClient:
    return RocketChatClient(
        base_url="http://rc.example",
        user_id="bot",
        token="tok",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_get_rooms_filters_to_supported_types():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/subscriptions.get"
        return httpx.Response(
            200,
            json={
                "update": [
                    {"rid": "room-c", "t": "c"},
                    {"rid": "room-p", "t": "p"},
                    {"rid": "room-d", "t": "d"},
                    {"rid": "room-l", "t": "l"},  # livechat, unsupported
                ],
                "success": True,
            },
        )

    client = _client_with(handler)
    rooms = await client.get_rooms()
    assert {r.id for r in rooms} == {"room-c", "room-p", "room-d"}


@pytest.mark.asyncio
async def test_get_new_messages_excludes_boundary_and_sorts_ascending():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/channels.history"
        assert request.url.params["roomId"] == "room-c"
        return httpx.Response(
            200,
            json={
                "messages": [
                    {"_id": "3", "msg": "third", "ts": "2020-01-01T00:00:03.000Z", "u": {"_id": "u1"}},
                    {"_id": "1", "msg": "boundary", "ts": "2020-01-01T00:00:01.000Z", "u": {"_id": "u1"}},
                    {"_id": "2", "msg": "second", "ts": "2020-01-01T00:00:02.000Z", "u": {"_id": "u1"}},
                ],
                "success": True,
            },
        )

    from rockbot.chat.rocketchat_client import Room

    client = _client_with(handler)
    oldest = parse_ts("2020-01-01T00:00:01.000Z")
    messages = await client.get_new_messages(Room(id="room-c", type="c"), oldest)

    assert [m.msg_id for m in messages] == ["2", "3"]  # boundary excluded, ascending order


@pytest.mark.asyncio
async def test_get_new_messages_returns_empty_on_rate_limit():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"success": False})

    from rockbot.chat.rocketchat_client import Room

    client = _client_with(handler)
    messages = await client.get_new_messages(Room(id="room-c", type="c"), dt.datetime.now(dt.timezone.utc))
    assert messages == []


@pytest.mark.asyncio
async def test_send_message_posts_room_id_and_text():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read()
        return httpx.Response(200, json={"success": True})

    client = _client_with(handler)
    await client.send_message("room-c", "hello")
    assert b'"roomId":"room-c"' in captured["body"]
    assert b'"text":"hello"' in captured["body"]
