# Recent-Label Dependence in Cross-Dataset Conformal SOH Evaluation: A Benchmark-Integrity Case Study

Official replication package for the manuscript:

**"Recent-Label Dependence in Cross-Dataset Conformal SOH Evaluation: A Benchmark-Integrity Case Study"**
Qingsong Shan, Qianning Liu (Jiangxi University of Finance and Economics)
Target journal: *Reliability Engineering & System Safety* (Short Communication / Case Study)

---

## Overview

Conformal prediction (CP) provides distribution-free uncertainty guarantees for
battery State of Health (SOH) estimation. This case study audits how benchmark
design choices — specifically recent-label availability, cell-block separation,
and time-forward calibration — affect reported coverage validity when
conformal SOH algorithms are evaluated across real-world cycle trajectories.

The repository contains the complete deterministic analysis pipeline, the
dataset preprocessing and QA-gating code, all experiment metrics and run
manifests, the numerical single source of truth (`paper/data/metrics.json`),
and the Quarto manuscript sources. All results are derived exclusively from
the public **CALCE**, **NASA**, and **Oxford** battery degradation corpora
(45 QA-passing cells); no synthetic data are used anywhere.

---

## Repository structure

```text
NEX-CP-conformal-soh-audit/
├── README.md                   # This file
├── LICENSE                     # MIT License
├── pyproject.toml              # Package metadata and locked dependency versions
├── requirements.txt            # Pinned Python dependencies
├── environment.yml             # Conda environment specification (equivalent)
│
├── scripts/                    # Self-contained analysis pipeline (run from repo root)
│   ├── download_data.py        # Prints manual acquisition instructions for the 3 datasets
│   ├── preprocess_real_battery.py            # Raw data -> QA-gated cycle-level SOH table + splits
│   ├── run_real_experiments.py               # exp001-exp005: main coverage audit, ablation,
│   │                                         #   cross-protocol transfer, stress probe, cost screen
│   ├── run_fpa_repair_experiment.py          # exp006/exp007: baseline & dependence-aware repair analyses
│   ├── run_reliability_audit_experiment.py   # exp008/exp009: reliability & safety-boundary audit
│   ├── run_hard_regime_audit_experiment.py   # exp010: hard-regime audit (no recent labels)
│   ├── run_original_paper_substance_experiment.py # exp011: feature-schema measurement-validity audit
│   ├── run_shift_adaptive_cp_comparator.py   # exp012: shift-adaptive conformal comparator
│   └── run_pcr_20260718_repair.py            # Batch driver that deterministically reruns the
│                                             #   repair runners with their locked arguments
│
├── src/                        # Empty package skeletons only (no implementation).
│                               # The analysis pipeline is entirely under scripts/.
│
├── data/
│   ├── raw/                    # Raw datasets (NOT included; manual download, gitignored)
│   ├── processed/              # Generated cycle-level tables (not tracked)
│   └── splits/                 # Tracked preprocessing outputs: QA log (45 passing cells),
│                               # split manifest, run manifest, skipped-cell ledger
│
├── experiments/                # One directory per experiment (see experiments/README.md)
│   ├── exp001_main/ ... exp005_edge/
│   │                           # exp001-exp005: results/metrics.json only
│   ├── exp006_fpa_repair/ ... exp012_shift_adaptive_cp_comparator/
│   │                           # exp006-exp012: results/metrics.json + results/run_manifest.json
│   │                           # (plus split manifests and task-specific outputs)
│   └── _template/              # Scaffold for new experiment directories
│
└── paper/
    ├── data/                   # Numerical SSOT
    │   ├── metrics.json        # Every number quoted in text, tables, and figures
    │   ├── metrics_manifest.yaml
    │   └── external_facts.yaml
    ├── source/                 # Quarto manuscript (index.qmd + section files),
    │   │                       # references/main.bib, Elsevier assets
    │   └── figures/            # Vector figures (PDF) used by the manuscript
    ├── scripts/                # SSOT maintenance & consistency-check utilities
    └── templates/              # Reference copies of elsarticle / quarto-elsevier assets
```

---

## Requirements

- **Python 3.11** (results were produced with CPython 3.11.15; `pyproject.toml`
  allows `>=3.11,<3.13`)
- Python-side dependencies are pinned identically in `requirements.txt`,
  `environment.yml`, and `pyproject.toml` (numpy 2.2.6, pandas 2.3.3,
  scikit-learn 1.7.2, scipy 1.15.3, plus supporting packages)

Install with pip:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

or with conda:

```bash
conda env create -f environment.yml
conda activate nex-cp-conformal-soh-audit
```

The `scripts/run_*.py` runners are self-contained and are executed directly
from the repository root; no package installation (`pip install -e .`) is
required.

---

## Data acquisition

Raw battery data are **not redistributed** here and must be obtained manually
from the three public sources:

- **CALCE Battery Research Group**: <https://calce.umd.edu/battery-data> → place under `data/raw/calce/`
- **NASA Ames PCoE Data Set Repository**: <https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/> → place under `data/raw/nasa/`
- **Oxford Battery Degradation Dataset 1**: <https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac> → place under `data/raw/oxford/`

`python scripts/download_data.py` prints the same instructions with
per-dataset layout notes. See `data/README.md` for details.

---

## Reproducing the analysis

### Step 1 — Preprocessing and QA gating

```bash
python scripts/preprocess_real_battery.py
```

Builds `data/processed/real_battery_cycle_level_features.csv` from `data/raw/`,
applies per-cell QA gating (55 candidate cells → 45 passing), and writes the
time-forward, cell-separated splits to `data/splits/`. The tracked artifacts
under `data/splits/` already contain these outputs, so this step is only
needed to verify the pipeline end-to-end.

### Step 2 — Experiment runners

```bash
python scripts/run_real_experiments.py                  # exp001-exp005
python scripts/run_fpa_repair_experiment.py             # exp006/exp007 analyses
python scripts/run_reliability_audit_experiment.py      # exp008/exp009 analyses
python scripts/run_hard_regime_audit_experiment.py      # exp010
python scripts/run_original_paper_substance_experiment.py # exp011
python scripts/run_shift_adaptive_cp_comparator.py      # exp012
```

Each runner reads the processed table and split manifest, and rewrites the
`results/` directory of its experiment(s). `scripts/run_pcr_20260718_repair.py`
is a batch driver that reruns the three repair runners with the exact locked
arguments used for the reported metrics. All reported metrics are already
committed under `experiments/*/results/` and aggregated in
`paper/data/metrics.json`.

### Step 3 — Rendering the manuscript (optional)

Requires Quarto and a TeX Live installation, plus the rendering-only Python
packages listed in `requirements.txt`:

```bash
quarto render paper/source/index.qmd
```

The manuscript injects every quoted number from `paper/data/metrics.json` at
render time; no numerical result is hard-coded in the text.

---

## Citation

If you use this code or data, please cite:

> Qingsong Shan, Qianning Liu. "Recent-Label Dependence in Cross-Dataset
> Conformal SOH Evaluation: A Benchmark-Integrity Case Study." Jiangxi
> University of Finance and Economics. Replication package:
> <https://github.com/QuantDiviner/NEX-CP-conformal-soh-audit>

```bibtex
@misc{shan_liu_conformal_soh_audit,
  author       = {Shan, Qingsong and Liu, Qianning},
  title        = {Recent-Label Dependence in Cross-Dataset Conformal {SOH}
                  Evaluation: A Benchmark-Integrity Case Study},
  howpublished = {Replication package,
                  \url{https://github.com/QuantDiviner/NEX-CP-conformal-soh-audit}},
  year         = {2026},
}
```

---

## License

This repository is licensed under the [MIT License](LICENSE). The underlying
battery datasets remain the property of their respective providers (CALCE,
NASA, Oxford) and are subject to their own terms of use.
