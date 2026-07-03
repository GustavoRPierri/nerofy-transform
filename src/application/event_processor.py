import asyncio
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any

from src.domain.entities.table_schema import TABLE_COLUMNS
from src.domain.interfaces.repositories import IGlueCatalog, IStorageReader, IStorageWriter
from src.infrastructure.storage.s3_adapter import S3StorageAdapter


logger = logging.getLogger(__name__)

_KEY_PATTERN = re.compile(
    r"^bronze/(?P<entity>\w+)/(?P<path>.+)/"
    r"year=(?P<year>\d{4})/month=(?P<month>\d{2})/day=(?P<day>\d{2})/"
    r"(?P<filename>.+)\.json$"
)

class EventProcessor:
    def __init__(
        self,
        reader: IStorageReader,
        writer: IStorageWriter,
        catalog: IGlueCatalog,
        silver_bucket: str,
        glue_database: str,
    ):
        self._reader = reader
        self._writer = writer
        self._catalog = catalog
        self._silver_bucket = silver_bucket
        self._glue_database = glue_database

    async def execute(self, event) -> None:

        bucket = event.bucket
        key = event.object

        if not bucket or not key:
            logger.warning("Registro S3 sem bucket e/ou key: %s", json.dumps(event))
            return
        else:
            logger.info("Processando evento S3: bucket=%s, key=%s", bucket, key)

        match = _KEY_PATTERN.match(key)
        if not match:
            logger.warning("Chave S3 ignorada (fora do padrao esperado): %s", key)
            return
        
        entity = match.group("entity")
        year = match.group("year")
        month = match.group("month")
        day = match.group("day")

        data = await self._reader.read_json(bucket, key)
        rows = self._flatten(entity, data)

        if not rows:
            logger.info("Nenhuma linha extraida de %s, ignorando", key)
            return

        silver_key = f"silver/{entity}/year={year}/month={month}/day={day}/data.parquet"
        await self._writer.write_parquet(self._silver_bucket, silver_key, rows)

        await self._ensure_table(entity, year, month, day)       


    def _flatten(self, entity: str, data: dict) -> list[dict[str, Any]]:
        """Extrai linhas tabulares do JSON original conforme a entidade."""
        now = datetime.now(timezone.utc).isoformat()

        if entity == "items":
            return self._flatten_item(data, now)
        elif entity == "transactions":
            return self._flatten_transactions(data, now)
        elif entity == "connectors":
            return self._flatten_connector(data, now)
        else:
            logger.warning("Entidade desconhecida: %s", entity)
            return []

    def _flatten_item(self, data: dict, now: str) -> list[dict[str, Any]]:
        event = data.get("event", {})
        item = data.get("item", {})
        connector = item.get("connector", {})
        accounts = data.get("accounts", [])

        row = {
            "event_id": event.get("id", ""),
            "item_id": item.get("id", ""),
            "status": item.get("status", ""),
            "connector_id": connector.get("id", 0),
            "connector_name": connector.get("name", ""),
            "accounts": json.dumps(accounts),
            "processed_at": now,
        }
        return [row]

    def _flatten_transactions(self, data: dict, now: str) -> list[dict[str, Any]]:
        transactions = data.get("transactions", data.get("data", []))
        if isinstance(transactions, dict):
            transactions = [transactions]

        rows = []
        for txn in transactions:
            rows.append({
                "event_id": data.get("event_id", ""),
                "account_id": txn.get("accountId", txn.get("account_id", "")),
                "transaction_id": txn.get("id", ""),
                "description": txn.get("description", ""),
                "amount": float(txn.get("amount", 0)),
                "date": txn.get("date", ""),
                "category": txn.get("category", ""),
                "processed_at": now,
            })
        return rows

    def _flatten_connector(self, data: dict, now: str) -> list[dict[str, Any]]:
        event = data.get("event", {})
        connector = data.get("connector", {})

        row = {
            "event_id": event.get("id", ""),
            "connector_id": connector.get("id", 0),
            "name": connector.get("name", ""),
            "primary_color": connector.get("primaryColor", ""),
            "processed_at": now,
        }
        return [row]

    async def _ensure_table(self, entity: str, year: str, month: str, day: str) -> None:
        columns = TABLE_COLUMNS.get(entity)
        if not columns:
            logger.warning("Schema desconhecido para entidade %s", entity)
            return

        s3_location = f"s3://{self._silver_bucket}/silver/{entity}/"
        table_name = entity

        await self._catalog.create_or_update_table(
            database=self._glue_database,
            table=table_name,
            s3_location=s3_location,
            columns=columns,
        )