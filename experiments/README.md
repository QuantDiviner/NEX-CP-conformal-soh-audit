# Experiments

This directory contains the twelve experiments reported in the manuscript.
Each experiment directory holds:

- `plan.md` — pre-registered purpose, data policy, and analysis plan
- `metadata.json` — experiment metadata
- `report.md` — closing report with findings
- `results/metrics.json` — metrics consumed by the paper SSOT (`paper/data/metrics.json`)
- `results/run_manifest.json` — execution manifest (exp006–exp012 only; includes
  code version, package versions, seeds, and CLI arguments)
- `records/` — internal review records kept for audit traceability

## Experiment roster

| Experiment | Role |
|---|---|
| `exp001_main` | Main marginal and conditional coverage audit of conformal SOH intervals on QA-gated CALCE/NASA/Oxford real data |
| `exp002_ablation` | Feature and calibration ablation: dependence of the exp001 result on `prev_soh` persistence and resistance features |
| `exp003_cross_protocol` | Leave-domain-out cross-protocol transfer stress test |
| `exp004_stress_failure` | Real residual stress probe: interval behavior under systematically biased point predictions |
| `exp005_edge` | Host-only compute-cost screen for the selected interval path (not a deployment claim) |
| `exp006_fpa_repair` | Repair round 1: RESS-level comparative baselines, dependence-aware coverage intervals, cross-protocol failure diagnostics |
| `exp007_fpa_round2_repair` | Repair round 2: cross-family UQ baselines and decision-utility analysis |
| `exp008_reliability_audit` | Reliability and safety-boundary audit: when intervals are trustworthy and when protocol non-exchangeability breaks them |
| `exp009_fpa_round4_repair` | Repair round 4: experiment-level blocker resolution for the RESS route |
| `exp010_hard_regime_audit` | Hard-regime audit: no recent SOH label at decision time, multi-step-ahead targets, threshold sweep, multiplicity-controlled decision utility |
| `exp011_original_paper_substance` | Measurement-validity experiment: whether feature-schema choices alter cross-dataset interval reliability and safety-decision conclusions on identical splits |
| `exp012_shift_adaptive_cp_comparator` | Comparator test: can a shift-adaptive conformal method recover a usable trust/recalibrate/abstain envelope under the same protocol shifts |

exp001–exp005 were run before the run-manifest convention was adopted and
contain only `results/metrics.json` under `results/`; exp006–exp012 also
contain `results/run_manifest.json` (plus `split_manifest.json` and
task-specific outputs).

The runner scripts live in `scripts/` (see the repository root `README.md`
for the script-to-experiment mapping). `_template/` is a scaffold for new
experiment directories.
