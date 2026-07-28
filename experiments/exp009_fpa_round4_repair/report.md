# exp009_fpa_round4_repair Report

**Status**: validated_route_A

## Purpose

This experiment implements the P0 workstreams from the FPA Round 4 revision
plan for Reliability Engineering & System Safety:

- P0-R1: lock q-selection and headline width reproducibility.
- P0-R2: record claim-boundary audit.
- P0-R3: gate width comparisons by coverage alignment.
- P0-R4: rerun leave-NASA under a common feature schema.
- P0-R5: suppress or flag low-denominator decision-utility cells.

## Key Results

| Task | Method | Coverage | Cell CI low | Width | q/qhat |
|---|---|---:|---:|---:|---:|
| main_heldout | persistence_anchor_protocol_mondrian_cp | 0.9471 | 0.9417 | 0.0369 | 0.9300 |
| main_heldout | cqr_gradient_boosting | 0.9522 | 0.9416 | 0.1020 | 0.0033 |
| main_heldout | ngboost_normal_cqr | 0.8390 | 0.4875 | 0.0860 | 0.0194 |
| leave_NASA_out | persistence_anchor_protocol_mondrian_cp | 0.8060 | 0.7349 | 0.0267 | 0.9300 |
| leave_NASA_out | cqr_gradient_boosting | 0.9218 | 0.8930 | 0.2095 | 0.0024 |
| leave_NASA_out_common_feature_schema | persistence_anchor_protocol_mondrian_cp | 0.8060 | 0.7349 | 0.0267 | 0.9300 |
| leave_NASA_out_common_feature_schema | cqr_gradient_boosting | 0.6885 | 0.6299 | 0.1524 | 0.0012 |

## P0-R1 Reproducibility Lock

The main held-out persistence result is reproduced with `q=0.93`, coverage
0.9471, cell-block CI low 0.9417, and mean width 0.0369. The q-selection trace
is stored under:

- `results/metrics.json`
  `.tasks.main_heldout.methods.persistence_anchor_protocol_mondrian_cp.q_selection_trace`

The deterministic regeneration command is stored in:

- `results/run_manifest.json`
  `.deterministic_regeneration_command`

The exp006/exp007 width discrepancy is explained by q-selection: exp006 used a
wider selected q level (`q=0.97`, width near 0.2255), whereas exp007/exp008 and
this run select `q=0.93` under the validation-only coverage-first width
objective.

## P0-R2 Claim-Boundary Audit

The run records a claim-boundary audit in `results/metrics.json`.

Remaining flagged files:

- `docs/narrative-framework.md`
- `docs/research-summary.md`
- `experiments/exp008_reliability_audit/report.md`

These flags are conservative string matches. They must be resolved before
manuscript work, but no `paper/` files were edited in this experiment.

## P0-R3 Coverage-Aligned Comparison

Main held-out CQR is coverage-aligned against the persistence anchor
(`coverage_gap=0.0052`) and therefore width comparison is permitted for that
cell. QR and NGBoost are not coverage-aligned and should be interpreted as
coverage recovery/collapse diagnostics, not as width-superiority comparisons.

The full machine-readable alignment table is:

- `results/baseline_alignment.json`

## P0-R4 Harmonized Leave-NASA Diagnostic

The harmonized leave-NASA diagnostic uses the common feature schema:

- `cycle_index`
- `log_cycle_index`
- `prev_soh`

Removing unavailable feature and missingness indicators reduces max absolute
SMD from 7.0219 to 1.3000. This confirms that the original shift diagnostic was
dominated by feature-schema/missingness effects. However, the persistence
anchor's leave-NASA coverage remains 0.8060 because that interval is driven by
`prev_soh` residual calibration rather than the learned feature schema. The
mechanism interpretation must therefore separate:

- feature-schema shift as the dominant measured covariate shift, and
- residual protocol/dataset non-exchangeability as the remaining coverage
  failure.

## P0-R5 Decision Utility Reliability

Decision-utility outputs now include:

- denominator count,
- effective cell count,
- interpretation labels,
- threshold-sweep multiplicity family size.

Cells below `min_decision_denominator=5` are marked
`suppressed_low_denominator` or `suppressed_no_denominator`; they must not be
used as definitive safety claims.

## Artifacts

- `results/metrics.json`
- `results/run_manifest.json`
- `results/split_manifest.json`
- `results/baseline_alignment.json`
- `results/decision_utility_ci.json`
- `results/shift_diagnostics.json`

Synthetic data was not used.
