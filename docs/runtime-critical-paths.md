# Runtime Critical Paths

Data: 2026-03-10

## Objetivo

Registrar caminhos que devem ser tratados como sensiveis para nao quebrar a demo atual.

## Caminhos runtime criticos (alta sensibilidade)

- `backend/`
- `backend/app/`
- `backend/data/`
- `frontend/`
- `frontend/src/`
- `frontend/package.json`
- `frontend/vite.config.ts`
- `scripts/`
- `scripts/mvp_bootstrap.py`
- `scripts/mvp_bootstrap.bat`

## Regras de preservacao para estes caminhos

1. Nao alterar codigo sem mudanca planejada e validada.
2. Nao mover ou renomear pasta/arquivo.
3. Nao alterar imports ou paths de execucao.
4. Nao mudar bootstrap da demo sem plano dedicado.
5. Nao apagar dados de `backend/data/` sem backup e aprovacao explicita.

## Caminhos nao criticos (mas relevantes)

- `docs/` (documentacao)
- `origin/` (referencia historica)
- `.logs/`, `test_tmp_bootstrap/`, caches locais (`.tmp*`, `.pytest_cache`, `node_modules`, `dist`)

## Nota operacional

Nesta auditoria nao houve alteracao em caminhos runtime criticos; apenas criacao de documentacao de classificacao.

