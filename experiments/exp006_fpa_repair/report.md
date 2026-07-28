# exp006_fpa_repair Report

**Status**: pending_review

**Generated**: 2026-07-18T05:10:29.292105

## Results Summary

Contribution-positioning verdict: `scoped_positive_method_claim_allowed`.

| Task | Method | Coverage | Cell-block CI low | Mean width | RMSE |
|---|---|---:|---:|---:|---:|
| main_heldout | persistence_anchor_protocol_mondrian_cp | 0.9479 | 0.9417 | 0.0375 | 0.0385 |
| main_heldout | qr_gradient_boosting | 0.8795 | 0.8263 | 0.0919 | 0.0381 |
| main_heldout | cqr_gradient_boosting | 0.9587 | 0.9501 | 0.1021 | 0.0381 |
| main_heldout | ngboost_normal_cqr | 0.8407 | 0.4879 | 0.0744 | 0.0432 |
| leave_CALCE_out | persistence_anchor_protocol_mondrian_cp | 0.9535 | 0.9492 | 0.0864 | 0.0365 |
| leave_CALCE_out | qr_gradient_boosting | 0.5097 | 0.4507 | 0.0491 | 0.0959 |
| leave_CALCE_out | cqr_gradient_boosting | 0.7553 | 0.6913 | 0.1572 | 0.0959 |
| leave_CALCE_out | ngboost_normal_cqr | 0.7920 | 0.7396 | 0.2068 | 0.0993 |
| target_recalibrated_CALCE | persistence_anchor_protocol_mondrian_cp | 0.8274 | 0.7934 | 0.0190 | 0.0351 |
| target_recalibrated_CALCE | qr_gradient_boosting | 0.5187 | 0.3822 | 0.2628 | 0.1114 |
| target_recalibrated_CALCE | cqr_gradient_boosting | 0.6555 | 0.5293 | 0.2903 | 0.1114 |
| target_recalibrated_CALCE | ngboost_normal_cqr | 0.6141 | 0.4766 | 0.2494 | 0.1158 |
| leave_NASA_out | persistence_anchor_protocol_mondrian_cp | 0.8032 | 0.7039 | 0.0267 | 0.0347 |
| leave_NASA_out | qr_gradient_boosting | 0.8681 | 0.8202 | 0.2115 | 0.1084 |
| leave_NASA_out | cqr_gradient_boosting | 0.9039 | 0.8604 | 0.2157 | 0.1084 |
| leave_NASA_out | ngboost_normal_cqr | 0.2899 | 0.2077 | 0.0793 | 0.1230 |
| target_recalibrated_NASA | persistence_anchor_protocol_mondrian_cp | 0.9400 | 0.8943 | 0.0561 | 0.0395 |
| target_recalibrated_NASA | qr_gradient_boosting | 0.7625 | 0.7075 | 0.2362 | 0.1092 |
| target_recalibrated_NASA | cqr_gradient_boosting | 0.8799 | 0.8362 | 0.2461 | 0.1092 |
| target_recalibrated_NASA | ngboost_normal_cqr | 0.7407 | 0.5726 | 0.2259 | 0.1101 |
| leave_Oxford_out | persistence_anchor_protocol_mondrian_cp | 0.9902 | 0.9785 | 0.0418 | 0.0114 |
| leave_Oxford_out | qr_gradient_boosting | 0.4051 | 0.3270 | 0.0973 | 0.0361 |
| leave_Oxford_out | cqr_gradient_boosting | 0.4286 | 0.3496 | 0.1050 | 0.0361 |
| leave_Oxford_out | ngboost_normal_cqr | 0.1585 | 0.1356 | 0.0580 | 0.0521 |
| target_recalibrated_Oxford | persistence_anchor_protocol_mondrian_cp | 0.9442 | 0.8821 | 0.0160 | 0.0161 |
| target_recalibrated_Oxford | qr_gradient_boosting | 0.9871 | 0.9694 | 0.0421 | 0.0206 |
| target_recalibrated_Oxford | cqr_gradient_boosting | 0.9871 | 0.9694 | 0.0421 | 0.0206 |
| target_recalibrated_Oxford | ngboost_normal_cqr | 0.4807 | 0.4058 | 0.0264 | 0.0205 |

## FPA Repair Coverage

- Same-split CQR/QR baselines: complete.
- Dependence-aware cell-block bootstrap CIs: complete.
- Cross-protocol failure diagnostics: complete.
- Run and split manifests: complete.

Synthetic data was not used.
