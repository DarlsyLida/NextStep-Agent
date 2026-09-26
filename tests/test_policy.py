from app.agent import Agent
from app.models import ActionKind


def test_send_message_is_consequential():
    assert Agent.classify_action("sendMessage", {"message": "hello"}) == ActionKind.consequential


def test_fake_excuse_is_harmful():
    assert Agent.classify_action("draftMessage", {"message": "fake medical excuse"}) == ActionKind.harmful
