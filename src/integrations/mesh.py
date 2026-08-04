import time
from collections import deque
from typing import Any

from openai import AsyncOpenAI

from src.config import settings
from src.integrations.schemas import MeshCompletion, MeshEmbedding, MeshUsage

CALL_LOG_SIZE = 200

_client: AsyncOpenAI | None = None
_call_log: deque[MeshUsage] = deque(maxlen=CALL_LOG_SIZE)


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.mesh_api_key:
            raise RuntimeError("MESH_API_KEY is unset; every AI call must route through Mesh")
        _client = AsyncOpenAI(
            base_url=settings.mesh_base_url,
            api_key=settings.mesh_api_key,
            timeout=settings.mesh_timeout_seconds,
        )
    return _client


def _log(usage: MeshUsage) -> MeshUsage:
    _call_log.append(usage)
    return usage


def recent_calls(limit: int = 20) -> list[MeshUsage]:
    return list(_call_log)[-limit:][::-1]


def call_count() -> int:
    return len(_call_log)


def reset_call_log() -> None:
    _call_log.clear()


async def chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    **kwargs: Any,
) -> MeshCompletion:
    model = model or settings.mesh_chat_model
    started = time.perf_counter()
    response = await get_client().chat.completions.create(
        model=model, messages=messages, **kwargs
    )
    usage = _log(_usage_from(response, model, started))
    return MeshCompletion(content=response.choices[0].message.content or "", usage=usage)


async def embed(text: str, model: str | None = None) -> MeshEmbedding:
    model = model or settings.mesh_embed_model
    started = time.perf_counter()
    response = await get_client().embeddings.create(model=model, input=text)
    usage = _log(_usage_from(response, model, started))
    return MeshEmbedding(vector=response.data[0].embedding, usage=usage)


async def embed_many(texts: list[str], model: str | None = None) -> list[MeshEmbedding]:
    model = model or settings.mesh_embed_model
    started = time.perf_counter()
    response = await get_client().embeddings.create(model=model, input=texts)
    usage = _log(_usage_from(response, model, started))
    ordered = sorted(response.data, key=lambda d: d.index)
    return [MeshEmbedding(vector=item.embedding, usage=usage) for item in ordered]


def _usage_from(response: Any, model: str, started: float) -> MeshUsage:
    raw = getattr(response, "usage", None)
    return MeshUsage(
        model=model,
        prompt_tokens=getattr(raw, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(raw, "completion_tokens", 0) or 0,
        total_tokens=getattr(raw, "total_tokens", 0) or 0,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
