from src.integrations import mesh


async def test_every_ai_call_routes_through_mesh():
    mesh.reset_call_log()
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
