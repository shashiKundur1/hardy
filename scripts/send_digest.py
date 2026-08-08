import asyncio

from src.database import create_schema
from src.integrations import mailer
from src.observability import configure_logging, get_logger
from src.recommendations import digest

logger = get_logger("scripts.digest")


async def main() -> None:
    configure_logging()
    await create_schema()
    if not mailer.configured():
        logger.warning("SMTP_HOST and SMTP_USER are unset; the run will compose but not send")
    result = await digest.run()
    logger.info("considered %s accounts, sent %s", result["considered"], result["sent"])


if __name__ == "__main__":
    asyncio.run(main())
