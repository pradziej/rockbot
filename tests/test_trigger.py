from rockbot.core.trigger import extract_query


def test_ignores_unaddressed_messages():
    assert extract_query("just chatting", "/rockbot") is None
    assert extract_query("/rockboturgent", "/rockbot") is None  # not a word boundary


def test_extracts_query_after_trigger():
    assert extract_query("/rockbot what's up?", "/rockbot") == "what's up?"


def test_is_case_insensitive_on_trigger():
    assert extract_query("/RockBot hello", "/rockbot") == "hello"


def test_bare_trigger_returns_empty_string():
    assert extract_query("/rockbot", "/rockbot") == ""
    assert extract_query("  /rockbot  ", "/rockbot") == ""
