import asyncio
import json
from typing import Annotated, Any

import aiofiles
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, UserInputRequestedEvent
from autogen_core import CancellationToken
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from ...ai.agents.calender import CalendarAgent
from ...ai.agents.github import GitHubAgent
from ...ai.teams.time_log import get_timelog_team, get_timelog_history, timelog_state_path, timelog_history_path, \
    TimeLogTeam
from ...api.dependencies import get_current_superuser, get_current_user, logger
from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...core.utils.cache import cache
from ...crud.crud_timelog import crud_timelogs
from ...crud.crud_users import crud_users
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ...models.timelog import TimeLogRead, TimeLogCreate, TimeLogCreateInternal, TimeLogUpdate, TimeLogBatchRead, \
    TimeLogBatchUpsertResponse, TimeLogBatchUpsert, TimeLogBatchUpdate, TimeLogBatchDelete, TimeLogBatchCreate
from ...models.user import UserRead



router = APIRouter(tags=["time_logs"])

@router.post("/user/{user_id}/time_log", response_model=TimeLogRead, status_code=201)
async def write_time_log(
    request: Request,
    user_id: str,
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

@router.post("/user/{user_id}/time_logs/batch", response_model=TimeLogBatchRead, status_code=201)
async def write_time_logs_batch(
    request: Request,
    user_id: str,
    time_logs_batch: TimeLogBatchCreate,
    # current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TimeLogBatchRead:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    # if current_user["id"] != db_user["id"]:
    #     raise ForbiddenException()

    try:
        # Prepare all time logs with user ID
        time_log_internals = [
            TimeLogCreateInternal(**{**time_log.model_dump(), "creator_id": db_user["id"]})
            for time_log in time_logs_batch.timelogs
        ]
        
        # Use upsert_multi for efficient batch operation
        result = await crud_timelogs.upsert_multi(
            db=db,
            instances=time_log_internals,
            schema_to_select=TimeLogRead,
            return_as_model=True
        )
        
        await db.commit()  # Ensure the changes are committed to the database
        
        # Extract timelogs from the result and format response
        created_time_logs = result.get('data', []) if isinstance(result, dict) else result
        return TimeLogBatchRead(timelogs=created_time_logs, failed_entries=[])
        
    except Exception as e:
        # If batch operation fails, return all as failed entries
        failed_entries = [
            {"time_log": time_log.model_dump(), "error": str(e)}
            for time_log in time_logs_batch.timelogs
        ]
        return TimeLogBatchRead(timelogs=[], failed_entries=failed_entries)

@router.post("/user/{user_id}/time_logs/upsert", response_model=TimeLogBatchUpsertResponse, status_code=201)
@cache("user_{user_id}_time_log_cache", pattern_to_invalidate_extra=["user_{user_id}_time_logs:*"])
async def upsert_time_logs_batch(
    request: Request,
    user_id: str,
    time_logs_batch: TimeLogBatchUpsert,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TimeLogBatchUpsertResponse:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    try:
        # Prepare all time logs with user ID
        time_log_internals = [
            TimeLogCreateInternal(**{**time_log.model_dump(), "created_by_user_id": db_user["id"]})
            for time_log in time_logs_batch.timelogs
        ]
        
        # Use upsert_multi for efficient batch operation
        created_time_logs = await crud_timelogs.upsert_multi(
            db=db,
            instances=time_log_internals,
            schema_to_select=TimeLogRead,
            return_as_model=True,
            update_existing=time_logs_batch.update_existing
        )
        
        return TimeLogBatchUpsertResponse(timelogs=created_time_logs, failed_entries=[])
        
    except Exception as e:
        # If batch operation fails, return all as failed entries
        failed_entries = [
            {"time_log": time_log.model_dump(), "error": str(e)}
            for time_log in time_logs_batch.timelogs
        ]
        return TimeLogBatchUpsertResponse(timelogs=[], failed_entries=failed_entries)

@router.patch("/user/{user_id}/time_logs/batch")
@cache("user_{user_id}_time_log_cache", pattern_to_invalidate_extra=["user_{user_id}_time_logs:*"])
async def update_time_logs_batch(
    request: Request,
    user_id: str,
    batch_update: TimeLogBatchUpdate,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    filters = {"created_by_user_id": db_user["id"], "is_deleted": False}
    
    if batch_update.start_date:
        filters["created_at__gte"] = batch_update.start_date
    if batch_update.end_date:
        filters["created_at__lte"] = batch_update.end_date
    if batch_update.tags:
        filters["tags__contains"] = batch_update.tags

    await crud_timelogs.update(
        db=db,
        object=batch_update.values,
        allow_multiple=True,
        **filters
    )

    return {"message": "Time Logs batch updated"}

@router.delete("/user/{user_id}/time_logs/batch")
@cache("user_{user_id}_time_log_cache", pattern_to_invalidate_extra=["user_{user_id}_time_logs:*"])
async def erase_time_logs_batch(
    request: Request,
    user_id: str,
    batch_delete: TimeLogBatchDelete,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    filters = {"created_by_user_id": db_user["id"], "is_deleted": False}
    
    if batch_delete.start_date:
        filters["created_at__gte"] = batch_delete.start_date
    if batch_delete.end_date:
        filters["created_at__lte"] = batch_delete.end_date
    if batch_delete.tags:
        filters["tags__contains"] = batch_delete.tags

    await crud_timelogs.delete(
        db=db,
        allow_multiple=True,
        **filters
    )

    return {"message": "Time Logs batch deleted"}

@router.get("/user/{user_id}/time_logs", response_model=PaginatedListResponse[TimeLogRead])
@cache(
    key_prefix="user_{user_id}_time_logs:page_{page}:items_per_page:{items_per_page}",
    resource_id_name="user_id",
    expiration=60,
)
async def read_time_logs(
    request: Request,
    user_id: str,
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
    request: Request, user_id: str, id: int, db: Annotated[AsyncSession, Depends(async_get_db)]
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
    user_id: str,
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
    user_id: str,
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
    request: Request, user_id: str, id: int, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=user_id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    db_time_log = await crud_timelogs.get(db=db, schema_to_select=TimeLogRead, id=id, is_deleted=False)
    if db_time_log is None:
        raise NotFoundException("Time Log not found")

    await crud_timelogs.db_delete(db=db, id=id)
    return {"message": "Time Log deleted from the database"}

@router.get("/timelog")
async def get_timelog():
    github_agent = GitHubAgent(github_token=settings.GITHUB_ACCESS_TOKEN)
    team_result = await TimeLogTeam(github_agent=github_agent.assistant, calendar_agent=CalendarAgent.assistant).run("John Doe")
    timelog = next((msg.content for msg in team_result.messages if msg.source == 'timelog'), None)
    return {"message": timelog}

# example socket
@router.websocket("/ws")
async def timelog_chat(websocket: WebSocket):
    print("Websocket connected")
    await websocket.accept()
    receive_lock = asyncio.Lock()

    # User input function used by the team.
    async def _user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
        print("Before user input requested")
        async with receive_lock:
            try:
                # Get user message.
                data = await websocket.receive_json()
                if not data:
                    raise ValueError("Received empty message")
                message = TextMessage.model_validate(data)
                print("User input requested")
                return message.content
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                raise ValueError("Invalid JSON received")
            except Exception as e:
                print(f"Error receiving user input: {e}")
                raise

    try:
        print("Before get_timelog_team")
        while True:
            async with receive_lock:
                # Get user message.
                data = await websocket.receive_json()
                if not data:
                    raise ValueError("Received empty message")
                request = TextMessage.model_validate(data)
                print(f"Received message: {request.content}")
            try:
                # Get the team and respond to the message.
                github_agent = GitHubAgent(github_token=settings.GITHUB_ACCESS_TOKEN)
                team = await get_timelog_team(_user_input, github_agent=github_agent.assistant, calendar_agent=CalendarAgent.assistant)
                history = await get_timelog_history()
                if not isinstance(history, list):
                    history = []
                stream = team.run_stream(task=request)
                async for message in stream:
                    if isinstance(message, TaskResult):
                        continue
                    await websocket.send_json(message.model_dump())
                    if not isinstance(message, UserInputRequestedEvent):
                        # Don't save user input events to history.
                        history.append(message.model_dump())

                # Save team state to file.
                async with aiofiles.open(timelog_state_path, "w") as file:
                    state = await team.save_state()
                    await file.write(json.dumps(state))

                # Save chat history to file.
                async with aiofiles.open(timelog_history_path, "w") as file:
                    await file.write(json.dumps(history))

            except Exception as e:
                # Send error message to client
                error_message = {
                    "type": "error",
                    "content": f"Error: {str(e)}",
                    "source": "system"
                }
                await websocket.send_json(error_message)
                # Re-enable input after error
                await websocket.send_json({
                    "type": "UserInputRequestedEvent",
                    "content": "An error occurred. Please try again.",
                    "source": "system"
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except asyncio.CancelledError:
        logger.error("Task was cancelled")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Unexpected error: {str(e)}",
                "source": "system"
            })
        except:
            pass