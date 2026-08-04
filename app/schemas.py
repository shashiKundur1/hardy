from pydantic import BaseModel


class MeshUsage(BaseModel):
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0


class MeshCompletion(BaseModel):
    content: str
    usage: MeshUsage


class MeshEmbedding(BaseModel):
    vector: list[float]
    usage: MeshUsage
