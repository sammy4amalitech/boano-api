from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict
import asyncio
import json

from app.agents.chat_manager import AgentChatManager
from app.api.websocket_manager import ConnectionManager
from app.models.chat import ChatRequest, ChatResponse, StreamingChatRequest

router = APIRouter()
manager = ConnectionManager()

# REST Endpoints for one-shot interactions
@router.post("/query/simple", response_model=ChatResponse)
async def handle_simple_query(request: ChatRequest):
    """
    Simple query-response endpoint for basic questions
    """
    try:
        chat_manager = AgentChatManager()
        response = await chat_manager.initiate_basic_chat(request.message)
        return ChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/specialized", response_model=ChatResponse)
async def handle_specialized_query(request: ChatRequest):
    """
    Specialized endpoint for code and math queries
    """
    try:
        chat_manager = AgentChatManager()
        if request.chat_type == "code":
            response = await chat_manager.initiate_code_chat(request.message)
        elif request.chat_type == "math":
            response = await chat_manager.initiate_math_chat(request.message)
        else:
            response = await chat_manager.initiate_basic_chat(request.message)
        return ChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoints for interactive sessions
@router.websocket("/ws/interactive/{chat_id}")
async def interactive_chat_websocket(websocket: WebSocket, chat_id: str):
    """
    Interactive WebSocket endpoint for real-time chat with basic assistant
    """
    await manager.connect(websocket)
    chat_manager = AgentChatManager()
    
    try:
        while True:
            data = await websocket.receive_json()
            request = StreamingChatRequest(**data)
            
            # Create task for processing the message
            chat_task = asyncio.create_task(
                chat_manager.initiate_basic_chat(request.message)
            )
            
            # Send real-time updates
            async def send_updates():
                while True:
                    try:
                        msg = await chat_manager.outgoing_queue.get()
                        await websocket.send_json({"type": "update", "content": msg})
                    except asyncio.CancelledError:
                        break
            
            update_task = asyncio.create_task(send_updates())
            
            # Wait for chat completion
            result = await chat_task
            update_task.cancel()
            
            # Send final response
            await websocket.send_json({"type": "final", "content": result})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})
        manager.disconnect(websocket)

@router.websocket("/ws/specialized/{chat_id}")
async def specialized_chat_websocket(websocket: WebSocket, chat_id: str):
    """
    Specialized WebSocket endpoint for code and math interactions
    """
    await manager.connect(websocket)
    chat_manager = AgentChatManager()
    
    try:
        while True:
            data = await websocket.receive_json()
            request = StreamingChatRequest(**data)
            
            # Select appropriate chat type
            if request.chat_type == "code":
                chat_method = chat_manager.initiate_code_chat
            elif request.chat_type == "math":
                chat_method = chat_manager.initiate_math_chat
            else:
                chat_method = chat_manager.initiate_basic_chat
            
            # Create task for processing the message
            chat_task = asyncio.create_task(
                chat_method(request.message)
            )
            
            # Send real-time updates
            async def send_updates():
                while True:
                    try:
                        msg = await chat_manager.outgoing_queue.get()
                        await websocket.send_json({"type": "update", "content": msg})
                    except asyncio.CancelledError:
                        break
            
            update_task = asyncio.create_task(send_updates())
            
            # Wait for chat completion
            result = await chat_task
            update_task.cancel()
            
            # Send final response
            await websocket.send_json({"type": "final", "content": result})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})
        manager.disconnect(websocket)
