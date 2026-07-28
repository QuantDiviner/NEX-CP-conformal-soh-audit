# exp007_fpa_round2_repair: Cross-family UQ and decision-utility repair

## Purpose

Execute the FPA Round 2 exit-B repairs for Reliability Engineering & System
Safety after `exp006_fpa_repair` closed as Route E.

## Data Policy

- Real CALCE, NASA, and Oxford cycle-level SOH data only.
- Synthetic data is forbidden.
- Inputs are `data/processed/real_battery_cycle_level_features.csv` and
  `data/splits/real_battery_splits.json`.

## Predeclared Selection Rule

Use validation coverage-first width minimization for q/interval selection.
Dependence-aware cell/domain bootstrap CIs are reported for inference and
pass/fail auditing, but they are not used to tune q. This aligns the repair
selection rule with the exp001-style validation-only rule and prevents q/width
drift from being introduced by changing the tuning objective.

## Methods

- `persistence_anchor_protocol_mondrian_cp`
- `qr_gradient_boosting`
- `cqr_gradient_boosting`
- `ngboost_normal_cqr`: NGBoost Normal predictive distribution with conformalized
  interval

## Required Analyses

- Same task set as exp006: main held-out, leave-domain-out, and target
  recalibrated CALCE/NASA/Oxford tasks.
- Coverage, cell/domain-block CI, width, MAE/RMSE, subgroup audit.
- Failure diagnostics comparing persistence CP, CQR/QR, and NGBoost collapse
  modes.
- SOH threshold utility at 0.80 and 0.70: false-safe, false-alarm, uncertain
  rate, predicted-safe and predicted-unsafe rates.
- Legacy manifests for exp001-exp004 with explicit provenance limitations.

## Success Criteria

The experiment succeeds if it completes the Round 2 repair packet:

1. at least one bounded cross-family UQ baseline exists;
2. q/selection rule is locked and recorded;
3. decision-utility analysis is present;
4. legacy manifests are generated or limitations are explicit;
5. no synthetic data is used.

## Source Plan

Final Round 2 FPA repair plan:
`docs/reports/20260530_164103_fpa_revision_20260530_163246_revision_plan.md`
