# Football Agentic Assistant

An agentic AI workflow where an LLM (Groq / Qwen) autonomously decides which tool to call to answer football questions, with multi-turn conversation memory.

## Tools

| Tool | Source | What it does |
|---|---|---|
| `calculate_standings` | local | Points and goal difference from match results |
| `days_until_match` | local | Days left until a given date |
| `get_next_match` | TheSportsDB API | A team's next upcoming fixture |
| `get_match_result` | TheSportsDB API | A team's most recent result |

## Project structure

```
src/
  football_tools.py   # tool schemas + implementations
  agent.py            # agent loop (tool calling, max-iteration guard, memory)
  app.py              # Streamlit chat UI with per-tool usage log
  api.py              # FastAPI REST service
```

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_key
```

TheSportsDB works without a key (public test key `123`).

## Run

Streamlit UI:

```bash
python -m streamlit run src/app.py
```

REST API (Swagger UI at http://127.0.0.1:8000/docs):

```bash
python -m uvicorn src.api:app --reload
```

### Endpoints

- `POST /chat` - full agent conversation
- `GET /teams/{team_name}/next-match` - next fixture
- `GET /teams/{team_name}/last-result` - last result

Team names must be in English (e.g. `Al Ahly`).

## Tech stack

Python, Groq (OpenAI-compatible tool calling), Streamlit, FastAPI, TheSportsDB API