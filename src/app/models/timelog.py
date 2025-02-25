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

    def __init__(self, **data):
        super().__init__(**data)
        # Convert timezone-aware datetimes to naive UTC
        if self.start_time and self.start_time.tzinfo:
            self.start_time = self.start_time.astimezone(timezone.utc).replace(tzinfo=None)
        if self.end_time and self.end_time.tzinfo:
            self.end_time = self.end_time.astimezone(timezone.utc).replace(tzinfo=None)


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
    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            # Ensure start_time and end_time are timezone-aware
            if 'start_time' in obj and isinstance(obj['start_time'], datetime):
                if obj['start_time'].tzinfo is None:
                    obj['start_time'] = obj['start_time'].replace(tzinfo=timezone.utc)
            if 'end_time' in obj and isinstance(obj['end_time'], datetime):
                if obj['end_time'].tzinfo is None:
                    obj['end_time'] = obj['end_time'].replace(tzinfo=timezone.utc)
        return super().model_validate(obj)


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
    timelogs: list[TimeLogCreateInternal] = Field(..., min_items=1)
    update_existing: bool = Field(default=True, description="Whether to update existing timelogs or skip them")
    creator_id: str = Field(..., description="ID of the user creating the timelogs")


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
    failed_entries: List[dict] = Field(default_factory=list)

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            # Extract timelogs from either 'data' key or root level
            timelogs = obj.get('data', obj.get('timelogs', []))
            failed_entries = obj.get('failed_entries', [])
            obj = {'timelogs': timelogs, 'failed_entries': failed_entries}
        return super().model_validate(obj)

