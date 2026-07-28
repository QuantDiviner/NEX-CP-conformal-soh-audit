# exp010_hard_regime_audit Report

**Status**: pending_review

## Results Summary

This experiment audits SOH interval reliability without using a recent SOH label.
It includes current-cycle no-label estimation and 5/20-cycle-ahead targets.

| Horizon | Task | Selected method | Coverage | Cell CI low | Width | Usable envelope? |
|---|---|---|---:|---:|---:|---|
| horizon_0 | main_heldout | stage_mondrian_cqr_no_recent_label | 0.9673 | 0.8717 | 0.2895 | yes |
| horizon_0 | leave_CALCE_out | stage_mondrian_cqr_no_recent_label | 0.8649 | 0.8291 | 0.4818 | no |
| horizon_0 | target_recalibrated_CALCE | stage_mondrian_cqr_no_recent_label | 0.4221 | 0.2819 | 0.3746 | no |
| horizon_0 | leave_NASA_out | stage_mondrian_cqr_no_recent_label | 0.2164 | 0.1405 | 0.0643 | no |
| horizon_0 | target_recalibrated_NASA | stage_mondrian_cqr_no_recent_label | 0.7075 | 0.5202 | 0.4294 | no |
| horizon_0 | leave_Oxford_out | stage_mondrian_cqr_no_recent_label | 0.0157 | 0.0087 | 0.3264 | no |
| horizon_0 | target_recalibrated_Oxford | stage_mondrian_cqr_no_recent_label | 1.0000 | 1.0000 | 0.4019 | yes |
| horizon_5 | main_heldout | stage_mondrian_cqr_no_recent_label | 0.9723 | 0.8624 | 0.2993 | yes |
| horizon_5 | leave_CALCE_out | stage_mondrian_cqr_no_recent_label | 0.8587 | 0.8209 | 0.4909 | no |
| horizon_5 | target_recalibrated_CALCE | stage_mondrian_cqr_no_recent_label | 0.4249 | 0.2743 | 0.4107 | no |
| horizon_5 | leave_NASA_out | stage_mondrian_cqr_no_recent_label | 0.1117 | 0.0596 | 0.0410 | no |
| horizon_5 | target_recalibrated_NASA | stage_mondrian_cqr_no_recent_label | 0.5833 | 0.3778 | 0.3668 | no |
| horizon_5 | leave_Oxford_out | stage_mondrian_cqr_no_recent_label | 0.0127 | 0.0054 | 0.3239 | no |
| horizon_5 | target_recalibrated_Oxford | stage_mondrian_cqr_no_recent_label | 1.0000 | 1.0000 | 0.3343 | yes |
| horizon_20 | main_heldout | stage_mondrian_cqr_no_recent_label | 0.9808 | 0.8927 | 0.3251 | yes |
| horizon_20 | leave_CALCE_out | stage_mondrian_cqr_no_recent_label | 0.8427 | 0.7996 | 0.4666 | no |
| horizon_20 | target_recalibrated_CALCE | stage_mondrian_cqr_no_recent_label | 0.3937 | 0.2484 | 0.4065 | no |
| horizon_20 | leave_NASA_out | stage_mondrian_cqr_no_recent_label | 0.0906 | 0.0410 | 0.0485 | no |
| horizon_20 | target_recalibrated_NASA | stage_mondrian_cqr_no_recent_label | 0.7179 | 0.4516 | 0.4270 | no |
| horizon_20 | leave_Oxford_out | stage_mondrian_cqr_no_recent_label | 0.0256 | 0.0096 | 0.3362 | no |
| horizon_20 | target_recalibrated_Oxford | stage_mondrian_cqr_no_recent_label | 0.3699 | 0.0822 | 0.1088 | no |

## Multiplicity

False-safe family size: 378.
Bonferroni survivors: 151.
BH-style survivors: 151.

## External Dataset Status

No additional QA-compatible modern battery dataset is available under data/raw in the current local evidence base; this run records the conditional external-validity gap rather than fabricating or synthesizing data.

Synthetic data was not used.
