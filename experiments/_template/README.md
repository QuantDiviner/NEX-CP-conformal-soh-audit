# Experiment template

Scaffold for a new experiment directory. Copy it and fill in the files:

```bash
cp -r experiments/_template experiments/exp013_short_description
```

A real experiment in this repository contains:

```
expXXX_short_description/
├── plan.md            # purpose, data policy, and analysis plan (before running)
├── metadata.json      # experiment metadata
├── report.md          # close-out report with findings (after running)
└── results/
    └── metrics.json   # metrics consumed by paper/data/metrics.json
```

See any of `exp001_main` … `exp012_shift_adaptive_cp_comparator` for complete
examples, and `experiments/README.md` for the roster. Analysis code lives in
self-contained runners under `scripts/`; the `config.yaml` in this template is
a documentation placeholder only — runners take their settings from CLI
arguments.
