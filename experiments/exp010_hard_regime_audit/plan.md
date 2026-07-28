# exp010_hard_regime_audit Plan

## Purpose

Resolve FPA Round 5 B/EXPERIMENT blockers for Reliability Engineering & System
Safety by auditing the reliability-relevant hard regime:

- no recent SOH label available at decision time;
- multi-step-ahead SOH targets;
- broader SOH threshold sweep;
- multiplicity-controlled decision utility;
- schema-vs-residual shift separation across all cross-protocol tasks;
- adaptive conformal recovery comparator.

## Source Plan

- `docs/reports/20260530_215915_fpa_revision_20260530_215247_revision_plan.md`

## Data Policy

- Real CALCE, NASA, and Oxford SOH data only.
- Synthetic data is prohibited.
- Processed input: `data/processed/real_battery_cycle_level_features.csv`
- Split manifest: `data/splits/real_battery_splits.json`

No additional QA-compatible modern battery dataset is available under
`data/raw` in the current local evidence base. This experiment records that
external-validity limitation explicitly rather than fabricating data.

## Execution

```bash
python scripts/run_hard_regime_audit_experiment.py \
  --output-exp exp010_hard_regime_audit \
  --seed 42 \
  --bootstrap-reps 1000 \
  --min-decision-denominator 5 \
  --horizons 0,5,20
```

## Expected Outputs

- `experiments/exp010_hard_regime_audit/results/metrics.json`
- `experiments/exp010_hard_regime_audit/results/multiplicity_control.json`
- `experiments/exp010_hard_regime_audit/results/run_manifest.json`
- `experiments/exp010_hard_regime_audit/results/split_manifest.json`

## Closure Criteria

- No method uses `prev_soh` or `prev_soh_missing` as a feature.
- Horizon 0, 5, and 20 audits are present.
- Each task reports coverage, cell/domain CIs, false-safe/false-alarm/uncertain
  rates, and cost curves.
- Decision utility includes Bonferroni and BH-style multiplicity summaries.
- All leave-domain tasks include original-schema, common-schema, and residual
  shift diagnostics.
- The stage-Mondrian CQR recovery comparator is evaluated under the hard
  regime.

