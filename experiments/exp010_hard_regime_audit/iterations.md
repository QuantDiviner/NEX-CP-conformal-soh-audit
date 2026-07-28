# exp010_hard_regime_audit Iterations

## Iteration 1

- Time: 2026-05-30
- Source plan:
  `docs/reports/20260530_215915_fpa_revision_20260530_215247_revision_plan.md`
- Command:

```bash
python scripts/run_hard_regime_audit_experiment.py --output-exp exp010_hard_regime_audit --seed 42 --bootstrap-reps 1000 --min-decision-denominator 5 --horizons 0,5,20
```

- Result: generated `results/metrics.json`, `results/multiplicity_control.json`,
  `results/run_manifest.json`, and `results/split_manifest.json`.
- External review:
  `docs/reports/20260530_223324_D-EXP-exp010_hard_regime_audit_codex.md`
- Review route: A
- Reviewer note: `iterations.md` was absent during review; this file backfills
  that archival completeness issue without changing the experimental result.
- Closure: supports bounded RESS hard-regime reliability/safety audit claims
  only; broad transfer and method-superiority claims remain unsupported.
