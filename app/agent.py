import uuid
from datetime import datetime, timezone

from .client import NextStepClient
from .config import (
    APPROVAL_TTL_SECONDS,
    MAX_EXECUTION_ACTIONS,
    MAX_SEARCH_CALLS,
    MAX_TOOL_CALLS,
)
from .models import (
    Action,
    ActionKind,
    ActionStatus,
    RunRequest,
    TraceEvent,
    TraceLabel,
)
from .store import ActionStore
from .tools import draft_message, send_message


class Agent:
    def __init__(self):
        self.client = NextStepClient()
        self.store = ActionStore()

    def trace(self, run_id, label, message, data=None):
        self.store.add_trace(
            run_id,
            TraceEvent(
                label=label,
                message=message,
                data=data or {},
            ),
        )

    @staticmethod
    def classify_action(tool: str, payload: dict):
        harmful_terms = [
            "fake medical excuse",
            "fake excuse",
            "message my ex until she replies",
            "keep messaging my ex",
        ]

        combined = f"{tool} {payload}".lower()

        if any(term in combined for term in harmful_terms):
            return ActionKind.harmful

        if tool == "sendMessage":
            return ActionKind.consequential

        if tool in {"createTask", "updateSituation"}:
            return ActionKind.reversible

        return ActionKind.read_only

    @staticmethod
    def user_requested_autonomy(text: str) -> bool:
        """
        Detect requests to reduce unnecessary confirmation friction.

        This preference does NOT override consequential-action safety gates.
        """
        text_lower = text.lower()

        autonomy_phrases = [
            "just do everything",
            "stop asking me",
            "don't ask me",
            "do everything for me",
            "just do it",
            "don't keep asking",
            "no need to ask",
            "handle everything",
        ]

        return any(
            phrase in text_lower
            for phrase in autonomy_phrases
        )

    @staticmethod
    def requires_confirmation(action_kind: ActionKind) -> bool:
        """
        Consequential and harmful actions can never bypass confirmation.
        """
        return action_kind in {
            ActionKind.consequential,
            ActionKind.harmful,
        }

    async def run(self, request: RunRequest):
        run_id = f"run_{uuid.uuid4().hex[:10]}"

        self.trace(
            run_id,
            TraceLabel.reasoning,
            "Understanding the user's situation.",
        )

        text_lower = request.text.lower()

        # ---------------------------------------------------------
        # USER AUTONOMY PREFERENCE
        # ---------------------------------------------------------

        autonomy_requested = self.user_requested_autonomy(request.text)

        if autonomy_requested:
            self.trace(
                run_id,
                TraceLabel.reasoning,
                (
                    "User requested fewer confirmations. "
                    "Routine low-risk actions may proceed automatically, "
                    "but consequential actions still require explicit confirmation."
                ),
                {
                    "autonomy_requested": True,
                    "consequential_confirmation_required": True,
                },
            )

        # ---------------------------------------------------------
        # SAFETY BOUNDARIES
        # ---------------------------------------------------------

        if (
            "what's the point" in text_lower
            or "don't want to deal" in text_lower
        ):
            self.trace(
                run_id,
                TraceLabel.reasoning,
                (
                    "Detected possible emotional distress; "
                    "normal task planning is paused."
                ),
            )

            return {
                "run_id": run_id,
                "mode": "support",
                "summary": (
                    "You sound overwhelmed, so I won't turn this into a "
                    "normal productivity plan. Please consider reaching "
                    "out to someone you trust and getting immediate local "
                    "help if you may be in danger."
                ),
                "actions": [],
                "trace": [
                    e.model_dump(mode="json")
                    for e in self.store.get_trace(run_id)
                ],
            }

        if (
            "1500-word essay" in text_lower
            and "assignment" in text_lower
        ):
            self.trace(
                run_id,
                TraceLabel.reasoning,
                "Request is outside the intended NextStep use case.",
            )

            return {
                "run_id": run_id,
                "mode": "out_of_scope",
                "summary": (
                    "NextStep is for deciding what to do next, "
                    "not completing an assignment. I can help break "
                    "the assignment into manageable next steps."
                ),
                "actions": [],
                "trace": [
                    e.model_dump(mode="json")
                    for e in self.store.get_trace(run_id)
                ],
            }

        if "upi pin" in text_lower:
            self.trace(
                run_id,
                TraceLabel.reasoning,
                (
                    "Detected untrusted content requesting "
                    "sensitive credentials."
                ),
            )

            return {
                "run_id": run_id,
                "mode": "safe_refusal",
                "summary": (
                    "The pasted message contains an instruction to "
                    "request a UPI PIN. I will treat that as untrusted "
                    "content and will not request or expose credentials."
                ),
                "actions": [],
                "trace": [
                    e.model_dump(mode="json")
                    for e in self.store.get_trace(run_id)
                ],
            }

        if (
            "fake medical excuse" in text_lower
            or "message my ex until she replies" in text_lower
        ):
            self.trace(
                run_id,
                TraceLabel.reasoning,
                "Request conflicts with the agent safety policy.",
            )

            return {
                "run_id": run_id,
                "mode": "refused",
                "summary": (
                    "I can't help fabricate a medical excuse "
                    "or facilitate repeated unwanted contact."
                ),
                "actions": [],
                "trace": [
                    e.model_dump(mode="json")
                    for e in self.store.get_trace(run_id)
                ],
            }

        # ---------------------------------------------------------
        # NEXTSTEP ANALYSIS
        # ---------------------------------------------------------

        try:
            self.trace(
                run_id,
                TraceLabel.reasoning,
                "Calling NextStep analysis service.",
            )

            analysis = await self.client.analyze(
                request.text,
                request.locale,
                request.client_time,
                request.chaos,
            )

        except Exception as exc:
            print(
                f"Analysis service error: "
                f"{type(exc).__name__}: {exc}"
            )

            self.trace(
                run_id,
                TraceLabel.reasoning,
                (
                    "Analysis service failed; "
                    "no consequential action will be executed."
                ),
                {
                    "error": type(exc).__name__,
                    "details": str(exc),
                },
            )

            return {
                "run_id": run_id,
                "mode": "degraded",
                "summary": (
                    "The analysis service failed or timed out. "
                    "No external action was executed."
                ),
                "actions": [],
                "error": type(exc).__name__,
                "error_details": str(exc),
                "trace": [
                    e.model_dump(mode="json")
                    for e in self.store.get_trace(run_id)
                ],
            }

        # ---------------------------------------------------------
        # ANALYSIS RESULT
        # ---------------------------------------------------------

        self.trace(
            run_id,
            TraceLabel.reasoning,
            "Analysis received.",
            {
                "situation_id": analysis.get("situation_id"),
                "version": analysis.get("version"),
                "mode": analysis.get("mode"),
            },
        )

        actions = []

        next_action = analysis.get("next_action")

        if next_action:
            payload = {
                "title": next_action.get("text", ""),
                "issue_id": next_action.get("issue_id"),
            }

            action_id = f"act_{uuid.uuid4().hex[:10]}"

            # Classify the proposed action instead of assuming
            # everything is reversible.
            action_kind = self.classify_action(
                "createTask",
                payload,
            )

            action = Action(
                action_id=action_id,
                kind=action_kind,
                tool="createTask",
                payload=payload,
                situation_version=analysis.get("version"),
                payload_hash=self.store.hash_payload(payload),
            )

            self.store.save_action(action)

            # -----------------------------------------------------
            # AUTONOMY BEHAVIOUR
            # -----------------------------------------------------

            if autonomy_requested:
                if self.requires_confirmation(action.kind):
                    self.trace(
                        run_id,
                        TraceLabel.asking,
                        (
                            "The user requested fewer confirmations, "
                            "but this action is consequential and "
                            "still requires explicit confirmation."
                        ),
                        {
                            "action_id": action_id,
                            "action_kind": action.kind.value,
                        },
                    )

                else:
                    # Low-risk reversible action.
                    self.trace(
                        run_id,
                        TraceLabel.confirmed,
                        (
                            "User requested reduced confirmation friction. "
                            "Automatically approving this low-risk reversible action."
                        ),
                        {
                            "action_id": action_id,
                            "action_kind": action.kind.value,
                        },
                    )

                    try:
                        action = self.store.confirm(action)

                        action = await self.execute(
                            action_id,
                            analysis.get("version"),
                        )

                        self.trace(
                            run_id,
                            TraceLabel.executed,
                            "Low-risk action executed automatically.",
                            {
                                "action_id": action_id,
                                "status": action.status.value,
                            },
                        )

                    except Exception as exc:
                        self.trace(
                            run_id,
                            TraceLabel.reasoning,
                            "Automatic low-risk action execution failed.",
                            {
                                "action_id": action_id,
                                "error": type(exc).__name__,
                            },
                        )

            else:
                self.trace(
                    run_id,
                    TraceLabel.proposing,
                    "Proposed the next action without executing it.",
                    {
                        "action_id": action_id,
                    },
                )

            actions.append(
                action.model_dump(mode="json")
            )

        # ---------------------------------------------------------
        # TRACE
        # ---------------------------------------------------------

        self.trace(
            run_id,
            TraceLabel.asking,
            "Clarifying questions are preserved for the user.",
        )

        return {
            "run_id": run_id,
            "mode": analysis.get("mode"),
            "situation_id": analysis.get("situation_id"),
            "version": analysis.get("version"),
            "summary": analysis.get("summary"),
            "issues": analysis.get("issues", []),
            "priorities": analysis.get("priorities", []),
            "next_action": next_action,
            "clarifying_questions": analysis.get(
                "clarifying_questions",
                [],
            ),
            "actions": actions,
            "autonomy_requested": autonomy_requested,
            "trace": [
                e.model_dump(mode="json")
                for e in self.store.get_trace(run_id)
            ],
        }

    def confirm(
        self,
        action_id: str,
        expected_version: int,
    ):
        action = self.store.get_action(action_id)

        if not action:
            raise KeyError("action_not_found")

        if action.situation_version != expected_version:
            raise ValueError("stale_situation_version")

        action = self.store.confirm(action)

        return action

    async def execute(
        self,
        action_id: str,
        expected_version: int,
    ):
        action = self.store.get_action(action_id)

        if not action:
            raise KeyError("action_not_found")

        # Idempotency: already executed actions are not executed again.
        if action.status == ActionStatus.executed:
            return action

        # Execution requires confirmation.
        if action.status != ActionStatus.confirmed:
            raise ValueError("confirmation_required")

        # Prevent execution against an outdated situation.
        if action.situation_version != expected_version:
            raise ValueError("stale_situation_version")

        # Approval expires after the configured TTL.
        if action.approved_at:
            age = (
                datetime.now(timezone.utc)
                - action.approved_at
            ).total_seconds()

            if age > APPROVAL_TTL_SECONDS:
                raise ValueError("approval_expired")

        action.status = ActionStatus.executing

        try:
            if action.tool == "sendMessage":
                result = send_message(
                    action.payload["recipient"],
                    action.payload["message"],
                    action.action_id,
                )

            elif action.tool == "createTask":
                from .tools import create_task

                result = create_task(
                    action.payload["title"]
                )

            elif action.tool == "updateSituation":
                from .tools import update_situation

                result = update_situation(
                    action.payload["text"]
                )

            else:
                result = {
                    "status": "no-op",
                    "tool": action.tool,
                }

            action.result = result
            action.status = ActionStatus.executed

        except Exception as exc:
            action.status = ActionStatus.failed
            action.result = {
                "error": type(exc).__name__
            }

        self.store.save_action(action)

        return action