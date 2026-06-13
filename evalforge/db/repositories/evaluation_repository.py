from sqlalchemy import select

from core.schemas import EvalRequest, EvalResponse
from db.entities.evaluation import EvaluationEntity
from db.session import get_reader_session, get_writer_session


class EvaluationRepository:
    async def save(
        self, request: EvalRequest, response: EvalResponse, user_public_id: str | None = None
    ) -> EvaluationEntity:
        result = response.result
        entity = EvaluationEntity(
            user_public_id=user_public_id,
            task=request.task,
            input=request.input,
            model=result.model,
            response=response.output or "",
            scores_json={
                name: {"score": ds.score, "justification": ds.justification}
                for name, ds in result.scores.items()
            },
            latency_ms=result.latency_ms,
            verdict=result.verdict,
        )
        async with get_writer_session() as session:
            session.add(entity)
            await session.flush()
        return entity

    async def find_by_public_id(self, public_id: str) -> EvaluationEntity | None:
        async with get_reader_session() as session:
            result = await session.execute(
                select(EvaluationEntity).where(EvaluationEntity.public_id == public_id)
            )
            return result.scalar_one_or_none()

    async def list_by_user(self, user_public_id: str, limit: int = 50) -> list[EvaluationEntity]:
        async with get_reader_session() as session:
            result = await session.execute(
                select(EvaluationEntity)
                .where(EvaluationEntity.user_public_id == user_public_id)
                .order_by(EvaluationEntity.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def delete_by_user(self, user_public_id: str) -> int:
        from sqlalchemy import delete
        async with get_writer_session() as session:
            result = await session.execute(
                delete(EvaluationEntity).where(EvaluationEntity.user_public_id == user_public_id)
            )
            return result.rowcount

    async def list_by_model(self, model: str, limit: int = 50) -> list[EvaluationEntity]:
        async with get_reader_session() as session:
            result = await session.execute(
                select(EvaluationEntity)
                .where(EvaluationEntity.model == model)
                .order_by(EvaluationEntity.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
