from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_superuser, get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...core.utils.cache import cache
from ...crud.crud_timelog import crud_timelogs
from ...crud.crud_users import crud_users
from ...models.timelog import TimeLogRead, TimeLogCreate, TimeLogCreateInternal
from ...models.user import UserRead

router = APIRouter(tags=["time_logs"])

@router.post("/user/{user_id}/time_log", response_model=TimeLogRead, status_code=201)
async def write_time_log(
    request: Request,
    user_id: int,
    time_log: TimeLogCreate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TimeLogRead:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    time_log_internal_dict = time_log.model_dump()
    time_log_internal_dict["created_by_user_id"] = db_user["id"]

    time_log_internal = TimeLogCreateInternal(**time_log_internal_dict)
    created_time_log: TimeLogRead = await crud_timelogs.create(db=db, object=time_log_internal)
    return created_time_log

@router.get("/user/{user_id}/time_logs", response_model=PaginatedListResponse[TimeLogRead])
@cache(
    key_prefix="user_{user_id}_time_logs:page_{page}:items_per_page:{items_per_page}",
    resource_id_name="user_id",
    expiration=60,
)
async def read_time_logs(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if not db_user:
        raise NotFoundException("User not found")

    time_logs_data = await crud_timelogs.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        schema_to_select=TimeLogRead,
        created_by_user_id=db_user["id"],
        is_deleted=False,
    )

    response: dict[str, Any] = paginated_response(crud_data=time_logs_data, page=page, items_per_page=items_per_page)
    return response

@router.get("/user/{user_id}/time_log/{id}", response_model=TimeLogRead)
@cache(key_prefix="user_{user_id}_time_log_cache", resource_id_name="id")
async def read_time_log(
    request: Request, user_id: int, id: int, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    db_time_log: TimeLogRead | None = await crud_timelogs.get(
        db=db, schema_to_select=TimeLogRead, id=id, created_by_user_id=db_user["id"], is_deleted=False
    )
    if db_time_log is None:
        raise NotFoundException("Time Log not found")

    return db_time_log

@router.patch("/user/{user_id}/time_log/{id}")
@cache("user_{user_id}_time_log_cache", resource_id_name="id", pattern_to_invalidate_extra=["user_{user_id}_time_logs:*"])
async def patch_time_log(
    request: Request,
    user_id: int,
    id: int,
    values: TimeLogUpdate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    db_time_log = await crud_timelogs.get(db=db, schema_to_select=TimeLogRead, id=id, is_deleted=False)
    if db_time_log is None:
        raise NotFoundException("Time Log not found")

    await crud_timelogs.update(db=db, object=values, id=id)
    return {"message": "Time Log updated"}

@router.delete("/user/{user_id}/time_log/{id}")
@cache("user_{user_id}_time_log_cache", resource_id_name="id", to_invalidate_extra={"user_{user_id}_time_logs": "user_{user_id}"})
async def erase_time_log(
    request: Request,
    user_id: int,
    id: int,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    db_time_log = await crud_timelogs.get(db=db, schema_to_select=TimeLogRead, id=id, is_deleted=False)
    if db_time_log is None:
        raise NotFoundException("Time Log not found")

    await crud_timelogs.delete(db=db, id=id)
    return {"message": "Time Log deleted"}

@router.delete("/user/{user_id}/db_time_log/{id}", dependencies=[Depends(get_current_superuser)])
@cache("user_{user_id}_time_log_cache", resource_id_name="id", to_invalidate_extra={"user_{user_id}_time_logs": "user_{user_id}"})
async def erase_db_time_log(
    request: Request, user_id: int, id: int, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    db_time_log = await crud_timelogs.get(db=db, schema_to_select=TimeLogRead, id=id, is_deleted=False)
    if db_time_log is None:
        raise NotFoundException("Time Log not found")

    await crud_timelogs.db_delete(db=db, id=id)
    return {"message": "Time Log deleted from the database"}