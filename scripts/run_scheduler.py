import asyncio

from src.database import create_schema
from src.integrations import mailer
from src.observability import configure_logging, get_logger
from src.recommendations import schedule

logger = get_logger("scripts.scheduler")


async def main() -> None:
    configure_logging()
    await create_schema()
    if not mailer.configured():
        logger.warning("SMTP_HOST and SMTP_USER are unset; digests will compose but not send")
    schedule.start()
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("scheduler stopped")
