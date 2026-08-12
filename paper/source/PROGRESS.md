# Paper Writing Workflow Progress

Start time: 2026-06-01T00:00:00+08:00
Pre-flight: passed (Layer 1 passed; Layer 2 passed; Layer 2.5 passed; Layer 3 auto-repaired)
Target journal: Reliability Engineering & System Safety
Article type: Short Communication / Case Study
Current phase: Phase 4 - Review complete
Current section: manuscript revision loop complete

## Gate Status

- Research Navigator `pre-paper-writing`: PASS
- Research Navigator `pre-manuscript-work`: PASS
- Latest FPA: Round 11 Exit A with required reviewers `codex=A`, `claude=A`

## Phase Status

| Phase | Status | Notes |
|---|---|---|
| Phase 0 Pre-flight | complete | Core documents, experiment reports, metrics, and guards verified. |
| Phase 1 Preparation | complete refreshed pass | Journal matrix, writing norms, constraints, metrics design, gap analysis, references initialized; template assets and Tier 0 exemplar layer added 2026-06-02. |
| Phase 2 Architecture | complete initial pass | Single-entry Quarto structure created at `paper/source/paper.qmd`. |
| Phase 3 Drafting | complete initial pass | Abstract, highlights, and section skeletons drafted with dynamic metrics and claim boundaries. |
| Phase 4 Review | complete | Manuscript revision loop completed with external Opus/Codex gates; final Codex verdict publishable with P0=0/P1=0. |

## Section Progress

| Section | Status | Iteration |
|---|---|---:|
| Introduction | draft skeleton | 1 |
| Related Work | draft skeleton | 1 |
| Methodology | draft skeleton | 1 |
| Results | draft skeleton | 1 |
| Discussion | draft skeleton | 1 |
| Conclusion | draft skeleton | 1 |
| Abstract | draft skeleton | 1 |
| Highlights | draft skeleton | 1 |

## Issue Log

- Existing `index.qmd`, `methodology.qmd`, `experiments.qmd`, and `conclusion.qmd` contain YAML headers from an older scaffold. The governed render entry is now `paper.qmd`; legacy files should not be rendered directly.
- Phase 1 literature records are discovery records and must be cross-validated in Phase 4 before final submission.
- PDF render requires `LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8` in this environment.
- 2026-06-02 paper-writing workflow refresh:
  - Layer 2.5 sentinels added and passed:
    `validate_metrics_manifest.py`, `recompute_aggregates.py`,
    `check_hardcoded_numbers.py`, `validate_external_facts.py`.
  - `paper/data/metrics_manifest.yaml` registers 114 top-level metric keys.
  - `paper/data/external_facts.yaml` registers RESS/Elsevier/template/dataset
    facts.
  - Elsevier `elsarticle` assets were downloaded to
    `paper/templates/elsevier/`; generic Quarto Elsevier assets were downloaded
    to `paper/templates/quarto-elsevier/`.
  - RESS exemplar layer initially recorded ScienceDirect PDF HTTP 403, then was
    completed with three open accepted-manuscript PDFs from institutional
    repositories and promoted to Tier 1.
  - Tier 1 exemplar rules were applied: descriptive technical title, abstract
    problem/framework/evidence/implication order, explicit contribution and
    paper-organization paragraphs, case-study audit object before results, and
    bounded concluding remarks.
  - Results tables now render dynamically from `metrics.json` rather than
    static hard-coded manuscript values.
- 2026-06-03 citation verification (closing EDITORIAL_REPORT open item):
  - `shen` review citation verified against CrossRef (DOI 10.1109/TTE.2023.3293551):
    IEEE Trans. Transp. Electrific., vol. 10, no. 1, pp. 1465–1481, 2024.
    Corrected missing 5th author (H. T. Shen) and year (2023→2024); key
    renamed `shen2023review`→`shen2024review` and updated in `02-related-work.qmd`.
  - `Wu et al.` confirmed absent from `main.bib` (not cited); no dangling reference.
  - Paper re-rendered; regenerated `paper.tex`/`paper.pdf` carry no stale key.
  - Remaining submission blockers are user-input only: author block/affiliations/
    corresponding author and optional code-repository deposit.
- Manuscript revision reports:
  - `docs/reports/20260601_133741_S1_Opus审稿报告_R1.md`
  - `docs/reports/20260601_133741_S1_Codex审稿报告_R1.md`
  - `docs/reports/20260601_142059_S2_Codex审稿报告_R2.md`
  - `docs/reports/20260601_142958_S2_Opus审稿报告_R3.md`
  - `docs/reports/20260601_143324_S2_Codex审稿报告_R4.md`
- 2026-06-14 paper-writing workflow maintenance revision:
  - Expanded Related Work with conformal foundations, battery uncertainty/transfer,
    and benchmark-integrity/leakage positioning using already verified references.
  - Strengthened Methodology, Discussion, and Conclusion around measurement-validity
    scope, shift-adaptive comparator interpretation, and the five contribution
    closures.
  - Added `paper/scripts/core_manuscript_lint.py` project wrapper so the core
    lint gate checks authored QMD/Markdown files rather than Quarto-generated
    `index.tex`.
  - Re-rendered `paper/output/index.pdf` and `paper/output/index.md` with
    `quarto render paper/source/index.qmd --execute --no-cache`.
