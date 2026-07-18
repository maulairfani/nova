from datetime import datetime

from pydantic import BaseModel


class ConversationOut(BaseModel):
    id: str
    title: str
    updated_at: datetime


class ConversationRenameRequest(BaseModel):
    title: str


class StepOut(BaseModel):
    type: str
    label: str


class ChartOut(BaseModel):
    chart_id: str
    title: str
    chart_type: str


class MessageOut(BaseModel):
    role: str
    content: str
    steps: list[StepOut] = []
    charts: list[ChartOut] = []
