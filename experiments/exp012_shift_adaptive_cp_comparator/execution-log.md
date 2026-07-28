# exp012_shift_adaptive_cp_comparator Execution Log

## Run 1

- Command: `python scripts/run_shift_adaptive_cp_comparator.py --output-exp exp012_shift_adaptive_cp_comparator --seed 42 --bootstrap-reps 1000 --min-decision-denominator 5`
- Status: completed
- Synthetic data used: false
- Outputs:
  - `experiments/exp012_shift_adaptive_cp_comparator/results/metrics.json`
  - `experiments/exp012_shift_adaptive_cp_comparator/results/comparator_summary.json`
  - `experiments/exp012_shift_adaptive_cp_comparator/results/decision_utility_ci.json`
  - `experiments/exp012_shift_adaptive_cp_comparator/results/multiplicity_control.json`
  - `experiments/exp012_shift_adaptive_cp_comparator/results/run_manifest.json`
  - `experiments/exp012_shift_adaptive_cp_comparator/results/split_manifest.json`

## Outcome Snapshot

Weighted shift-adaptive CQR recovered the target coverage / cell-CI envelope for
`main_heldout`, `leave_NASA_out`, and `target_recalibrated_Oxford`. It did not
recover `leave_CALCE_out`, `target_recalibrated_CALCE`,
`target_recalibrated_NASA`, or `leave_Oxford_out`.
