# Repository Risk Analysis

Data: 2026-03-10

## Escopo

Analise de risco estrutural com base na classificacao de pastas:
- runtime critico
- referencia
- documentacao
- artefato gerado
- cache/temp

## Matriz de risco por categoria

| Categoria | Risco de impacto na demo | Justificativa |
|---|---|---|
| runtime critico | alto | alteracoes podem quebrar execucao, integracao e bootstrap. |
| referencia | medio | uso indevido pode gerar dependencia nao planejada (`origin/`). |
| documentacao | baixo | risco operacional baixo, impacto principal e de governanca. |
| artefato gerado | medio | limpeza/mudanca sem criterio pode interromper ambiente local. |
| cache/temp | baixo | normalmente recriavel, mas remocoes agressivas podem afetar fluxo local temporariamente. |

## Riscos concretos identificados

1. Misturar `origin/` com runtime oficial.
- Impacto: acoplamento legado e inconsistencia arquitetural.
- Nivel: medio.

2. Alterar `scripts/` sem validacao ponta a ponta.
- Impacto: demo pode nao subir corretamente.
- Nivel: alto.

3. Modificar `frontend/package.json` ou `frontend/vite.config.ts` sem controle.
- Impacto: quebra de build/dev server.
- Nivel: alto.

4. Alterar estrutura de `backend/data/` sem compatibilidade.
- Impacto: APIs podem retornar vazio, erro ou inconsistencias.
- Nivel: alto.

5. Tratar dependencias locais (`node_modules`, `.vendor`, `.venv`, `.deps`) como codigo-fonte.
- Impacto: ruido de versionamento e falhas de reproducao.
- Nivel: medio.

## Medidas de mitigacao recomendadas

1. Proteger caminhos runtime criticos com regra explicita de nao-movimentacao em tarefas estruturais.
2. Registrar qualquer mudanca em bootstrap como tarefa separada, com checklist de validacao.
3. Manter `origin/` como referencia somente documental/conceitual.
4. Evitar limpeza agressiva de artefatos/cache sem autorizacao explicita.
5. Priorizar organizacao documental antes de qualquer reestrutura fisica.

## Conclusao

O repositorio esta apto para evolucao organizada, desde que mudancas estruturais continuem priorizando preservacao de runtime e isolamento de referencias legadas.

