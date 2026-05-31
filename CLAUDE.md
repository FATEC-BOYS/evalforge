# evalforge — Project Memory

## Repositório
- GitHub: `fatec-boys/evalforge`
- Branch de desenvolvimento: `main` (PR #26 mergeada)

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

## Sprint 3 — CONCLUÍDA ✓
Issues fechadas: #9, #10

### Entregáveis
- `evalforge/core/dimensions.py` — `EvalDimension` + `DIMENSIONS` (4 dimensões: accuracy, reasoning, safety, latency)
- `evalforge/core/orchestrator.py` — `OrchestratorGraph` com LangGraph: execute → evaluate → END
- Testes: **60/60 passando** (Sprint 1 + 2 + 3)

### Arquitetura do pipeline
```
EvalRequest → execute_node (ExecutorAgent) → evaluate_node (EvaluatorAgent) → EvalResponse
                     ↓ erro                        ↓ erro
                 error_node → END             error_node → END
```

## Sprint 4 — CONCLUÍDA ✓
Issues fechadas: #11, #12

### Entregáveis
- `evalforge/api/main.py` — FastAPI app com lifespan, CORS, handlers de exceção, `GET /health`, `POST /evaluate`
- `evalforge/api/dependencies.py` — `RequestContext`, `get_request_id()`, `get_orchestrator()`
- Testes: **74/74 passando** (Sprint 1 + 2 + 3 + 4)

## Sprint 5 — CONCLUÍDA ✓
Issue fechada: #15

### Entregáveis
- `README.md` — reescrito em inglês com diagrama Mermaid, tabela de dimensões, verdict logic, getting started, design decisions, roadmap

## Sprint 6 — CONCLUÍDA ✓
Issues: Docker + DB

### Entregáveis
- `Dockerfile` + `docker-compose.yml` + `.dockerignore` — ambiente de desenvolvimento com postgres, redis e api
- `evalforge/db/base.py` — `BaseEntity` com `id` (BINARY/uuid4), `public_id`, `created_at`, `updated_at`; defaults gerados via SQLAlchemy `init` event
- `evalforge/db/session.py` — `writer_engine`, `reader_engine`, `get_writer_session()`, `get_reader_session()` com `@asynccontextmanager`
- `evalforge/db/entities/evaluation.py` — `EvaluationEntity` com todas as colunas da avaliação
- `evalforge/db/repositories/evaluation_repository.py` — `save()`, `find_by_public_id()`, `list_by_model()`
- `alembic.ini` + `alembic/env.py` — migrações async com autogenerate
- `core/orchestrator.py` atualizado — persiste avaliação após pipeline; falha no save loga mas não quebra resposta
- Testes: **97/97 passando** (Sprint 1 + 2 + 3 + 4 + 5 + 6)

### Decisões técnicas
- `uuid7` incompatível com Python 3.14 — substituído por `uuid.uuid4()` da stdlib
- SQLAlchemy `default=lambda` só roda no INSERT; defaults em instanciação via `@event.listens_for(BaseEntity, "init")`
- Sessões reader/writer mockadas nos testes via `monkeypatch` + SQLite in-memory (aiosqlite)
- `asyncpg` adicionado ao requirements (driver PostgreSQL assíncrono)

## Setup local
```powershell
cd evalforge\evalforge
.venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
pytest tests/ -v
```
