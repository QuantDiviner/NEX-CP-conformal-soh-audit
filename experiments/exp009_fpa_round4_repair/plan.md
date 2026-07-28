# exp009_fpa_round4_repair Plan

## Purpose

Resolve FPA Round 4 exit-B experiment-level blockers for the Reliability
Engineering & System Safety target journal.

## Source Plan

- FPA revision plan:
  `docs/reports/20260530_210059_fpa_revision_20260530_205235_revision_plan.md`
- Required workstreams covered in this experiment: P0-R1 through P0-R5.

## Data Policy

- Real CALCE, NASA, and Oxford SOH data only.
- Synthetic data is prohibited.
- Processed input: `data/processed/real_battery_cycle_level_features.csv`
- Split manifest: `data/splits/real_battery_splits.json`

## Execution

Run:

```bash
python scripts/run_reliability_audit_experiment.py \
  --output-exp exp009_fpa_round4_repair \
  --seed 42 \
  --bootstrap-reps 1000 \
  --min-decision-denominator 5 \
  --include-ngboost \
  --add-harmonized-leave-nasa
```

## Expected Outputs

- `experiments/exp009_fpa_round4_repair/results/metrics.json`
- `experiments/exp009_fpa_round4_repair/results/run_manifest.json`
- `experiments/exp009_fpa_round4_repair/results/split_manifest.json`
- `experiments/exp009_fpa_round4_repair/results/baseline_alignment.json`
- `experiments/exp009_fpa_round4_repair/results/decision_utility_ci.json`
- `experiments/exp009_fpa_round4_repair/results/shift_diagnostics.json`

## Closure Criteria

- q-selection trace and deterministic regeneration command are present.
- Width comparisons are explicitly gated by coverage alignment.
- `leave_NASA_out_common_feature_schema` separates feature-schema shift from
  residual dataset/protocol shift.
- Low-denominator decision-utility cells are suppressed or marked exploratory.
- Claim-boundary audit is recorded and no paper/manuscript files are edited.

