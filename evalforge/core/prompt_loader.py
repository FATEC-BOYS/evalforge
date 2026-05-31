from pathlib import Path

from infra.exceptions import EvalException

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise EvalException(
            message="Prompt file not found",
            context={"prompt_name": name, "expected_path": str(path)},
        )
    return path.read_text(encoding="utf-8")
