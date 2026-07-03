from abc import ABC, abstractmethod

from src.domain.entities.table_schema import GlueColumn


class IStorageReader(ABC):
    @abstractmethod
    async def read_json(self, bucket: str, key: str) -> dict: ...

    @abstractmethod
    async def list_objects(self, bucket: str, prefix: str) -> list[str]: ...


class IStorageWriter(ABC):
    @abstractmethod
    async def write_parquet(
        self, bucket: str, key: str, data: list[dict], schema: dict | None = None
    ) -> None: ...


class IGlueCatalog(ABC):
    @abstractmethod
    async def table_exists(self, database: str, table: str) -> bool: ...

    @abstractmethod
    async def create_or_update_table(
        self, database: str, table: str, s3_location: str, columns: list[GlueColumn]
    ) -> None: ...
