from sqlalchemy import select

from db.entities.audit_log import AuditLogEntity
from db.session import get_reader_session, get_writer_session


class AuditLogRepository:
    async def append(
        self,
        user_public_id: str,
        request_id: str,
        action: str,
        result: str,
        model: str | None = None,
        security_score: float | None = None,
        error_message: str | None = None,
    ) -> AuditLogEntity:
        entity = AuditLogEntity(
            user_public_id=user_public_id,
            request_id=request_id,
            action=action,
            result=result,
            model=model,
            security_score=security_score,
            error_message=error_message,
        )
        async with get_writer_session() as session:
            session.add(entity)
            await session.flush()
        return entity

    async def list_recent(self, limit: int = 100) -> list[AuditLogEntity]:
        async with get_reader_session() as session:
            result = await session.execute(
                select(AuditLogEntity)
                .order_by(AuditLogEntity.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
