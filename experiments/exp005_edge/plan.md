# exp005_edge: Host compute-cost screen

## Purpose

Measure host-only compute cost for the scoped selected interval path:
`prev_soh` persistence prediction plus protocol-Mondrian conformal interval
lookup.

## Scope

This is **not** edge/deployment evidence and must not be used as an industrial
hardware claim. It is a supporting compute-cost screen on the current host.

## Data Policy

- Real held-out feature rows only.
- Synthetic data is forbidden.

## Timed Path

For 512 real test rows:

1. read `prev_soh`;
2. map `calibration_group` to a precomputed calibration radius;
3. emit lower/upper interval.

Warmup: 20 repetitions. Timed repetitions: 300. Report mean, p95, std,
platform, Python version, and sample count.

Comparators on the same 512-row batch:

- persistence-only lookup;
- persistence-anchor interval lookup;
- gradient-boosting predictor inference.

All reported per-sample values are amortized batch throughput, not serving
latency.

## Success Criterion

The experiment is successful if it reports a reproducible host compute-cost
screen with the timed path and platform clearly specified.
