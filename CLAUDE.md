# evalforge — Project Memory

## Repositório
- GitHub: `fatec-boys/evalforge`
- Branch de desenvolvimento: `claude/intelligent-feynman-OCjzM`
- Branch base: `main`
- PR aberta: #26

## Sprint 1 — CONCLUÍDA ✓
Issues fechadas: #1, #2, #3, #4

### Entregáveis
- Estrutura de pastas completa com `__init__.py` em todos os módulos
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
- `evalforge/infra/config.py` — `Settings` via pydantic-settings + singleton `settings`
- `evalforge/infra/logger.py` — `configure_logging(app_env)` + `get_logger(name)` com structlog
- `evalforge/infra/exceptions.py` — hierarquia de exceções com raiz em `EvalException`
- Testes: **16/16 passando** em `tests/infra/`

### Convenções estabelecidas
- Zero `os.environ` direto — usar sempre `from infra.config import settings`
- Zero `print()` — usar sempre `from infra.logger import get_logger`
- Todo erro herda de `EvalException` com `message` e `context` obrigatórios
- Zero catch silencioso (`except: pass`)

## Sprint 2 — PRÓXIMA
Issues: #5, #6, #7, #8

| Issue | Arquivo | Descrição |
|-------|---------|-----------|
| #5 | `prompts/executor.md`, `prompts/evaluator.md`, `core/prompt_loader.py` | Prompts versionados + loader |
| #6 | `core/schemas.py` | Pydantic models: `EvalRequest`, `ExecutorOutput`, `DimensionScore`, `EvaluationResult`, `EvalResponse` |
| #7 | `agents/executor.py` | `ExecutorAgent` — chama Anthropic, mede latência e custo |
| #8 | `agents/evaluator.py` | `EvaluatorAgent` — avalia em 4 dimensões, calcula verdict |

## Setup local
```powershell
cd evalforge\evalforge
.venv\Scripts\Activate.ps1
pytest tests/infra/ -v
```
