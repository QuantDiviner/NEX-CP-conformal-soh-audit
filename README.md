# Recent-Label Availability and Benchmark Integrity in Conformal SOH Estimation

Official replication package for the manuscript:  
**"Recent-Label Availability and Benchmark Integrity in Conformal SOH Estimation"**  
*Target Journal*: Reliability Engineering & System Safety (RESS) — Case Study

---

## 📌 Abstract & Repository Overview

Conformal prediction (CP) provides distribution-free uncertainty guarantees for battery State of Health (SOH) estimation. However, when evaluating conformal SOH algorithms across real-world cycle trajectories, benchmark design choices—specifically recent-label availability, cell-block separation, and time-forward calibration—profoundly affect reported coverage validity.

This repository provides the complete, deterministic replication code, dataset preprocessing pipelines, metrics single source of truth (`paper/data/metrics.json`), and Quarto manuscript sources for auditing conformal battery SOH evidence across public **CALCE**, **NASA**, and **Oxford** battery degradation corpora.

---

## 📁 Repository Structure

```text
NEX-CP-conformal-soh-audit/
├── README.md                   # Repository guide and reproducibility instructions
├── LICENSE                     # MIT License
├── pyproject.toml              # Build & package metadata
├── requirements.txt            # Locked Python dependencies
├── environment.yml             # Conda environment specification
├── research.conf               # Immutable experiment configuration
│
├── src/                        # Core Python library
│   ├── models/                 # Quantile Regression, CQR, and CP backbones
│   └── utils/                  # Evaluation, bootstrap CI, and QA utilities
│
├── scripts/                    # Executable workflow scripts
│   ├── download_data.py        # Dataset downloader (CALCE, NASA, Oxford)
│   ├── preprocess_real_battery.py # Real-data QA filtering & cell-block split generator
│   ├── run_real_experiments.py # Main conformal evaluation runner (exp001 - exp005)
│   ├── run_reliability_audit_experiment.py  # Reliability audit (exp008)
│   ├── run_hard_regime_audit_experiment.py   # Hard regime audit (exp010)
│   ├── run_original_paper_substance_experiment.py # Schema sensitivity audit (exp011)
│   └── run_shift_adaptive_cp_comparator.py   # Shift-adaptive CP comparator (exp012)
│
├── data/                       # Preprocessing QA & Split Metadata
│   ├── splits/
│   │   ├── real_battery_preprocess_qa.csv  # QA pass/fail logs across 44 battery cells
│   │   ├── real_battery_splits.json         # Time-forward cell-separated splits
│   │   └── real_battery_skipped_sources.json
│   └── README.md
│
├── experiments/                # Experiment execution manifests and reports
│   ├── exp001_main/            # Main marginal & conditional coverage audit
│   ├── exp003_cross_protocol/  # Cross-dataset transfer stress test
│   ├── exp008_reliability_audit/ # Reliability & safety boundary audit
│   ├── exp011_original_paper_substance/ # Controlled schema-bundle audit
│   └── exp012_shift_adaptive_cp_comparator/ # Shift-adaptive comparator
│
└── paper/                      # Quarto paper source & numerical SSOT
    ├── data/
    │   ├── metrics.json        # Primary numerical SSOT for all figures & tables
    │   ├── metrics_manifest.yaml
    │   └── external_facts.yaml
    ├── figures/                # Vector artwork (PDF/SVG)
    └── source/                 # Quarto manuscript (.qmd) & Elsevier LaTeX templates
```

---

## 🛠️ Installation & Setup

### 1. Environment Setup

Python 3.10+ is recommended. Create and activate a clean virtual environment:

```bash
# Using venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Dataset Access

This study utilizes real cycle-level battery aging records from three public repositories:
- **CALCE Battery Research Group**: [https://calce.umd.edu/battery-data](https://calce.umd.edu/battery-data)
- **NASA Ames PCoE Repository**: [https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)
- **Oxford Battery Degradation Dataset**: [https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac](https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac)

To download or verify raw dataset records, execute:

```bash
python scripts/download_data.py
```

---

## 🚀 Quickstart & Reproducibility Guide

### Step 1: Preprocessing & Leakage-Safe QA Audit

Run the preprocessing QA pipeline to inspect cell records, apply capacity spike filtering, and generate time-forward cell-block splits:

```bash
python scripts/preprocess_real_battery.py
```

Outputs will be saved in `data/splits/real_battery_preprocess_qa.csv` and `data/splits/real_battery_splits.json`.

### Step 2: Running Conformal Calibration Audits

To reproduce the core conformal calibration experiments, execute the evaluation runners:

```bash
# Main conformal calibration & cross-protocol stress test (exp001 - exp005)
python scripts/run_real_experiments.py

# Reliability and safety threshold failure audit (exp008)
python scripts/run_reliability_audit_experiment.py

# Shift-adaptive conformal comparator (exp012)
python scripts/run_shift_adaptive_cp_comparator.py
```

### Step 3: Compiling the Manuscript

The paper is written using Quarto and rendered with Elsevier LaTeX assets:

```bash
# Render manuscript to PDF
quarto render paper/source/index.qmd --to pdf
```

---

## 📊 Data & Code Availability Statement

For manuscript submission (Option C repository deposit):
- **Code & Manifests**: Deposited in this repository (`NEX-CP-conformal-soh-audit`).
- **Numerical SSOT**: All active numbers in text, tables, and figures are dynamically read from `paper/data/metrics.json`.

---

## 📜 License

This repository is licensed under the [MIT License](LICENSE).
