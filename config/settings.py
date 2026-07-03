import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_region: str = Field(default="sa-east-1", alias="APP_AWS_REGION")
    s3_bronze_bucket: str = Field(default="", alias="S3_BRONZE_BUCKET")
    s3_silver_bucket: str = Field(default="", alias="S3_SILVER_BUCKET")
    glue_database: str = Field(default="nerofy", alias="GLUE_DATABASE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    env: str = Field(default="dev", alias="ENV")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def setup_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(levelname)s | %(name)s | %(message)s",
        )


settings = Settings()
