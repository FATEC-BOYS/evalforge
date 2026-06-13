from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.evaluator import EvaluatorAgent
from agents.executor import ExecutorAgent
from agents.security_evaluator import SecurityEvaluatorAgent
from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult, ExecutorOutput
from db.repositories.evaluation_repository import EvaluationRepository
from infra.exceptions import OrchestratorException
from infra.logger import get_logger

_SECURITY_MIN_SCORE = 5.0


class EvalState(TypedDict):
    """Shared state passed between LangGraph nodes throughout the evaluation pipeline."""

    request: EvalRequest
    security_result: DimensionScore | None
    executor_output: ExecutorOutput | None
    evaluation_result: EvaluationResult | None
    error: str | None


async def security_check_node(state: EvalState) -> dict:
    try:
        agent = SecurityEvaluatorAgent()
        result = await agent.run(state["request"])
        if result.score < _SECURITY_MIN_SCORE:
            return {
                "security_result": result,
                "error": f"Input rejected: security score {result.score} below threshold {_SECURITY_MIN_SCORE}",
            }
        return {"security_result": result}
    except Exception as e:
        return {"error": str(e)}


async def execute_node(state: EvalState) -> dict:
    try:
        agent = ExecutorAgent()
        result = await agent.run(state["request"])
        return {"executor_output": result}
    except Exception as e:
        return {"error": str(e)}


async def evaluate_node(state: EvalState) -> dict:
    try:
        agent = EvaluatorAgent()
        result = await agent.run(state["request"], state["executor_output"])
        return {"evaluation_result": result}
    except Exception as e:
        return {"error": str(e)}


async def handle_error_node(state: EvalState) -> dict:
    logger = get_logger(__name__)
    logger.error("pipeline_failed", error=state["error"])
    return {}


def should_execute(state: EvalState) -> str:
    if state["error"] is not None:
        return "handle_error"
    return "execute"


def should_continue(state: EvalState) -> str:
    if state["error"] is not None:
        return "handle_error"
    return "evaluate"


def _build_graph():
    graph = StateGraph(EvalState)

    graph.add_node("security_check", security_check_node)
    graph.add_node("execute", execute_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("handle_error", handle_error_node)

    graph.set_entry_point("security_check")

    graph.add_conditional_edges(
        "security_check",
        should_execute,
        {"execute": "execute", "handle_error": "handle_error"},
    )
    graph.add_conditional_edges(
        "execute",
        should_continue,
        {"evaluate": "evaluate", "handle_error": "handle_error"},
    )
    graph.add_conditional_edges(
        "evaluate",
        should_continue,
        {"evaluate": END, "handle_error": "handle_error"},
    )
    graph.add_edge("handle_error", END)

    return graph.compile()


class OrchestratorGraph:
    """LangGraph pipeline: security_check → execute → evaluate → persist → END."""

    def __init__(self) -> None:
        self.graph = _build_graph()
        self.logger = get_logger(__name__)

    async def run(self, request: EvalRequest) -> EvalResponse:
        """Execute the full evaluation pipeline and return the scored response."""
        self.logger.info("orchestrator_started", task=request.task, model=request.model)

        initial_state = EvalState(
            request=request,
            security_result=None,
            executor_output=None,
            evaluation_result=None,
            error=None,
        )

        final_state = await self.graph.ainvoke(initial_state)

        if final_state["error"] is not None:
            raise OrchestratorException(
                message="Pipeline failed during execution",
                context={
                    "error": final_state["error"],
                    "task": request.task,
                    "model": request.model,
                },
            )

        if final_state["evaluation_result"] is None:
            raise OrchestratorException(
                message="Pipeline completed without evaluation result",
                context={"task": request.task, "model": request.model},
            )

        evaluation_result = final_state["evaluation_result"]
        security_result = final_state["security_result"]
        if security_result is not None:
            evaluation_result = evaluation_result.model_copy(update={"security": security_result})

        self.logger.info(
            "orchestrator_completed",
            verdict=evaluation_result.verdict,
            security_score=security_result.score if security_result else None,
        )

        response = EvalResponse(
            request=request,
            result=evaluation_result,
            output=final_state["executor_output"].response if final_state.get("executor_output") else None,
        )

        try:
            repo = EvaluationRepository()
            entity = await repo.save(request, response)
            self.logger.info("evaluation_persisted", public_id=entity.public_id)
        except Exception as e:
            self.logger.error("evaluation_persist_failed", error=str(e))

        return response
