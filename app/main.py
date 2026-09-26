from fastapi import FastAPI, HTTPException

from .agent import Agent
from .models import ConfirmRequest, ExecuteRequest, RunRequest

app = FastAPI(title="NextStep Agent", version="0.1.0")
agent = Agent()


@app.get("/")
async def root():
    return {
        "name": "NextStep Agent",
        "version": "0.1.0",
        "status": "ready",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/runs")
async def create_run(request: RunRequest):
    return await agent.run(request)


@app.get("/trace/{run_id}")
async def get_trace(run_id: str):
    return {
        "run_id": run_id,
        "trace": [e.model_dump(mode="json") for e in agent.store.get_trace(run_id)],
    }


@app.post("/actions/{action_id}/confirm")
async def confirm_action(action_id: str, request: ConfirmRequest):
    try:
        action = agent.confirm(action_id, request.expected_situation_version)
        return action.model_dump(mode="json")
    except KeyError:
        raise HTTPException(404, "action_not_found")
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.post("/actions/{action_id}/execute")
async def execute_action(action_id: str, request: ExecuteRequest):
    try:
        action = await agent.execute(action_id, request.expected_situation_version)
        return action.model_dump(mode="json")
    except KeyError:
        raise HTTPException(404, "action_not_found")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
