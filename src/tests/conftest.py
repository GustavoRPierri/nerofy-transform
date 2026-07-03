import pytest


@pytest.fixture
def item_bronze_data():
    return {
        "event": {"id": "evt-001", "type": "item/updated"},
        "item": {
            "id": "item-abc",
            "status": "UPDATED",
            "connector": {"id": 201, "name": "Itau", "primaryColor": "#EC7000"},
        },
        "accounts": [
            {"id": "acc-001", "type": "BANK", "name": "Conta Corrente", "balance": 1500.0},
        ],
    }


@pytest.fixture
def transactions_bronze_data():
    return {
        "event_id": "evt-002",
        "account_id": "acc-001",
        "transactions": [
            {"id": "txn-001", "description": "Pix recebido", "amount": 500.0, "date": "2026-05-20", "category": "income"},
        ],
    }


@pytest.fixture
def connector_bronze_data():
    return {
        "event": {"id": "evt-003", "type": "connector/updated"},
        "connector": {"id": 201, "name": "Itau", "primaryColor": "#EC7000"},
    }


@pytest.fixture
def s3_event_record():
    return {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {
                    "bucket": {"name": "nerofy-bronze-dev"},
                    "object": {
                        "key": "bronze/items/item-abc/year=2026/month=07/day=03/item_evt-001.json"
                    },
                },
            }
        ]
    }
