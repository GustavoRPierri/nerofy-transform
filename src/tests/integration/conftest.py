"""Fixtures para testes de integracao contra Lambda na AWS."""

import json
import os

import boto3
import pytest


# ── AWS Clients (session-scoped) ────────────────────────────────────────────

@pytest.fixture(scope="session")
def aws_region() -> str:
    return os.environ.get("AWS_DEFAULT_REGION", "sa-east-1")


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="session")
def s3_client(aws_region):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def glue_client(aws_region):
    return boto3.client("glue", region_name=aws_region)


# ── Env Var Fixtures ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_lambda_name() -> str:
    name = os.environ.get("TEST_LAMBDA_NAME")
    if not name:
        pytest.skip("TEST_LAMBDA_NAME nao configurado.")
    return name


@pytest.fixture(scope="session")
def test_s3_bronze_bucket() -> str:
    bucket = os.environ.get("TEST_S3_BRONZE_BUCKET")
    if not bucket:
        pytest.skip("TEST_S3_BRONZE_BUCKET nao configurado.")
    return bucket


@pytest.fixture(scope="session")
def test_s3_silver_bucket() -> str:
    bucket = os.environ.get("TEST_S3_SILVER_BUCKET")
    if not bucket:
        pytest.skip("TEST_S3_SILVER_BUCKET nao configurado.")
    return bucket


@pytest.fixture(scope="session")
def test_glue_database() -> str:
    database = os.environ.get("TEST_GLUE_DATABASE")
    if not database:
        pytest.skip("TEST_GLUE_DATABASE nao configurado.")
    return database


# ── S3 Event Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def s3_event_items(test_s3_bronze_bucket):
    return {
        "Records": [{
            "eventSource": "aws:s3",
            "s3": {
                "bucket": {"name": test_s3_bronze_bucket},
                "object": {
                    "key": "bronze/items/item-test-001/year=2026/month=07/day=04/item_evt-integ-001.json"
                },
            },
        }]
    }


@pytest.fixture
def s3_event_transactions(test_s3_bronze_bucket):
    return {
        "Records": [{
            "eventSource": "aws:s3",
            "s3": {
                "bucket": {"name": test_s3_bronze_bucket},
                "object": {
                    "key": "bronze/transactions/item_test/account_test/year=2026/month=07/day=04/evt-integ-002.json"
                },
            },
        }]
    }


@pytest.fixture
def s3_event_connectors(test_s3_bronze_bucket):
    return {
        "Records": [{
            "eventSource": "aws:s3",
            "s3": {
                "bucket": {"name": test_s3_bronze_bucket},
                "object": {
                    "key": "bronze/connectors/201/year=2026/month=07/day=04/evt-integ-003.json"
                },
            },
        }]
    }


@pytest.fixture
def s3_event_invalid():
    return {"foo": "bar"}


# ── Test Data Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def test_item_json():
    return {
        "event": {"id": "evt-integ-001", "type": "item/updated"},
        "item": {
            "id": "item-test-001",
            "status": "UPDATED",
            "connector": {"id": 201, "name": "Itau", "primaryColor": "#EC7000"},
        },
        "accounts": [
            {"id": "acc-001", "type": "BANK", "name": "Conta Corrente", "balance": 1500.0},
        ],
    }


@pytest.fixture
def test_transactions_json():
    return {
        "event_id": "evt-integ-002",
        "account_id": "acc-001",
        "transactions": [
            {"id": "txn-001", "description": "Pix recebido", "amount": 500.0, "date": "2026-05-20", "category": "income"},
        ],
    }


@pytest.fixture
def test_connector_json():
    return {
        "event": {"id": "evt-integ-003", "type": "connector/updated"},
        "connector": {"id": 201, "name": "Itau", "primaryColor": "#EC7000"},
    }


# ── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
def upload_to_bronze(s3_client, test_s3_bronze_bucket):
    def _upload(key: str, data: dict) -> str:
        s3_client.put_object(
            Bucket=test_s3_bronze_bucket,
            Key=key,
            Body=json.dumps(data),
            ContentType="application/json",
        )
        return key
    return _upload
