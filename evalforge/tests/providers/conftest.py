import pytest


@pytest.fixture
def sample_system_prompt():
    return "You are a helpful assistant. Return only JSON."


@pytest.fixture
def sample_user_message():
    return "Task: Summarize\n\nInput: The quick brown fox."


@pytest.fixture
def mock_anthropic_provider_response():
    return {
        "content": [{"type": "text", "text": '{"response": "A fox summary."}'}],
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


@pytest.fixture
def mock_openai_provider_response():
    return {
        "choices": [
            {
                "message": {
                    "content": '{"response": "A fox summary."}',
                    "role": "assistant",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        },
    }
