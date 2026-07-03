import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(dotenv_path=ROOT / ".env", override=True)

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(name)s | %(message)s")

from scripts.local_mock import MockGlueCatalog, MockStorageReader, MockStorageWriter
from src.application.transform_service import TransformService

logger = logging.getLogger(__name__)


async def run():
    reader = MockStorageReader(data={
        "event": {"id": "evt-local", "type": "item/updated"},
        "item": {"id": "item-local", "status": "UPDATED", "connector": {"id": 201, "name": "Itau"}},
        "accounts": [{"id": "acc-local", "type": "BANK", "name": "Conta", "balance": 1000.0}],
    })
    writer = MockStorageWriter()
    catalog = MockGlueCatalog()

    service = TransformService(
        reader=reader,
        writer=writer,
        catalog=catalog,
        silver_bucket="nerofy-silver-dev",
        glue_database="nerofy",
    )

    await service.process_file(
        bucket="nerofy-bronze-dev",
        key="bronze/items/item-local/year=2026/month=07/day=03/item_evt-local.json",
    )

    logger.info("Parquet escrito: %s", writer.written)
    logger.info("Tabela criada: %s", catalog.create_or_update_table.called)


if __name__ == "__main__":
    asyncio.run(run())
