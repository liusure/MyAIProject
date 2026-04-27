import uuid

from pydantic import BaseModel

from src.schemas.plan import ChatResponse


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    id: uuid.UUID
    messages: list[dict]
    context: dict | None = None

    class Config:
        from_attributes = True
