#!/usr/bin/env python3
"""Generate Quarto metadata that must live in the Elsevier front matter."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "metrics.json"
OUT = ROOT / "source" / "_generated_metadata.yml"


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%"


def yaml_block(text: str, indent: int = 2) -> str:
    pad = " " * indent
    return "\n".join(f"{pad}{line}" if line else "" for line in text.splitlines())


def main() -> None:
    metrics = json.loads(DATA.read_text())

    leave_nasa_artifact_delta = next(
        row
        for row in metrics["original_paper_substance_schema_delta_summary"]["rows"]
        if row["task"] == "leave_NASA_out"
        and row["comparison"] == "artifact_bookkeeping_as_used_minus_clean_original"
    )["coverage_delta"]
    largest_recent_label_delta = metrics[
        "original_paper_substance_schema_delta_summary"
    ]["largest_abs_coverage_delta"]["coverage_delta"]
    leave_nasa_recent_delta = next(
        row
        for row in metrics["original_paper_substance_schema_delta_summary"]["rows"]
        if row["task"] == "leave_NASA_out"
        and row["comparison"]
        == "recent_label_reference_common_no_recent_minus_prev_soh_reference"
    )["coverage_delta"]
    decision_rules = metrics["original_paper_substance_decision_rules"]
    negative_control_failures = decision_rules["negative_control_failures"]
    lnas_decision = next(
        row for row in decision_rules["rows"] if row["task"] == "leave_NASA_out"
    )
    adaptive_rows = metrics["shift_adaptive_comparator_comparator_summary"]["rows"]
    adaptive_recovered = sum(1 for row in adaptive_rows if row["adaptive_meets_target"])
    adaptive_total = len(adaptive_rows)
    adaptive_point_failure_recovered = sum(
        1
        for row in adaptive_rows
        if row["adaptive_meets_target"]
        and row["standard_coverage"] < metrics["main_baseline_target_coverage"]
    )
    adaptive_lower_bound_recovered = sum(
        1
        for row in adaptive_rows
        if row["adaptive_meets_target"]
        and row["standard_cell_ci_low"] < metrics["main_baseline_target_coverage"]
        and row["adaptive_cell_ci_low"] >= metrics["main_baseline_target_coverage"]
    )
    if adaptive_point_failure_recovered == 0:
        point_failure_clause = "without recovering a standard point-coverage failure"
    else:
        point_failure_clause = (
            f"while recovering {adaptive_point_failure_recovered} standard "
            "point-coverage failures"
        )
    if adaptive_lower_bound_recovered == 1:
        lower_bound_clause = "one standard lower-bound shortfall crosses the lower-bound envelope"
    else:
        lower_bound_clause = (
            f"{adaptive_lower_bound_recovered} standard lower-bound shortfalls "
            "cross the envelope"
        )

    main_baseline = metrics["scoped_method_repair_tasks"]["main_heldout"]["methods"]["persistence_anchor_protocol_mondrian_cp"]
    abstract = (
        "Cross-dataset conformal prediction can provide misleading battery state-of-health "
        "(SOH) evidence when prediction-time information and benchmark construction are unclear. "
        "We audit real CALCE, NASA, and Oxford cycle-level records through "
        f"{len(metrics['_meta']['source_experiments'])} diagnostic analyses, treating the benchmark as the measurement object. "
        f"A same-protocol baseline reaches {pct(main_baseline['coverage'])} coverage "
        f"with a cell-block confidence-interval lower bound of {pct(main_baseline['cell_block_ci_low'])}, but this result "
        "uses the most recent measured SOH. In method-matched comparisons, removing that reference "
        f"changes coverage by as much as {100 * largest_recent_label_delta:+.1f} percentage points; "
        f"the leave-NASA contrast is {100 * leave_nasa_recent_delta:+.1f} points. The as-used schema bundle changes "
        f"leave-NASA coverage by {100 * leave_nasa_artifact_delta:+.1f} points and increases false "
        f"acceptance by {100 * lnas_decision['fs_delta']:+.0f} points at SOH {lnas_decision['fs_threshold'].replace('soh_threshold_', '')} "
        f"(exact p={lnas_decision['fs_exact_pvalue']:.3g}). The bundle changes multiple columns and "
        "the independent-control gate fails, blocking field-specific causal attribution. A heuristic "
        f"localized-residual comparator reaches nominal point coverage on {adaptive_recovered} of "
        f"{adaptive_total} tasks and recovers {adaptive_point_failure_recovered} standard point failure. "
        "Conformal SOH coverage should therefore not be treated as deployment reliability until recent-label "
        "availability, split integrity, controls, cell-aware uncertainty, and threshold decisions are audited."
    )

    keywords = [
        "conformal prediction",
        "measurement validity",
        "battery state-of-health",
        "benchmark integrity",
        "covariate shift",
        "reliability engineering",
    ]

    content = [
        "# Generated by paper/scripts/generate_elsevier_metadata.py; do not edit by hand.",
        "abstract: |",
        yaml_block(abstract),
        "keywords:",
        *(f"  - {keyword}" for keyword in keywords),
        "",
    ]
    OUT.write_text("\n".join(content))


if __name__ == "__main__":
    main()
