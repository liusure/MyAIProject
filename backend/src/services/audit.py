import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog


class AuditService:
    """操作日志记录服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        details: dict,
        device_id: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=uuid.uuid4(),
            device_id=device_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
