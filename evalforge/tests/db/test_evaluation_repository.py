from contextlib import asynccontextmanager

import pytest
import pytest_asyncio

from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult
from db.entities.evaluation import EvaluationEntity
from db.repositories.evaluation_repository import EvaluationRepository


@pytest_asyncio.fixture(loop_scope="function")
async def repo(writer_session, monkeypatch):
    """Patch both session factories to use the same in-memory session."""

    @asynccontextmanager
    async def _writer():
        yield writer_session

    @asynccontextmanager
    async def _reader():
        yield writer_session

    monkeypatch.setattr(
        "db.repositories.evaluation_repository.get_writer_session", _writer
    )
    monkeypatch.setattr(
        "db.repositories.evaluation_repository.get_reader_session", _reader
    )
    return EvaluationRepository()


def _make_response(model="claude-sonnet-4-20250514", verdict="PASS"):
    return EvalResponse(
        request=EvalRequest(
            task="Summarize this text",
            input="The quick brown fox jumps over the lazy dog",
            model=model,
        ),
        result=EvaluationResult(
            accuracy=DimensionScore(score=9.0, justification="Accurate."),
            reasoning=DimensionScore(score=8.5, justification="Clear."),
            safety=DimensionScore(score=10.0, justification="Safe."),
            latency_ms=320.0,
            verdict=verdict,
            model=model,
        ),
    )


@pytest.mark.asyncio
async def test_save_persists_evaluation(repo, sample_eval_request, sample_eval_response):
    entity = await repo.save(sample_eval_request, sample_eval_response)
    assert isinstance(entity, EvaluationEntity)
    assert entity.task == "Summarize this text"
    assert entity.verdict == "PASS"
    assert entity.public_id is not None


@pytest.mark.asyncio
async def test_save_maps_scores_correctly(repo, sample_eval_request, sample_eval_response):
    entity = await repo.save(sample_eval_request, sample_eval_response)
    assert entity.accuracy_score == 9.0
    assert entity.reasoning_score == 8.5
    assert entity.safety_score == 10.0
    assert entity.latency_ms == 320.0


@pytest.mark.asyncio
async def test_find_by_public_id_returns_entity(repo, sample_eval_request, sample_eval_response):
    entity = await repo.save(sample_eval_request, sample_eval_response)
    found = await repo.find_by_public_id(entity.public_id)
    assert found is not None
    assert found.task == entity.task
    assert found.verdict == entity.verdict


@pytest.mark.asyncio
async def test_find_by_public_id_returns_none_when_not_found(repo):
    result = await repo.find_by_public_id("nonexistent-public-id-xyz")
    assert result is None


@pytest.mark.asyncio
async def test_list_by_model_returns_correct_entries(repo):
    request_a = EvalRequest(
        task="Task A", input="Input A", model="claude-sonnet-4-20250514"
    )
    request_b = EvalRequest(task="Task B", input="Input B", model="gpt-4o")
    response_a = _make_response(model="claude-sonnet-4-20250514")
    response_b = _make_response(model="gpt-4o")

    await repo.save(request_a, response_a)
    await repo.save(request_a, _make_response(model="claude-sonnet-4-20250514"))
    await repo.save(request_b, response_b)

    result = await repo.list_by_model("claude-sonnet-4-20250514")
    assert len(result) == 2
    assert all(e.model == "claude-sonnet-4-20250514" for e in result)


@pytest.mark.asyncio
async def test_list_by_model_respects_limit(repo):
    model = "claude-sonnet-4-20250514"
    request = EvalRequest(task="Task", input="Input", model=model)
    response = _make_response(model=model)
    for _ in range(5):
        await repo.save(request, response)

    result = await repo.list_by_model(model, limit=3)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_list_by_model_returns_empty_list_when_no_match(repo):
    result = await repo.list_by_model("nonexistent-model-xyz")
    assert result == []


@pytest.mark.asyncio
async def test_public_id_is_unique_across_saves(repo, sample_eval_request, sample_eval_response):
    entity1 = await repo.save(sample_eval_request, sample_eval_response)
    entity2 = await repo.save(sample_eval_request, sample_eval_response)
    assert entity1.public_id != entity2.public_id
