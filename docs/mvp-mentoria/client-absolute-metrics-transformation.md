# Client Absolute Metrics Transformation (Mock)

Data: 2026-05-21

## Objetivo

Definir um mock padrao para metricas absolutas de clients, mapear as regras de transformacao para relativo, e registrar um exemplo de processamento modular para reuso em backend.

Escopo atual: cobrir todas as regras v2 presentes no snapshot sincronizado do Supabase (`backend/data/metrics.json`).

Implementacao de referencia:
- backend/app/services/client_metric_transformation_service.py

## Regras em string

As regras em string sao geradas dinamicamente para todas as metricas carregadas do Supabase.

Resumo do snapshot atual:

1. Modos de scoring cobertos
- `first_match`
- `sum_matches`
- `per_unit`

2. Operadores/condicoes cobertos
- `op`: `eq`, `lt`, `lte`, `gt`, `gte`
- `range`
- `contains`
- `contains_any`
- combinadores: `any`, `all`, `not`
- suporte a `field` para payloads objeto

3. Acoes cobertas
- `assign`
- `assign_range`

4. Bases de normalizacao cobertas
- `max_score`
- `max_range`
- `mcv`

## Regras em codigo

Trecho de referencia (logica implementada em Python) usado no backend:

```python
def score_relative_python(metric_id: str, absolute_value: Any, *, metric_rules_by_id: dict[str, dict[str, Any]]) -> float:
  metric = metric_rules_by_id.get(metric_id)
  if metric is None:
    raise ScoreCalculationError("metric rule not found")

  scoring_rules = metric["scoring_rules"]
  scoring = scoring_rules.get("scoring", {})
  mode = str(scoring.get("mode") or "first_match")

  if mode == "per_unit":
    points_per_unit = float(scoring["points_per_unit"])
    score = max(0.0, float(absolute_value)) * points_per_unit
  else:
    rules = scoring.get("rules") or []
    matched = [rule for rule in rules if _match_when(rule.get("when") or {}, absolute_value)]
    if not matched:
      fallback = scoring.get("fallback")
      if not isinstance(fallback, dict):
        raise ScoreCalculationError("no scoring rule matched")
      score = _evaluate_action(fallback, absolute_value)
    elif mode == "sum_matches":
      score = sum(_evaluate_action(rule.get("then") or {}, absolute_value) for rule in matched)
    else:
      score = _evaluate_action(matched[0].get("then") or {}, absolute_value)

  basis = _resolve_normalization_basis(
    metric=metric,
    scoring_rules=scoring_rules,
    matched_rules=matched if mode != "per_unit" else [],
    score=float(score),
  )
  return round(0.0 if basis <= 0 else max(0.0, min(1.0, float(score) / basis)), 6)
```

Implementacao real:
- `load_supabase_metric_rules_by_id`
- `score_relative_python_from_metric`
- `score_relative_python`
- `build_mock_client_absolute_metrics`
- `transform_client_absolute_metrics_python_with_rules`

Todos em `backend/app/services/client_metric_transformation_service.py`.

## Exemplo de processamento

### Input absoluto (recorte)

```json
{
  "client_id": "std_supabase_rules",
  "pillar_id": "plr_1",
  "metric_id": "met_1",
  "baseline_absolute": 14,
  "current_absolute": 22.5,
  "goal_absolute": 31
}
```

### Transformacao

1. Resolver regra da metrica por metric_id
2. Calcular score para baseline/current/goal via engine Python (`score_relative_python`)
3. Ler normalized_score de cada valor
4. Agregar media relativa por pilar

### Output relativo (recorte)

```json
{
  "metricId": "met_1",
  "absolute": {
    "baseline": 14.0,
    "current": 22.5,
    "goal": 31.0
  },
  "relative": {
    "baseline": 0.25,
    "current": 0.5,
    "goal": 1.0
  }
}
```

## Agregacao por pilar

Para cada client e pilar:

- baseline_pilar = media(rel_baseline_metricas)
- current_pilar = media(rel_current_metricas)
- goal_pilar = media(rel_goal_metricas)

Exemplo (Client Supabase Rules / pilar plr_1):
- `met_1`: base=0.25, current=0.5, goal=1.0
- `met_2`: base=0.25, current=1.0, goal=1.0

Resultado:
- baseline = (0.25 + 0.25)/2 = 0.25
- current = (0.5 + 1.0)/2 = 0.75
- goal = (1.0 + 1.0)/2 = 1.00

## Uso rapido

Para gerar o payload completo de mock + transformacao:

```python
from app.services.client_metric_transformation_service import process_mock_client_absolute_metrics

payload = process_mock_client_absolute_metrics()
```

O payload retorna:
- rulesAsString
- sourceRows
- processingMode (`python_rules`)
- metricsCovered
- parityWithDeclarative
- transformed (clients, pillars, metrics, relatives)
