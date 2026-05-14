import os
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Literal
from google import genai
from google.genai import types

from dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["AI"])

# ── Module-level setup ───────────────────────────────────────────────
if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is not set in .env")

client = genai.Client()
MODEL_NAME = "gemini-3.1-flash-lite"
GENERATION_CONFIG = types.GenerateContentConfig(temperature=0.7, max_output_tokens=512)

SYSTEM_CONTEXT = (
    "You are a helpful Python programming assistant for college students. "
    "Answer questions about Python, web development, and AI. "
    "Keep responses under 200 words unless more detail is truly needed."
)

# ── Session management ───────────────────────────────────────────────
chat_sessions: dict[int, object] = {}

def get_or_create_session(user_id: int):
    if user_id not in chat_sessions:
        chat_sessions[user_id] = client.chats.create(
            model=MODEL_NAME,
            history=[
                {"role": "user",  "parts": [{"text": SYSTEM_CONTEXT}]},
                {"role": "model", "parts": [{"text": "Understood. Ready to help."}]},
            ]
        )
    return chat_sessions[user_id]

# ── Schemas for /chat ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    reply: str

# ── POST /ai/chat ────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    request: ChatRequest,
    current_user=Depends(get_current_user),
):
    session = get_or_create_session(current_user.id)
    try:
        response = session.send_message(request.message)
        return ChatResponse(reply=response.text.strip())
    except ValueError:
        raise HTTPException(status_code=400,
                            detail="Message could not be processed — try rephrasing.")
    except Exception as exc:
        print(f"[chat] Gemini error: {exc}")
        raise HTTPException(status_code=503, detail="AI service unavailable.")

# ── DELETE /ai/chat/reset ────────────────────────────────────────────
@router.delete("/chat/reset", status_code=204)
def reset_chat(current_user=Depends(get_current_user)):
    chat_sessions.pop(current_user.id, None)
    return Response(status_code=204)