import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .models import Action, ActionStatus, TraceEvent


class ActionStore:
    def __init__(self):
        self.actions: dict[str, Action] = {}
        self.traces: dict[str, list[TraceEvent]] = {}

    @staticmethod
    def hash_payload(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def save_action(self, action: Action) -> Action:
        self.actions[action.action_id] = action
        return action

    def get_action(self, action_id: str) -> Action | None:
        return self.actions.get(action_id)

    def add_trace(self, run_id: str, event: TraceEvent):
        self.traces.setdefault(run_id, []).append(event)

    def get_trace(self, run_id: str) -> list[TraceEvent]:
        return self.traces.get(run_id, [])

    def confirm(self, action: Action):
        action.status = ActionStatus.confirmed
        action.approved_at = datetime.now(timezone.utc)
        return self.save_action(action)
