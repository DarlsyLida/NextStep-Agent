from datetime import datetime, timedelta, timezone
from typing import Any


def calculate_time(minutes: int) -> dict[str, Any]:
    return {
        "tool": "calculateTime",
        "minutes": minutes,
        "human": f"{minutes} minutes",
    }


def create_task(title: str, due: str | None = None) -> dict[str, Any]:
    return {
        "tool": "createTask",
        "task_id": f"task_{abs(hash((title, due))) % 10_000_000}",
        "title": title,
        "due": due,
        "status": "created",
    }


def update_situation(text: str) -> dict[str, Any]:
    return {
        "tool": "updateSituation",
        "status": "updated",
        "text": text,
    }


def search_information(query: str) -> dict[str, Any]:
    return {
        "tool": "searchInformation",
        "query": query,
        "status": "stubbed",
        "results": [],
    }


def draft_message(recipient: str, message: str) -> dict[str, Any]:
    return {
        "tool": "draftMessage",
        "recipient": recipient,
        "message": message,
        "status": "drafted",
    }


def send_message(recipient: str, message: str, action_id: str) -> dict[str, Any]:
    # Safe stub: this challenge MVP deliberately does not send real messages.
    return {
        "tool": "sendMessage",
        "action_id": action_id,
        "recipient": recipient,
        "message": message,
        "status": "simulated_sent",
    }
