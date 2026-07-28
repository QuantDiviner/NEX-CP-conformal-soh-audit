# exp011_original_paper_substance Plan

## Purpose

Supply the user-approved new substance required for a RESS Original Paper route
after FPA Round 8. This is not another method-superiority repair. It is a
measurement-validity experiment testing whether feature-schema choices alter
cross-dataset SOH interval reliability and safety-decision conclusions on the
same real-data splits.

## Source Gate

- User direction: Round 8 option 2, approve new substantive evidence for RESS
  Original Paper.
- State transition: `GLOBAL_DIAGNOSING -> EXP_PLANNING` via T-GDIAG-EXP.
- Trajectory checkpoint: `.checkpoints/trajectory_ack.json`.

## Data Policy

- Real CALCE, NASA, and Oxford SOH data only unless an additional local dataset
  passes the existing QA preprocessor.
- Synthetic data is prohibited.
- The `MIT_Stanford_Toyota` raw-data symlink is audited for availability, but it
  cannot support a claim unless mounted and accepted by QA.

## Execution

```bash
python scripts/run_original_paper_substance_experiment.py \
  --output-exp exp011_original_paper_substance \
  --seed 42 \
  --bootstrap-reps 1000 \
  --min-decision-denominator 5
```

## Design

For each main and cross-protocol task at horizon 0, fit the same CQR gradient
boosting interval procedure under four schema definitions:

- `as_used_exp010_schema`: exact exp010 task schema, retained for audit.
- `clean_original_no_recent_schema`: exp010 no-recent schema after removing
  bookkeeping features such as `source_row_id` and `target_cycle_index`.
- `common_cycle_no_recent_schema`: `cycle_index`, `log_cycle_index`.
- `common_cycle_prev_soh_reference_schema`: `cycle_index`, `log_cycle_index`,
  `prev_soh`; reference only, not a no-recent-label decision policy.
- `clean_original_negative_control_schema`: duplicate clean-original fitted
  intervals with the same row-alignment mask and an inert constant-zero schema
  marker, used as a negative-control check of the delta machinery.

The experiment reports paired cell-block bootstrap CIs for schema-induced
coverage deltas and false-safe-rate deltas on identical test rows. All schemas
within a task use the same train/cal/test rows after intersecting non-null
feature requirements.

## Preregistered Delta Classes

| Comparison | Class | Claim Use |
|---|---|---|
| `as_used_exp010_schema - clean_original_no_recent_schema` | bookkeeping artifact isolation | May support the schema-artifact headline |
| `clean_original_no_recent_schema - common_cycle_no_recent_schema` | legitimate feature-set sensitivity | Scope and robustness only |
| `common_cycle_no_recent_schema - common_cycle_prev_soh_reference_schema` | reference-only recent-label sensitivity | Not a policy recommendation |
| `clean_original_no_recent_schema - clean_original_negative_control_schema` | negative control for delta machinery | Must not trigger |

Artifact is declared only if the bookkeeping-artifact comparison has a
Bonferroni-adjusted paired cell-block CI excluding zero and either absolute
coverage delta is at least 0.03 or at least one false-safe-rate delta CI excludes
zero. If the negative control triggers, the instrument is invalid and the
artifact claim is blocked.

If the bookkeeping-artifact comparison triggers for any task, exp010
no-recent-label conclusions that used `source_row_id` or `target_cycle_index`
must be downgraded or explicitly labeled contaminated before any later FPA.

## Expected Outputs

- `experiments/exp011_original_paper_substance/results/metrics.json`
- `experiments/exp011_original_paper_substance/results/schema_delta_summary.json`
- `experiments/exp011_original_paper_substance/results/multiplicity_control.json`
- `experiments/exp011_original_paper_substance/results/external_dataset_inventory.json`
- `experiments/exp011_original_paper_substance/results/run_manifest.json`
- `experiments/exp011_original_paper_substance/results/split_manifest.json`

## Closure Criteria

- Every reported row is generated from real QA-accepted battery data.
- Schema comparisons use identical task splits and identical interval method.
- Coverage deltas include paired cell-block bootstrap 95% CIs.
- Headline delta CIs use Bonferroni adjustment across all preregistered
  schema-delta coverage and false-safe tests.
- False-safe deltas are reported across SOH thresholds 0.90 to 0.65 with
  low-denominator suppression.
- External dataset availability is recorded without fabricating data or treating
  unmounted data as evidence.
- Claims remain measurement-validity / benchmark-reliability claims, not
  method-superiority or deployment claims.

## External Plan Review

- Review: `docs/reports/20260531_105241_D-PLAN-exp011_original_paper_substance_opus.md`
- P0 fixes incorporated before execution:
  - Added `as_used_exp010_schema - clean_original_no_recent_schema` as the
    isolated bookkeeping-artifact contrast.
  - Added preregistered artifact decision rules and a negative-control schema.
  - Restored multiplicity-adjusted headline delta CIs and
    `multiplicity_control.json`.
  - Reframed `as_used_exp010_schema` as a contaminated condition under test and
    added an exp010 downgrade trigger.

## Amendment 1: Negative-Control Implementation

The first formal execution showed that fitting a new GB-CQR model after adding a
constant zero feature can still change predictions through implementation-level
tie/randomness effects. That behavior invalidates the negative-control
instrument as a pure delta-machinery check. The script now implements the
negative control by duplicating the clean-original fitted intervals under the
same row-alignment mask and inert constant-zero schema marker. Any non-zero delta
after this amendment is therefore a bug in the paired-delta machinery, not model
refitting noise.
