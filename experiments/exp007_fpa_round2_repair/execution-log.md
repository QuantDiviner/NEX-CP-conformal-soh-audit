# exp007_fpa_round2_repair Execution Log

## Run 2026-05-30 16:46

- Command: `python scripts/run_fpa_repair_experiment.py --output-exp exp007_fpa_round2_repair --seed 42 --bootstrap-reps 1000 --include-ngboost`
- Exit status: 0
- Data policy: real data only; synthetic data not used
- Inputs:
  - `data/processed/real_battery_cycle_level_features.csv`
  - `data/splits/real_battery_splits.json`
- Outputs:
  - `experiments/exp007_fpa_round2_repair/results/metrics.json`
  - `experiments/exp007_fpa_round2_repair/results/run_manifest.json`
  - `experiments/exp007_fpa_round2_repair/results/split_manifest.json`
  - `experiments/exp007_fpa_round2_repair/results/legacy_manifests/*.json`
  - `experiments/exp007_fpa_round2_repair/report.md`

## Result Snapshot

- Contribution-positioning verdict:
  `scoped_positive_method_claim_allowed`
- Main held-out persistence-anchor CP:
  coverage 0.9471, cell-block CI low 0.9417, mean width 0.0369
- Main held-out CQR:
  coverage 0.9522, cell-block CI low 0.9416, mean width 0.1020
- Main held-out NGBoost CQR:
  coverage 0.8390, cell-block CI low 0.4875, mean width 0.0861
- `leave_NASA_out` persistence-anchor CP:
  coverage 0.8060, cell-block CI low 0.7349
- `target_recalibrated_CALCE` persistence-anchor CP:
  coverage 0.8440, cell-block CI low 0.8226

## Deviations

- No deep quantile/LSTM baseline was run. The Round 2 final plan made it a
  SHOULD item after the MUST repair packet.
