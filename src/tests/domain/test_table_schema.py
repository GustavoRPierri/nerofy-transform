import pytest
from src.domain.entities.table_schema import GlueColumn, TABLE_COLUMNS


class TestGlueColumn:
    def test_to_glue_dict_produces_correct_shape(self):
        col = GlueColumn(Name="event_id", Type="string")
        assert col.to_glue_dict() == {"Name": "event_id", "Type": "string"}

    def test_construct_with_aliases(self):
        col = GlueColumn(Name="event_id", Type="string")
        assert col.name == "event_id"
        assert col.type == "string"

    def test_all_entities_have_columns(self):
        for entity in ("items", "transactions", "connectors"):
            assert entity in TABLE_COLUMNS
            assert len(TABLE_COLUMNS[entity]) > 0

    def test_all_columns_have_required_fields(self):
        for columns in TABLE_COLUMNS.values():
            for col in columns:
                assert col.name
                assert col.type
