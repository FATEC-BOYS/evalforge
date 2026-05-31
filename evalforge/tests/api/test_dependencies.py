from api.dependencies import RequestContext, get_orchestrator, get_request_context, get_request_id
from core.orchestrator import OrchestratorGraph


def test_get_request_id_returns_string():
    result = get_request_id()
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_request_id_returns_unique_values():
    first = get_request_id()
    second = get_request_id()
    assert first != second


def test_get_request_context_returns_request_context():
    result = get_request_context()
    assert isinstance(result, RequestContext)
    assert isinstance(result.request_id, str)
    assert len(result.request_id) > 0


def test_get_orchestrator_returns_orchestrator_graph():
    result = get_orchestrator()
    assert isinstance(result, OrchestratorGraph)
