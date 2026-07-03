import logging

import boto3
from botocore.exceptions import ClientError

from src.domain.entities.table_schema import GlueColumn
from src.domain.interfaces.repositories import IGlueCatalog

logger = logging.getLogger(__name__)


class GlueCatalogAdapter(IGlueCatalog):
    def __init__(self):
        self._glue = boto3.client("glue")

    async def table_exists(self, database: str, table: str) -> bool:
        try:
            self._glue.get_table(DatabaseName=database, Name=table)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "EntityNotFoundException":
                return False
            logger.error("Erro ao verificar tabela %s.%s: %s", database, table, e)
            raise

    async def create_or_update_table(
        self, database: str, table: str, s3_location: str, columns: list[GlueColumn]
    ) -> None:
        input = {
            "Name": table,
            "StorageDescriptor": {
                "Columns": [col.to_glue_dict() for col in columns],
                "Location": s3_location,
                "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                "SerdeInfo": {
                    "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                },
            },
            "TableType": "EXTERNAL_TABLE",
            "Parameters": {"classification": "parquet"},
        }
        try:
            if await self.table_exists(database, table):
                self._glue.update_table(DatabaseName=database, TableInput=input)
                logger.info("Tabela %s.%s atualizada no Glue Catalog", database, table)
            else:
                self._glue.create_table(DatabaseName=database, TableInput=input)
                logger.info("Tabela %s.%s criada no Glue Catalog", database, table)
        except ClientError as e:
            logger.error("Erro ao registrar tabela %s.%s: %s", database, table, e)
            raise
