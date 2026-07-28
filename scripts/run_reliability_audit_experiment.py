#!/usr/bin/env python3
"""Run exp008 reliability/safety audit on real battery SOH data."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

import run_fpa_repair_experiment as base


ROOT = Path(__file__).resolve().parents[1]
OUT_EXP = "exp008_reliability_audit"
Q_GRID = (0.90, 0.93, 0.95, 0.97, 0.99, 1.00)
COMMON_FEATURE_SCHEMA = ["cycle_index", "log_cycle_index", "prev_soh"]
FORBIDDEN_CLAIM_PATTERNS = {
    "superiority": ("superior", "outperform", "beats", "best-performing", "method superiority"),
    "deployment": ("deployment-ready", "deployable", "hardware-ready", "real-time deployment"),
    "universal_transfer": ("universal transfer", "generalizes across all", "broad cross-protocol universality"),
}


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def rate_ci_by_cell(
    frame: pd.DataFrame,
    numerator: np.ndarray,
    denominator: np.ndarray,
    seed: int,
    reps: int,
    min_denominator: int,
) -> dict:
    if not np.any(denominator):
        return {
            "rate": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "denominator_n": 0,
            "effective_cell_count": 0,
            "interpretation": "suppressed_no_denominator",
        }
    cells = frame["cell_id"].astype(str).to_numpy()
    unique, inverse = np.unique(cells, return_inverse=True)
    den_cells = np.unique(cells[denominator])
    rate = float(np.sum(numerator & denominator) / np.sum(denominator))
    interpretation = (
        "interpretable"
        if int(np.sum(denominator)) >= min_denominator and len(den_cells) >= 2
        else "suppressed_low_denominator_or_cells"
    )
    if len(unique) < 2:
        return {
            "rate": rate,
            "ci_low": rate,
            "ci_high": rate,
            "denominator_n": int(np.sum(denominator)),
            "effective_cell_count": int(len(den_cells)),
            "interpretation": interpretation,
        }
    rng = np.random.default_rng(seed)
    group_den = np.bincount(
        inverse, weights=np.asarray(denominator, dtype=float), minlength=len(unique)
    )
    group_num = np.bincount(
        inverse,
        weights=np.asarray(numerator & denominator, dtype=float),
        minlength=len(unique),
    )
    boot = []
    for _ in range(reps):
        sampled = rng.integers(0, len(unique), size=len(unique))
        den_total = float(np.sum(group_den[sampled]))
        if den_total > 0:
            boot.append(float(np.sum(group_num[sampled]) / den_total))
    # Normal-approximation interval (point +/- z * bootstrap SE), clamped to [0,1],
    # for consistency with the schema/artifact family and to avoid the skewed extreme
    # percentiles a cell-block bootstrap can produce under cell heterogeneity.
    if boot:
        se = float(np.std(boot, ddof=1)) if len(boot) > 1 else 0.0
        z = NormalDist().inv_cdf(0.975)
        ci_low = max(0.0, rate - z * se)
        ci_high = min(1.0, rate + z * se)
    else:
        se, ci_low, ci_high = 0.0, rate, rate
    return {
        "rate": rate,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "se": se,
        "ci_method": "normal_approx",
        "denominator_n": int(np.sum(denominator)),
        "effective_cell_count": int(len(den_cells)),
        "interpretation": interpretation,
    }


def decision_utility_ci(
    frame: pd.DataFrame,
    y: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    seed: int,
    reps: int,
    min_denominator: int,
) -> dict:
    out = {}
    thresholds = (0.80, 0.70)
    families = ("false_safe", "false_alarm", "uncertain")
    multiplicity_n = len(thresholds) * len(families)
    for threshold in thresholds:
        actual_unsafe = y < threshold
        actual_safe = ~actual_unsafe
        predicted_safe = lower >= threshold
        predicted_unsafe = upper < threshold
        uncertain = ~(predicted_safe | predicted_unsafe)
        false_safe = predicted_safe & actual_unsafe
        false_alarm = predicted_unsafe & actual_safe
        out[f"soh_threshold_{threshold:.2f}"] = {
            "false_safe_per_actual_unsafe": rate_ci_by_cell(frame, false_safe, actual_unsafe, seed, reps, min_denominator),
            "false_alarm_per_actual_safe": rate_ci_by_cell(frame, false_alarm, actual_safe, seed + 11, reps, min_denominator),
            "uncertain_rate": rate_ci_by_cell(frame, uncertain, np.ones(len(y), dtype=bool), seed + 23, reps, min_denominator),
            "predicted_safe_rate": float(np.mean(predicted_safe)),
            "predicted_unsafe_rate": float(np.mean(predicted_unsafe)),
            "multiplicity_family_n": multiplicity_n,
            "multiplicity_note": "Interpret threshold/task sweeps as a family; low-denominator cells are suppressed or exploratory.",
        }
    return out


def cost_curve(utility_ci: dict) -> dict:
    out = {}
    for threshold_key, item in utility_ci.items():
        fs = item["false_safe_per_actual_unsafe"]["rate"]
        fa = item["false_alarm_per_actual_safe"]["rate"]
        unc = item["uncertain_rate"]["rate"]
        out[threshold_key] = {}
        for ratio in (1, 2, 5, 10, 20):
            out[threshold_key][f"false_safe_cost_ratio_{ratio}"] = float(ratio * fs + fa + 0.25 * unc)
    return out


def cell_reliability(frame: pd.DataFrame, covered: np.ndarray) -> dict:
    rows = []
    for cell, g in frame.groupby("cell_id"):
        idx = frame.index.isin(g.index)
        if int(np.sum(idx)) < 20:
            continue
        rows.append({"cell_id": str(cell), "coverage": float(np.mean(covered[idx])), "n": int(np.sum(idx))})
    if not rows:
        return {"cells": [], "min_cell_coverage": None, "fraction_cells_ge_085": None}
    coverages = np.asarray([row["coverage"] for row in rows], dtype=float)
    return {
        "cells": sorted(rows, key=lambda row: row["coverage"]),
        "min_cell_coverage": float(np.min(coverages)),
        "fraction_cells_ge_085": float(np.mean(coverages >= 0.85)),
        "fraction_cells_ge_090": float(np.mean(coverages >= 0.90)),
    }


def shift_diagnostics(cal: pd.DataFrame, test: pd.DataFrame, fcols: list[str]) -> dict:
    rows = []
    for col in fcols:
        if col not in cal.columns or col not in test.columns:
            continue
        a = cal[col].to_numpy(dtype=float)
        b = test[col].to_numpy(dtype=float)
        pooled = float(np.sqrt(0.5 * (np.nanvar(a) + np.nanvar(b))))
        if not np.isfinite(pooled) or pooled <= 1e-12:
            continue
        rows.append({
            "feature": col,
            "cal_mean": float(np.nanmean(a)),
            "test_mean": float(np.nanmean(b)),
            "standardized_mean_diff": float((np.nanmean(b) - np.nanmean(a)) / pooled),
        })
    rows = sorted(rows, key=lambda row: abs(row["standardized_mean_diff"]), reverse=True)
    return {
        "top_standardized_mean_differences": rows[:12],
        "max_abs_standardized_mean_diff": float(abs(rows[0]["standardized_mean_diff"])) if rows else 0.0,
        "cal_domains": cal["domain"].value_counts().to_dict(),
        "test_domains": test["domain"].value_counts().to_dict(),
    }


def fit_intervals(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    cal_idx: np.ndarray,
    val_idx: np.ndarray,
    test_idx: np.ndarray,
    fcols: list[str],
    seed: int,
    include_ngboost: bool,
    min_denominator: int,
) -> dict[str, dict]:
    train = df.loc[train_idx].copy()
    cal = df.loc[cal_idx].copy()
    val = df.loc[val_idx].copy()
    test = df.loc[test_idx].copy()
    y_train = train["soh"].to_numpy()
    y_cal = cal["soh"].to_numpy()
    y_test = test["soh"].to_numpy()
    out = {}

    cal_resid = np.abs(y_cal - cal["prev_soh"].to_numpy())
    val_y = val["soh"].to_numpy()
    val_pred = val["prev_soh"].to_numpy()
    best_q = base.TARGET
    best_score = float("inf")
    q_selection_trace = []
    for q_level in Q_GRID:
        if len(val):
            radius = base.mondrian_radius(cal, cal_resid, val["calibration_group"], q_level)
            metrics = base.interval_metrics(val, val_y, val_pred - radius, val_pred + radius, val_pred, seed, 200)
            score = base.exp001_compatible_selection_score(metrics)
            q_selection_trace.append({
                "q_level": float(q_level),
                "validation_coverage": float(metrics["coverage"]),
                "validation_mean_width": float(metrics["mean_width"]),
                "selection_score": float(score),
            })
            if score < best_score:
                best_q, best_score = q_level, score
    center = test["prev_soh"].to_numpy()
    radius = base.mondrian_radius(cal, cal_resid, test["calibration_group"], best_q)
    out["persistence_anchor_protocol_mondrian_cp"] = {
        "frame": test,
        "y": y_test,
        "lower": center - radius,
        "upper": center + radius,
        "center": center,
        "q_level": float(best_q),
        "q_selection_grid": list(Q_GRID),
        "q_selection_trace": q_selection_trace,
        "q_selection_objective": "validation-only coverage-first width minimization; objective = mean_width + max(0, target_coverage - validation_coverage) * 1000; test metrics are not used for q selection",
        "operational_assumption": "`prev_soh` must be available at decision time; otherwise this is nowcasting or one-step lag-constrained forecasting.",
    }

    lower_model, upper_model, center_model = base.fit_gb_quantiles(train[fcols], y_train, seed)
    cal_lower = lower_model.predict(cal[fcols])
    cal_upper = upper_model.predict(cal[fcols])
    test_lower = lower_model.predict(test[fcols])
    test_upper = upper_model.predict(test[fcols])
    center = center_model.predict(test[fcols])
    lower = np.minimum(test_lower, test_upper)
    upper = np.maximum(test_lower, test_upper)
    out["qr_gradient_boosting"] = {"frame": test, "y": y_test, "lower": lower, "upper": upper, "center": center}
    cal_low = np.minimum(cal_lower, cal_upper)
    cal_high = np.maximum(cal_lower, cal_upper)
    scores = np.maximum.reduce([cal_low - y_cal, y_cal - cal_high, np.zeros_like(y_cal)])
    qhat = base.conformal_q(scores, alpha=1 - base.TARGET)
    out["cqr_gradient_boosting"] = {
        "frame": test,
        "y": y_test,
        "lower": lower - qhat,
        "upper": upper + qhat,
        "center": center,
        "qhat": float(qhat),
    }

    if include_ngboost:
        try:
            from ngboost import NGBRegressor
            from ngboost.distns import Normal

            ngb = NGBRegressor(Dist=Normal, n_estimators=300, learning_rate=0.03, random_state=seed, verbose=False)
            ngb.fit(train[fcols], y_train)
            cal_dist = ngb.pred_dist(cal[fcols])
            test_dist = ngb.pred_dist(test[fcols])
            cal_center = np.asarray(cal_dist.params["loc"], dtype=float)
            cal_scale = np.maximum(np.asarray(cal_dist.params["scale"], dtype=float), 1e-8)
            center = np.asarray(test_dist.params["loc"], dtype=float)
            scale = np.maximum(np.asarray(test_dist.params["scale"], dtype=float), 1e-8)
            cal_lower = cal_center - base.Z90 * cal_scale
            cal_upper = cal_center + base.Z90 * cal_scale
            scores = np.maximum.reduce([cal_lower - y_cal, y_cal - cal_upper, np.zeros_like(y_cal)])
            qhat = base.conformal_q(scores, alpha=1 - base.TARGET)
            out["ngboost_normal_cqr"] = {
                "frame": test,
                "y": y_test,
                "lower": center - base.Z90 * scale - qhat,
                "upper": center + base.Z90 * scale + qhat,
                "center": center,
                "qhat": float(qhat),
            }
        except Exception as exc:
            out["ngboost_normal_cqr"] = {"skipped": True, "reason": f"{type(exc).__name__}: {exc}"}

    return out, cal, test


def summarize_method(interval: dict, seed: int, reps: int, min_denominator: int) -> dict:
    if interval.get("skipped"):
        return interval
    frame = interval["frame"]
    y = interval["y"]
    lower = interval["lower"]
    upper = interval["upper"]
    center = interval["center"]
    covered = (y >= lower) & (y <= upper)
    utility = decision_utility_ci(frame, y, lower, upper, seed, reps, min_denominator)
    item = {
        **base.interval_metrics(frame, y, lower, upper, center, seed, reps),
        "decision_utility_ci": utility,
        "decision_cost_curve": cost_curve(utility),
        "double_coverage": {
            "marginal_coverage": float(np.mean(covered)),
            "cell_reliability": cell_reliability(frame, covered),
        },
    }
    for key in ("q_level", "qhat", "q_selection_grid", "q_selection_trace", "q_selection_objective", "operational_assumption"):
        if key in interval:
            item[key] = interval[key]
    return item


def task_audit(task_name: str, task: dict) -> dict:
    methods = {name: row for name, row in task["methods"].items() if not row.get("skipped")}
    persistence = methods.get("persistence_anchor_protocol_mondrian_cp")
    alignment = {}
    if persistence:
        for name, row in methods.items():
            if name == "persistence_anchor_protocol_mondrian_cp":
                continue
            alignment[name] = {
                "coverage_gap_vs_persistence": float(row["coverage"] - persistence["coverage"]),
                "width_ratio_vs_persistence": float(row["mean_width"] / max(persistence["mean_width"], 1e-12)),
                "coverage_aligned": bool(abs(row["coverage"] - persistence["coverage"]) <= 0.03),
                "width_comparison_permitted": bool(abs(row["coverage"] - persistence["coverage"]) <= 0.03),
                "interpretation_rule": "Report width ratio only when coverage_aligned is true; otherwise report coverage recovery/collapse without superiority language.",
            }
    return {
        "task": task_name,
        "coverage_aligned_baseline_view": alignment,
    }


def claim_boundary_audit() -> dict:
    paths = [
        ROOT / "docs" / "narrative-framework.md",
        ROOT / "docs" / "research-summary.md",
        ROOT / "experiments" / "exp008_reliability_audit" / "report.md",
    ]
    findings = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(errors="replace")
        lowered = text.lower()
        for family, patterns in FORBIDDEN_CLAIM_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in lowered:
                    findings.append({
                        "path": str(path.relative_to(ROOT)),
                        "family": family,
                        "pattern": pattern,
                        "action": "must_remove_or_bound_before_manuscript_work",
                    })
    return {
        "audited_paths": [str(path.relative_to(ROOT)) for path in paths if path.exists()],
        "forbidden_claim_patterns": FORBIDDEN_CLAIM_PATTERNS,
        "findings": findings,
        "claim_boundary": "conditional reliability/safety audit only; no method-superiority, deployment-readiness, or universal-transfer headline",
    }


def add_harmonized_leave_nasa_task(tasks: dict, df: pd.DataFrame) -> None:
    if "leave_NASA_out" not in tasks:
        return
    train_idx, cal_idx, val_idx, test_idx, _ = tasks["leave_NASA_out"]
    available = [col for col in COMMON_FEATURE_SCHEMA if col in df.columns]
    tasks["leave_NASA_out_common_feature_schema"] = (train_idx, cal_idx, val_idx, test_idx, available)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--include-ngboost", action="store_true")
    parser.add_argument("--output-exp", default=OUT_EXP)
    parser.add_argument("--min-decision-denominator", type=int, default=5)
    parser.add_argument("--add-harmonized-leave-nasa", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(base.PROCESSED)
    splits = base.read_json(base.SPLITS)
    tasks = base.build_tasks(df, splits)
    if args.add_harmonized_leave_nasa:
        add_harmonized_leave_nasa_task(tasks, df)
    exp_dir = ROOT / "experiments" / args.output_exp
    tasks_out = {}
    baseline_alignment = {}
    shift_out = {}
    utility_out = {}
    prev_soh_audit = {}

    for task_name, (train_idx, cal_idx, val_idx, test_idx, fcols) in tasks.items():
        intervals, cal, test = fit_intervals(
            df,
            train_idx,
            cal_idx,
            val_idx,
            test_idx,
            fcols,
            args.seed,
            args.include_ngboost,
            args.min_decision_denominator,
        )
        methods = {
            name: summarize_method(interval, args.seed, args.bootstrap_reps, args.min_decision_denominator)
            for name, interval in intervals.items()
        }
        tasks_out[task_name] = {
            "n_train": int(len(train_idx)),
            "n_cal": int(len(cal_idx)),
            "n_val": int(len(val_idx)),
            "n_test": int(len(test_idx)),
            "features": fcols,
            "methods": methods,
        }
        baseline_alignment[task_name] = task_audit(task_name, tasks_out[task_name])
        shift_out[task_name] = shift_diagnostics(cal, test, fcols)
        utility_out[task_name] = {
            name: row.get("decision_utility_ci")
            for name, row in methods.items()
            if not row.get("skipped")
        }
        prev_soh_audit[task_name] = {
            "prev_soh_feature_available": "prev_soh" in fcols,
            "persistence_anchor_requires_prev_soh_at_decision_time": True,
            "claim_boundary": "nowcasting_or_one_step_lag_constrained_forecasting",
        }

    run_manifest = {
        "generated_at": datetime.now().isoformat(),
        "script": "scripts/run_reliability_audit_experiment.py",
        "argv": sys.argv,
        "experiment_id": args.output_exp,
        "seed": args.seed,
        "bootstrap_reps": args.bootstrap_reps,
        "include_ngboost": bool(args.include_ngboost),
        "min_decision_denominator": int(args.min_decision_denominator),
        "add_harmonized_leave_nasa": bool(args.add_harmonized_leave_nasa),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "runtime_packages": base.runtime_packages(),
        "git_commit": base.git_commit(),
        "synthetic_data_used": False,
        "target_journal": "Reliability Engineering & System Safety",
        "claim_type": "reliability_safety_audit",
        "deterministic_regeneration_command": (
            "python scripts/run_reliability_audit_experiment.py "
            f"--output-exp {args.output_exp} --seed {args.seed} "
            f"--bootstrap-reps {args.bootstrap_reps} "
            f"--min-decision-denominator {args.min_decision_denominator} "
            + ("--include-ngboost " if args.include_ngboost else "")
            + ("--add-harmonized-leave-nasa" if args.add_harmonized_leave_nasa else "")
        ).strip(),
        "fpa_revision_plan": "docs/reports/20260530_210059_fpa_revision_20260530_205235_revision_plan.md",
    }
    metrics = {
        "target_coverage": base.TARGET,
        "cell_ci_floor": base.CELL_CI_FLOOR,
        "claim_positioning": "abandon-forward reliability/safety audit; not method superiority",
        "coverage_alignment_policy": "width comparisons are permitted only for coverage-aligned cells; non-aligned cells are coverage recovery/collapse diagnostics",
        "decision_utility_policy": {
            "min_denominator": int(args.min_decision_denominator),
            "low_denominator_action": "suppress_or_flag_as_exploratory",
            "multiplicity_action": "report family size for threshold/task sweeps and avoid definitive safety claims from isolated cells",
        },
        "feature_schema_policy": {
            "harmonized_leave_nasa_enabled": bool(args.add_harmonized_leave_nasa),
            "common_feature_schema": COMMON_FEATURE_SCHEMA,
            "purpose": "separate feature-missingness shift from residual protocol/dataset shift",
        },
        "claim_boundary_audit": claim_boundary_audit(),
        "tasks": tasks_out,
        "prev_soh_availability_audit": prev_soh_audit,
        "baseline_alignment": baseline_alignment,
        "shift_diagnostics": shift_out,
        "decision_utility_ci": utility_out,
        "run_manifest": run_manifest,
        "split_manifest": {
            "processed_data": str(base.PROCESSED.relative_to(ROOT)),
            "processed_data_sha256": base.sha256(base.PROCESSED),
            "split_manifest": str(base.SPLITS.relative_to(ROOT)),
            "split_manifest_sha256": base.sha256(base.SPLITS),
            "split_counts": {k: len(v) for k, v in splits.items()},
        },
    }
    write_json(exp_dir / "results" / "metrics.json", metrics)
    write_json(exp_dir / "results" / "decision_utility_ci.json", utility_out)
    write_json(exp_dir / "results" / "shift_diagnostics.json", shift_out)
    write_json(exp_dir / "results" / "baseline_alignment.json", baseline_alignment)
    write_json(exp_dir / "results" / "run_manifest.json", run_manifest)
    write_json(exp_dir / "results" / "split_manifest.json", metrics["split_manifest"])
    print(json.dumps({"status": "ok", "metrics": str(exp_dir / "results" / "metrics.json")}, indent=2))


if __name__ == "__main__":
    main()
