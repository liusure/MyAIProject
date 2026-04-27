import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation


class ConversationService:
    """对话业务逻辑"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, device_id: str) -> Conversation:
        conv = Conversation(id=uuid.uuid4(), device_id=device_id, messages=[], context=None)
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        result = await self.db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
        structured_data: dict | None = None,
    ) -> Conversation:
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if structured_data:
            message["structured_data"] = structured_data

        messages = list(conversation.messages) if conversation.messages else []
        messages.append(message)
        conversation.messages = messages
        conversation.updated_at = datetime.utcnow()
        await self.db.flush()
        return conversation

    async def get_context_messages(self, conversation: Conversation, max_turns: int = 10) -> list[dict]:
        messages = conversation.messages or []
        recent = messages[-max_turns * 2:] if len(messages) > max_turns * 2 else messages
        return [{"role": m["role"], "content": m["content"]} for m in recent]
