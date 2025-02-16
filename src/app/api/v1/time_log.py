import json
import logging

import aiofiles
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, UserInputRequestedEvent
from autogen_core import CancellationToken
from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect

from src.app.ai.agents.calender import CalendarAgent
from src.app.ai.agents.github import GitHubAgent
from src.app.ai.teams.time_log import TimeLogTeam, get_timelog_team, get_timelog_history, timelog_state_path, \
    timelog_history_path
from src.app.core.config import AccessTokenSettings
import asyncio

router = APIRouter(tags=["timelog"])
logger = logging.getLogger(__name__)

tokens = AccessTokenSettings()
@router.get("/timelog")
async def get_timelog():
    github_agent = GitHubAgent(repository="https://github.com/sammy4gh/time-tracker-full-stack.git", github_token=tokens.GITHUB_ACCESS_TOKEN)
    team_result = await TimeLogTeam(github_agent=github_agent.assistant, calendar_agent=CalendarAgent.assistant).run("John Doe")
    timelog = next((msg.content for msg in team_result.messages if msg.source == 'timelog'), None)
    return {"message": timelog}




# example socket
@router.websocket("/ws")
async def timelog_chat(websocket: WebSocket):
    print("Websocket connected")
    await websocket.accept()

    # User input function used by the team.
    async def _user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
        print("Before user input requested")
        try:
            # Get user message.
            data = await websocket.receive_text()
            if not data:
                raise ValueError("Received empty message")
            message = TextMessage.model_validate(json.loads(data))
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
            # Get user message.
            data = await websocket.receive_json()
            if not data:
                raise ValueError("Received empty message")
            request = TextMessage.model_validate(data)
            print(f"Received message: {request.content}")
            try:
                # Get the team and respond to the message.
                github_agent = GitHubAgent(repository="https://github.com/sammy4gh/time-tracker-full-stack.git",
                                           github_token=tokens.GITHUB_ACCESS_TOKEN)

                team = await get_timelog_team(_user_input, github_agent=github_agent.assistant,calendar_agent=CalendarAgent.assistant)
                history = await get_timelog_history()
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

@router.websocket("/ws/timelog")
async def timelog_chat(websocket: WebSocket):
    print("Websocket connected")
    await websocket.accept()

    # User input function used by the team.
    async def _user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
        data = await websocket.receive_json()
        message = TextMessage.model_validate(data)
        return message.content

    try:
        while True:
            data = await websocket.receive_json()
            # await websocket.send_text(f"Message text was: {data}")
            # request = TextMessage.model_validate(data)

            try:
                # Get the team and respond to the message.
                print("Before get_timelog_team")
                # await websocket.send_text(f"Before get_timelog_team : {request.content}")
                # team = await get_timelog_team(_user_input)
                # history = await get_timelog_history()
                # stream = team.run_stream(task=request)
                # async for message in stream:
                #     if isinstance(message, TaskResult):
                #         continue
                #     await websocket.send_json(message.model_dump())
                #     if not isinstance(message, UserInputRequestedEvent):
                #         # Don't save user input events to history.
                #         history.append(message.model_dump())
                #
                # # Save team state to file.
                # async with aiofiles.open(timelog_state_path, "w") as file:
                #     state = await team.save_state()
                #     await file.write(json.dumps(state))
                #
                # # Save chat history to file.
                # async with aiofiles.open(timelog_history_path, "w") as file:
                #     await file.write(json.dumps(history))
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
        print("Client disconnected")