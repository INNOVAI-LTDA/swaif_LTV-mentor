# ADR: Transição de terminologia de roles (`mentor`/`aluno` -> `provider`/`client`)

- Status: Aprovado
- Data: 2026-05-07

## Contexto

A plataforma evolui para nomenclatura canônica multi-segmento (`provider`, `client`), mas o contrato v1 está congelado e expõe `mentor` e `aluno` em endpoints/payloads públicos.

## Decisão

1. **Interface pública v1 permanece estável**
   - Endpoints e payloads v1 continuam usando `mentor` e `aluno`.
2. **Normalização interna de roles**
   - Camada de segurança/autenticação passa a normalizar internamente:
     - `mentor` -> `provider`
     - `aluno`/`student` -> `client`
   - Tokens passam a carregar role interna canônica.
3. **Compatibilidade de leitura/escrita**
   - Entradas legadas e canônicas são aceitas durante a transição.
   - Respostas v1 continuam retornando termos legados (`mentor`, `aluno`) enquanto o contrato v1 estiver vigente.

## Plano de depreciação por fases

- **Fase 1 (compat):** aceitar aliases legados/canônicos; manter saída pública v1 legada.
- **Fase 2 (dual-read/write):** persistência/integrações internas aceitam e emitem ambos os formatos com adaptadores explícitos.
- **Fase 3 (switch default):** `provider`/`client` tornam-se padrão interno e de novos contratos/versionamentos.
- **Fase 4 (remoção legado):** remover aliases legados após janela de migração e comunicação formal.

## Consequências

- Reduz risco de regressão no frontend e integrações existentes.
- Permite evolução sem quebra imediata de contratos.
- Exige cobertura de testes de compatibilidade até a conclusão da Fase 4.
