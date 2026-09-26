from app.agent import Agent
from app.models import ActionKind


def test_send_message_is_consequential():
    assert Agent.classify_action(
        "sendMessage",
        {"message": "hello"},
    ) == ActionKind.consequential


def test_fake_excuse_is_harmful():
    assert Agent.classify_action(
        "draftMessage",
        {"message": "fake medical excuse"},
    ) == ActionKind.harmful


def test_just_do_everything_requests_autonomy():
    assert Agent.user_requested_autonomy(
        "Just do everything, stop asking me."
    ) is True


def test_stop_asking_requests_autonomy():
    assert Agent.user_requested_autonomy(
        "Stop asking me and handle everything."
    ) is True


def test_normal_request_does_not_request_autonomy():
    assert Agent.user_requested_autonomy(
        "Help me figure out what I should do next."
    ) is False


def test_reversible_action_does_not_require_confirmation():
    assert Agent.requires_confirmation(
        ActionKind.reversible
    ) is False


def test_read_only_action_does_not_require_confirmation():
    assert Agent.requires_confirmation(
        ActionKind.read_only
    ) is False


def test_consequential_action_requires_confirmation():
    assert Agent.requires_confirmation(
        ActionKind.consequential
    ) is True


def test_harmful_action_requires_confirmation():
    assert Agent.requires_confirmation(
        ActionKind.harmful
    ) is True