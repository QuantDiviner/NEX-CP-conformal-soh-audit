# exp012_shift_adaptive_cp_comparator Plan

## Purpose

Resolve the FPA Round 10 C5 comparative-validity blocker for the RESS Short
Communication / Case Study route. The experiment tests whether a conformal
method designed for non-exchangeability can recover a usable
trust/recalibrate/abstain envelope under the same real-data protocol shifts
already audited in exp008-exp011.

This is a narrow FPA repair, not a return to method-superiority framing. The
allowed outcome is either:

- shift-adaptive conformal calibration still fails, strengthening the RESS
  safety warning; or
- shift-adaptive conformal calibration partially recovers coverage, turning the
  contribution into a bounded recovery/failure-envelope case study.

## Source Gate

- User direction: continue RESS after the Round 10 better-angle escalation.
- FPA source: `docs/reports/20260531_121759_20260531_121759_fpa_chain_summary.md`
- Blocking reviewer report:
  `docs/reports/20260531_122702_20260531_121759_fpa_R1_claude_claude.md`
- Triggered cluster: `methodology_extension` in `docs/fpa-better-angle-ledger.md`

## Data Policy

- Real CALCE, NASA, and Oxford SOH data only.
- Synthetic data is prohibited.
- No new dataset is required for the P0 repair. The fourth-dataset issue remains
  a disclosed C4 scope boundary unless a QA-compatible local dataset is mounted
  and accepted by the existing preprocessor.

## Execution

```bash
python scripts/run_shift_adaptive_cp_comparator.py \
  --output-exp exp012_shift_adaptive_cp_comparator \
  --seed 42 \
  --bootstrap-reps 1000 \
  --min-decision-denominator 5
```

## Design

Run on the existing split definitions and task family used by the current RESS
evidence package:

- `main_heldout`
- leave-one-domain-out tasks for CALCE, NASA, Oxford
- target-recalibrated CALCE, NASA, Oxford

Compare the already established non-shift-designed baselines against at least
one shift-adaptive conformal comparator on identical rows:

- baseline reference: CQR gradient boosting under the current task schema
- required adaptive comparator: weighted conformal CQR with validation-selected
  covariate-shift bandwidth
- optional if feasible: online ACI-style residual calibration using validation
  only for parameter choice and test stream order only for sequential updates

The weighted comparator must use calibration residuals with weights derived from
predeclared shift features available in both calibration and test rows. Candidate
features are `cycle_index`, `log_cycle_index`, and the clean no-recent schema
features used by exp011. Bandwidth / neighbor parameters are selected on
validation coverage-first width objective only; test metrics are never used for
selection.

## Required Outputs

- `experiments/exp012_shift_adaptive_cp_comparator/results/metrics.json`
- `experiments/exp012_shift_adaptive_cp_comparator/results/comparator_summary.json`
- `experiments/exp012_shift_adaptive_cp_comparator/results/decision_utility_ci.json`
- `experiments/exp012_shift_adaptive_cp_comparator/results/multiplicity_control.json`
- `experiments/exp012_shift_adaptive_cp_comparator/results/run_manifest.json`
- `experiments/exp012_shift_adaptive_cp_comparator/results/split_manifest.json`

## Closure Criteria

- Every reported row is generated from real QA-accepted battery data.
- All methods use identical train/cal/validation/test rows per task.
- Test-set results are not used for method or bandwidth selection.
- Coverage, mean width, SOH-normalized width, MAE, RMSE, cell-block CIs, and
  false-safe / false-alarm decision utility are reported for each comparator.
- Decision utility uses `min_decision_denominator=5` suppression.
- Multiplicity and effective cell counts are reported for false-safe claims.
- Interpretation remains RESS reliability / measurement-validity evidence, not
  broad transfer, deployment, Neural-ODE, NEX-CP, or method-superiority evidence.

## FPA Decision Rule

After external experiment review closes this experiment, rerun FPA under the
same RESS Short Communication / Case Study benchmark-integrity standard.

- If the adaptive comparator also fails under protocol shift, report a stronger
  negative safety warning.
- If it recovers only some tasks, report the recovered tasks as bounded
  preconditions and the unrecovered tasks as the reliability boundary.
- If it broadly succeeds, demote the current "unsafe under shift" language and
  reframe the paper around the recovery envelope.
