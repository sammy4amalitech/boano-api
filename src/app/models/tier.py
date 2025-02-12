from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field


class TierBase(SQLModel):
    name: str = Field(..., schema_extra={"example": "free"})


class Tier(TierBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: Optional[datetime] = None


class TierRead(TierBase):
    id: int
    created_at: datetime


class TierCreate(TierBase):
    pass


class TierCreateInternal(TierCreate):
    pass


class TierUpdate(SQLModel):
    name: Optional[str] = None


class TierUpdateInternal(TierUpdate):
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class TierDelete(SQLModel):
    pass
