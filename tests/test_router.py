import pytest

from rockbot.core.router import MessageContext, Router


def _ctx(text: str) -> MessageContext:
    return MessageContext(channel_id="c1", sender_id="u1", text=text)


@pytest.mark.asyncio
async def test_first_matching_handler_wins():
    async def no_match(ctx: MessageContext) -> str | None:
        return None

    async def always_pong(ctx: MessageContext) -> str | None:
        return "pong"

    router = Router()
    router.register("no_match", no_match)
    router.register("always_pong", always_pong)

    assert await router.dispatch(_ctx("hello")) == "pong"


@pytest.mark.asyncio
async def test_returns_none_when_no_handler_matches():
    async def no_match(ctx: MessageContext) -> str | None:
        return None

    router = Router()
    router.register("no_match", no_match)

    assert await router.dispatch(_ctx("hello")) is None
