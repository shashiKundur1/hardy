import asyncio
import json

from src.catalog import service
from src.database import create_schema, session_factory
from src.integrations import vectorstore


async def main() -> None:
    await create_schema()
    await vectorstore.ensure_collection()
    async with session_factory() as session:
        synced = await service.resync_all(session)
        state = await service.consistency(session)
    print(f"embedded and upserted {synced} products through Mesh")
    print(json.dumps(state, indent=2))
    if not state["in_sync"]:
        raise SystemExit("stores are not in sync")


if __name__ == "__main__":
    asyncio.run(main())
