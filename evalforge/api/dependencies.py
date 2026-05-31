from dataclasses import dataclass

import uuid7

from core.orchestrator import OrchestratorGraph


@dataclass
class RequestContext:
    request_id: str


def get_request_id() -> str:
    return str(uuid7.uuid7())


def get_request_context() -> RequestContext:
    request_id = get_request_id()
    return RequestContext(request_id=request_id)


def get_orchestrator() -> OrchestratorGraph:
    return OrchestratorGraph()
