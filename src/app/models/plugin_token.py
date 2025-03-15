from datetime import UTC, datetime
from typing import Optional
import uuid as uuid_pkg

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from ..models import User


class PluginTokenBase(SQLModel):
    plugin_name: str = Field(...)
    access_token: str = Field(...)
    refresh_token: Optional[str] = Field(default=None)
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    raw_token_data: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON)
    )

class PluginToken(PluginTokenBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid_pkg.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )

    user: "User" = Relationship(back_populates="plugin_tokens")

class PluginTokenCreate(PluginTokenBase):
    pass

class PluginTokenCreateInternal(PluginTokenCreate):
    user_id: str

class PluginTokenRead(PluginTokenBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime]

class PluginTokenUpdate(PluginTokenBase):
    id: str

class PluginTokenUpdateInternal(PluginTokenUpdate):
    user_id: str

class PluginTokenDelete:
    id: str
    user_id: str
