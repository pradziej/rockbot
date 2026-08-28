# rockbot

A small, extensible Rocket.Chat bot that forwards user messages to a local
[Ollama](https://ollama.com) model and posts the reply back.

## How it works

- `rocketchat-async` opens a websocket to Rocket.Chat's Realtime API and
  subscribes to messages in every channel the bot user is a member of.
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
rocketchat --(websocket)--> RockBot --(trigger?)--> Router --> handlers (ping, ...)
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
  the channels it should listen in** (the bot only subscribes to channels
  it's already a member of at startup).
- A Personal Access Token for that bot user (Rocket.Chat: avatar menu ->
  My Account -> Personal Access Tokens). Set `ROCKETCHAT_USER_ID` to the
  bot's user id and `ROCKETCHAT_TOKEN` to the generated token; the bot
  authenticates over the realtime API's token-based `login`/`resume`
  call, so no password is stored.
- A local Ollama server (`ollama serve`) with the configured model pulled
  (`ollama pull llama3.2`).

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
