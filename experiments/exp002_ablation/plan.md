# exp002_ablation: Feature and calibration ablation

## Purpose

Quantify how much the closed exp001 interval-calibration result depends on
sequential persistence (`prev_soh`) and resistance features.

## Data Policy

- Real data only from `data/raw` NAS symlinks.
- Synthetic data is forbidden.
- Inputs must come from `scripts/preprocess_real_battery.py`.

## Conditions

All conditions use the same real-data split manifest and validation-only
selection rule as exp001.

| Condition | Dropped features |
|---|---|
| full_features | none |
| without_prev_soh | `prev_soh`, `prev_soh_missing` |
| without_resistance | `internal_resistance`, `internal_resistance_missing` |
| without_prev_soh_and_resistance | all features above |

For `without_prev_soh*` conditions, persistence-anchor conformal candidates are
disabled because they consume `prev_soh` outside the design matrix.

## Metrics

For every condition report selected method, coverage, coverage CI, mean width,
SOH-normalized width, MAE, RMSE, per-domain coverage, and persistence baseline
where applicable.

Primary comparison: `delta_vs_full` for coverage, mean width, MAE, and RMSE.

## Success Criterion

The ablation is successful if it produces all four predeclared conditions and
quantifies dependence on `prev_soh` and resistance features. It is not required
that all ablated conditions pass the exp001 coverage criterion.
