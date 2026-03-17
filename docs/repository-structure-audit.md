# Repository Structure Audit

Data: 2026-03-10  
Escopo: classificacao estrutural do repositorio atual (sem alteracao de runtime).

## Regras aplicadas nesta auditoria

- Nenhum arquivo de runtime foi alterado.
- Nenhuma pasta foi movida.
- Nenhum script de projeto foi executado.

## Estrutura observada (raiz)

- `.logs/`
- `backend/`
- `docs/`
- `frontend/`
- `origin/`
- `scripts/`
- `test_tmp_bootstrap/`

## Classificacao por pasta

| Pasta | Classificacao | Observacao |
|---|---|---|
| `.logs/` | artefato gerado | logs locais de execucao. |
| `backend/` | runtime critico | API, servicos, dados e bootstrap backend da demo. |
| `docs/` | documentacao | arquitetura, contratos, planos e auditorias. |
| `frontend/` | runtime critico | app React/Vite usado pela demo. |
| `origin/` | referencia | base historica/conceitual, nao runtime oficial. |
| `scripts/` | runtime critico | bootstrap e automacao de execucao da demo. |
| `test_tmp_bootstrap/` | cache/temp | temporarios de teste/bootstrap. |

## Subpastas relevantes (backend)

| Pasta | Classificacao | Observacao |
|---|---|---|
| `backend/app/` | runtime critico | codigo principal da API. |
| `backend/data/` | runtime critico | fonte de dados persistidos da demo. |
| `backend/tests/` | referencia | validacao/garantia de comportamento (nao runtime de producao). |
| `backend/.vendor/` | artefato gerado | dependencias locais vendorizadas. |
| `backend/.deps/` | artefato gerado | dependencias locais auxiliares. |
| `backend/.venv/` | artefato gerado | ambiente virtual local. |
| `backend/.hypothesis/` | cache/temp | cache de testes baseados em propriedades. |
| `backend/.pytest_cache/` | cache/temp | cache do pytest. |
| `backend/.tmp*` | cache/temp | temporarios locais de execucao/testes. |
| `backend/test_tmp*` | cache/temp | temporarios de teste. |
| `backend/.localtmp/` | cache/temp | temporarios locais. |

## Subpastas relevantes (frontend)

| Pasta | Classificacao | Observacao |
|---|---|---|
| `frontend/src/` | runtime critico | codigo da interface e integracao. |
| `frontend/node_modules/` | artefato gerado | dependencias instaladas localmente. |
| `frontend/dist/` | artefato gerado | build gerado. |

## Subpastas relevantes (docs/origin/scripts)

| Pasta | Classificacao | Observacao |
|---|---|---|
| `docs/architecture/` | documentacao | diretrizes de arquitetura e processo. |
| `docs/mvp-mentoria/` | documentacao | contratos, planos e auditorias do MVP. |
| `origin/adapters|contexts|hooks|lib|scripts|services|tests` | referencia | material legado para consulta conceitual. |
| `scripts/__pycache__/` | cache/temp | cache de bytecode Python. |

## Conclusao

A estrutura atual separa bem o que e runtime (`backend/`, `frontend/`, `scripts/`) do que e apoio (`docs/`, `origin/`, caches e artefatos gerados).  
A preservacao das pastas runtime criticas deve ser prioridade em qualquer reorganizacao futura.

