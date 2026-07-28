# exp011_original_paper_substance Report

**Status**: pending_review

## Results Summary

This experiment supplies user-approved new substance for a RESS Original Paper route.
It audits whether schema choices change interval reliability and safety-decision metrics on identical real-data task splits.

| Task | Comparison | Coverage delta | 95% block CI | Width delta | MAE delta |
|---|---|---:|---:|---:|---:|
| main_heldout | artifact_bookkeeping_as_used_minus_clean_original | -0.0409 | [-0.2163, 0.1345] | 0.0199 | 0.0186 |
| main_heldout | negative_control_clean_original_minus_zero_control | -0.0112 | [-0.0297, 0.0074] | -0.0113 | 0.0008 |
| main_heldout | legitimate_feature_richness_clean_original_minus_common_no_recent | -0.0052 | [-0.0925, 0.0822] | -0.0256 | -0.0010 |
| main_heldout | recent_label_reference_common_no_recent_minus_prev_soh_reference | 0.0133 | [-0.1871, 0.2138] | 0.1681 | 0.0528 |
| main_heldout | as_used_vs_common_no_recent | -0.0461 | [-0.2656, 0.1735] | -0.0058 | 0.0176 |
| leave_CALCE_out | artifact_bookkeeping_as_used_minus_clean_original | 0.0318 | [0.0125, 0.0512] | 0.0540 | -0.0008 |
| leave_CALCE_out | negative_control_clean_original_minus_zero_control | -0.0062 | [-0.0101, -0.0023] | -0.0091 | 0.0017 |
| leave_CALCE_out | legitimate_feature_richness_clean_original_minus_common_no_recent | 0.1815 | [0.1026, 0.2604] | 0.0733 | -0.0786 |
| leave_CALCE_out | recent_label_reference_common_no_recent_minus_prev_soh_reference | -0.1008 | [-0.1681, -0.0334] | 0.1821 | 0.1359 |
| leave_CALCE_out | as_used_vs_common_no_recent | 0.2133 | [0.1230, 0.3037] | 0.1273 | -0.0794 |
| target_recalibrated_CALCE | artifact_bookkeeping_as_used_minus_clean_original | -0.0217 | [-0.0694, 0.0260] | -0.0614 | -0.0097 |
| target_recalibrated_CALCE | negative_control_clean_original_minus_zero_control | -0.0002 | [-0.0266, 0.0262] | -0.0002 | -0.0110 |
| target_recalibrated_CALCE | legitimate_feature_richness_clean_original_minus_common_no_recent | 0.0153 | [-0.0115, 0.0421] | 0.0360 | -0.0196 |
| target_recalibrated_CALCE | recent_label_reference_common_no_recent_minus_prev_soh_reference | -0.6042 | [-0.7360, -0.4724] | -0.0476 | 0.1645 |
| target_recalibrated_CALCE | as_used_vs_common_no_recent | -0.0064 | [-0.0304, 0.0176] | -0.0254 | -0.0294 |
| leave_NASA_out | artifact_bookkeeping_as_used_minus_clean_original | -0.1198 | [-0.2053, -0.0343] | -0.0415 | -0.0321 |
| leave_NASA_out | negative_control_clean_original_minus_zero_control | -0.0098 | [-0.0204, 0.0007] | -0.0033 | -0.0056 |
| leave_NASA_out | legitimate_feature_richness_clean_original_minus_common_no_recent | 0.0804 | [0.0244, 0.1364] | 0.0385 | 0.0334 |
| leave_NASA_out | recent_label_reference_common_no_recent_minus_prev_soh_reference | -0.3189 | [-0.4066, -0.2311] | -0.0640 | 0.0456 |
| leave_NASA_out | as_used_vs_common_no_recent | -0.0394 | [-0.0773, -0.0014] | -0.0030 | 0.0013 |
| target_recalibrated_NASA | artifact_bookkeeping_as_used_minus_clean_original | -0.0996 | [-0.3117, 0.1125] | -0.0275 | -0.0054 |
| target_recalibrated_NASA | negative_control_clean_original_minus_zero_control | -0.0013 | [-0.0160, 0.0135] | 0.0028 | -0.0001 |
| target_recalibrated_NASA | legitimate_feature_richness_clean_original_minus_common_no_recent | 0.1354 | [-0.2511, 0.5219] | -0.0324 | -0.0403 |
| target_recalibrated_NASA | recent_label_reference_common_no_recent_minus_prev_soh_reference | -0.4151 | [-0.7336, -0.0966] | 0.0647 | 0.0693 |
| target_recalibrated_NASA | as_used_vs_common_no_recent | 0.0358 | [-0.2023, 0.2738] | -0.0599 | -0.0458 |
| leave_Oxford_out | artifact_bookkeeping_as_used_minus_clean_original | 0.0039 | [-0.0051, 0.0129] | 0.1287 | -0.0155 |
| leave_Oxford_out | negative_control_clean_original_minus_zero_control | -0.0020 | [-0.0095, 0.0056] | -0.0183 | -0.0019 |
| leave_Oxford_out | legitimate_feature_richness_clean_original_minus_common_no_recent | -0.0020 | [-0.0095, 0.0056] | 0.0046 | 0.0585 |
| leave_Oxford_out | recent_label_reference_common_no_recent_minus_prev_soh_reference | -0.3757 | [-0.5313, -0.2202] | 0.1049 | 0.3075 |
| leave_Oxford_out | as_used_vs_common_no_recent | 0.0020 | [-0.0046, 0.0085] | 0.1333 | 0.0430 |
| target_recalibrated_Oxford | artifact_bookkeeping_as_used_minus_clean_original | 0.0000 | [0.0000, 0.0000] | -0.0215 | 0.0124 |
| target_recalibrated_Oxford | negative_control_clean_original_minus_zero_control | -0.0043 | [-0.0210, 0.0124] | -0.0245 | 0.0339 |
| target_recalibrated_Oxford | legitimate_feature_richness_clean_original_minus_common_no_recent | -0.0043 | [-0.0210, 0.0124] | -0.5656 | -0.2321 |
| target_recalibrated_Oxford | recent_label_reference_common_no_recent_minus_prev_soh_reference | 0.0429 | [-0.0162, 0.1020] | 0.8411 | 0.3103 |
| target_recalibrated_Oxford | as_used_vs_common_no_recent | -0.0043 | [-0.0210, 0.0124] | -0.5871 | -0.2197 |

## External Dataset Inventory

Additional QA-usable external dataset available now: False.

## Data Policy

Synthetic data was not used. Any external dataset must pass the same real-data QA preprocessor before it can support a claim.
