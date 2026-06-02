# Validacao Manual E2E - Provider Supabase Runtime

Data: 2026-05-29

## 1. Objetivo

Validar manualmente que os fluxos runtime A/B/C/D operam com Supabase e sem dependencia de JSON:

- A: Centro de Comando
- B: Radar
- C: Matriz
- D: Admin Database View

## 2. Pre-condicoes

- `SUPABASE_DB_URL` configurado.
- backend e frontend ativos.
- `SUPABASE_RUNTIME_REQUIRED=true` no ambiente de validacao.
- usuarios de teste ativos:
  - admin
  - provider A
  - provider B (controle de isolamento)

## 3. Script de subida recomendado

No root do repositorio:

```powershell
.\scripts\start-human-validation.ps1 -Install
```

Execucoes seguintes:

```powershell
.\scripts\start-human-validation.ps1
```

## 4. Roteiro de validacao

### 4.1 Admin

1. Fazer login como admin.
2. Abrir `GET /admin/database-view` (via UI admin ou chamada direta).
3. Confirmar presenca de:
   - organizations
   - users (admins/providers/clients)
   - products
   - enrollments
   - pillars
   - metrics
   - measurements
   - checkpoints
   - integrity
4. Confirmar que `password_hash` nao aparece em nenhuma secao.

### 4.2 Provider A

1. Fazer login como provider A.
2. Abrir Centro de Comando.
3. Confirmar que lista apenas clients da carteira do provider A.
4. Abrir Radar agregado.
5. Abrir Radar individual de client da carteira.
6. Abrir Matriz de renovacao.
7. Validar filtros `all`, `critical`, `rescue` e coerencia visual dos quadrantes.

### 4.3 Isolamento

1. Com token/provider A, tentar acessar client vinculado ao provider B:
   - `/mentor/radar/alunos/{client_id_provider_b}`
2. Resultado esperado:
   - bloqueio por `404`/`403` padronizado (sem vazamento de dados).

### 4.4 Guardrail runtime required

1. Derrubar ambiente.
2. Subir backend com `SUPABASE_RUNTIME_REQUIRED=true` e sem `SUPABASE_DB_URL`.
3. Chamar endpoint Supabase-only (ex: `/mentor/matriz-renovacao` autenticado provider).
4. Resultado esperado:
   - `503`
   - `error.code = SUPABASE_DB_URL_REQUIRED`

## 5. Evidencias a anexar

- screenshot/tela da Database View com secoes carregadas.
- screenshot/tela Centro de Comando, Radar e Matriz do provider A.
- resposta de erro para tentativa de acesso cross-provider.
- resposta de erro com `SUPABASE_DB_URL_REQUIRED` no cenário guardrail.

## 6. Resultado final (preencher)

- Admin ve dataset completo: `[] sim` `[] nao`
- Provider A ve apenas sua carteira: `[] sim` `[] nao`
- Provider A nao acessa carteira B: `[] sim` `[] nao`
- Fluxos A/B/C/D sem JSON: `[] sim` `[] nao`
- Guardrail runtime required validado: `[] sim` `[] nao`

Observacoes:

```text
<preencher>
```
