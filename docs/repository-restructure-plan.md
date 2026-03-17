# Repository Restructure Plan (Safe and Non-Invasive)

Data: 2026-03-10
Base: `docs/repository-structure-audit.md`, `docs/runtime-critical-paths.md`, `docs/repository-risk-analysis.md`

## 1) Objetivo do plano

Preparar o repositorio para evolucao como plataforma (core + skins + entregas por cliente), sem alterar runtime atual da demo.

Guardrails deste plano:
- nao alterar codigo
- nao alterar paths runtime
- nao mover `backend/` ou `frontend/`

## 2) Estrutura alvo (conceitual)

```text
repo/
  backend/                      # runtime critico (intacto)
  frontend/                     # runtime critico (intacto)
  scripts/                      # runtime critico (intacto)

  docs/
    architecture/               # arquitetura e operacao de plataforma
    mvp-mentoria/               # contratos e historico da demo atual
    product/                    # visao de produto e roadmap
    clients/                    # pacotes por cliente
    references/                 # papel de origin e outras referencias
    repository-structure-audit.md
    runtime-critical-paths.md
    repository-risk-analysis.md
    repository-restructure-plan.md

  .github/
    ISSUE_TEMPLATE/             # modelos de issue
    workflows/                  # CI/CD (fase futura, se necessario)

  README.md                     # onboarding do repositorio
  .gitignore                    # higiene de versionamento
```

## 3) Itens que podem ser reorganizados agora (baixo risco)

1. Documentacao:
- criar/ajustar `docs/product/`, `docs/clients/`, `docs/references/`
- consolidar guias de arquitetura e processo em `docs/architecture/`

2. Governanca de repositorio:
- criar/ajustar `README.md` (raiz)
- criar/ajustar `.gitignore` (raiz)
- criar `.github/ISSUE_TEMPLATE/`

3. Classificacao e trilhas:
- documentar inventario de pastas sensiveis
- documentar papel de `origin/` como referencia historica

## 4) Itens que devem permanecer intactos nesta fase

- `backend/` (toda a arvore)
- `frontend/` (toda a arvore)
- `scripts/` (toda a arvore)
- `backend/data/`
- `backend/app/`
- `frontend/src/`
- `frontend/package.json`
- `frontend/vite.config.ts`
- fluxo atual de bootstrap da demo

## 5) Itens que devem ser apenas documentados (nao mover agora)

1. `origin/`
- manter intacto
- registrar como referencia historica/conceitual
- proibir dependencia estrutural no runtime atual

2. Pastas de artefato/cache/temp
- `frontend/node_modules`, `frontend/dist`
- `backend/.venv`, `backend/.vendor`, `backend/.deps`
- `backend/.tmp*`, `backend/test_tmp*`, `.logs`, `test_tmp_bootstrap`
- apenas classificar e orientar limpeza manual futura (sem executar agora)

3. Candidatos de reorganizacao futura
- padronizacao de documentacao por dominio (produto, cliente, arquitetura)
- eventual separacao entre core/skin/client em fase posterior, com plano dedicado e validacao de demo

## 6) Sequencia recomendada (sem risco para runtime)

1. Consolidar documentacao de estrutura e risco (ja iniciado).
2. Criar camada de governanca (`README`, `.gitignore`, templates de issue).
3. Formalizar trilha de entrega por cliente em `docs/clients/`.
4. Validar que nenhuma mudanca tocou runtime.

## 7) Fora de escopo desta fase

- refatoracao de codigo
- mudanca de imports
- mudanca de paths de execucao
- mover/renomear `backend/`, `frontend/`, `scripts/`
- alteracao de bootstrap/runtime da demo

## 8) Criterio de sucesso

Plano aprovado quando:
- estrutura alvo esta definida documentalmente
- itens de baixo risco estao claros para execucao
- runtime critico esta explicitamente preservado
- `origin/` esta tratado como referencia, sem acoplamento runtime
