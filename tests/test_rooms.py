from rockbot.chat.rocketchat_client import Room
from rockbot.core.rooms import parse_room_list, resolve_rooms


def test_parse_room_list_splits_and_strips():
    assert parse_room_list(" general , ByehQjC44FwMeiLbX ,alice") == [
        "general",
        "ByehQjC44FwMeiLbX",
        "alice",
    ]


def test_parse_room_list_ignores_empty_entries_and_blank_string():
    assert parse_room_list("general,,  ,alice") == ["general", "alice"]
    assert parse_room_list("") == []
    assert parse_room_list("   ") == []


def test_resolve_rooms_matches_by_id_and_by_name_case_insensitively():
    subscriptions = [
        Room(id="room-c-id", type="c", name="general"),
        Room(id="room-d-id", type="d", name="alice"),
    ]

    resolved, unresolved = resolve_rooms(subscriptions, ["room-c-id", "Alice"])

    assert resolved == [subscriptions[0], subscriptions[1]]
    assert unresolved == []


def test_resolve_rooms_reports_unmatched_entries():
    subscriptions = [Room(id="room-c-id", type="c", name="general")]

    resolved, unresolved = resolve_rooms(subscriptions, ["general", "nonexistent"])

    assert resolved == [subscriptions[0]]
    assert unresolved == ["nonexistent"]


def test_resolve_rooms_id_match_takes_priority_over_name_match():
    # A room's own ID could coincidentally equal another room's name.
    other = Room(id="other-id", type="c", name="room-c-id")
    target = Room(id="room-c-id", type="c", name="target")

    resolved, unresolved = resolve_rooms([other, target], ["room-c-id"])

    assert resolved == [target]
    assert unresolved == []
