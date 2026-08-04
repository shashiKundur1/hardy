import asyncio

from src.integrations import mesh


def test_all_ai_calls_route_through_mesh():
    async def run():
        assert mesh.get_client().base_url.host == "api.meshapi.ai"

        completion = await mesh.chat(
            [{"role": "user", "content": "Reply with exactly: ok"}], max_tokens=5
        )
        assert "ok" in completion.content.lower()
        assert completion.usage.total_tokens > 0

        embedding = await mesh.embed("Lodge 12in cast iron skillet")
        assert len(embedding.vector) == 1536

        batch = await mesh.embed_many(["cast iron skillet", "waxed canvas backpack"])
        assert len(batch) == 2
        assert batch[0].vector != batch[1].vector

        assert mesh.call_count() == 3

    mesh.reset_call_log()
    asyncio.run(run())


if __name__ == "__main__":
    test_all_ai_calls_route_through_mesh()
    print("PASS: chat, embed and embed_many all route through Mesh")
