# Runbook - Login local de aluno no backend MVP

## Objetivo

Documentar o menor fluxo seguro para validar login de `aluno` em ambiente local,
sem alterar regras de autenticacao nem contratos da API.

## Contexto tecnico

- O backend autentica usuarios a partir de `backend/data/users.json`.
- O contexto de aluno e resolvido por email: o email autenticado deve corresponder
  a um `student` ativo com matricula ativa.
- O papel `client` e normalizado para `aluno` no endpoint `/me`.

## Passo 1 - Escolher um aluno ativo existente

Use um `student` ativo ja presente em `backend/data/students.json` e confirme que
existe uma matricula ativa correspondente em `backend/data/enrollments.json`.

## Passo 2 - Criar usuario de autenticacao para o mesmo email

No root do repositório, execute:

```bash
python - <<'PY'
from backend.app.storage.user_repository import UserRepository
from backend.app.core.security import hash_password

repo = UserRepository("backend/data/users.json")
repo.create(
    id="usr_local_aluno",
    email="<email_do_student_ativo>",
    password_hash=hash_password("<senha_temporaria_local>"),
    role="aluno",
    is_active=True,
)
print("usuario criado")
PY
```

Notas:

- Se o email ja existir em `users.json`, a criacao falha por duplicidade.
- Para manter compatibilidade legada, `role="client"` tambem funciona, pois o
  backend normaliza para `aluno`.

## Passo 3 - Autenticar

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<email_do_student_ativo>","password":"<senha_temporaria_local>"}'
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
