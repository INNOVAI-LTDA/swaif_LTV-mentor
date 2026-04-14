# Plano de Extração do Kernel DEVA

## Visão Geral

**Objetivo:** Extrair o núcleo genérico do SAD (Sistema de Apoio à Decisão) entregue ao cliente, transformando-o no produto **DEVA** - um motor de retenção e alinhamento de valor agnóstico, capaz de ser instanciado para diferentes clientes e produtos cíclicos.

**Conceito Central:** 
- **DEVA** = Kernel genérico que minimiza o *Gap de Valor* entre o prometido na venda e o percebido durante o consumo
- **Instância** = DEVA[Cliente][Produto] + Configurações específicas + Identidade visual do cliente
- **Exemplo atual:** DEVA[Acelerador Médico][Mentoria] = repositório atual do cliente

---

## Fase 1: Inventário e Mapeamento Detalhado

### Objetivo
Catalogar todos os artefatos do repositório atual, classificando-os como:
- **Core (DEVA Kernel):** Elementos genéricos que compõem a essência do SAD
- **Instance-Specific:** Elementos específicos do cliente (Acelerador Médico/Mentoria)
- **Hybrid:** Elementos que precisam ser refatorados para separar o genérico do específico

### Atividades

#### 1.1 Mapeamento de Entidades de Domínio
- [ ] Listar todas as entidades atuais (Matriz, Radar, Centro de Comando, etc.)
- [ ] Para cada entidade, identificar:
  - Atributos genéricos (ex: `valor_prometido`, `valor_percebido`, `ciclo_inicio`, `ciclo_fim`)
  - Atributos específicos do cliente (ex: terminologia médica, campos customizados)
  - Relacionamentos entre entidades
- [ ] Definir modelo canonical para cada entidade do kernel DEVA

#### 1.2 Mapeamento de APIs e Endpoints
- [ ] Catalogar todos os endpoints FastAPI existentes
- [ ] Classificar cada endpoint como Core/Instance/Hybrid
- [ ] Identificar dependências de configuração específica do cliente
- [ ] Documentar payloads de entrada/saída atuais vs. desejados no kernel

#### 1.3 Mapeamento de Frontend
- [ ] Inventariar todos os componentes React
- [ ] Identificar componentes de UI genéricos (tabelas, gráficos, formulários)
- [ ] Identificar componentes com hardcoded de identidade visual (cores, logos, textos)
- [ ] Mapear rotas e navegação atual
- [ ] Catalogar estados globais e contextos React

#### 1.4 Mapeamento de Persistência
- [ ] Analisar estrutura atual de arquivos JSON
- [ ] Identificar schemas de dados
- [ ] Mapear dependências de caminhos e estruturas de diretórios
- [ ] Documentar padrões de leitura/escrita atuais

#### 1.5 Mapeamento de Regras de Negócio
- [ ] Extrair todas as regras de cálculo (KPIs, métricas, gaps)
- [ ] Identificar fórmulas genéricas vs. específicas
- [ ] Documentar fluxos de decisão e critérios de alerta
- [ ] Catalogar thresholds e valores hardcoded

### Deliverables da Fase 1
- 📄 `reports/inventory/entities-mapping.md` - Matriz completa de entidades
- 📄 `reports/inventory/api-endpoints-catalog.md` - Catálogo de APIs classificado
- 📄 `reports/inventory/frontend-components-map.md` - Mapa de componentes React
- 📄 `reports/inventory/data-persistence-analysis.md` - Análise de persistência
- 📄 `reports/inventory/business-rules-catalog.md` - Catálogo de regras de negócio
- 📄 `reports/inventory/classification-matrix.md` - Matriz Core/Instance/Hybrid consolidada

### Critérios de Aceite
- ✅ 100% dos arquivos do repositório classificados
- ✅ Modelo canonical de todas as entidades documentado
- ✅ Dependências entre módulos mapeadas
- ✅ Lista de hardcodings a serem removidos identificada

---

## Fase 2: Design da Arquitetura do Kernel DEVA

### Objetivo
Projetar a arquitetura técnica do DEVA Kernel, definindo:
- Estrutura de diretórios do novo repositório
- Mecanismos de configuração e extensão
- Contratos de interface entre kernel e instâncias
- Estratégia de multi-tenancy e isolamento

### Atividades

#### 2.1 Definição da Estrutura do Repositório Kernel
Proposta inicial de estrutura:
```
deva-core/
├── src/
│   ├── core/               # Núcleo imutável do DEVA
│   │   ├── domain/         # Entidades canônicas
│   │   ├── services/       # Serviços de negócio genéricos
│   │   ├── metrics/        # Cálculos de KPIs e Gap de Valor
│   │   └── engine/         # Motor de decisões e alertas
│   ├── api/                # FastAPI modular
│   │   ├── routes/         # Rotas genéricas
│   │   ├── middleware/     # Auth, logging, multi-tenancy
│   │   └── schemas/        # Pydantic models canônicos
│   ├── persistence/        # Camada de dados abstrata
│   │   ├── repositories/   # Interfaces de repo
│   │   ├── adapters/       # JSON, SQL, etc.
│   │   └── schemas/        # Schemas de armazenamento
│   └── config/             # Configuração do kernel
│       ├── settings.py     # Settings base
│       ├── themes.py       # Sistema de temas
│       └── extensions.py   # Registro de extensões
├── instances/              # Exemplos de instâncias (dev apenas)
│   └── sample-instance/    # Instância de exemplo para testes
├── tests/
├── docs/
└── pyproject.toml
```

#### 2.2 Design do Sistema de Configuração
- [ ] Definir formato de configuração de instância (YAML/JSON)
- [ ] Especificar schema de configuração obrigatória vs. opcional
- [ ] Projetar mecanismo de override de configurações
- [ ] Definir sistema de variáveis de ambiente para secrets

#### 2.3 Design do Sistema de Temas e Identidade Visual
- [ ] Criar especificação de tema (cores, fonts, logos, spacing)
- [ ] Definir contrato de customização de componentes UI
- [ ] Projetar sistema de white-label para frontend
- [ ] Especificar suporte a múltiplos idiomas (i18n)

#### 2.4 Design do Modelo de Dados Canonical
- [ ] Definir entidades core do DEVA:
  - `CyclicProduct` (produto cíclico genérico)
  - `ValuePromise` (valor prometido na venda)
  - `ValuePerception` (valor percebido ao longo do ciclo)
  - `DecisionMatrix` (matriz de decisão configurável)
  - `EvolutionRadar` (radar de evolução parametrizável)
  - `CommandCenter` (centro de comando agnóstico)
  - `Cycle` (instância de consumo de um produto por um cliente)
  - `Stakeholder` (provedor e consumidor, agnósticos)
- [ ] Especificar relacionamentos e cardinalidades
- [ ] Definir eventos de domínio (ValueAligned, GapDetected, CycleRenewed, etc.)

#### 2.5 Design da API do Kernel
- [ ] Especificar endpoints genéricos com parâmetros de instanciação
- [ ] Definir contratos de autenticação e autorização multi-tenant
- [ ] Projetar sistema de versionamento de API
- [ ] Especificar webhooks e integrações extensíveis

#### 2.6 Design da Estratégia de Extensão
- [ ] Definir pontos de extensão (extension points)
- [ ] Especificar API para plugins/customizações
- [ ] Projetar sistema de hooks para lógica customizada
- [ ] Definir limites do que pode/m deve ser customizado

### Deliverables da Fase 2
- 📄 `reports/architecture/kernel-structure-spec.md` - Especificação da estrutura
- 📄 `reports/architecture/configuration-system-design.md` - Design do sistema de configuração
- 📄 `reports/architecture/theming-system-spec.md` - Especificação de temas e white-label
- 📄 `reports/architecture/canonical-data-model.md` - Modelo de dados canônico completo
- 📄 `reports/architecture/api-contract-spec.md` - Contrato de API do kernel
- 📄 `reports/architecture/extension-mechanism-design.md` - Design de extensões
- 📄 `reports/architecture/multi-tenancy-strategy.md` - Estratégia de multi-tenancy
- 📊 `reports/architecture/component-diagram.png` - Diagrama de componentes (se aplicável)

### Critérios de Aceite
- ✅ Arquitetura aprovada para suportar múltiplas instâncias
- ✅ Modelo de dados canônico cobre todos os casos de uso identificados
- ✅ Mecanismos de configuração permitem customização sem modificar o kernel
- ✅ Estratégia de white-label definida para frontend e backend

---

## Fase 3: Refatoração e Extração do Kernel

### Objetivo
Implementar fisicamente a separação entre kernel e instância, criando:
1. Novo repositório `deva-core` com o kernel genérico
2. Branch/refatoração do repositório atual como instância de exemplo

### Atividades

#### 3.1 Criação do Repositório deva-core
- [ ] Inicializar novo repositório Git `deva-core`
- [ ] Configurar estrutura de diretórios conforme Fase 2
- [ ] Setup de tooling (pyproject.toml, linting, testing, CI/CD)
- [ ] Configurar ambiente de desenvolvimento local

#### 3.2 Migração do Domain Layer
- [ ] Extrair entidades de domínio para `deva-core/src/core/domain/`
- [ ] Generalizar atributos específicos (remover hardcoded de "mentoria", "médico", etc.)
- [ ] Implementar modelo canonical definido na Fase 2
- [ ] Criar factories builders para entidades
- [ ] Implementar value objects e enums genéricos

#### 3.3 Migração dos Serviços de Negócio
- [ ] Extrair serviços para `deva-core/src/core/services/`
- [ ] Parametrizar regras de negócio (tornar thresholds configuráveis)
- [ ] Generalizar cálculos de KPIs e métricas
- [ ] Implementar motor de Gap de Valor agnóstico
- [ ] Criar interfaces para serviços extensíveis

#### 3.4 Migração da Camada de API
- [ ] Reimplementar rotas FastAPI no kernel
- [ ] Tornar endpoints agnósticos via parâmetros de instância
- [ ] Implementar middleware de multi-tenancy
- [ ] Criar schemas Pydantic canônicos
- [ ] Implementar sistema de versionamento de API

#### 3.5 Migração da Camada de Persistência
- [ ] Criar camada de abstração de repositórios
- [ ] Implementar adaptador JSON (para compatibilidade com legado)
- [ ] Projetar interfaces para futuros adaptadores (SQL, NoSQL)
- [ ] Implementar sistema de migração de dados entre versões
- [ ] Criar repositórios canônicos para todas as entidades

#### 3.6 Migração do Frontend (React)
- [ ] Criar pacote npm `@deva/core-ui` ou similar
- [ ] Extrair componentes genéricos para biblioteca compartilhável
- [ ] Implementar sistema de temas (CSS variables, styled-components, etc.)
- [ ] Criar HOCs/hooks para injeção de configuração de instância
- [ ] Generalizar textos e labels (preparar para i18n)
- [ ] Remover referências hardcoded a logos, cores, identidades
- [ ] Criar componentes de layout configuráveis

#### 3.7 Implementação do Sistema de Configuração
- [ ] Implementar loader de configuração (YAML/JSON)
- [ ] Criar schema de validação de configuração
- [ ] Implementar sistema de override e merge de configs
- [ ] Criar configuração de exemplo para instância do cliente atual
- [ ] Implementar detecção de configuração inválida

#### 3.8 Implementação do Sistema de Temas
- [ ] Criar engine de aplicação de temas no backend (API responses)
- [ ] Implementar sistema de temas no frontend (CSS, assets)
- [ ] Criar tema de exemplo baseado na instância atual do cliente
- [ ] Documentar processo de criação de novos temas

### Deliverables da Fase 3
- 📦 Repositório `deva-core` funcional com kernel completo
- 📦 Branch/refatoração da instância do cliente apontando para o kernel
- 📄 `docs/migration-guide.md` - Guia de migração de instâncias existentes
- 📄 `docs/configuration-reference.md` - Referência completa de configuração
- 📄 `docs/theming-guide.md` - Guia de criação de temas
- 🧪 Suite de testes do kernel com >80% de coverage
- 🧪 Tests de integração kernel-instância

### Critérios de Aceite
- ✅ Kernel funciona independentemente de qualquer instância específica
- ✅ Instância do cliente atual funciona apontando para o kernel
- ✅ Todos os testes passam em ambos os repositórios
- ✅ Configuração permite customizar comportamento sem modificar código do kernel
- ✅ Tema do cliente é aplicado via configuração, não hardcoded

---

## Fase 4: Validação e Testes

### Objetivo
Validar que o kernel DEVA e a instância do cliente funcionam corretamente, isoladamente e integrados.

### Atividades

#### 4.1 Testes Unitários do Kernel
- [ ] Cobrir todas as entidades de domínio
- [ ] Testar todos os serviços e cálculos de métricas
- [ ] Validar schemas de API e serialização
- [ ] Testar adaptadores de persistência
- [ ] Validar sistema de configuração e temas

#### 4.2 Testes de Integração
- [ ] Testar fluxo completo: API → Serviço → Persistência
- [ ] Validar multi-tenancy (múltiplas instâncias simultâneas)
- [ ] Testar cenários de configuração inválida
- [ ] Validar webhooks e extensões

#### 4.3 Testes End-to-End da Instância
- [ ] Reprodzir todos os casos de uso do cliente atual
- [ ] Validar que métricas e KPIs são calculados corretamente
- [ ] Testar UI com tema do cliente aplicado
- [ ] Validar fluxos de decisão e alertas

#### 4.4 Testes de Performance
- [ ] Benchmark de operações críticas
- [ ] Testar com volume de dados realista
- [ ] Validar tempos de resposta da API
- [ ] Identificar gargalos de performance

#### 4.5 User Acceptance Testing (UAT)
- [ ] Validar com stakeholders que a funcionalidade está preservada
- [ ] Coletar feedback sobre usabilidade da instância
- [ ] Verificar se Gap de Valor está sendo calculado corretamente
- [ ] Validar relatórios e dashboards

### Deliverables da Fase 4
- 📊 `reports/testing/unit-tests-coverage-report.md` - Relatório de coverage
- 📊 `reports/testing/integration-tests-results.md` - Resultados de integração
- 📊 `reports/testing/e2e-validation-report.md` - Validação E2E
- 📊 `reports/testing/performance-benchmark.md` - Benchmark de performance
- 📊 `reports/testing/uat-feedback-summary.md` - Resumo de feedback UAT
- ✅ Todos os testes críticos passando
- ✅ Performance dentro de SLAs definidos

### Critérios de Aceite
- ✅ Coverage de testes unitários >80%
- ✅ 100% dos casos de uso do cliente validados
- ✅ Performance equivalente ou superior à versão original
- ✅ Zero regressões funcionais identificadas
- ✅ UAT aprovado pelos stakeholders

---

## Fase 5: Documentação e Preparação para Novas Instâncias

### Objetivo
Produzir documentação completa e ferramentas para facilitar a criação de novas instâncias do DEVA.

### Atividades

#### 5.1 Documentação Técnica do Kernel
- [ ] Documentar arquitetura e decisões de design (ADR)
- [ ] Criar guia de contribuição para o kernel
- [ ] Documentar API completa (OpenAPI/Swagger)
- [ ] Criar tutoriais de desenvolvimento local
- [ ] Documentar processos de release e versionamento

#### 5.2 Documentação para Criadores de Instâncias
- [ ] Criar guia "Getting Started" para nova instância
- [ ] Documentar processo de configuração passo-a-passo
- [ ] Criar template de configuração para copiar/colar
- [ ] Documentar processo de criação de tema customizado
- [ ] Criar exemplos de extensões e customizações
- [ ] Documentar limitações e melhores práticas

#### 5.3 Criação de Templates e Boilerplates
- [ ] Criar template de repositório para nova instância
- [ ] Desenvolver CLI para scaffolding de instâncias (opcional)
- [ ] Criar repositório de exemplo completo
- [ ] Desenvolver scripts de migração de dados
- [ ] Criar templates de configuração para cenários comuns

#### 5.4 Documentação Operacional
- [ ] Criar guia de deploy do kernel
- [ ] Documentar estratégias de hospedagem (Docker, K8s, serverless)
- [ ] Criar runbooks de operação e monitoramento
- [ ] Documentar backup e recovery
- [ ] Criar checklist de go-live para nova instância

#### 5.5 Material de Treinamento
- [ ] Criar apresentação conceitual do DEVA
- [ ] Desenvolver workshop de onboarding para novos times
- [ ] Criar vídeos tutoriais (setup, configuração, customização)
- [ ] Desenvolver FAQs e troubleshooting guide

### Deliverables da Fase 5
- 📚 `deva-core/docs/` - Documentação técnica completa
- 📚 `docs/instance-creator-guide.md` - Guia para criadores de instâncias
- 📚 `docs/configuration-template.yaml` - Template de configuração
- 📚 `docs/theming-starter-kit/` - Kit inicial para temas
- 🛠️ `templates/instance-boilerplate/` - Boilerplate de nova instância
- 🛠️ (Opcional) `deva-cli` - Ferramenta de scaffolding
- 📹 Materiais de treinamento e onboarding

### Critérios de Aceite
- ✅ Nova instância pode ser criada em < 1 dia seguindo a documentação
- ✅ Documentação revisada e aprovada por terceiros
- ✅ Templates testados e funcionais
- ✅ Pelo menos uma pessoa externa consegue criar instância de teste sem ajuda

---

## Fase 6: Separação Final e Go-Live

### Objetivo
Executar a separação definitiva entre kernel e instância, preparando ambos para produção independente.

### Atividades

#### 6.1 Limpeza e Polimento Final
- [ ] Remover código morto e comentários de TODO antigos
- [ ] Refatorar code smells identificados durante o processo
- [ ] Padronizar naming conventions em ambos os repositórios
- [ ] Otimizar imports e dependências
- [ ] Revisar logs e mensagens de erro

#### 6.2 Setup de CI/CD Independente
- [ ] Configurar pipelines CI/CD para `deva-core`
- [ ] Configurar pipelines CI/CD para instância do cliente
- [ ] Implementar versionamento semântico automático
- [ ] Configurar publicação de pacotes (npm, PyPI se aplicável)
- [ ] Setup de ambientes de staging e production

#### 6.3 Estratégia de Versionamento
- [ ] Definir política de versionamento do kernel (SemVer)
- [ ] Definir compatibilidade entre versões do kernel e instâncias
- [ ] Criar matriz de compatibilidade documentada
- [ ] Implementar deprecation warnings para APIs antigas
- [ ] Definir política de LTS (Long Term Support)

#### 6.4 Plano de Migração da Instância Existente
- [ ] Criar branch `legacy` no repositório atual (backup)
- [ ] Renomear branch principal para refletir nova arquitetura
- [ ] Atualizar README e documentação do repositório da instância
- [ ] Comunicar mudanças para stakeholders
- [ ] Agendar janela de deploy em produção

#### 6.5 Monitoramento e Observabilidade
- [ ] Implementar logging estruturado no kernel
- [ ] Configurar métricas de saúde do sistema
- [ ] Setup de alertas para erros críticos
- [ ] Implementar tracing distribuído (se aplicável)
- [ ] Criar dashboards de monitoramento

#### 6.6 Go-Live
- [ ] Deploy do kernel em ambiente de produção
- [ ] Deploy da instância refactorada em produção
- [ ] Monitoramento intensivo pós-deploy
- [ ] Rollback plan pronto se necessário
- [ ] Comunicação oficial de lançamento

### Deliverables da Fase 6
- ✅ Repositório `deva-core` publicado e versionado (v1.0.0)
- ✅ Repositório da instância do cliente separado e funcional
- ✅ CI/CD operacional em ambos os repositórios
- ✅ Monitoramento e alertas configurados
- ✅ Plano de rollback documentado e testado
- ✅ Comunicação de lançamento enviada
- ✅ Post-mortem da migração documentado

### Critérios de Aceite
- ✅ Kernel publicado como v1.0.0 com tag Git
- ✅ Instância do cliente operando em produção sem issues
- ✅ Zero downtime durante a migração (ou dentro da janela planejada)
- ✅ Métricas de performance e erro dentro do baseline anterior
- ✅ Stakeholders informados e satisfeitos

---

## Cronograma Estimado

| Fase | Duração Estimada | Dependências |
|------|------------------|--------------|
| Fase 1: Inventário e Mapeamento | 3-5 dias | Nenhuma |
| Fase 2: Design da Arquitetura | 5-7 dias | Fase 1 concluída |
| Fase 3: Refatoração e Extração | 10-15 dias | Fase 2 aprovada |
| Fase 4: Validação e Testes | 5-7 dias | Fase 3 concluída |
| Fase 5: Documentação | 3-5 dias | Paralelo às Fases 3-4 |
| Fase 6: Separação e Go-Live | 3-5 dias | Fases 1-5 concluídas |

**Total Estimado:** 29-44 dias úteis (~6-9 semanas)

---

## Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Perda de funcionalidade durante refatoração | Alto | Média | Testes abrangentes, UAT antecipado, rollback plan |
| Complexidade subestimada do kernel | Médio | Alta | Iterações curtas, validação contínua da arquitetura |
| Resistência do cliente a mudanças | Médio | Baixa | Comunicação clara, demonstração de benefícios, zero impacto percebido |
| Vazamento de lógica específica para o kernel | Alto | Média | Revisões de código rigorosas, checklist de generalização |
| Performance degradada no kernel | Médio | Baixa | Benchmarks contínuos, otimizações iterativas |
| Documentação incompleta | Médio | Alta | Revisão por terceiros, teste com usuários reais |

---

## Próximos Passos Imediatos

1. **Aprovação deste plano** pelo solicitante
2. **Início da Fase 1** - Inventário e Mapeamento Detalhado
3. **Setup de tracking** - Criar issues/tasks para cada atividade
4. **Definição de checkpoints** - Reuniões de validação ao final de cada fase

---

## Glossário

- **DEVA:** Kernel genérico do Sistema de Apoio à Decisão para redução do Gap de Valor
- **Gap de Valor:** Distância entre valor prometido na venda e valor percebido durante o consumo
- **Instância:** DEVA configurado para um cliente e produto específicos (DEVA[Cliente][Produto])
- **Kernel:** Núcleo genérico e agnóstico do DEVA
- **Cyclic Product:** Produto com ciclo de consumo definido (mentoria, plano médico, consultoria)
- **Multi-tenancy:** Capacidade do kernel de servir múltiplas instâncias isoladas
- **White-label:** Personalização completa de identidade visual por instância

---

*Documento criado para aprovação do plano de extração do kernel DEVA.*
*Versão: 1.0*
*Data: $(date)*