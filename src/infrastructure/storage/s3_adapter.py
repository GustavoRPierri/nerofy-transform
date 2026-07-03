import json
import logging

import boto3
from botocore.exceptions import ClientError

from src.domain.interfaces.repositories import IStorageReader, IStorageWriter

logger = logging.getLogger(__name__)


class S3StorageAdapter(IStorageReader, IStorageWriter):
    def __init__(self):
        self._s3 = boto3.client("s3")

    async def read_json(self, bucket: str, key: str) -> dict:
        try:
            response = self._s3.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read().decode("utf-8")
            return json.loads(body)
        except ClientError as e:
            logger.error("Erro ao ler s3://%s/%s: %s", bucket, key, e)
            raise

    async def list_objects(self, bucket: str, prefix: str) -> list[str]:
        try:
            keys: list[str] = []
            paginator = self._s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
            return keys
        except ClientError as e:
            logger.error("Erro ao listar s3://%s/%s: %s", bucket, prefix, e)
            raise

    async def write_parquet(
        self, bucket: str, key: str, data: list[dict], schema: dict | None = None
    ) -> None:
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq

            table = pa.Table.from_pylist(data)
            buf = pa.BufferOutputStream()
            pq.write_table(table, buf)
            self._s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=buf.getvalue().to_pybytes(),
                ContentType="application/x-parquet",
            )
            logger.info("Parquet salvo s3://%s/%s (%d linhas)", bucket, key, len(data))
        except ClientError as e:
            logger.error("Erro ao escrever parquet s3://%s/%s: %s", bucket, key, e)
            raise
