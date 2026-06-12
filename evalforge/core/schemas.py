from __future__ import annotations

from pydantic import BaseModel, field_validator

from core.dimensions import EvalDimension


class EvalRequest(BaseModel):
    task: str
    input: str
    model: str = "claude-sonnet-4-20250514"
    dimensions: list[EvalDimension] | None = None

    @field_validator("task", "input", "model")
    @classmethod
    def must_be_non_empty(cls, v: str, info) -> str:
        if not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return v


class ExecutorOutput(BaseModel):
    response: str
    latency_ms: float
    cost_usd: float

    @field_validator("response")
    @classmethod
    def response_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("response must not be empty")
        return v

    @field_validator("latency_ms", "cost_usd")
    @classmethod
    def must_be_non_negative(cls, v: float, info) -> float:
        if v < 0:
            raise ValueError(f"{info.field_name} must be >= 0")
        return v


class DimensionScore(BaseModel):
    score: float
    justification: str

    @field_validator("score")
    @classmethod
    def score_must_be_in_range(cls, v: float) -> float:
        if v < 0.0 or v > 10.0:
            raise ValueError(f"score must be between 0.0 and 10.0, got {v}")
        return v

    @field_validator("justification")
    @classmethod
    def justification_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("justification must not be empty")
        return v


_VALID_VERDICTS = {"PASS", "FAIL"}


class EvaluationResult(BaseModel):
    scores: dict[str, DimensionScore]
    latency_ms: float
    verdict: str
    model: str

    @field_validator("latency_ms")
    @classmethod
    def latency_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("latency_ms must be >= 0")
        return v

    @field_validator("verdict")
    @classmethod
    def verdict_must_be_valid(cls, v: str) -> str:
        if v not in _VALID_VERDICTS:
            raise ValueError(f"verdict must be one of {sorted(_VALID_VERDICTS)}, got '{v}'")
        return v

    @field_validator("model")
    @classmethod
    def model_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("model must not be empty")
        return v


class EvalResponse(BaseModel):
    request: EvalRequest
    result: EvaluationResult
