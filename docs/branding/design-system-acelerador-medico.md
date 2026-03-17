# Design System Inicial — Cliente Acelerador Médico

Este documento consolida uma primeira extração prática da identidade visual observada nos assets enviados pelo cliente e serve como fonte de verdade para o Codex na fase de validação visual das telas.

## 1. Objetivo

Evitar que o Codex invente uma identidade visual nova.

A proposta é usar:
- os logos enviados pelo cliente
- os ícones enviados pelo cliente
- os prints de referência
- a linguagem visual do site de referência

para orientar a V1 visual da demo.

## 2. Assets disponíveis

### Logos
- `logo v1.png`
- `logo v2.png`
- `logo v3.png`
- `logo v4.png`
- `logo v5.png`

### Ícones
- `ícone v1.png`
- `ícone v2.png`
- `ícone v3.png`
- `ícone v4.png`

### Referências visuais
- `examplos_id_vis_01.png`
- `examplos_id_vis_02.png`
- `examplos_id_vis_03.png`

### Referência web
- `https://aceleradormedico.com.br/`

## 3. Direção visual observada

A linguagem visual percebida é:
- premium
- escura
- orientada a performance
- forte contraste
- dourado como cor de destaque
- branco como cor de leitura
- superfícies em grafite/preto

Essa estética comunica:
- autoridade
- resultado
- alta percepção de valor
- posicionamento executivo

## 4. Paleta recomendada

### Cores base

| Token | Hex | Uso recomendado |
|---|---|---|
| `bg-primary` | `#090909` | fundo principal da aplicação |
| `bg-secondary` | `#121212` | variação de fundo |
| `surface-primary` | `#1A1A1A` | cards, paineis, caixas |
| `surface-secondary` | `#242424` | hover, blocos internos |
| `border-default` | `#333333` | bordas |
| `text-primary` | `#FFFFFF` | texto principal |
| `text-secondary` | `#BFBFBF` | texto secundário |
| `accent-primary` | `#FAB800` | destaques, CTA, ícones ativos |
| `accent-secondary` | `#FFBD00` | hover/variações do destaque |
| `danger` | `#D64545` | alertas críticos |
| `success` | `#39B56A` | confirmação/sucesso |
| `warning` | `#D9A100` | avisos |

### CSS tokens sugeridos

```css
:root {
  --color-bg-primary: #090909;
  --color-bg-secondary: #121212;

  --color-surface-primary: #1A1A1A;
  --color-surface-secondary: #242424;

  --color-border-default: #333333;

  --color-text-primary: #FFFFFF;
  --color-text-secondary: #BFBFBF;

  --color-accent-primary: #FAB800;
  --color-accent-secondary: #FFBD00;

  --color-danger: #D64545;
  --color-success: #39B56A;
  --color-warning: #D9A100;
}
```

## 5. Tipografia sugerida

Sem depender de inspeção completa do CSS do site, a recomendação segura é usar:
- `"Montserrat", "Inter", sans-serif`

### Hierarquia sugerida

| Elemento | Peso | Tamanho sugerido |
|---|---:|---:|
| Título principal | 700 | 28–36px |
| Título de seção | 600 | 20–24px |
| Subtítulo | 500 | 16–18px |
| Texto normal | 400 | 14–16px |
| Legenda/auxiliar | 400 | 12–13px |

## 6. Componentes-base

### 6.1 Botão primário

Papel: CTA principal

```css
.button-primary {
  background: #FAB800;
  color: #000000;
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-weight: 600;
}
```

Diretrizes:
- usar em ações principais
- não exagerar na quantidade de botões primários na mesma tela
- hover pode usar `#FFBD00`

### 6.2 Botão secundário

Papel: ação complementar

```css
.button-secondary {
  background: transparent;
  color: #FAB800;
  border: 1px solid #FAB800;
  border-radius: 8px;
  padding: 10px 18px;
  font-weight: 500;
}
```

### 6.3 Input / campo de texto

```css
.input-field {
  background: #1A1A1A;
  color: #FFFFFF;
  border: 1px solid #333333;
  border-radius: 6px;
  padding: 10px 12px;
}
```

Diretrizes:
- placeholder em cinza médio
- borda de foco em dourado

### 6.4 Card / caixa de conteúdo

```css
.card {
  background: #1A1A1A;
  border: 1px solid #333333;
  border-radius: 10px;
  padding: 20px;
}
```

Diretrizes:
- sombra muito discreta
- priorizar separação por contraste e espaçamento

### 6.5 Sidebar

Direção visual:
- fundo escuro
- item ativo com destaque dourado
- ícone do cliente visível no topo
- logo completo opcionalmente no header principal

### 6.6 Tabelas / grids de dados

Direção visual:
- cabeçalho em superfície mais escura
- texto principal branco
- texto auxiliar cinza
- linhas com separação sutil
- chips de status usando accent/warning/danger/success

## 7. Uso do logo e do ícone

### Logo completo
Usar em:
- tela de login
- header principal
- páginas institucionais internas, se houver

### Ícone
Usar em:
- sidebar
- favicon
- áreas compactas de navegação

### Regras
- não recriar nem reinterpretar o logo
- não inventar novos ícones de marca
- usar os assets enviados como fonte oficial

## 8. Diretrizes por tela

### 8.1 Login
Objetivo visual:
- causar boa primeira impressão
- parecer premium
- manter simplicidade

Blocos sugeridos:
- logo
- título curto
- formulário
- CTA principal

Opcional:
- imagem ou textura de fundo derivada da identidade

### 8.2 Mentor
Objetivo visual:
- visão executiva
- foco em clareza, performance e decisão

Blocos sugeridos:
- KPIs no topo
- navegação para Matriz / Centro / Radar
- cards de resumo
- lista/tabela de alunos
- blocos bem espaçados

### 8.3 Aluno
Objetivo visual:
- visão mais pessoal
- foco em progresso, trajetória e leitura individual

Blocos sugeridos:
- radar como peça central
- timeline/jornada
- indicadores
- visão limpa e menos densa do que a do mentor

### 8.4 Admin
Objetivo visual:
- eficiência operacional
- organização de dados
- clareza de CRUD e ingestão

Blocos sugeridos:
- abas bem definidas
- tabelas
- formulários
- ações claras
- hierarquia bem forte para não parecer confuso

## 9. Espaçamento e ritmo visual

### Recomendações
- grid com espaçamento generoso
- usar 8px como unidade-base
- padding de cards entre 16 e 24px
- gaps de seções entre 20 e 32px

### Evitar
- excesso de bordas pesadas
- excesso de dourado
- excesso de elementos competindo por atenção

O dourado deve funcionar como sinal de importância, não como tinta jogada na parede inteira.

## 10. Regras para o Codex

Use este bloco como instrução operacional:

```text
Use este documento como fonte de verdade visual.

Regras:
- não inventar uma identidade nova
- usar os assets enviados pelo cliente
- usar a paleta descrita neste design system
- preservar a assinatura visual base da plataforma
- adaptar branding sem redesenhar o produto do zero
- manter consistência entre Login, Mentor, Aluno e Admin
- se houver dúvida de aplicação visual, priorizar:
  1. legibilidade
  2. contraste
  3. hierarquia
  4. sobriedade premium
```

## 11. Próximos entregáveis sugeridos

Depois deste documento, o próximo passo ideal é pedir ao Codex:
1. `client-branding-spec.md`
2. tela de Login
3. tela do Mentor
4. tela do Aluno
5. tela do Admin
6. auditoria visual consolidada

## 12. Sugestão de localização

```text
docs/design-system-client.md
```

ou, se quiser estruturar melhor:

```text
docs/branding/acelerador-medico-design-system.md
```
