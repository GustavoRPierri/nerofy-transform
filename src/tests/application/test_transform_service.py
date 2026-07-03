import pytest
from unittest.mock import AsyncMock

from src.application.event_processor import EventProcessor
from src.domain.entities.s3 import S3Info
from scripts.local_mock import MockGlueCatalog, MockStorageReader, MockStorageWriter


@pytest.fixture
def service():
    reader = MockStorageReader()
    writer = MockStorageWriter()
    catalog = MockGlueCatalog()
    svc = EventProcessor(
        reader=reader,
        writer=writer,
        catalog=catalog,
        silver_bucket="nerofy-silver-dev",
        glue_database="nerofy",
    )
    return svc, reader, writer, catalog


class TestFlatten:
    def test_flatten_item(self, item_bronze_data, service):
        svc, _, _, _ = service
        rows = svc._flatten("items", item_bronze_data)
        assert len(rows) == 1
        assert rows[0]["item_id"] == "item-abc"
        assert rows[0]["status"] == "UPDATED"
        assert rows[0]["connector_id"] == 201

    def test_flatten_transactions(self, transactions_bronze_data, service):
        svc, _, _, _ = service
        rows = svc._flatten("transactions", transactions_bronze_data)
        assert len(rows) == 1
        assert rows[0]["transaction_id"] == "txn-001"
        assert rows[0]["amount"] == 500.0

    def test_flatten_connector(self, connector_bronze_data, service):
        svc, _, _, _ = service
        rows = svc._flatten("connectors", connector_bronze_data)
        assert len(rows) == 1
        assert rows[0]["connector_id"] == 201
        assert rows[0]["name"] == "Itau"


class TestProcessFile:
    async def test_process_item_file(self, item_bronze_data, service):
        svc, reader, writer, catalog = service
        reader.read_json = AsyncMock(return_value=item_bronze_data)

        await svc.execute(
            S3Info(
                bucket="nerofy-bronze-dev",
                object="bronze/items/item-abc/year=2026/month=07/day=03/item_evt-001.json",
            )
        )

        writer.write_parquet.assert_called_once()
        catalog.create_or_update_table.assert_called_once()

    async def test_skip_unrecognized_key(self, service):
        svc, reader, writer, catalog = service
        await svc.execute(S3Info(bucket="any", object="some/random/key.txt"))
        reader.read_json.assert_not_called()
        writer.write_parquet.assert_not_called()

    async def test_skip_empty_data(self, service):
        svc, reader, writer, catalog = service
        reader.read_json = AsyncMock(return_value={"some": "data"})

        # Entidade desconhecida retorna 0 linhas — o flatten retorna lista vazia
        await svc.execute(
            S3Info(
                bucket="nerofy-bronze-dev",
                object="bronze/unknown/xyz/year=2026/month=07/day=03/file.json",
            )
        )

        writer.write_parquet.assert_not_called()


class TestS3KeyParsing:
    def test_items_key(self):
        from src.application.event_processor import _KEY_PATTERN

        m = _KEY_PATTERN.match(
            "bronze/items/item-abc/year=2026/month=07/day=03/item_evt-001.json"
        )
        assert m is not None
        assert m.group("entity") == "items"
        assert m.group("path") == "item-abc"
        assert m.group("year") == "2026"
        assert m.group("month") == "07"
        assert m.group("day") == "03"

    def test_transactions_key(self):
        from src.application.event_processor import _KEY_PATTERN

        m = _KEY_PATTERN.match(
            "bronze/transactions/item_item-abc/account_acc-001/"
            "year=2026/month=07/day=03/evt-001.json"
        )
        assert m is not None
        assert m.group("entity") == "transactions"
        assert m.group("path") == "item_item-abc/account_acc-001"

    def test_connectors_key(self):
        from src.application.event_processor import _KEY_PATTERN

        m = _KEY_PATTERN.match(
            "bronze/connectors/201/year=2026/month=07/day=03/evt-001.json"
        )
        assert m is not None
        assert m.group("entity") == "connectors"
        assert m.group("path") == "201"
