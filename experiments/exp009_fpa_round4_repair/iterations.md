# exp009_fpa_round4_repair Iterations

## Iteration 1

- Time: 2026-05-30
- Source plan:
  `docs/reports/20260530_210059_fpa_revision_20260530_205235_revision_plan.md`
- Command:

```bash
python scripts/run_reliability_audit_experiment.py --output-exp exp009_fpa_round4_repair --seed 42 --bootstrap-reps 1000 --min-decision-denominator 5 --include-ngboost --add-harmonized-leave-nasa
```

- Result: generated `results/metrics.json` and associated split, run,
  alignment, decision-utility, and shift-diagnostic artifacts.
- External review:
  `docs/reports/20260530_211022_D-EXP-exp009_fpa_round4_repair_codex.md`
- Review route: A
- Follow-up governance cleanup: claim-boundary string hits were rewritten to
  avoid false positives before paper/manuscript work.

