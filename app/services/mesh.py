import time
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas import MeshCompletion, MeshEmbedding, MeshUsage

_client: AsyncOpenAI | None = None

_call_log: list[MeshUsage] = []
MAX_CALL_LOG = 100


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.mesh_api_key:
            raise RuntimeError("MESH_API_KEY is not set. Every AI call must route through Mesh.")
        _client = AsyncOpenAI(
            base_url=settings.mesh_base_url,
            api_key=settings.mesh_api_key,
        )
    return _client


def _record(usage: MeshUsage) -> MeshUsage:
    _call_log.append(usage)
    if len(_call_log) > MAX_CALL_LOG:
        del _call_log[:-MAX_CALL_LOG]
    return usage


def recent_calls(limit: int = 20) -> list[MeshUsage]:
    return _call_log[-limit:][::-1]


def call_count() -> int:
    return len(_call_log)


async def chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    **kwargs: Any,
) -> MeshCompletion:
    settings = get_settings()
    model = model or settings.mesh_chat_model
    started = time.perf_counter()

    response = await get_client().chat.completions.create(
        model=model, messages=messages, **kwargs
    )

    raw = response.usage
    usage = _record(MeshUsage(
        model=model,
        prompt_tokens=getattr(raw, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(raw, "completion_tokens", 0) or 0,
        total_tokens=getattr(raw, "total_tokens", 0) or 0,
        latency_ms=int((time.perf_counter() - started) * 1000),
    ))
    return MeshCompletion(content=response.choices[0].message.content or "", usage=usage)


async def embed(text: str, model: str | None = None) -> MeshEmbedding:
    settings = get_settings()
    model = model or settings.mesh_embed_model
    started = time.perf_counter()

    response = await get_client().embeddings.create(model=model, input=text)

    raw = response.usage
    usage = _record(MeshUsage(
        model=model,
        prompt_tokens=getattr(raw, "prompt_tokens", 0) or 0,
        total_tokens=getattr(raw, "total_tokens", 0) or 0,
        latency_ms=int((time.perf_counter() - started) * 1000),
    ))
    return MeshEmbedding(vector=response.data[0].embedding, usage=usage)
