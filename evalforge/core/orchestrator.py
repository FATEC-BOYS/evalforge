from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.evaluator import EvaluatorAgent
from agents.executor import ExecutorAgent
from core.schemas import EvalRequest, EvalResponse, EvaluationResult, ExecutorOutput
from infra.exceptions import OrchestratorException
from infra.logger import get_logger


class EvalState(TypedDict):
    request: EvalRequest
    executor_output: ExecutorOutput | None
    evaluation_result: EvaluationResult | None
    error: str | None


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


async def error_node(state: EvalState) -> dict:
    logger = get_logger(__name__)
    logger.error("pipeline_failed", error=state["error"])
    return {}


def should_continue(state: EvalState) -> str:
    if state["error"] is not None:
        return "error"
    return "evaluate"


def _build_graph():
    graph = StateGraph(EvalState)

    graph.add_node("execute", execute_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("error", error_node)

    graph.set_entry_point("execute")

    graph.add_conditional_edges(
        "execute",
        should_continue,
        {"evaluate": "evaluate", "error": "error"},
    )
    graph.add_conditional_edges(
        "evaluate",
        should_continue,
        {"evaluate": END, "error": "error"},
    )
    graph.add_edge("error", END)

    return graph.compile()


class OrchestratorGraph:
    def __init__(self) -> None:
        self.graph = _build_graph()
        self.logger = get_logger(__name__)

    async def run(self, request: EvalRequest) -> EvalResponse:
        self.logger.info("orchestrator_started", task=request.task, model=request.model)

        initial_state = EvalState(
            request=request,
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

        self.logger.info(
            "orchestrator_completed",
            verdict=final_state["evaluation_result"].verdict,
        )

        return EvalResponse(
            request=request,
            result=final_state["evaluation_result"],
        )
