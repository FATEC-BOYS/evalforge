from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.dependencies import RequestContext, get_orchestrator, get_request_context
from core.orchestrator import OrchestratorGraph
from core.schemas import EvalRequest, EvalResponse
from infra.config import settings
from infra.exceptions import EvalException
from infra.logger import configure_logging, get_logger


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
    allow_headers=["Content-Type"],
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


@app.post("/evaluate", response_model=EvalResponse)
async def evaluate(
    request: EvalRequest,
    context: RequestContext = Depends(get_request_context),
    orchestrator: OrchestratorGraph = Depends(get_orchestrator),
) -> EvalResponse:
    logger = get_logger(__name__)
    logger.info(
        "evaluate_request_received",
        request_id=context.request_id,
        task=request.task,
        model=request.model,
    )

    response = await orchestrator.run(request)

    logger.info(
        "evaluate_request_completed",
        request_id=context.request_id,
        verdict=response.result.verdict,
    )

    return response
