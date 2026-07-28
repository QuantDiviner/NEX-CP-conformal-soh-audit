# Paper

Quarto manuscript sources and the numerical single source of truth (SSOT).

## Layout

- `source/` — Quarto manuscript (`index.qmd` plus `01-`–`06-` section files),
  `references/main.bib`, `highlights.md`, and the Elsevier assets
  (`elsarticle.cls`, `elsarticle-num.bst`, `ieee.csl`, `_extensions/elsevier/`).
  Vector figures (PDF) live in `source/figures/`.
- `data/` — numerical SSOT:
  - `metrics.json` — every number quoted in text, tables, and figures
  - `metrics_manifest.yaml` — semantic manifest for the metrics
  - `external_facts.yaml` — ledger of external facts cited in the manuscript
- `scripts/` — maintenance utilities for the SSOT (`collect_results.py`,
  `recompute_aggregates.py`, `validate_metrics_manifest.py`,
  `validate_external_facts.py`, `check_hardcoded_numbers.py`, and related
  linters). These are internal consistency checkers, not part of the analysis
  pipeline.
- `templates/` — pristine copies of the Elsevier `elsarticle` package and the
  Quarto `quarto-journals/elsevier` extension, kept for reference.

## Rendering

```bash
quarto render paper/source/index.qmd
```

requires Quarto plus a TeX Live installation, and the Python packages listed
under the "paper rendering" section of `requirements.txt` (the manuscript
executes Python inline to inject numbers from `paper/data/metrics.json`).
