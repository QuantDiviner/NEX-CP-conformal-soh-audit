# exp003_cross_protocol: Leave-domain-out cross-protocol stress

## Purpose

Evaluate whether conformal SOH intervals calibrated on real battery data transfer
across dataset/protocol domains.

## Data Policy

- Real data only from `data/raw` NAS symlinks.
- Synthetic data is forbidden.
- QA-gated inputs must come from `scripts/preprocess_real_battery.py`.

## Splits

- `leave_{domain}_out`: train/cal/validation on all other domains, test on all
  QA-passing rows from the held-out domain.
- `target_recalibrated_{domain}`: train on source domains plus early target
  cycles, calibrate/validate on earlier target cycles, test on later target
  cycles.
- CALCE calibration and audit groups are split into `CALCE_CS2`,
  `CALCE_CX2`, and other protocol groups when present.

## Methods

Candidate conformal methods:

- Standard split conformal.
- NEX weighted conformal using `log_cycle_index` only; no cell-global
  `cycle_norm` feature is permitted.
- Calibration-group Mondrian conformal.
- Online adaptive conformal using sequentially observed real residuals. This is
  the designated primary cross-protocol family when validation coverage is at
  least 0.90.
- Persistence-anchored conformal, where the point prediction is `prev_soh` and
  conformal calibration is applied to the real one-step persistence residual.
- Protocol-conditional Mondrian calibration keyed by `CALCE_CS2`/`CALCE_CX2`
  when those groups are present.

Point predictors: ridge, gradient boosting, random forest, extra trees. Models
may use `prev_soh` only in the explicitly sequential one-step setting, matching
the persistence baseline comparator. No future SOH, future capacity, or
cell-global maximum-cycle normalization is permitted.

## Predeclared Selection Rule

Selection uses validation/calibration data only. Test metrics are never used for
model or method selection.

1. Discard no candidate solely by width.
2. For cross-protocol tasks, select an online-adaptive candidate first if it has
   validation coverage >= 0.90; choose the narrowest such online-adaptive
   candidate on validation data.
3. If no online-adaptive candidate reaches validation coverage >= 0.90, rank
   all candidates with validation coverage at or above 0.90 by validation mean
   width.
4. Rank under-covering candidates after all coverage-valid candidates, with a
   large penalty proportional to the coverage shortfall.
5. Online adaptive `q_level` is tuned on validation data only.

## Metrics and Success Criteria

Primary metric: coverage at nominal 90%.

Success criterion: each held-out-domain or target-recalibrated task must reach
coverage >= 0.90 with non-degenerate width and CI lower bound >= 0.85, matching
PROJECT_CHARTER.md Section 2.

Secondary metrics:

- mean width, median width, SOH-normalized width
- MAE, RMSE
- per-domain, per-calibration-group, and per-cell coverage
- persistence baseline MAE/RMSE

## Bounded Rerun and Negative-Result Trigger

This plan implements the final Route-B bounded rerun requested by the
`20260520_022311` external review. If, after persistence-anchored conformal and
protocol-conditional calibration, clean QA-gated results still fail the
cross-protocol success criterion, exp003 should close as Route E scoped negative
result rather than force a positive claim.
