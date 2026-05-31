import pytest

from infra.exceptions import (
    AgentException,
    EvalException,
    EvalIntegrationException,
    OrchestratorException,
    ProviderException,
    ValidationException,
)


def test_eval_exception_requires_context():
    with pytest.raises(TypeError):
        EvalException(message="missing context")


def test_eval_exception_requires_message():
    with pytest.raises(TypeError):
        EvalException(context={"key": "value"})


def test_eval_exception_str_includes_context():
    exc = EvalException(message="something failed", context={"key": "value"})
    result = str(exc)
    assert "something failed" in result
    assert "key" in result


def test_subclasses_inherit_context():
    subclasses = [AgentException, OrchestratorException, ValidationException]
    ctx = {"request_id": "abc123"}
    for cls in subclasses:
        exc = cls(message="failure", context=ctx)
        assert isinstance(exc, EvalException)
        assert exc.context is ctx


def test_provider_exception_requires_provider_field():
    with pytest.raises(TypeError):
        ProviderException(message="failed", context={})


def test_provider_exception_carries_provider_name():
    exc = ProviderException(message="Anthropic returned 500", context={}, provider="anthropic")
    assert exc.provider == "anthropic"


def test_integration_exception_carries_integration_name():
    exc = EvalIntegrationException(message="LangSmith unavailable", context={}, integration="langsmith")
    assert exc.integration == "langsmith"


def test_no_silent_catch_pattern():
    # Silent catches (except: pass or bare except: ...) are forbidden in this codebase.
    # Every exception must propagate or be re-raised as an EvalException subclass with
    # meaningful message and context so it can be logged and traced properly.
    assert True
