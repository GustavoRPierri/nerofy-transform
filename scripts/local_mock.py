from unittest.mock import AsyncMock


class MockStorageReader:
    def __init__(self, data: dict | None = None):
        self._data = data or {}
        self.read_json = AsyncMock(return_value=self._data)
        self.list_objects = AsyncMock(return_value=[])


class MockStorageWriter:
    def __init__(self):
        self.write_parquet = AsyncMock()
        self.written: list[tuple[str, str, list[dict]]] = []

        async def _write_parquet(bucket, key, data, schema=None):
            self.written.append((bucket, key, data))

        self.write_parquet.side_effect = _write_parquet


class MockGlueCatalog:
    def __init__(self):
        self.table_exists = AsyncMock(return_value=False)
        self.create_or_update_table = AsyncMock()
