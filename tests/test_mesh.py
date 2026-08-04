import asyncio

from app.services import mesh


def test_chat_and_embed_route_through_mesh():
    async def run():
        assert mesh.get_client().base_url.host == "api.meshapi.ai"

        completion = await mesh.chat(
            [{"role": "user", "content": "Reply with exactly: ok"}], max_tokens=5
        )
        assert "ok" in completion.content.lower()
        assert completion.usage.total_tokens > 0
        assert completion.usage.latency_ms > 0

        embedding = await mesh.embed("Lodge 12in cast iron skillet")
        assert len(embedding.vector) == 1536

        assert mesh.call_count() == 2
        assert len(mesh.recent_calls()) == 2

    asyncio.run(run())


if __name__ == "__main__":
    test_chat_and_embed_route_through_mesh()
    print("PASS: chat and embeddings both round-trip through Mesh")
