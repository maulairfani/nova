from pydantic import BaseModel


class UsageOut(BaseModel):
    used: int
    limit: int
    remaining: int
    reset_seconds: int
