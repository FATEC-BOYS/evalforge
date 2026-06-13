import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from api.dependencies import (
    AuthenticatedUser,
    RequestContext,
    get_admin_user,
    get_current_user,
    get_evaluation_repository,
    get_orchestrator,
    get_redis,
    get_request_context,
)
from api.rate_limit import check_rate_limit
from auth.router import router as auth_router
from billing.router import router as billing_router
from core.orchestrator import OrchestratorGraph
from core.schemas import EvalRequest, EvalResponse
from db.repositories.audit_log_repository import AuditLogRepository
from db.repositories.evaluation_repository import EvaluationRepository
from infra.config import settings
from infra.exceptions import EvalException, RateLimitException
from infra.logger import configure_logging, get_logger
from tasks.evaluation_processor import EvaluationProcessor


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(app_env=settings.APP_ENV)
    logger = get_logger(__name__)
    logger.info("evalforge_started", env=settings.APP_ENV)
    yield
    logger.info("evalforge_stopped")


app = FastAPI(
    title="evalforge",
    description="A systematic LLM evaluation platform with multi-agent orchestration.",
    version="0.1.0",
    lifespan=lifespan,
)

_origins = ["*"] if settings.APP_ENV == "development" else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router)
app.include_router(billing_router)


@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": exc.message,
            "context": exc.context,
            "retry_after": exc.retry_after,
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(EvalException)
async def eval_exception_handler(request: Request, exc: EvalException) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": exc.message, "context": exc.context},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = get_logger(__name__)
    logger.error("unexpected_error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}


@app.post("/evaluate")
async def evaluate(
    request: EvalRequest,
    context: RequestContext = Depends(get_request_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> dict:
    logger = get_logger(__name__)
    logger.info(
        "evaluate_request_received",
        request_id=context.request_id,
        user=current_user.public_id,
        task=request.task,
        model=request.model,
    )

    await check_rate_limit(current_user.public_id, redis, tier=current_user.tier)

    evaluation_id = str(uuid.uuid4())

    EvaluationProcessor.delay(request.model_dump(), current_user.public_id, evaluation_id)

    logger.info(
        "evaluate_task_dispatched",
        evaluation_id=evaluation_id,
        user=current_user.public_id,
    )

    try:
        await AuditLogRepository().append(
            user_public_id=current_user.public_id,
            request_id=context.request_id,
            action="evaluate",
            result="processing",
            model=request.model,
        )
    except Exception as e:
        logger.error("audit_log_failed", error=str(e))

    return {"evaluation_id": evaluation_id, "status": "processing"}


@app.get("/evaluate/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    entity = await EvaluationRepository().find_by_public_id(evaluation_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {
        "evaluation_id": entity.public_id,
        "status": "completed",
        "verdict": entity.verdict,
        "scores": entity.scores_json,
        "latency_ms": entity.latency_ms,
        "model": entity.model,
        "created_at": entity.created_at.isoformat(),
    }


@app.get("/audit")
async def get_audit_log(
    limit: int = 100,
    _admin: AuthenticatedUser = Depends(get_admin_user),
) -> list[dict]:
    entries = await AuditLogRepository().list_recent(limit=limit)
    return [
        {
            "public_id": e.public_id,
            "user_public_id": e.user_public_id,
            "request_id": e.request_id,
            "action": e.action,
            "result": e.result,
            "model": e.model,
            "security_score": e.security_score,
            "error_message": e.error_message,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]
