from datetime import datetime, timezone
from typing import Optional, List
import uuid as uuid_pkg

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship
from pydantic import validator


class UserBase(SQLModel):
    name: str = Field(..., min_length=2, max_length=30, schema_extra={"example": "User Userson"})
    username: str = Field(..., min_length=2, max_length=20, regex="^[a-z0-9]+$", schema_extra={"example": "userson"})
    email: str = Field(..., schema_extra={"example": "user.userson@example.com"})
    uuid: str = Field(unique=True, default_factory=lambda: str(uuid_pkg.uuid4()))


class User(UserBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid_pkg.uuid4()), primary_key=True)
    profile_image_url: str = Field("https://www.profileimageurl.com")
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    email: str = Field(..., unique=True)
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    is_deleted: bool = Field(default=False)
    timelogs: List["TimeLog"] = Relationship(back_populates="creator")


class UserRead(SQLModel):
    id: str
    uuid: str
    name: str
    username: str
    email: str
    profile_image_url: str


class UserCreate(UserBase):
    pass


class UserCreateInternal(UserBase):
    pass


class UserUpdate(SQLModel):
    name: Optional[str] = Field(None, min_length=2, max_length=30)
    username: Optional[str] = Field(None, min_length=2, max_length=20, regex="^[a-z0-9]+$")
    email: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserUpdateInternal(UserUpdate):
    pass


class UserTierUpdate(SQLModel):
    pass


class UserDelete(SQLModel):
    is_deleted: bool
    deleted_at: datetime


class UserRestoreDeleted(SQLModel):
    is_deleted: bool
