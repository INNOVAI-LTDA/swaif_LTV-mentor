# Relatório: calculadora de score das métricas

Data: 2026-05-08

## Escopo
Validar a calculadora responsável por converter `value_current` bruto de `Measurement` em score da `Metric` usando `scoring_rules`, `score_type` e normalização por `max_score`, `max_range` ou `mcv`.

## Resultado principal
A calculadora foi implementada no backend com suporte à gramática v2 em `scoring_rules.version = 2`, preservando compatibilidade com a gramática legada v1 baseada em lista.

- `Measurement.value_current` continua sendo armazenado como valor bruto editável.
- O score calculado passa a ser usado na recomputação normalizada do `measurement_overall`.
- A geração inicial de `measurement_overalls` usa `measurements` reais quando existirem.
- Novas métricas criadas sem gramática explícita passam a nascer com um `scoring_rules` v2 seguro, com `fallback` de score `0`.

## Arquivos principais envolvidos

- `backend/app/services/metric_score_service.py`
- `backend/app/storage/metric_repository.py`
- `backend/app/services/admin_metric_service.py`
- `backend/app/services/method_config_service.py`
- `backend/app/services/student_workspace_service.py`
- `backend/app/storage/measurement_overall_repository.py`
- `backend/app/api/routes/student_workspace.py`
- `backend/tests/unit/test_metric_score_service.py`
- `backend/tests/unit/test_student_workspace_service_scoring.py`
- `backend/tests/unit/test_admin_metric_service.py`
- `backend/tests/unit/test_method_config_service.py`
- `backend/tests/integration/test_metric_repository.py`

## Testes executados

### 1. Suíte focada consolidada

Comando executado:

```powershell
python -m pytest tests/unit/test_metric_score_service.py tests/unit/test_student_workspace_service_scoring.py tests/unit/test_admin_metric_service.py tests/unit/test_method_config_service.py tests/integration/test_metric_repository.py
```

Resultado:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-7.4.4, pluggy-1.6.0
rootdir: C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor\backend
plugins: anyio-4.9.0, hypothesis-6.150.2, asyncio-0.23.3, cov-4.1.0, subtests-0.7.0, schemathesis-3.27.1
asyncio: mode=Mode.STRICT
collected 17 items

tests\unit\test_metric_score_service.py ......
tests\unit\test_student_workspace_service_scoring.py ..
tests\unit\test_admin_metric_service.py .....
tests\unit\test_method_config_service.py ...
tests\integration\test_metric_repository.py .

============================= 17 passed in 3.35s ==============================
```

Cobertura desses testes:

1. `static` v2: aplica regra única por faixa e normaliza por `max_score`.
2. `range` v2: usa `assign_range` e normaliza por `max_range`.
3. `accumulative` v2: soma múltiplas regras compatíveis.
4. `object sum_matches` v2: avalia campos nomeados dentro de payload estruturado.
5. `per_unit` v2: multiplica quantidade por pontos unitários e normaliza por `mcv`.
6. Compatibilidade v1: mantém cálculo com a gramática legada baseada em lista.
7. `measurement_overall`: converte measurements reais em `goal/base/real` normalizados.
8. `student_workspace_service.update_self_measurement_current`: aceita valor bruto alto e recompõe o overall normalizado.
9. `admin_metric_service`: cria métrica administrativa com defaults v2 persistíveis.
10. `method_config_service`: cria métrica de método com defaults coerentes com v2.
11. `metric_repository`: persiste `scoring_rules.version = 2` e base de normalização padrão em novas métricas.

### 2. Validação adicional tentada por API

Foi tentada validação mais ampla via `tests/api/test_student_workspace_api.py`, mas a suíte continua bloqueada por um problema pré-existente e não relacionado à calculadora.

Bloqueio observado:

```text
TypeError: StudentVinculoService.__init__() got an unexpected keyword argument 'contacts'
```

Origem do bloqueio:

- `backend/app/api/routes/admin_students.py`

## Resultados concretos da calculadora

Os exemplos abaixo foram executados contra a configuração atual de `backend/data/metrics.json`, já migrada para a gramática v2.

### Saídas coletadas

| Métrica | Valor bruto | Score | Score normalizado | Base de normalização | Regras acionadas |
|---|---:|---:|---:|---:|---|
| `mtr_faturamento` | `500000.5` | `20.0` | `1.0` | `20.0` | `[2]` |
| `mtr_faturamento` | `100000` | `10.0` | `0.5` | `20.0` | `[1]` |
| `mtr_taxa-conversao` | `49.9` | `5.0` | `0.25` | `20.0` | `[0]` |
| `mtr_taxa-conversao` | `50` | `20.0` | `1.0` | `20.0` | `[1]` |
| `mtr_gratidao` | `respondeu` | `4.0` | `1.0` | `4.0` | `[0]` |
| `mtr_processos` | `['Vendas', 'RH']` | `10.0` | `0.666667` | `15.0` | `[0, 2]` |
| `mtr_numero-servicos` | `4` | `8.0` | `1.0` | `6.0` | `[]` |

## Interpretação dos exemplos

### Faturamento

- Regra configurada:
  - `< 100000` -> `5`
  - `>= 100000 e <= 500000` -> `10`
  - `> 500000` -> `20`
- Exemplo validado: `500000.5`
- Resultado: `score = 20` e `score normalizado = 20 / 20 = 1.0`

### Taxa de Conversão

- `49.9` cai na regra `< 50` e produz `5`.
- `50` cai na regra `>= 50` e produz `20`.

### Gratidão

- `respondeu` ativa `assign_range = { min: 1, max: 4, policy: max }`.
- A implementação atual resolve esse caso usando o teto configurado para o intervalo, então o resultado foi `4`.

### Processos

- Como `scoring.mode = sum_matches`, a pontuação soma regras compatíveis.
- Com `['Vendas', 'RH']`, o resultado é `5 + 5 = 10`.

### Número de Serviços

- Como a gramática v2 usa `scoring.mode = per_unit`, a pontuação é quantidade multiplicada pelos pontos unitários.
- Para `4` serviços: `4 x 2 = 8`.
- Como `max_score_basis = MCV` e `mcv = 6`, a normalização usa `8 / 6`, mas fica limitada a `1.0`.
- Nesse modo, `matched_rule_indexes` fica vazio porque o score não depende de casamento de regras discretas.

## Observações relevantes

1. O valor bruto continua no `Measurement`; a calculadora não sobrescreve esse dado com score.
2. O uso operacional do score acontece no `measurement_overall`, onde `goal`, `base` e `real` passam a refletir score normalizado.
3. Métricas com `sum_matches` e `per_unit` dependem do formato do valor bruto fornecido:
   - lista ou set de opções para `sum_matches` baseado em seleção;
   - objeto para `sum_matches` baseado em campos nomeados;
   - quantidade numérica para `per_unit`.
4. A gramática v2 deixou explícitos os elementos antes implícitos: formato de input, modo de avaliação, ação de score e base de normalização.
5. Para métricas recém-criadas sem configuração explícita, o default v2 retorna score `0` com normalização por `max_score = 1`, evitando persistência em formato legado vazio.

## Próximas validações recomendadas

1. Desbloquear a suíte de API corrigindo a instanciação de `StudentVinculoService` em `backend/app/api/routes/admin_students.py`.
2. Decidir se as respostas da API devem expor também `score` e `normalizedScore`, além do valor bruto.
3. Definir semântica final para `assign_range.policy = clamp_input` caso o produto queira score interpolado para inputs numéricos.