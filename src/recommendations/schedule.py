from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import settings
from src.observability import get_logger
from src.recommendations import digest
from src.recommendations.constants import DIGEST_MISFIRE_GRACE_SECONDS

DIGEST_JOB_ID = "daily-digest"

logger = get_logger("schedule")


def build() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.digest_timezone)
    scheduler.add_job(
        digest.run,
        CronTrigger(hour=settings.digest_hour, minute=0),
        id=DIGEST_JOB_ID,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=DIGEST_MISFIRE_GRACE_SECONDS,
    )
    return scheduler


def start() -> AsyncIOScheduler:
    scheduler = build()
    scheduler.start()
    logger.info(
        "daily digest scheduled for %02d:00 %s", settings.digest_hour, settings.digest_timezone
    )
    return scheduler


def start_if_enabled() -> AsyncIOScheduler | None:
    if not settings.scheduler_enabled:
        logger.info("scheduler off in this process; a dedicated service runs the digest")
        return None
    return start()
