# exp008_reliability_audit Report

**Status**: closed Route A (RESS reliability/safety audit)

## Results Summary

This experiment implements the abandon-forward RESS reliability/safety audit.
It does not make a performance-dominance claim.

### Main Held-Out Reliability

| Method | Coverage | Cell-block CI low | Mean width | False-safe @0.80 | False-alarm @0.80 | Uncertain @0.80 |
|---|---:|---:|---:|---:|---:|---:|
| persistence_anchor_protocol_mondrian_cp | 0.9471 | 0.9417 | 0.0369 | 0.0142 | 0.0209 | 0.1765 |
| qr_gradient_boosting | 0.8898 | 0.8449 | 0.0954 | 0.0110 | 0.0076 | 0.2919 |
| cqr_gradient_boosting | 0.9522 | 0.9416 | 0.1020 | 0.0110 | 0.0066 | 0.2970 |
| ngboost_normal_cqr | 0.8390 | 0.4875 | 0.0864 | 0.0087 | 0.0665 | 0.4352 |

Coverage-aligned main-held-out comparison: CQR is coverage-aligned with
persistence but has 2.76x wider intervals. QR and NGBoost are not
coverage-aligned.

### Cross-Protocol Failure Boundary

`leave_NASA_out` remains a sharp non-exchangeability example:

| Method | Coverage | Cell-block CI low | Mean width | False-safe @0.80 | Uncertain @0.80 |
|---|---:|---:|---:|---:|---:|
| persistence_anchor_protocol_mondrian_cp | 0.8060 | 0.7349 | 0.0267 | 0.0190 | 0.0605 |
| qr_gradient_boosting | 0.8899 | 0.8576 | 0.2046 | 0.0079 | 0.4079 |
| cqr_gradient_boosting | 0.9218 | 0.8930 | 0.2095 | 0.0063 | 0.4199 |
| ngboost_normal_cqr | 0.2761 | 0.2141 | 0.0697 | 0.7943 | 0.0770 |

The audit supports conditional trust, not unrestricted transfer: CQR can recover
coverage on leave-NASA only by widening intervals roughly 7.84x relative to
persistence, while NGBoost collapses with a high false-safe rate.

### Shift Diagnostics

- `target_recalibrated_CALCE` max absolute standardized mean difference: 2.9901.
- `leave_NASA_out` max absolute standardized mean difference: 7.0219.

These values are used as empirical shift-to-failure diagnostics, not as physical
mechanism claims.

### Operational Assumption

All tasks require `prev_soh` availability for the persistence-anchor reference.
The claim boundary is therefore nowcasting or one-step lag-constrained
forecasting unless the deployment setting can provide the previous SOH at
decision time.

## Output Files

- `results/metrics.json`
- `results/decision_utility_ci.json`
- `results/shift_diagnostics.json`
- `results/baseline_alignment.json`
- `results/run_manifest.json`
- `results/split_manifest.json`

Synthetic data was not used.

## External Review Closure

Clean-room Codex review closed the experiment as Route A with high confidence:
`docs/reports/20260530_173340_D-EXP-exp008_reliability_audit_codex.md`.

Allowed claim: the experiment supports the downgraded RESS
reliability/safety-audit narrative: conditional trust boundaries, protocol
non-exchangeability coverage failure, and SOH-threshold false-safe/false-alarm
decision risk.

Forbidden claim: Neural-ODE, NEX-CP, persistence-anchor performance dominance,
unrestricted cross-protocol transfer, or deployment/BMS hardware readiness.
