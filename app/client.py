import uuid
import httpx

from .config import CANDIDATE_ID, NEXTSTEP_BASE_URL

class NextStepClient:
    def __init__(self):
        self.base = NEXTSTEP_BASE_URL.rstrip("/")

    def _headers(self, idempotency_key: str | None = None, chaos: str | None = None):
        headers = {
            "X-Candidate-Id": CANDIDATE_ID,
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if chaos:
            headers["X-Chaos"] = chaos
        return headers

    async def analyze(self, text: str, locale: str, client_time=None, chaos=None):
        payload = {"text": text, "locale": locale}
        if client_time:
            payload["client_time"] = client_time.isoformat()
        key = str(uuid.uuid4())

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base}/v1/situations",
                headers=self._headers(key, chaos),
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def get_situation(self, situation_id: str, chaos=None):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base}/v1/situations/{situation_id}",
                headers=self._headers(chaos=chaos),
            )
            response.raise_for_status()
            return response.json()

    async def scenarios(self):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base}/v1/scenarios",
                headers={"X-Candidate-Id": CANDIDATE_ID},
            )
            response.raise_for_status()
            return response.json()
