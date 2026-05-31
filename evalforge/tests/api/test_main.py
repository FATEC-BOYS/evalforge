import pytest
from unittest.mock import AsyncMock

from infra.exceptions import EvalException


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(app_client):
    response = await app_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "env" in response.json()


@pytest.mark.asyncio
async def test_evaluate_endpoint_returns_200(app_client, mock_eval_request_payload):
    response = await app_client.post("/evaluate", json=mock_eval_request_payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_evaluate_endpoint_returns_eval_response_schema(
    app_client, mock_eval_request_payload
):
    response = await app_client.post("/evaluate", json=mock_eval_request_payload)
    body = response.json()
    assert "request" in body
    assert "result" in body
    assert body["result"]["verdict"] == "PASS"
    assert body["result"]["accuracy"]["score"] == 9.0
    assert body["result"]["safety"]["score"] == 10.0


@pytest.mark.asyncio
async def test_evaluate_endpoint_calls_orchestrator_once(
    app_client, mock_orchestrator, mock_eval_request_payload
):
    await app_client.post("/evaluate", json=mock_eval_request_payload)
    mock_orchestrator.run.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_endpoint_passes_correct_request_to_orchestrator(
    app_client, mock_orchestrator, mock_eval_request_payload
):
    await app_client.post("/evaluate", json=mock_eval_request_payload)
    call_arg = mock_orchestrator.run.call_args[0][0]
    assert call_arg.task == "Summarize this text"
    assert call_arg.input == "The quick brown fox jumps over the lazy dog"


@pytest.mark.asyncio
async def test_eval_exception_returns_422(
    app_client, mock_orchestrator, mock_eval_request_payload
):
    mock_orchestrator.run = AsyncMock(
        side_effect=EvalException(
            message="Something went wrong",
            context={"detail": "test error"},
        )
    )
    response = await app_client.post("/evaluate", json=mock_eval_request_payload)
    assert response.status_code == 422
    assert response.json()["error"] == "Something went wrong"
    assert response.json()["context"]["detail"] == "test error"


@pytest.mark.asyncio
async def test_unexpected_exception_returns_500(
    app_client, mock_orchestrator, mock_eval_request_payload
):
    mock_orchestrator.run = AsyncMock(side_effect=RuntimeError("boom"))
    response = await app_client.post("/evaluate", json=mock_eval_request_payload)
    assert response.status_code == 500
    assert response.json()["error"] == "An unexpected error occurred"
    assert "boom" not in response.json()["error"]
    assert "traceback" not in str(response.json())


@pytest.mark.asyncio
async def test_unexpected_exception_does_not_expose_internals(
    app_client, mock_orchestrator, mock_eval_request_payload
):
    mock_orchestrator.run = AsyncMock(
        side_effect=RuntimeError("secret internal detail")
    )
    response = await app_client.post("/evaluate", json=mock_eval_request_payload)
    assert "secret internal detail" not in str(response.json())


@pytest.mark.asyncio
async def test_evaluate_request_id_is_logged(app_client, mock_eval_request_payload):
    response = await app_client.post("/evaluate", json=mock_eval_request_payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cors_headers_present_in_development(app_client):
    response = await app_client.get(
        "/health", headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
