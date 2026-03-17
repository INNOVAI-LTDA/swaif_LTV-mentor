# Naming e notas de dominio (MVP mentoria)

## 1) Visualizacoes centrais e papeis (assinatura do produto)
- Centro de Comando: operacao diaria por excecao, com foco em risco, progresso de ciclo e gatilhos de renovacao.
- Radar de Transformacao: comparacao de baseline/atual/projecao por eixo do metodo.
- Matriz de Renovacao Antecipada: priorizacao de renovacao e resgate por quadrantes de progresso x engajamento.

## 2) Termos clinicos detectados que devem migrar para mentoria

| Termo atual (clinico) | Termo alvo (mentoria) | Observacao |
|---|---|---|
| paciente | aluno | padrao principal para pessoa atendida |
| medico / painel medico | mentor / painel do mentor | visto em CTAs de proposta |
| clinica | operacao de mentoria / programa | evitar linguagem de saude |
| jornada biologica | jornada de transformacao | manter ideia de evolucao |
| biomarcador | indicador | manter `indicador` no cadastro e monitoramento |
| eixo biologico / pilares biologicos | pilar do metodo | alinhado ao cadastro de pilares |
| protocolo clinico | metodo / protocolo de mentoria | ambos aceitos no contexto atual |
| intervencao urgente | acao de recuperacao | para risco de churn/desengajamento |
| idade bio / evolucao biologica | score de evolucao | nome mais neutro para mentoria |
| causa provavel (anomalia) | hipotese de bloqueio | linguagem de acompanhamento |

## 3) Dados que parecem resumidos vs detalhados (visao geral)

### Resumidos (listas, bolhas, topo)
- contagens (ativos, alertas, D-45)
- LTV total e oportunidades agregadas
- progresso e engajamento em percentual
- status de urgencia e prioridade por cor/tag

### Detalhados (painel lateral, drawer, radar)
- indicadores por item (`metricValues` ou `markers`)
- checkpoints da jornada
- texto de motivo de renovacao e sugestao de plano
- eixo a eixo de baseline/atual/projecao no radar

## 4) Ambiguidades e inconsistencias de nomenclatura
- Entidade de pessoa alterna entre `patient`, `student`, `client`.
- Hooks tambem alternam: `useStudents`, `useClients`, `useStudentRadar`, `useClientRadar`.
- Campo de programa alterna entre `programName` e `plan`.
- `getBioAgeDelta` retorna percentual de engajamento, nao delta biologico.
- Em `jpe-hub.jsx`, `getRisk` depende de `p.segments`, mas o fluxo principal usa `urgency`.
- Fluxo de anomalia existe no layout, mas em partes do codigo esta desacoplado da interacao principal.
- Terminologia de UI mistura portugues e ingles (`watch`, `rescue`, `Management by Exception`, `Business Intelligence Clinico`).

## 5) Normalizacao sugerida para a primeira entrega
- Pessoa: usar `aluno` em labels; manter chave tecnica unica (`student`) no backend para evitar churn de contrato.
- Profissional: usar `mentor` em labels; evitar `medico`.
- Programa: padronizar campo de dominio em `mentorshipName` (ou manter `programName` com alias de migracao).
- Indicadores: padronizar em `indicators` no backend, com alias de leitura para `markers`/`metricValues` na camada de adaptacao.
- Urgencia: manter enum tecnico claro (`normal|watch|rescue|critical`) e mapear para rotulos de mentoria no frontend.
