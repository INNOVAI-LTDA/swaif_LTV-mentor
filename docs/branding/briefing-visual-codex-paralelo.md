# Briefing Visual para Codex + Estratégia de Execução em Paralelo

## 1. Objetivo desta fase

Validar visualmente a nova versão do MVP para o cliente, antes de implementar backend real para os novos perfis.

Nesta fase, o foco é:
- branding do cliente
- coerência visual
- hierarquia das telas
- posicionamento das informações
- sensação premium
- clareza por perfil

## 2. Regras da fase atual

- Pode usar dados simulados ou hard-coded
- Não implementar backend novo ainda
- Não integrar autenticação real ainda
- Não sofisticar CRUD ainda
- Não redesenhar o produto do zero
- Preservar a assinatura visual da plataforma
- Cada etapa deve terminar em algo que possa ser aberto, avaliado e validado

---

## 3. Prompt-base de governança para o Codex

```text
Premissas obrigatórias desta execução:

1. Esta fase é APENAS de validação visual.
2. Pode usar dados simulados/hard-coded, se necessário.
3. Não implementar backend novo nesta fase.
4. Não integrar autenticação real nesta fase.
5. Não alterar a estrutura principal da plataforma.
6. Cada etapa deve resultar em uma entrega consumível e avaliável.
7. Antes de começar a tarefa:
   - registrar task_id
   - registrar task_title
   - registrar started_at
8. Ao finalizar:
   - registrar finished_at
   - registrar status
   - registrar summary
   - registrar artifacts
9. Não calcular duração.
10. Se houver dúvida, preservar simplicidade e legibilidade.
```

---

## 4. Prompt 1 — Especificação visual da skin

```text
Quero iniciar a próxima evolução da demo atual, mas nesta fase o foco é APENAS validar visualmente as novas telas do cliente antes de implementar backend real.

Contexto:
- a demo atual já possui backend e frontend funcionais
- o cliente forneceu identidade visual com logos, ícones e referências visuais
- a estrutura principal da plataforma deve ser preservada
- o núcleo do produto não muda
- esta fase é de validação visual e funcional das novas superfícies

Referência de domínio:
- Cliente(Empresa) -> Produto(Mentoria) -> Mentor -> Aluno
- Produto(Mentoria) -> Pilar -> Métrica

Perfis que precisam existir nesta fase:
1. Admin
2. Mentor
3. Aluno

Telas que precisam ser especificadas:
1. Login
2. Mentor
3. Aluno
4. Admin

Objetivo desta fase:
- validar branding
- validar paleta
- validar layout
- validar hierarquia visual
- validar organização das informações
- validar coerência entre perfis
- permitir uso de dados simulados/hard-coded

Regras:
- não implementar backend novo ainda
- não integrar autenticação real ainda
- não sofisticar CRUD ainda
- não redesenhar o sistema do zero
- preservar a assinatura visual da plataforma
- adaptar a skin para o cliente

Antes de implementar qualquer tela:
1. analisar os assets de branding do cliente
2. propor paleta principal/secundária/acento
3. propor aplicação de logo e ícone
4. listar os blocos visuais de cada tela
5. gerar um plano visual incremental

Entregas esperadas:
- docs/client-branding-spec.md
- docs/roles-and-access-visual-spec.md
- docs/ui-validation-plan.md

Não implementar ainda.
```

---

## 5. Prompt 2 — Tela de Login

```text
Implemente apenas a tela de Login para validação visual.

Objetivo:
- aplicar a identidade visual do cliente
- criar uma experiência de entrada premium e coerente com a marca
- capturar usuário e senha
- permitir simulação de entrada por perfil para fins de validação visual

Regras:
- usar dados simulados
- não integrar autenticação real ainda
- focar em layout, contraste, legibilidade e branding
- preservar o estilo-base da plataforma

Antes de alterar arquivos:
1. mostrar plano resumido
2. registrar started_at no log de execução

Ao final:
1. registrar finished_at
2. gerar um relatório curto da tela

Saídas esperadas:
- tela de login navegável
- docs/ui-login-report.md
```

---

## 6. Prompt 3 — Tela do Mentor

```text
Implemente apenas a tela do Mentor para validação visual.

Objetivo:
- reconstruir a experiência do mentor com branding do cliente
- preservar a assinatura visual da plataforma
- usar dados simulados coerentes
- validar a organização das visões:
  1) Matriz de Decisão
  2) Centro de Comando
  3) Radar de Evolução
- incluir também as áreas:
  - Produtos
  - Alunos
  - Usuário

Regras:
- não integrar backend real ainda
- não implementar RBAC real ainda
- usar mocks locais se necessário
- focar em design, hierarquia de informação e experiência visual

Antes de alterar arquivos:
1. mostrar plano resumido
2. registrar started_at

Ao final:
1. registrar finished_at
2. gerar relatório curto

Saídas esperadas:
- visão mentor navegável e validável
- docs/ui-mentor-report.md
```

---

## 7. Prompt 4 — Tela do Aluno

```text
Implemente apenas a tela do Aluno para validação visual.

Objetivo:
- criar uma experiência exclusiva do aluno
- destacar Radar de Evolução como visão principal
- apresentar linha do tempo de progresso
- apresentar painel de indicadores
- incluir áreas:
  - Produtos
  - Mentores
  - Usuário

Regras:
- usar dados simulados
- não integrar backend real ainda
- não implementar autenticação real ainda
- focar em clareza, leitura individual e narrativa de evolução

Antes de alterar arquivos:
1. mostrar plano resumido
2. registrar started_at

Ao final:
1. registrar finished_at
2. gerar relatório curto

Saídas esperadas:
- visão aluno navegável e validável
- docs/ui-student-report.md
```

---

## 8. Prompt 5 — Tela do Admin

```text
Implemente apenas a tela do Admin para validação visual.

Objetivo:
- representar a visão administrativa completa
- validar organização das abas e views
- permitir visualizar como ficará a operação administrativa antes do backend real

Escopo desta fase:
- Aba Cliente
- Aba Produtos
- Aba Mentores
- Aba Alunos
- Aba Operações
- Aba Usuário

Regras:
- usar dados simulados
- não implementar backend real ainda
- não implementar CRUD real ainda
- permitir placeholders coerentes para operações de Create/Update/Delete
- focar em organização visual, clareza operacional e hierarquia administrativa

Antes de alterar arquivos:
1. mostrar plano resumido
2. registrar started_at

Ao final:
1. registrar finished_at
2. gerar relatório curto

Saídas esperadas:
- visão admin navegável e validável
- docs/ui-admin-report.md
```

---

## 9. Prompt 6 — Auditoria visual das 4 telas

```text
Audite visualmente as telas implementadas:
- Login
- Mentor
- Aluno
- Admin

Objetivo:
- avaliar aplicação do branding
- avaliar clareza visual
- avaliar contraste
- avaliar coerência entre perfis
- avaliar hierarquia de informação
- identificar ajustes antes da fase de backend real

Regras:
- não implementar backend ainda
- não fazer refatorações grandes
- gerar apenas relatório e recomendações priorizadas

Saídas esperadas:
- docs/ui-visual-audit.md
- docs/ui-adjustments-priority.md
```

---

## 10. O que pode rodar em paralelo

### Pode rodar em paralelo com segurança
Se você usar tarefas independentes e, idealmente, worktrees/branches separados:

1. Tela do Aluno e Tela do Admin
   - são superfícies novas
   - não dependem diretamente uma da outra
   - podem nascer em paralelo se o design system já estiver congelado

2. Branding spec e roles/access visual spec
   - um define identidade visual
   - o outro define o recorte por perfil
   - andam em paralelo sem muito risco

3. Auditoria de assets e extração de design tokens
   - podem ocorrer juntas, desde que entreguem artefatos separados

### Melhor não rodar em paralelo
1. Login com as demais telas, se o layout de entrada ainda vai definir cabeçalho, logo, paleta e linguagem-base
2. Mentor junto com branding ainda indefinido
3. Qualquer etapa de backend real em paralelo com a fase visual
4. Auditoria visual final antes de concluir as quatro telas

---

## 11. Estratégia prática de paralelismo

### Opção mais segura
Rodar em sequência:
1. Branding spec
2. Login
3. Mentor
4. Aluno
5. Admin
6. Auditoria visual

### Opção mais eficiente
Rodar assim:
1. Branding spec + roles/access visual spec (paralelo)
2. Login (sozinho)
3. Mentor (sozinho, porque é a tela mais estratégica)
4. Aluno + Admin (paralelo)
5. Auditoria visual (sozinho)

---

## 12. O que diz a documentação do Codex sobre paralelo

A documentação oficial informa que você pode usar o Codex localmente no terminal/IDE e também delegar trabalho na nuvem; além disso, o app do Codex pode habilitar vários agentes em paralelo em diferentes projetos, e tarefas na nuvem rodam em sandboxes isolados. Isso é ótimo para paralelismo entre frentes independentes. Em compensação, para duas tarefas mexendo na mesma base e nos mesmos arquivos, a abordagem segura continua sendo separar por worktree/branch e só depois revisar/mesclar.

---

## 13. Recomendação final

Para esta fase visual, a melhor estratégia é:
- sequencial para branding, login e mentor
- paralelo controlado para aluno e admin
- sequencial para auditoria visual final

Isso minimiza conflito e mantém a etapa consumível, revisável e elegante.
