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

## Sprint 2 — CONCLUÍDA ✓
Issues fechadas: #5, #6, #7, #8

### Entregáveis
- `evalforge/core/schemas.py` — `EvalRequest`, `ExecutorOutput`, `DimensionScore`, `EvaluationResult`, `EvalResponse`
- `evalforge/prompts/executor.md` — system prompt do agente executor
- `evalforge/prompts/evaluator.md` — system prompt do agente evaluator (3 dimensões + safety threshold)
- `evalforge/core/prompt_loader.py` — `load_prompt(name)` com `EvalException` em arquivo ausente
- `evalforge/agents/executor.py` — `ExecutorAgent.run()` com medição de latência e custo
- `evalforge/agents/evaluator.py` — `EvaluatorAgent.run()` com verdict PASS/FAIL
- Testes: **43/43 passando** (Sprint 1 + Sprint 2)

### Regras de negócio estabelecidas
- `verdict = PASS` apenas se média ≥ 7.0 **e** safety ≥ 9.0
- Custo: $3/M tokens input, $15/M tokens output (Anthropic Sonnet)
- Prompts são arquivos `.md` versionados, nunca hardcoded em Python

## Sprint 3 — PRÓXIMA
Issues: #9, #10

| Issue | Arquivo | Descrição |
|-------|---------|-----------|
| #9 | `core/orchestrator.py` | `OrchestratorGraph` com LangGraph: execute → evaluate → END |
| #10 | `core/dimensions.py` | `EvalDimension` + `DIMENSIONS` com 4 dimensões padrão |

## Setup local
```powershell
cd evalforge\evalforge
.venv\Scripts\Activate.ps1
pytest tests/ -v
```
