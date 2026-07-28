# exp006_fpa_repair Execution Log

## Run 2026-05-30 16:16

- Command: `python scripts/run_fpa_repair_experiment.py --seed 42 --bootstrap-reps 1000`
- Exit status: 0
- Data policy: real data only; synthetic data not used
- Inputs:
  - `data/processed/real_battery_cycle_level_features.csv`
  - `data/splits/real_battery_splits.json`
- Outputs:
  - `experiments/exp006_fpa_repair/results/metrics.json`
  - `experiments/exp006_fpa_repair/results/run_manifest.json`
  - `experiments/exp006_fpa_repair/results/split_manifest.json`
  - `experiments/exp006_fpa_repair/report.md`

## Result Snapshot

- Contribution-positioning verdict:
  `negative_diagnostic_positioning_required`
- Main held-out persistence-anchor CP:
  coverage 0.9613, cell-block CI low 0.9523, mean width 0.2255
- Main held-out CQR:
  coverage 0.9522, cell-block CI low 0.9416, mean width 0.1020
- `target_recalibrated_CALCE` persistence-anchor CP:
  coverage 0.8440, cell-block CI low 0.8226
- `leave_NASA_out` persistence-anchor CP:
  coverage 0.8060, cell-block CI low 0.7349

## Deviations

- NGBoost was not run. The final repair plan made it optional if dependency and
  runtime costs stayed bounded. The required same-split CQR and QR baselines
  were completed without adding new dependencies.
