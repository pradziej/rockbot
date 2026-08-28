from rockbot.chat.rocketchat_client import Room


def parse_room_list(raw: str) -> list[str]:
    """Split a comma-separated ROCKBOT_ROOMS value into individual entries."""
    return [entry.strip() for entry in raw.split(",") if entry.strip()]


def resolve_rooms(subscriptions: list[Room], wanted: list[str]) -> tuple[list[Room], list[str]]:
    """Match configured room identifiers (IDs or names) against the bot's
    actual subscriptions - the only rooms it can poll.

    An entry is looked up by exact room ID first, then by name (channel
    name, group name, or the other participant's username for a DM),
    case-insensitively.

    Returns (resolved rooms, entries that couldn't be matched to any
    subscription - e.g. a typo, or the bot hasn't been invited yet).
    """
    by_id = {room.id: room for room in subscriptions}
    by_name = {room.name.lower(): room for room in subscriptions if room.name}

    resolved: list[Room] = []
    unresolved: list[str] = []
    for entry in wanted:
        room = by_id.get(entry) or by_name.get(entry.lower())
        if room is None:
            unresolved.append(entry)
        else:
            resolved.append(room)
    return resolved, unresolved
