# Runbook - Login local de aluno no backend MVP

## Objetivo

Documentar o menor fluxo seguro para validar login de `aluno` em ambiente local,
sem alterar regras de autenticacao nem contratos da API.

## Contexto tecnico

- O backend autentica usuarios a partir de `backend/data/users.json`.
- O contexto de aluno e resolvido por email: o email autenticado deve corresponder
  a um `student` ativo com matricula ativa.
- O papel `client` e normalizado para `aluno` no endpoint `/me`.
- Se o aluno existir em `students.json` e tentar login com a senha padrao
  `aluno_accmed`, o backend cria automaticamente o usuario de autenticacao
  com role `aluno` no primeiro login.

## Passo 1 - Escolher um aluno ativo existente

Use um `student` ativo ja presente em `backend/data/students.json` e confirme que
existe uma matricula ativa correspondente em `backend/data/enrollments.json`.

## Passo 2 - Usar a senha padrao no primeiro login

Senha padrao para primeiro acesso de aluno:

`aluno_accmed`

## Passo 3 - Autenticar

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<email_do_student_ativo>","password":"aluno_accmed"}'
```

## Passo 4 - Validar sessao e role

```bash
curl -s http://127.0.0.1:8000/me \
  -H "Authorization: Bearer <access_token>"
```

Resposta esperada: `role` canônica em `aluno`.

## Passo 5 - Validar endpoint protegido do aluno

```bash
curl -s http://127.0.0.1:8000/aluno/workspace/radar \
  -H "Authorization: Bearer <access_token>"
```

## Falhas comuns

- `ALUNO_CONTEXT_NOT_FOUND`: email autenticado sem `student` ativo correspondente.
- Contexto ambiguo: mais de um `student` ativo com o mesmo email.
- Matricula inativa para o `student` encontrado.

## Limpeza recomendada apos o teste

Remover o usuario de teste de `backend/data/users.json` quando o cenário local
for concluido.
