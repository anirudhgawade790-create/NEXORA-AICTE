import json
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.deps import get_current_user
from app.models import User
from app.rate_limit import limiter

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=1500)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=12)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(
    request: Request,
    payload: ChatRequest,
    user: User = Depends(get_current_user),
) -> ChatResponse:
    if not settings.AI_CHAT_API_KEY.strip():
        raise HTTPException(
            status_code=503,
            detail="General AI is not configured. Set AI_CHAT_API_KEY on the backend.",
        )
    if payload.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last chat message must be from the user.")

    conversation: list[Mapping[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are the friendly NEXORA workspace assistant. Reply naturally and "
                "concisely, matching the user's language (including Hinglish). Help with "
                "general questions and explain NEXORA's prototype features. The signed-in "
                f"user role is {user.role}. You cannot see user records or perform actions. "
                "Never claim to have accessed records, changed data, or made an official "
                "AICTE approval. For official regulatory decisions, direct the user to the "
                "competent authority."
            ),
        },
        *[message.model_dump() for message in payload.messages],
    ]
    body = json.dumps({
        "model": settings.AI_CHAT_MODEL,
        "messages": conversation,
        "max_tokens": 500,
    }).encode("utf-8")
    provider_request = UrlRequest(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.AI_CHAT_API_KEY.strip()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(provider_request, timeout=25) as response:
            result = json.loads(response.read())
    except HTTPError as exc:
        if exc.code in {401, 403}:
            raise HTTPException(
                status_code=502,
                detail="AI provider rejected the API key. Replace AI_CHAT_API_KEY with a valid OpenAI API key.",
            ) from exc
        if exc.code == 429:
            try:
                provider_error = json.loads(exc.read()).get("error", {})
            except (json.JSONDecodeError, AttributeError):
                provider_error = {}
            error_code = provider_error.get("code") if isinstance(provider_error, Mapping) else None
            if error_code in {"insufficient_quota", "credit_balance_exhausted"}:
                raise HTTPException(
                    status_code=503,
                    detail="OpenAI API billing has no available credits. Add API credits or billing to the OpenAI account.",
                ) from exc
            raise HTTPException(status_code=503, detail="AI assistant is busy. Please try again shortly.") from exc
        raise HTTPException(status_code=502, detail="AI provider request failed.") from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=503, detail="AI assistant is temporarily unavailable.") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an invalid response.") from exc

    try:
        reply = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an incomplete response.") from exc
    if not isinstance(reply, str) or not reply.strip():
        raise HTTPException(status_code=502, detail="AI provider returned an empty response.")
    return ChatResponse(reply=reply.strip())
