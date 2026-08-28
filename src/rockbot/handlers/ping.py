from rockbot.core.router import MessageContext


async def handle(ctx: MessageContext) -> str | None:
    """Example command handler: replies "pong" to "/rockbot ping"."""
    if ctx.text.strip().lower() == "ping":
        return "pong"
    return None
