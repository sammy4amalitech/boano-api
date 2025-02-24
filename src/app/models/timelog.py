from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, DateTime, String, Text
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
import uuid as uuid_pkg

from src.app.models import User


class TimeLogBase(SQLModel):
    task: str = Field(..., min_length=2, max_length=255, schema_extra={"example": "Project Planning"})
    description: Optional[str] = Field(default=None, schema_extra={"example": "Planning session for Q4 roadmap"})
    start_time: datetime
    end_time: datetime
    source: str = Field(..., max_length=50, schema_extra={"example": "manual"})


class TimeLog(TimeLogBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: str = Field(foreign_key="user.id")
    creator: Optional["User"] = Relationship(back_populates="timelogs")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )




class TimeLogRead(TimeLogBase):
    id: int
    creator_id: str
    created_at: datetime


class TimeLogCreate(TimeLogBase):
    pass


class TimeLogCreateInternal(TimeLogCreate):
    creator_id: str


class TimeLogUpdate(SQLModel):
    task: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    source: Optional[str] = Field(default=None, max_length=50)


class TimeLogUpdateInternal(TimeLogUpdate):
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class TimeLogDelete(SQLModel):
    pass

class TimeLogBatchUpsert(SQLModel):
    timelogs: list[TimeLogCreate] = Field(..., min_items=1)
    update_existing: bool = Field(default=True, description="Whether to update existing timelogs or skip them")

class TimeLogBatchUpsertResponse(SQLModel):
    timelogs: list[TimeLogRead]
    failed_entries: list[dict] = Field(default_factory=list)

class TimeLogBatchUpdate(SQLModel):
    values: TimeLogUpdate
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tags: Optional[list[str]] = None

class TimeLogBatchDelete(SQLModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tags: Optional[list[str]] = None

class TimeLogBatchCreate(SQLModel):
    timelogs: List[TimeLogCreate]

class TimeLogBatchRead(SQLModel):
    timelogs: List[TimeLogRead]
    failed_entries: List[dict] = []

