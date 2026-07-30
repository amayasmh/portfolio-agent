import os
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
load_dotenv("portfolio_agent/.env")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from portfolio_agent.agent import make_agent


import asyncio
from datetime import datetime, timezone
from google.cloud import bigquery

# ---------- Logging BigQuery ----------
BQ_TABLE = os.environ.get("BQ_TABLE", "")   # vide = logging désactivé (dev local)
bq_client = bigquery.Client() if BQ_TABLE else None

async def log_event(**fields):
    """Insertion fire-and-forget : ne bloque jamais, ne casse jamais le chat."""
    if not bq_client:
        return
    row = {"ts": datetime.now(timezone.utc).isoformat(), **fields}
    try:
        errors = await asyncio.to_thread(bq_client.insert_rows_json, BQ_TABLE, [row])
        if errors:
            print(f"BQ insert errors: {errors}")
    except Exception as e:
        print(f"BQ logging failed: {e}")



# ---------- Cascade de modèles ----------
MODEL_CHAIN = os.environ.get(
    "MODEL_CHAIN", "gemini-3.5-flash-lite,gemini-3.5-flash"
).split(",")

APP_NAME = "portfolio_agent"
session_service = InMemorySessionService()
runners = [
    Runner(agent=make_agent(m.strip()), app_name=APP_NAME, session_service=session_service)
    for m in MODEL_CHAIN
]

# ---------- App + CORS ----------
app = FastAPI(title="portfolio-agent API")

ALLOWED_ORIGINS = [
    "https://amayas.dev",
    "https://www.amayas.dev",

]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST"],
    allow_headers=["content-type"],
)

# ---------- Rate limiting per IP ----------
RATE_LIMIT, WINDOW_S = 10, 60          
_hits: dict[str, deque] = defaultdict(deque)

def check_rate_limit(ip: str):
    q, now = _hits[ip], time.time()
    while q and now - q[0] > WINDOW_S:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise HTTPException(429, "Rate limit exceeded. Try again in a minute.")
    q.append(now)

# ---------- Inputs ----------
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    session_id: str = Field(min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    lang: str = Field(default="", max_length=5)

# ---------- Endpoints ----------
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(body: ChatIn, request: Request):
    ip = (request.headers.get("x-forwarded-for") or request.client.host).split(",")[0].strip()
    t0 = time.monotonic()                                              # LOG: chrono

    try:
        check_rate_limit(ip)
    except HTTPException:
        asyncio.create_task(log_event(                                 # LOG: 429
            session_id=body.session_id, lang=body.lang, question=body.message,
            status="rate_limited", latency_ms=0))
        raise

    sid = body.session_id
    session = await session_service.get_session(app_name=APP_NAME, user_id=sid, session_id=sid)
    if session is None:
        await session_service.create_session(app_name=APP_NAME, user_id=sid, session_id=sid)

    content = types.Content(role="user", parts=[types.Part(text=body.message)])

    last_error = None
    for i, runner in enumerate(runners):
        try:
            reply = ""
            async for event in runner.run_async(user_id=sid, session_id=sid, new_message=content):
                if event.is_final_response() and event.content and event.content.parts:
                    reply = event.content.parts[0].text or ""
            asyncio.create_task(log_event(                             # LOG: succès
                session_id=sid, lang=body.lang, question=body.message, answer=reply,
                model_used=runner.agent.model, cascade_index=i, status="ok",
                latency_ms=int((time.monotonic() - t0) * 1000)))
            return {"reply": reply, "model": runner.agent.model}
        except Exception as e:
            msg = str(e)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "UNAVAILABLE" in msg or "503" in msg:
                last_error = msg
                continue
            asyncio.create_task(log_event(                             # LOG: erreur franche
                session_id=sid, lang=body.lang, question=body.message,
                model_used=runner.agent.model, cascade_index=i, status="error",
                error_type=msg[:200], latency_ms=int((time.monotonic() - t0) * 1000)))
            raise HTTPException(500, "Agent error")

    if last_error:
        print(f"All models exhausted. Last error: {last_error[:300]}")
    asyncio.create_task(log_event(                                     # LOG: cascade épuisée
        session_id=sid, lang=body.lang, question=body.message,
        status="all_models_exhausted", error_type=(last_error or "")[:200],
        latency_ms=int((time.monotonic() - t0) * 1000)))
    raise HTTPException(503, "All models exhausted — please try again later.")
