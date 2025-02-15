from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
import asyncio
import uvicorn
from src.app.ai.agents.chat_manager import AgentChatManager
from src.app.api.websocket_manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()

@app.post("/query")
async def handle_query(query: str):
    try:
        chat_manager = AgentChatManager(llm_config={"model": "gpt-3.5-turbo", "temperature": 0})
        response = await chat_manager.initiate_chat(query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    await manager.connect(websocket)
    chat_manager = AgentChatManager(llm_config={"model": "gpt-3.5-turbo", "temperature": 0})
    
    chat_task = asyncio.create_task(chat_manager.initiate_chat("Start chat with message from client"))
    
    async def send_loop():
        while True:
            msg = await chat_manager.outgoing_queue.get()
            if msg == "TERMINATE":
                break
            await manager.send_personal_message(msg, websocket)
    
    async def receive_loop():
        try:
            while True:
                data = await websocket.receive_text()
                await chat_manager.incoming_queue.put(data)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            print("WebSocket disconnected")

    await asyncio.gather(send_loop(), receive_loop())
    chat_task.cancel()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
