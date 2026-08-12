# A Benchmark-Integrity Audit Protocol for Conformal Battery State-of-Health Evaluation

Official replication repository and benchmark-integrity audit suite for conformal battery state-of-health (SOH) evaluation under distribution shift.

---

## 📌 Paper Overview

- **Title**: A Benchmark-Integrity Audit Protocol for Conformal Battery State-of-Health Evaluation
- **Authors**: Qingsong Shan¹ and Qianning Liu¹*
  - ¹ *School of Statistics and Data Science, Key Laboratory of Data Science in Finance and Economics, Jiangxi University of Finance and Economics, Nanchang, China*
  - * Corresponding Author: Qianning Liu (email: `liuqianning@jxufe.edu.cn`)

---

## 📝 Abstract

Conformal intervals for lithium-ion battery state-of-health (SOH) inform maintenance decisions, but cross-dataset validation can conceal measurement conditions. We develop a six-gate benchmark-integrity audit of prediction-time information, split integrity, cell-block uncertainty, schema controls, threshold decisions, and localization sensitivity. Twelve analyses use 13,831 eligible records from 13,876 CALCE, NASA, and Oxford observations. A pooled-domain, cell-held-out baseline reaches 94.8% coverage (cell-block lower bound 94.2%). Across six cross-dataset tasks, method-matched removal of the most recent measured SOH yields statistically supported coverage reductions in five tasks, by as much as 60.4 percentage points; the remaining task and pooled-domain baseline are compatible with no effect. The as-used schema bundle decreases leave-NASA coverage by 12.0 percentage points and increases false acceptance by 100.0 percentage points at the illustrative SOH cutoff 0.90 (exact paired-cell p = 9.54e-07); an independent control restricts interpretation to a bundle-level association. A localized-residual comparator recovers one point-coverage failure; its design carries no shift-robust guarantee. Each gate couples evidence requirements to claim bounds, yielding an executable pre-submission check demonstrated on three public battery benchmarks. Prospective applications are needed to establish detection performance.

---

## 🛡️ Six-Gate Benchmark-Integrity Audit Protocol

The repository implements a governed benchmark-integrity audit protocol comprising six explicit gates:

| Gate | Measurement Condition Examined | Evidence Required | Consequence of Failure |
| :--- | :--- | :--- | :--- |
| **G1** | Information set | State whether recent measured SOH or another oracle label is available at prediction time | No claim for settings without recent labels |
| **G2** | Split integrity | Verify task-appropriate disjoint training, validation, calibration, and test indices; require cell-disjoint histories where the task claims cell-level holdout | Treat coverage as split-contingent |
| **G3** | Uncertainty units | Report cell-block uncertainty rather than row-level i.i.d. intervals | Treat uncertainty as optimistic |
| **G4** | Schema sensitivity | Compare schema contrasts with an independent permuted-feature control and multiplicity adjustment | Bundle-level warning; no mechanism claim |
| **G5** | Decision consequences | Report threshold false acceptance and false rejection with record denominators, effective cell counts, and sparse-cell flags | Do not promote coverage to serviceability evidence |
| **G6** | Localization sensitivity | Compare standard and localized calibration as a sensitivity envelope | Failure: no empirical recovery; apparent success: point-coverage sensitivity only. Neither outcome authorizes a shift-robust claim without a guarantee-bearing method and verified assumptions |

---

## 📂 Repository Structure

```
.
├── paper/
│   ├── source/               # Quarto manuscript source files (.qmd, .tex)
│   ├── data/                 # Single Source of Truth (SSOT) metrics (metrics.json)
│   ├── figures/              # Manuscript figures (PDF format)
│   ├── submission/           # Submission packages (v1 archived, v2 ready)
│   │   ├── ress/             # Latest v2 submission bundle directory
│   │   ├── archive_v1_20260807/ # Archived v1 submission package
│   │   ├── ress_v1_submission_ready.zip # v1 zip archive
│   │   └── ress_v2_submission_ready.zip # v2 zip archive
│   └── scripts/              # Data collection, figure generation & audit scripts
├── experiments/              # 12 diagnostic analysis plans and results
├── data/                     # Public battery dataset provenance and splits
├── docs/                     # Governance, decision logs, and journal constraints
└── README.md                 # Project documentation (this file)
```

---

## 📊 Datasets Evaluated

The empirical audit evaluates **13,831 eligible cycle-level records** from **45 real lithium-ion battery cells** across three public laboratory platforms:
1. **CALCE** (Center for Advanced Life Cycle Engineering): 12 CS2/CX2 prismatic cells (11,592 eligible rows).
2. **NASA Ames Prognostics Data Repository**: 25 multi-batch Li-ion cells (1,728 eligible rows).
3. **Oxford Battery Degradation Dataset**: 8 Kokam pouch cells (511 eligible rows).

---

## ⚙️ Quick Start & Reproduction

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/QuantDiviner/NEX-CP-conformal-soh-audit.git
cd NEX-CP-conformal-soh-audit

# Create and activate Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Reproduce Manuscript & Render PDF

```bash
# Verify metrics and data integrity
python paper/scripts/validate_metrics_manifest.py

# Render complete manuscript with Quarto
cd paper/source
quarto render index.qmd
```

The compiled PDF will be generated in `paper/output/index.pdf`.

---

## 📜 License & Citation

The source code and protocol implementation are released under the [MIT License](LICENSE).

If you find this repository or protocol useful in your research, please cite our paper:

```bibtex
@article{shan2026benchmarkintegrity,
  title={A Benchmark-Integrity Audit Protocol for Conformal Battery State-of-Health Evaluation},
  author={Shan, Qingsong and Liu, Qianning},
  year={2026},
  note={Under review}
}
```
