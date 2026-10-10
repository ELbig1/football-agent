"""
Football Agent REST API
=========================
1) POST /chat                          -> full agent conversation
2) GET  /teams/{team_name}/next-match  -> next fixture, direct tool call
3) GET  /teams/{team_name}/last-result -> last result, direct tool call

Run from the project root:
    python -m uvicorn src.api:app --reload
Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.
"""

import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import run_agent
from football_tools import execute_get_next_match, execute_get_match_result

app = FastAPI(
    title="Football Agentic API",
    description=(
        "REST API exposing a football-specialized agentic workflow: "
        "an LLM (Groq/Qwen) decides which tool to call based on the question."
    ),
    version="1.0.0",
)


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list] = None


class ChatResponse(BaseModel):
    answer: str
    conversation_history: list


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
def chat(payload: ChatRequest):
    """Send a question; the agent decides which tool(s) to use."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message field can't be empty")

    answer, history = run_agent(
        payload.message,
        verbose=False,
        conversation_history=payload.conversation_history,
    )
    return ChatResponse(answer=answer, conversation_history=history)


@app.get("/teams/{team_name}/next-match", tags=["Tools"])
def next_match(team_name: str):
    """Next upcoming fixture for a team (English name, e.g. Al Ahly)."""
    return {"team": team_name, "result": execute_get_next_match(team_name)}


@app.get("/teams/{team_name}/last-result", tags=["Tools"])
def last_result(team_name: str):
    """Most recent result for a team (English name, e.g. Zamalek)."""
    return {"team": team_name, "result": execute_get_match_result(team_name)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
