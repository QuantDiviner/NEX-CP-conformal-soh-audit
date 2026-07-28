# exp001_main: Real-data marginal and non-exchangeable conformal SOH intervals

## Purpose

Evaluate marginal real-data SOH interval calibration on QA-gated CALCE, NASA,
and Oxford cycle-level battery data.

## Data Policy

- Real data only from `data/raw` NAS symlinks.
- Synthetic data is forbidden.
- QA-gated inputs must come from `scripts/preprocess_real_battery.py`.

## Splits

Use the cell-level split manifest in `data/splits/real_battery_splits.json`.
Calibration rows precede test rows within the split policy where time-forward
ordering applies.

## Methods

Candidate conformal methods:

- Standard split conformal.
- NEX weighted conformal using `log_cycle_index` only; no cell-global
  `cycle_norm` feature is permitted.
- Calibration-group Mondrian conformal.
- Online adaptive conformal using sequentially observed real residuals.
- Persistence-anchored conformal, where the point prediction is `prev_soh` and
  conformal calibration is applied to the real one-step persistence residual.

Point predictors: ridge, gradient boosting, random forest, extra trees. Models
may use `prev_soh` only in the explicitly sequential one-step setting, matching
the persistence baseline comparator. No future SOH, future capacity, or
cell-global maximum-cycle normalization is permitted.

## Predeclared Selection Rule

Selection uses validation/calibration data only. Test metrics are never used for
model or method selection.

1. Rank candidates with validation coverage at or above 0.90 by validation mean
   width.
2. Rank under-covering candidates after all coverage-valid candidates, with a
   large penalty proportional to the coverage shortfall.
3. Online adaptive `q_level` is tuned on validation data only.

## Metrics and Success Criteria

Primary metric: coverage at nominal 90%.

Success criterion: coverage >= 0.90 and every reported domain coverage >= 0.85,
matching PROJECT_CHARTER.md Section 2.

Secondary metrics:

- mean width, median width, SOH-normalized width
- MAE, RMSE
- per-domain, per-calibration-group, and per-cell coverage
- persistence baseline MAE/RMSE

## Negative-Result Boundary

If clean QA-gated real data still under-covers after the bounded selection and
calibration-group fixes, do not force a positive claim. Route to scoped negative
or diagnostic framing under PROJECT_CHARTER.md Section 2.
