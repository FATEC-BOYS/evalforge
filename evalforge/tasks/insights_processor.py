import asyncio
import json
from datetime import datetime, timezone

from tasks.evaluation_processor import celery_app
from infra.logger import get_logger
from infra.redis_client import get_redis_client
from ml.clustering import FailureClusterAnalyzer

_MIN_EVALUATIONS = 50


@celery_app.task(name="tasks.insights_processor.InsightsProcessor", bind=False)
def InsightsProcessor() -> dict:
    logger = get_logger(__name__)

    async def _run() -> dict:
        analyzer = FailureClusterAnalyzer()

        failed = await analyzer.get_failed_justifications()
        if len(failed) < _MIN_EVALUATIONS:
            return {"status": "insufficient_data", "count": len(failed)}

        clusters = await analyzer.analyze(failed)
        payload = {
            "clusters": clusters,
            "total_failures_analyzed": len(failed),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        redis = get_redis_client()
        try:
            await redis.set("insights:latest", json.dumps(payload))
        finally:
            await redis.aclose()

        return {"status": "completed", "clusters": len(clusters)}

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("insights_processor_failed", error=str(e))
        return {"status": "failed", "error": str(e)}
