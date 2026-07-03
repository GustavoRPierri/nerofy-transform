from pydantic import BaseModel, ConfigDict

class S3Info(BaseModel):
    bucket: str
    object: str
    model_config = ConfigDict(extra="ignore")

class S3Record(BaseModel):
    eventSource: str
    s3: S3Info
    model_config = ConfigDict(extra="ignore")

class S3Event(BaseModel):
    Records: list[S3Record]
    model_config = ConfigDict(extra="ignore")

    @property
    def events(self) -> list[S3Info]:
        return [record.s3 for record in self.Records]