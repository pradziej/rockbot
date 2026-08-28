# rockbot

A small, extensible Rocket.Chat bot that forwards user messages to a local
[Ollama](https://ollama.com) model and posts the reply back.

## How it works

- `rocketchat-async` opens a websocket to Rocket.Chat's Realtime API and
  subscribes to messages in every channel the bot user is a member of.
- Each incoming message is routed through a `Router`
  (`rockbot/core/router.py`): a list of handlers tried in order, first one
  to return a reply wins.
- The last handler is `handlers/llm_fallback.py`, which sends the message
  (plus a short rolling history) to Ollama's `/api/chat` endpoint via the
  `ollama` package and returns the model's answer.
- `ConversationStore` keeps the last N turns per channel in memory so the
  model has some context.

```
rocketchat --(websocket)--> RockBot --> Router --> handlers (ping, ...)
                                                 -> llm_fallback --> Ollama
```

## Adding a new command

Add a module under `rockbot/handlers/`, e.g. `handlers/help.py`:

```python
from rockbot.core.router import MessageContext

async def handle(ctx: MessageContext) -> str | None:
    if ctx.text.strip().lower() == "!help":
        return "Available commands: !ping, !help"
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
- A local Ollama server (`ollama serve`) with the configured model pulled
  (`ollama pull llama3.2`).

## Running

```bash
python -m rockbot
# or, after `pip install -e .`:
rockbot
```

## Testing

```bash
pytest
```
