import pytest
from pydantic import ValidationError

from providers.base import ProviderOutput


def test_provider_output_requires_text():
    with pytest.raises(ValidationError):
        ProviderOutput(input_tokens=0, output_tokens=0)


def test_provider_output_rejects_empty_text():
    with pytest.raises(ValidationError):
        ProviderOutput(text="", input_tokens=0, output_tokens=0)


def test_provider_output_rejects_negative_input_tokens():
    with pytest.raises(ValidationError):
        ProviderOutput(text="ok", input_tokens=-1, output_tokens=0)


def test_provider_output_rejects_negative_output_tokens():
    with pytest.raises(ValidationError):
        ProviderOutput(text="ok", input_tokens=0, output_tokens=-1)


def test_provider_output_accepts_zero_tokens():
    output = ProviderOutput(text="ok", input_tokens=0, output_tokens=0)
    assert output.text == "ok"
    assert output.input_tokens == 0
    assert output.output_tokens == 0
