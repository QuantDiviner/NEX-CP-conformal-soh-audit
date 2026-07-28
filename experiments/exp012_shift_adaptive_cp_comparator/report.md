# exp012_shift_adaptive_cp_comparator Report

**Status**: pending_review

## Results Summary

This experiment tests whether weighted shift-adaptive conformal CQR recovers reliability under the existing real-data protocol-shift tasks.

| Task | Standard cov | Adaptive cov | Adaptive CI low | Width ratio | Interpretation |
|---|---:|---:|---:|---:|---|
| main_heldout | 0.9587 | 0.8937 | 0.8371 | 0.942 | failure_boundary |
| leave_CALCE_out | 0.7553 | 0.6723 | 0.6092 | 0.512 | failure_boundary |
| target_recalibrated_CALCE | 0.6555 | 0.6797 | 0.5654 | 1.040 | failure_boundary |
| leave_NASA_out | 0.9039 | 0.9120 | 0.8705 | 1.005 | recovery_candidate |
| target_recalibrated_NASA | 0.8799 | 0.9374 | 0.8970 | 1.018 | recovery_candidate |
| leave_Oxford_out | 0.4286 | 0.4286 | 0.3496 | 0.987 | failure_boundary |
| target_recalibrated_Oxford | 0.9871 | 0.9871 | 0.9694 | 1.000 | recovery_candidate |

Synthetic data was not used.

## Claim Boundary

RESS reliability / measurement-validity diagnostic only; the localized-residual comparator has no covariate-shift conformal coverage guarantee and supports no method-superiority, broad-transfer, deployment, Neural-ODE, or NEX-CP claim.
