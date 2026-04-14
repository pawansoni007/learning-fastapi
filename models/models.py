from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Generic, Optional

from pydantic.types import T
from sqlmodel import SQLModel, Field

# Table Schema
class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime(timezone.utc), nullable=True, index=True)
 

# Request body schema
class CampaignCreate(SQLModel):
    name: str
    due_date: datetime
    created_at: datetime


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    due_date: Optional[datetime] = None


