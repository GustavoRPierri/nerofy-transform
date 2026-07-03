from pydantic import BaseModel, ConfigDict, Field


class GlueColumn(BaseModel):
    """Definição de uma coluna para o AWS Glue Data Catalog."""
    name: str = Field(alias="Name")
    type: str = Field(alias="Type")
    model_config = ConfigDict(extra="ignore")

    def to_glue_dict(self) -> dict[str, str]:
        """Serializa para o formato esperado pelo Glue SDK (boto3)."""
        return self.model_dump(by_alias=True)


TABLE_COLUMNS: dict[str, list[GlueColumn]] = {
    "items": [
        GlueColumn(Name="event_id", Type="string"),
        GlueColumn(Name="item_id", Type="string"),
        GlueColumn(Name="status", Type="string"),
        GlueColumn(Name="connector_id", Type="int"),
        GlueColumn(Name="connector_Name", Type="string"),
        GlueColumn(
            Name="accounts",
            Type="array<struct<id:string,Type:string,Name:string,balance:double>>",
        ),
        GlueColumn(Name="processed_at", Type="string"),
    ],
    "transactions": [
        GlueColumn(Name="event_id", Type="string"),
        GlueColumn(Name="account_id", Type="string"),
        GlueColumn(Name="transaction_id", Type="string"),
        GlueColumn(Name="description", Type="string"),
        GlueColumn(Name="amount", Type="double"),
        GlueColumn(Name="date", Type="string"),
        GlueColumn(Name="category", Type="string"),
        GlueColumn(Name="processed_at", Type="string"),
    ],
    "connectors": [
        GlueColumn(Name="event_id", Type="string"),
        GlueColumn(Name="connector_id", Type="int"),
        GlueColumn(Name="Name", Type="string"),
        GlueColumn(Name="primary_color", Type="string"),
        GlueColumn(Name="processed_at", Type="string"),
    ],
}
