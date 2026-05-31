class EvalException(Exception):
    def __init__(self, message: str, context: dict) -> None:
        self.message = message
        self.context = context
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"{self.message} | context: {self.context}"


class AgentException(EvalException):
    """Raised when an agent (executor or evaluator) fails internally."""


class OrchestratorException(EvalException):
    """Raised when the LangGraph orchestration fails."""


class ProviderException(EvalException):
    """Raised when an external LLM provider call fails."""

    def __init__(self, message: str, context: dict, provider: str) -> None:
        self.provider = provider
        super().__init__(message=message, context=context)


class ValidationException(EvalException):
    """Raised when input validation fails before reaching the agents."""


class EvalIntegrationException(EvalException):
    """Raised for any third-party integration failure outside of LLM providers."""

    def __init__(self, message: str, context: dict, integration: str) -> None:
        self.integration = integration
        super().__init__(message=message, context=context)


class RateLimitException(EvalException):
    """Raised when a user exceeds their request quota."""

    def __init__(self, message: str, context: dict, retry_after: int = 3600) -> None:
        self.retry_after = retry_after
        super().__init__(message=message, context=context)
