from db.entities.audit_log import AuditLogEntity
from db.session import get_writer_session


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
        return entity
