# rockbot

A small, extensible Rocket.Chat bot that forwards user messages to a local
[Ollama](https://ollama.com) model and posts the reply back.

## How it works

- `chat/rocketchat_client.py` talks to Rocket.Chat's plain REST API only -
  no websockets/realtime API, so it works fine behind proxies that force
  `ws://` to redirect to `https://` or otherwise don't support the
  websocket upgrade.
- `RockBot` polls: every `ROCKBOT_POLL_INTERVAL` seconds it lists the
  bot's rooms (`subscriptions.get`) and fetches each room's new messages
  since the last poll (`channels.history` / `groups.history` /
  `im.history`, depending on room type).
- By default every room the bot is a member of is polled. Set
  `ROCKBOT_ROOMS` to a comma-separated list to restrict this to specific
  rooms, given by ID and/or by name (channel/group name, or a DM
  counterpart's username) - `core/rooms.py` resolves names against the
  bot's subscriptions on every poll, so a room becomes watchable as soon
  as the bot is invited to it, no restart needed.
- The bot only responds to messages addressed to it via a trigger prefix
  (`ROCKBOT_TRIGGER`, default `/rockbot`) - e.g. `/rockbot how's it
  going?`. Anything else in the channel is ignored, so the bot doesn't
  answer every message. `core/trigger.py` strips the prefix; handlers only
  ever see the text after it (`/rockbot ping` arrives as `ping`).
- The remaining text is routed through a `Router`
  (`rockbot/core/router.py`): a list of handlers tried in order, first one
  to return a reply wins.
- The last handler is `handlers/llm_fallback.py`, which sends the message
  (plus a short rolling history) to Ollama's `/api/chat` endpoint via the
  `ollama` package and returns the model's answer.
- `ConversationStore` keeps the last N turns per channel in memory so the
  model has some context.

```
rocketchat <--(REST polling)-- RockBot --(trigger?)--> Router --> handlers (ping, ...)
                                                                -> llm_fallback --> Ollama
```

## Adding a new command

Add a module under `rockbot/handlers/`, e.g. `handlers/help.py`. Handlers
receive the text with the trigger already stripped:

```python
from rockbot.core.router import MessageContext

async def handle(ctx: MessageContext) -> str | None:
    if ctx.text.strip().lower() == "help":
        return "Available commands: ping, help"
    return None
```

Register it in `rockbot/handlers/__init__.py`, before `llm_fallback`
(handlers are tried in registration order, and the fallback always
answers):

```python
router.register("help", help.handle)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# edit .env with your Rocket.Chat credentials and Ollama settings
```

Requirements:

- A running Rocket.Chat instance, with a bot user created and **invited to
  the rooms it should listen in** (a newly-joined room is picked up on the
  next poll, but its message history before that point is never replayed).
  This also applies to `ROCKBOT_ROOMS` entries given by name: a room or DM
  can only be resolved if the bot already has a subscription to it (for a
  DM, that means the other person has already messaged the bot, or it was
  opened for them some other way).
- A Personal Access Token for that bot user (Rocket.Chat: avatar menu ->
  My Account -> Personal Access Tokens). Set `ROCKETCHAT_USER_ID` to the
  bot's user id and `ROCKETCHAT_TOKEN` to the generated token; these are
  sent as the standard `X-User-Id` / `X-Auth-Token` REST API headers, so
  no password is stored.
- A local Ollama server (`ollama serve`) with the configured model pulled
  (`ollama pull llama3.2`).
- If the bot is in many rooms, Rocket.Chat's default REST API rate limit
  may kick in (each poll cycle does one request per room). Raise the
  limit under Admin -> Rate Limiter, or increase `ROCKBOT_POLL_INTERVAL`.
- If the Rocket.Chat instance uses a self-signed TLS certificate, set
  `ROCKETCHAT_VERIFY_SSL=false` to skip certificate verification. Only do
  this for an instance you trust - it removes protection against
  man-in-the-middle attacks.

## Running

```bash
python -m rockbot
# or, after `pip install -e .`:
rockbot
```

In a channel the bot is a member of, address it with the trigger prefix:

```
/rockbot The quick brown fox...
```

Messages that don't start with the trigger (`ROCKBOT_TRIGGER`, default
`/rockbot`) are ignored.

### With Docker

```bash
docker build -t rockbot .
docker run --rm --env-file .env rockbot
```

Rocket.Chat and Ollama are expected to be reachable at the URLs in `.env`.
If they run on the host machine rather than in a container, point
`ROCKETCHAT_URL` / `OLLAMA_HOST` at `host.docker.internal` instead of
`localhost` (on Linux, add `--add-host=host.docker.internal:host-gateway`
to the `docker run` command).

## Testing

```bash
pytest
```
