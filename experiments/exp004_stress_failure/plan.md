# exp004_stress_failure: Real residual stress probe

## Purpose

Measure how the selected exp001 interval behaves when the point prediction is
systematically biased on real held-out rows.

## Data Policy

- Real held-out rows only.
- Synthetic rows are forbidden.
- Bias is applied to predictions, not by generating new samples.

## Predeclared Probe

Apply additive SOH prediction bias values:

`-0.05, -0.02, -0.01, -0.005, 0, +0.005, +0.01, +0.02, +0.05`

For every bias, recompute empirical coverage, width, MAE/RMSE, and domain audit
on the same real test rows. The selected conformal radius is not retuned.

## Success Criterion

The experiment is successful if it reports the empirical coverage sensitivity
curve and the smallest absolute bias at which marginal coverage falls below
0.90, if any.
