# exp006_fpa_repair: RESS FPA repair baselines and dependence-aware audit

## Purpose

Execute the MUST repairs from FPA Round 1 exit B for the target journal
Reliability Engineering & System Safety.

This experiment is a repair packet, not a new framework pivot. It tests whether
the current persistence-anchor conformal evidence remains publishable after
RESS-level comparative baselines, dependence-aware coverage intervals, and
cross-protocol failure diagnostics.

## Data Policy

- Use only the QA-gated real CALCE, NASA, and Oxford cycle-level SOH data.
- Synthetic data is forbidden.
- Inputs must come from `scripts/preprocess_real_battery.py` outputs and
  `data/splits/real_battery_splits.json`.

## Predeclared Contribution-Positioning Rule

Before interpreting results:

1. If persistence-anchor CP does not outperform feasible modern UQ baselines
   (CQR and quantile-regression intervals) on same-split coverage-width and
   error tradeoffs, the project must be positioned as a rigorous negative or
   diagnostic reliability study.
2. If persistence-anchor CP outperforms those baselines while meeting
   dependence-aware coverage criteria, the project may retain a scoped positive
   method claim.
3. Cross-protocol undercoverage may be reported as an honest diagnostic result
   if robust recalibration is not supported by the data.

## Methods

Same-split methods:

- `persistence_anchor_protocol_mondrian_cp`: one-step `prev_soh` prediction with
  calibration-group conformal radii.
- `cqr_gradient_boosting`: conformalized quantile regression using sklearn
  gradient-boosting quantile regressors.
- `qr_gradient_boosting`: raw quantile-regression interval using sklearn
  gradient-boosting quantile regressors.

The optional NGBoost baseline is deferred unless dependency installation is
already available and does not delay the repair loop.

## Tasks

- Main held-out split: train/cal/val/test from the existing cell-level split
  manifest.
- Leave-domain-out tasks for CALCE, NASA, and Oxford.
- Target-recalibrated tasks for CALCE, NASA, and Oxford.

## Metrics

Primary:

- coverage at nominal 90%
- cell-block bootstrap coverage CI low/high
- domain-block bootstrap coverage CI low/high when multiple domains are present
- mean width, median width, SOH-normalized width
- MAE and RMSE for interval centers

Diagnostics:

- per-domain, per-calibration-group, and per-cell coverage
- failure list for tasks/cells with cell-block CI low below 0.85
- residual summary by domain and degradation-stage bin
- contribution-positioning verdict from the predeclared rule

## Success Criteria

This repair succeeds if it produces a complete evidence packet resolving the
FPA Round 1 MUST items:

1. comparative CQR/QR baselines exist under the same split policy;
2. row-level Wald CIs are no longer the only pass/fail evidence;
3. NASA/CALCE cross-protocol failures are classified with dependence-aware CIs;
4. run and split manifests are written.

The experiment may close as positive scoped or negative diagnostic depending on
the predeclared contribution-positioning rule.

## Source Plan

Final FPA repair plan:
`docs/reports/20260530_161104_fpa_revision_20260530_160139_revision_plan.md`
