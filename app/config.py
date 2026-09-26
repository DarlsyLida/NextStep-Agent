import os
from dotenv import load_dotenv

load_dotenv()

CANDIDATE_ID = os.getenv("CANDIDATE_ID", "candidate@example.com")
NEXTSTEP_BASE_URL = os.getenv(
    "NEXTSTEP_BASE_URL",
    "https://nextstepmockapi.onrender.com",
)
MAX_TOOL_CALLS = 8
MAX_SEARCH_CALLS = 3
MAX_EXECUTION_ACTIONS = 5
APPROVAL_TTL_SECONDS = 600
