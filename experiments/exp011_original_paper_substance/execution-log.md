# exp011_original_paper_substance Execution Log

## Formal Run

- Command: `python scripts/run_original_paper_substance_experiment.py --output-exp exp011_original_paper_substance --seed 42 --bootstrap-reps 1000 --min-decision-denominator 5`
- Status: completed
- Outputs:
  - `experiments/exp011_original_paper_substance/results/metrics.json`
  - `experiments/exp011_original_paper_substance/results/schema_delta_summary.json`
  - `experiments/exp011_original_paper_substance/results/multiplicity_control.json`
  - `experiments/exp011_original_paper_substance/results/external_dataset_inventory.json`
  - `experiments/exp011_original_paper_substance/results/run_manifest.json`
  - `experiments/exp011_original_paper_substance/results/split_manifest.json`

## Amendment

The first formal run exposed that refitting GB-CQR with an added constant-zero
feature could trip the negative control through model-refitting sensitivity. The
script was amended so the negative control duplicates clean-original fitted
intervals and tests only the paired-delta machinery. The final outputs are from
the amended run.

## Amendment 2 (2026-06-19, manuscript-revision Loop B / Codex finding)

Codex's raw-recompute review (S1-C-R1-01, P0) found that the artifact-positivity
determination's false-safe delta tests did not apply the `min_decision_denominator`
floor that the manuscript states (cells with n<5 are exploratory). The sole
trigger for `target_recalibrated_Oxford` was a false-safe delta cell with
denominator 2 (delta -100 pp). `rate_delta_by_cell()` /
`schema_deltas()` were corrected to mark sub-floor cells
`suppressed_low_denominator`, which `decision_rules()` already excludes.

Re-ran (identical command, seed 42, reps 1000, min-decision-denominator 5):
`python scripts/run_original_paper_substance_experiment.py --output-exp exp011_original_paper_substance --seed 42 --bootstrap-reps 1000 --min-decision-denominator 5`

Result change: `artifact_positive_tasks` 4 -> 3
(was [leave_CALCE_out, leave_NASA_out, target_recalibrated_NASA, target_recalibrated_Oxford];
now [leave_CALCE_out, leave_NASA_out, target_recalibrated_NASA]).
Coverage deltas unchanged. Route-A finding (schema-to-decision mechanism case)
stands; only the spurious TOxf n=2 verdict was corrected. `paper/data/metrics.json`
re-collected; raw==SSOT verified for all 7 decision rows.
