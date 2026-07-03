import asyncio
import json
import logging
from typing import List

from config.settings import settings
from src.infrastructure.glue.glue_catalog import GlueCatalogAdapter
from src.infrastructure.storage.s3_adapter import S3StorageAdapter
from src.application.event_processor import EventProcessor
from src.domain.entities.s3 import S3Event
from src.domain.entities.s3 import S3Info

settings.setup_logging()
logger = logging.getLogger(__name__)

reader = S3StorageAdapter()
writer = S3StorageAdapter()
catalog = GlueCatalogAdapter()

_LOOP: asyncio.AbstractEventLoop | None = None
_semaphore = asyncio.Semaphore(5)


async def _process_event(event: S3Info) -> None:
    async with _semaphore:
        processor = EventProcessor(
            reader=reader,
            writer=writer,
            catalog=catalog,
            silver_bucket=settings.s3_silver_bucket,
            glue_database=settings.glue_database,
        )
        await processor.execute(event)


async def _process_all(events: List[S3Info]) -> None:
    results = await asyncio.gather(
        *[asyncio.create_task(_process_event(e)) for e in events],
        return_exceptions=True,
    )
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("Falha no evento %d: %s", i, r, exc_info=r)


def lambda_handler(event: dict, context) -> dict:
    global _LOOP
    try:
        parsed = S3Event.model_validate(event)
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    if _LOOP is None or _LOOP.is_closed():
        _LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_LOOP)
    try:
        _LOOP.run_until_complete(_process_all(parsed.events))
    except Exception as e:
        logger.error("Erro crítico: %s", e, exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": "Internal processing error"})}
    return {"statusCode": 200, "body": json.dumps({"message": "Events processed successfully"})}
