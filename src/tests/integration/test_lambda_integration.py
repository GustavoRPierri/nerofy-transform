"""
Testes de integracao contra a Lambda nerofy-transform.

Validam o pipeline completo: upload no bronze, invocacao da Lambda,
verificacao do parquet gerado na silver e tabela no Glue Catalog.
"""

import concurrent.futures
import json
import time


class TestLambdaInfrastructure:
    """Verifica que a Lambda e recursos de suporte foram criados."""

    def test_lambda_is_active(self, lambda_client, test_lambda_name):
        response = lambda_client.get_function(FunctionName=test_lambda_name)
        state = response["Configuration"]["State"]
        assert state == "Active", f"Lambda deveria estar Active, esta: {state}"

    def test_bronze_bucket_accessible(self, s3_client, test_s3_bronze_bucket):
        response = s3_client.head_bucket(Bucket=test_s3_bronze_bucket)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_silver_bucket_accessible(self, s3_client, test_s3_silver_bucket):
        response = s3_client.head_bucket(Bucket=test_s3_silver_bucket)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_glue_database_exists(self, glue_client, test_glue_database):
        response = glue_client.get_database(Name=test_glue_database)
        assert "Database" in response


class TestEndToEndProcessing:
    """Pipeline completo: upload no bronze -> invocar Lambda -> verificar silver + Glue."""

    def test_items_pipeline(
        self,
        lambda_client,
        s3_client,
        glue_client,
        test_lambda_name,
        test_s3_bronze_bucket,
        test_s3_silver_bucket,
        test_glue_database,
        s3_event_items,
        test_item_json,
        upload_to_bronze,
    ):
        """Upload de JSON de item no bronze, invoca Lambda e verifica parquet na silver."""
        key = s3_event_items["Records"][0]["s3"]["object"]["key"]
        silver_key = "silver/items/year=2026/month=07/day=04/data.parquet"
        upload_to_bronze(key, test_item_json)

        try:
            payload = self._invoke_lambda(lambda_client, test_lambda_name, s3_event_items)
            assert "statusCode" in payload, (
                f"Lambda nao retornou statusCode. Payload: {json.dumps(payload)}"
            )
            assert payload["statusCode"] == 200, (
                f"Lambda retornou {payload['statusCode']}: {payload.get('body')}"
            )

            self._wait_for_object(s3_client, test_s3_silver_bucket, silver_key, timeout=30)

            head = s3_client.head_object(Bucket=test_s3_silver_bucket, Key=silver_key)
            assert head["ContentType"] == "application/x-parquet"

            table = glue_client.get_table(DatabaseName=test_glue_database, Name="items")
            assert "Table" in table
            assert table["Table"]["TableType"] == "EXTERNAL_TABLE"

        finally:
            self._delete_if_exists(s3_client, test_s3_bronze_bucket, key)
            self._delete_if_exists(s3_client, test_s3_silver_bucket, silver_key)

    def test_invalid_event_returns_400(
        self,
        lambda_client,
        test_lambda_name,
        s3_event_invalid,
    ):
        """Evento S3 mal-formado deve retornar statusCode 400."""
        payload = self._invoke_lambda(lambda_client, test_lambda_name, s3_event_invalid)
        assert "statusCode" in payload, (
            f"Lambda nao retornou statusCode. Payload: {json.dumps(payload)}"
        )
        assert payload["statusCode"] == 400, (
            f"Esperado 400, retornou {payload['statusCode']}: {payload.get('body')}"
        )

    def test_concurrent_invocations(
        self,
        lambda_client,
        s3_client,
        test_lambda_name,
        test_s3_bronze_bucket,
        test_s3_silver_bucket,
        test_item_json,
        test_transactions_json,
        test_connector_json,
        s3_event_items,
        s3_event_transactions,
        s3_event_connectors,
        upload_to_bronze,
    ):
        """Multiplas invocacoes concorrentes nao devem causar crash ou corrupcao."""
        pairs = [
            (s3_event_items, test_item_json),
            (s3_event_transactions, test_transactions_json),
            (s3_event_connectors, test_connector_json),
        ]

        keys = []
        for event_dict, data in pairs:
            key = event_dict["Records"][0]["s3"]["object"]["key"]
            upload_to_bronze(key, data)
            keys.append(key)

        silver_keys = [
            "silver/items/year=2026/month=07/day=04/data.parquet",
            "silver/transactions/year=2026/month=07/day=04/data.parquet",
            "silver/connectors/year=2026/month=07/day=04/data.parquet",
        ]

        try:
            def invoke(event_payload):
                return self._invoke_lambda(lambda_client, test_lambda_name, event_payload)

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(invoke, ev)
                    for ev in [s3_event_items, s3_event_transactions, s3_event_connectors]
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            for i, payload in enumerate(results):
                assert "statusCode" in payload, (
                    f"Concorrente {i} nao retornou statusCode. Payload: {json.dumps(payload)}"
                )
                assert payload["statusCode"] == 200, (
                    f"Concorrente {i} retornou {payload['statusCode']}: {payload.get('body')}"
                )

            for sk in silver_keys:
                self._wait_for_object(s3_client, test_s3_silver_bucket, sk, timeout=30)

        finally:
            for key in keys:
                self._delete_if_exists(s3_client, test_s3_bronze_bucket, key)
            for sk in silver_keys:
                self._delete_if_exists(s3_client, test_s3_silver_bucket, sk)

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _invoke_lambda(lambda_client, function_name, event_payload):
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event_payload),
        )
        return json.loads(response["Payload"].read())

    @staticmethod
    def _wait_for_object(s3_client, bucket, key, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                s3_client.head_object(Bucket=bucket, Key=key)
                return
            except s3_client.exceptions.ClientError:
                time.sleep(1)
        raise TimeoutError(f"Objeto s3://{bucket}/{key} nao encontrado apos {timeout}s")

    @staticmethod
    def _delete_if_exists(s3_client, bucket, key):
        try:
            s3_client.delete_object(Bucket=bucket, Key=key)
        except Exception:
            pass
