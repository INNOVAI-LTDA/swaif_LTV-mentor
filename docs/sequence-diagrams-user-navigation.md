# Sequence Diagrams - User Navigation

Date: 2026-03-21

## Objetivo

Documentar os fluxos de navegacao por tipo de usuario no frontend atual, com foco nas telas efetivamente usadas no roteamento e nas guardas de autenticacao e autorizacao.

## Arquivos de referencia

- Roteamento principal: `frontend/src/app/routes.tsx`
- Redirecionamento por papel: `frontend/src/shared/auth/roleRouting.ts`
- Sessao e autenticacao: `frontend/src/app/providers/AuthProvider.tsx`
- Shell comum: `frontend/src/app/layout/AppLayout.tsx`

## Diretorio das telas

| Tela | Caminho |
| ---- | ------- |
| Login | `frontend/src/pages/LoginPage.tsx` |
| Acesso negado | `frontend/src/pages/AccessDeniedPage.tsx` |
| Admin | `frontend/src/features/admin/pages/AdminPage.tsx` |
| Aluno | `frontend/src/features/student/pages/StudentPage.tsx` |
| Hub interno mentor | `frontend/src/features/hub/pages/HubPage.tsx` |
| Centro de comando | `frontend/src/features/command-center/pages/CommandCenterPage.tsx` |
| Radar | `frontend/src/features/radar/pages/RadarPage.tsx` |
| Matriz de renovacao | `frontend/src/features/matrix/pages/MatrixPage.tsx` |
| Shell comum | `frontend/src/app/layout/AppLayout.tsx` |
| Pagina nao encontrada | `frontend/src/pages/NotFoundPage.tsxfrontend/src/pages/NotFoundPage.tsx` |

## 1. Usuario anonimo

```mermaid
sequenceDiagram
    actor U as Usuario
    participant L as LoginPage
    participant A as AuthProvider
    participant R as Router

    U->>L: Abre /login
    L->>A: consultar estado de sessao
    A-->>L: sem sessao valida
    U->>R: tenta abrir /app/*
    R->>A: validar autenticacao
    A-->>R: isAuthenticated = false
    R-->>L: redireciona para /login
```

Telas envolvidas:
- `frontend/src/pages/LoginPage.tsx`

## 2. Usuario Admin

```mermaid
sequenceDiagram
    actor U as Admin
    participant L as LoginPage
    participant A as AuthProvider
    participant R as Router
    participant P as AdminPage

    U->>L: informa usuario/senha
    L->>A: login(email, senha)
    A->>A: autentica + valida /me
    A-->>L: user.role = admin
    L->>R: navigate(/app/admin)
    R->>A: RequireAuth + RequireAdmin
    A-->>R: autorizado
    R-->>P: renderiza tela administrativa
```

Telas envolvidas:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/features/admin/pages/AdminPage.tsx`

## 3. Usuario Aluno

```mermaid
sequenceDiagram
    actor U as Aluno
    participant L as LoginPage
    participant A as AuthProvider
    participant R as Router
    participant P as StudentPage

    U->>L: inicia sessao de aluno
    L->>A: login real ou loginPreview(aluno)
    A-->>L: user.role = aluno
    L->>R: navigate(/app/aluno)
    R->>A: RequireAuth
    A-->>R: autorizado
    R-->>P: renderiza tela do aluno
```

Telas envolvidas:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/features/student/pages/StudentPage.tsx`

## 4. Usuario Mentor interno

Observacao:
- este fluxo so existe quando `VITE_ENABLE_INTERNAL_MENTOR_DEMO=true`
- o objetivo atual e validacao interna local, nao superficie publicada ao cliente

```mermaid
sequenceDiagram
    actor U as Mentor
    participant L as LoginPage
    participant A as AuthProvider
    participant R as Router
    participant M as MatrixPage

    U->>L: faz login como mentor
    L->>A: login(email, senha)
    A-->>L: user.role = mentor
    L->>R: navigate(/app/matriz-renovacao)
    R->>A: RequireAuth + RequireInternalMentorWorkspace
    A-->>R: mentor interno habilitado
    R-->>M: renderiza matriz de renovacao
```

Telas envolvidas:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/features/matrix/pages/MatrixPage.tsx`

## 5. Mentor com superficie interna desligada

```mermaid
sequenceDiagram
    actor U as Mentor
    participant L as LoginPage
    participant A as AuthProvider
    participant R as Router
    participant D as AccessDeniedPage

    U->>L: autentica como mentor
    L->>A: login(email, senha)
    A-->>L: user.role = mentor
    L->>R: navigate(/app/acesso-negado)
    R->>A: RequireAuth
    A-->>R: sessao valida, mas mentor interno desligado
    R-->>D: renderiza acesso negado
```

Telas envolvidas:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/AccessDeniedPage.tsx`

## 6. Usuario autenticado sem permissao administrativa

```mermaid
sequenceDiagram
    actor U as Usuario autenticado
    participant R as Router
    participant A as AuthProvider
    participant D as AccessDeniedPage

    U->>R: abre /app/admin
    R->>A: RequireAuth + RequireAdmin
    A-->>R: autenticado, mas role != admin
    R-->>D: renderiza acesso negado
```

Telas envolvidas:
- `frontend/src/pages/AccessDeniedPage.tsx`

## 7. Navegacao interna do mentor

```mermaid
sequenceDiagram
    actor U as Mentor
    participant S as AppLayout
    participant R as Router
    participant H as HubPage
    participant C as CommandCenterPage
    participant P as RadarPage
    participant M as MatrixPage

    U->>S: usa menu superior
    S->>R: /app/hub-interno
    R-->>H: Hub interno
    U->>S: clica Centro
    S->>R: /app/centro-comando
    R-->>C: Centro de comando
    U->>S: clica Radar
    S->>R: /app/radar
    R-->>P: Radar
    U->>S: clica Matriz
    S->>R: /app/matriz-renovacao
    R-->>M: Matriz
```

Telas envolvidas:
- `frontend/src/app/layout/AppLayout.tsx`
- `frontend/src/features/hub/pages/HubPage.tsx`
- `frontend/src/features/command-center/pages/CommandCenterPage.tsx`
- `frontend/src/features/radar/pages/RadarPage.tsx`
- `frontend/src/features/matrix/pages/MatrixPage.tsx`

## 8. Recuperacao de sessao apos falha temporaria

```mermaid
sequenceDiagram
    actor U as Usuario
    participant L as LoginPage
    participant A as AuthProvider
    participant API as Backend /me
    participant R as Router

    U->>L: envia login
    L->>A: login(email, senha)
    A->>API: validar perfil autenticado
    API-->>A: falha temporaria
    A-->>L: sessionRecoveryPending = true
    L-->>U: exibe banner de recuperacao
    U->>L: Tentar novamente
    L->>A: retrySessionValidation()
    A->>API: nova validacao de /me
    API-->>A: perfil valido
    A-->>R: sessao autenticada pronta
    R-->>U: libera rota da role
```

Telas envolvidas:
- `frontend/src/pages/LoginPage.tsx`

## Resumo operacional atual

- `Admin` e a superficie principal publicada.
- `Aluno` segue como rota funcional no app.
- `Mentor` permanece isolado do caminho publicado e depende de flag local explicita.
- `Acesso negado` e a tela padrao para bloqueios de papel ou de superficie nao publicada.
- O shell comum concentra a navegacao de alto nivel e oculta links conforme o papel e a flag de ambiente.
