from pydantic import BaseModel
from typing import Optional, Literal

class ChatRequest(BaseModel):
    message: str
    chat_type: Literal["basic", "code", "math"] = "basic"

class ChatResponse(BaseModel):
    type: str
    response: str
    error: Optional[str] = None

class StreamingChatRequest(BaseModel):
    message: str
    session_id: str
    chat_type: Literal["basic", "code", "math"] = "basic"
