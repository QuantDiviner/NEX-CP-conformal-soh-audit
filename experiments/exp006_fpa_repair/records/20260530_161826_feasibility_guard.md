# Feasibility Guard: exp006_fpa_repair

Time: 20260530_161826

## Stage 1 Mechanical Checks
- [x] results/metrics.json exists
- [x] metrics JSON parseable
- [x] synthetic data not declared
- [x] target coverage present
- [x] no NaN/Inf float values in metrics

## Gate 3 Findings
- P0-check: Contribution-positioning rule output is `negative_diagnostic_positioning_required`; reviewer must verify whether this closes the FPA contribution-risk MUST.
- P0-check: Dependence-aware failure list contains 129 task/cell entries; reviewer must verify whether NASA/CALCE failures are honestly classified.
- P1-check: NGBoost was not run because it was optional; reviewer must decide whether CQR+QR are sufficient for this repair round.
- P1-check: Row-level Wald intervals must not be used as pass/fail evidence for this repair.
