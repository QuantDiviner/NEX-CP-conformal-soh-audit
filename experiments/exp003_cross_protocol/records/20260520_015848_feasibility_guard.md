# Feasibility Guard: exp003_cross_protocol

Time: 20260520_015848

## Stage 1 Mechanical Checks
- [x] results/metrics.json exists
- [x] metrics JSON parseable
- [x] synthetic data not declared
- [x] target coverage present
- [x] no NaN/Inf float values in metrics

## Gate 3 Findings
- P0: leave-CALCE-out coverage is 0.6601172009651844, below 0.90 target.
- P0: target-recalibrated-CALCE coverage is 0.22914650667698858, below 0.90 target.
- P1: CALCE extraction uses summary spreadsheet capacity; protocol/date discontinuities require audit.
- P1: Cross-domain setup lacks protocol/chemistry-aware residual pooling.
