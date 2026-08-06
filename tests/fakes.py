import hashlib
import random

from src.config import settings
from src.integrations.schemas import MeshCompletion, MeshEmbedding, MeshUsage


def vector_for(text: str) -> list[float]:
    seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(settings.embedding_dim)]


class OfflineMesh:
    def __init__(self, replies: list[str] | None = None) -> None:
        self.replies = list(replies or [])
        self.chats: list[list[dict]] = []
        self.embedded: list[str] = []

    @property
    def calls(self) -> int:
        return len(self.chats) + len(self.embedded)

    def _usage(self, model: str | None) -> MeshUsage:
        return MeshUsage(model=model or "offline", total_tokens=1, latency_ms=1)

    async def chat(self, messages: list[dict], model: str | None = None, **_) -> MeshCompletion:
        self.chats.append(messages)
        content = self.replies.pop(0) if self.replies else "{}"
        return MeshCompletion(content=content, usage=self._usage(model))

    async def embed(self, text: str, model: str | None = None) -> MeshEmbedding:
        self.embedded.append(text)
        return MeshEmbedding(vector=vector_for(text), usage=self._usage(model))

    async def embed_many(self, texts: list[str], model: str | None = None) -> list[MeshEmbedding]:
        self.embedded.extend(texts)
        usage = self._usage(model)
        return [MeshEmbedding(vector=vector_for(text), usage=usage) for text in texts]
