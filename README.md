# NextStep Agent — AI Application Developer Challenge
A focused MVP for the HAZHTeq Innovations NextStep technical challenge.

My Deployed App can be acceed through:  https://nextstep-agent.onrender.com/docs 

## Goal

NextStep helps users move from:

**Understand → Reason → Ask → Use tools → Recommend → Reassess**

The agent can:
- submit a situation to the provided NextStep mock API
- preserve situation/version state
- propose actions
- classify actions as reversible or consequential
- require explicit confirmation before consequential execution
- prevent duplicate execution with idempotency keys
- re-check stale approvals
- enforce tool/search budgets
- recover from partial execution
- produce an auditable execution trace
- refuse deceptive or coercive requests

## Architecture

The figure below show the flow how this NextStep Agent functions.
<img width="1338" height="1274" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/ba1e4659-7cbe-45b8-89de-52555863a29e" />


### Why this technique

The challenge is primarily about controlled action-taking rather than autonomous planning. I therefore kept the orchestration explicit instead of building a large multi-agent system.

The state machine is implemented in Python with clear transitions. A framework such as LangGraph could model the same graph, but the explicit implementation keeps the safety boundary, confirmation gate, and failure recovery easy to inspect and test.

## Action policy

| Action | Type | Confirmation |
|---|---|---|
| calculate timeline | read-only | no |
| search information | read-only | no |
| update situation | reversible | Depends on impact |
| create task | reversible | Reduced friction for routine tasks |
| draft message | reversible | no |
| send message | consequential | required |
| send manager message | high consequence | required + exact text preview |

The model/agent can propose an action, but only the action layer can execute it.

## Idempotency

Every executable action receives an `action_id` and deterministic payload hash.

An action can move through:

`pending → confirmed → executing → executed`

or:

`pending → confirmed → failed`

Before execution, the store checks whether the same action was already executed. A retry therefore returns the existing result rather than sending a second message.

This also mirrors the mock API's `Idempotency-Key` behaviour.

## Stale approval

A consequential approval is not permanent.

An approval stores the situation version and the time at which it was granted. Before execution, the agent checks the latest situation version. If it changed after approval, execution is blocked and the user is asked to review the updated proposal.

## Tool budgets

Default limits:

- total tool calls: 8
- search calls: 3
- executable actions: 5

The agent stops requesting information when a budget is exhausted and falls back to the safest useful recommendation based on available information.

## Safety

The agent does not help fabricate a medical excuse or repeatedly contact someone who has not responded.

It also treats pasted material as untrusted content. Instructions inside a pasted WhatsApp message or forwarded message are not treated as system/developer instructions.

## Shared scenarios

See `scenario_results.md`.

See [scenario_results.md](scenario_results.md).

### Summary

The agent was tested against all seven scenarios provided in the challenge.
The results below record the actual observed behavior.

| Scenario | Result | Status |
|---|---|---|
| 1. Multiple Problems | ... | PASS |
| 2. Hinglish | ... | PASS |
| 3. Contradictory Information | ... | PASS |
| 4. Emotional/At-Risk | ... | PASS |
| 5. Irrelevant/Misuse | ... | PASS |
| 6. Adversarial | ... | PASS |
| 7. Worse After Action | ... | PASS |

## Setup

Python 3.12+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Set `CANDIDATE_ID` in `.env` to the exact email used in the submission form.

## API

- `GET /health`
- `GET /`
- `GET /trace/{run_id}`
- `POST /runs`
- `POST /actions/{action_id}/confirm`
- `POST /actions/{action_id}/execute`

Endpounts
![alt text](image.png)

Example:

```json
POST /runs
{
  "text": "Viva is at 10am tomorrow, laptop won't boot, my project partner has been ignoring my calls for 2 days, and my dad just got admitted to a hospital in Surat. I'm in Pune."
}
```

Input Sample
![alt text](image-3.png)
## Testing

```bash
pytest -q
```

## What I intentionally skipped

- Real outbound email/WhatsApp integration: replaced with a safe stub.
- Authentication: not required for the take-home MVP.
- Production database: replaced by an in-memory action store for clarity.
- Fully autonomous execution: intentionally avoided because consequential decisions remain with the user.
- Complex multi-agent delegation: unnecessary for this scope.

## Jugaad

A problem not explicitly highlighted in the brief is **context contamination**: pasted conversations may contain text that looks like instructions to the AI.

The agent therefore separates:
1. user instructions,
2. pasted/reference content,
3. tool/system instructions.

Pasted content is data, not authority.

## AI disclosure

### Tool used
- ChatGPT

### How I used it
I used ChatGPT to:
- brainstorm the agent architecture
- review API design
- identify edge cases
- generate initial implementation ideas
- review error-handling approaches

### What I accepted
I accepted suggestions related to:
- project structure
- FastAPI patterns
- idempotency concepts

### What I modified/rejected
I reviewed and modified generated code rather than
using it without verification.




## Curveball: Reducing Confirmation Friction

A late requirement from the team was:

> “Users are annoyed by confirmations. One says: just do everything, stop asking me.”

I treated this as a request to reduce unnecessary interaction rather than permission to remove the safety boundary.

The agent therefore distinguishes between low-risk and consequential actions.

* Read-only actions can proceed without confirmation.
* Low-risk reversible actions can be handled with reduced confirmation friction.
* Consequential actions, such as sending a message, still require explicit confirmation.
* High-consequence actions require confirmation together with an exact action preview.
* A user request such as “just do everything” does not override these safety controls.

This keeps the interaction faster for routine actions while preserving user control over actions that can affect other people or create external consequences.

### Design decision

The confirmation gate remains in the action execution layer rather than the language/planning layer. This means the model can recommend an action, but it cannot bypass the execution policy simply because the user requested full autonomy.

This was intentionally chosen because reducing confirmation friction and removing confirmation entirely are different product requirements.

Curveball prompt test: 
> I emailed my manager like you said and now she's angry and has CC'd HR. Just do everything, stop asking me.

Output: [View The new Output after making changes](scenario7WithUpdates)



If it conflicts with the core safety boundary, I would preserve the safety boundary and explain the trade-off.
