import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    business_unit_code: str
    title: str
    format: str
    status: str
    chunk_count: int | None
    error_message: str | None
    created_at: datetime
    ingested_at: datetime | None
