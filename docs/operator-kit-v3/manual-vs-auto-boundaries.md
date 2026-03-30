# Operator Kit V3 Manual Vs Auto Boundaries

## Purpose

Make the human-vs-automation boundary explicit so the operator kit stays safe and maintainable.

## Automate By Default

These responsibilities are good automation candidates:

- next-command routing
- context promotion
- contract validation
- artifact writing
- event logging
- workflow resume
- retry-on-invalid-contract once
- concise execution summaries

## Keep Manual By Default

These responsibilities should remain operator-controlled:

- accepting architecture changes
- accepting story boundaries
- accepting review closure
- approving deploy
- approving destructive data writes
- approving rollback in sensitive environments

## Semi-Automatic Zone

These may be automated only with explicit configuration:

- continue through approval gates
- auto-commit generated docs
- auto-open next workflow after review

## Rule Of Thumb

If a step primarily affects:

- context
- routing
- formatting
- execution bookkeeping

then it is a good automation candidate.

If a step primarily affects:

- business risk
- production risk
- scope acceptance
- destructive persistence

then it should remain manual.
