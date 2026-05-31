from sqlalchemy import select

from core.schemas import EvalRequest, EvalResponse
from db.entities.evaluation import EvaluationEntity
from db.session import get_reader_session, get_writer_session


class EvaluationRepository:
    async def save(self, request: EvalRequest, response: EvalResponse) -> EvaluationEntity:
        result = response.result
        entity = EvaluationEntity(
            task=request.task,
            input=request.input,
            model=result.model,
            response="",
            accuracy_score=result.accuracy.score,
            accuracy_justification=result.accuracy.justification,
            reasoning_score=result.reasoning.score,
            reasoning_justification=result.reasoning.justification,
            safety_score=result.safety.score,
            safety_justification=result.safety.justification,
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

    async def list_by_model(self, model: str, limit: int = 50) -> list[EvaluationEntity]:
        async with get_reader_session() as session:
            result = await session.execute(
                select(EvaluationEntity)
                .where(EvaluationEntity.model == model)
                .order_by(EvaluationEntity.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
