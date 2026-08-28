def extract_query(text: str, trigger: str) -> str | None:
    """Check whether `text` addresses the bot via `trigger` and pull out the rest.

    Returns None if the message isn't addressed to the bot (should be
    ignored), or the text following the trigger otherwise - which may be
    an empty string if the trigger was used with no query attached.
    """
    stripped = text.strip()
    trigger_lower = trigger.lower()
    stripped_lower = stripped.lower()

    if stripped_lower == trigger_lower:
        return ""
    if stripped_lower.startswith(trigger_lower + " "):
        return stripped[len(trigger):].strip()
    return None
