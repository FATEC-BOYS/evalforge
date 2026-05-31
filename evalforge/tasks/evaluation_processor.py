import asyncio
import json

from celery import Celery
from redis.exceptions import ConnectionError as RedisConnectionError

from core.orchestrator import OrchestratorGraph
from core.schemas import EvalRequest
from db.repositories.evaluation_repository import EvaluationRepository
from infra.config import settings
from infra.exceptions import OrchestratorException
from infra.logger import get_logger
from infra.redis_client import get_redis_client

celery_app = Celery(
    "evalforge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


@celery_app.task(
    name="tasks.evaluation_processor.EvaluationProcessor",
    bind=True,
    max_retries=3,
)
def EvaluationProcessor(
    self, request_dict: dict, user_public_id: str, task_id: str | None = None
) -> dict:
    logger = get_logger(__name__)
    _task_id = task_id or self.request.id

    async def _run() -> dict:
        redis = get_redis_client()
        lock_key = f"task_result:{_task_id}"
        redis_available = True

        try:
            locked = await redis.set(lock_key, "1", nx=True, ex=86400)
            if not locked:
                return {"status": "already_processed"}
        except (ConnectionError, RedisConnectionError) as e:
            logger.warning(
                "redis_unavailable_idempotency_skipped",
                task_id=_task_id,
                error=str(e),
            )
            redis_available = False

        eval_request = EvalRequest(**request_dict)
        response = await OrchestratorGraph().run(eval_request)

        try:
            entity = await EvaluationRepository().save(eval_request, response)
            result = {"status": "completed", "public_id": entity.public_id}
        except Exception as e:
            logger.error("evaluation_persist_failed", error=str(e), task_id=_task_id)
            result = {"status": "completed"}

        if redis_available:
            try:
                await redis.aclose()
            except Exception:
                pass

        return result

    try:
        return asyncio.run(_run())
    except OrchestratorException as e:
        logger.error("processor_failed", error=str(e), task_id=_task_id)
        return {"status": "failed", "error": str(e)}
