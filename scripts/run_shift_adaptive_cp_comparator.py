#!/usr/bin/env python3
"""Run exp012 shift-adaptive conformal comparator on existing real-data splits."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import run_fpa_repair_experiment as base
import run_hard_regime_audit_experiment as hard
import run_reliability_audit_experiment as rel


ROOT = Path(__file__).resolve().parents[1]
OUT_EXP = "exp012_shift_adaptive_cp_comparator"
SHIFT_FEATURE_PREFERRED = (
    "cycle_index",
    "log_cycle_index",
    "temperature_c",
    "current_a",
    "voltage_v",
    "capacity_ah",
)
BANDWIDTH_GRID = (0.25, 0.50, 1.00, 2.00, 4.00, float("inf"))
THRESHOLDS = (0.90, 0.85, 0.80, 0.75, 0.70, 0.65)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not np.any(mask):
        return base.conformal_q(values[np.isfinite(values)], alpha=1 - base.TARGET)
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / np.sum(weights)
    idx = int(np.searchsorted(cdf, q, side="left"))
    return float(values[min(idx, len(values) - 1)])


def shift_features(frame: pd.DataFrame, fcols: list[str]) -> list[str]:
    preferred = [c for c in SHIFT_FEATURE_PREFERRED if c in frame.columns and c in fcols]
    if preferred:
        return preferred
    fallback = [c for c in fcols if c not in {"prev_soh", "prev_soh_missing", "target_soh"}]
    return fallback[:5] if fallback else fcols[:5]


def scaled_matrix(frame: pd.DataFrame, cols: list[str], center: pd.Series, scale: pd.Series) -> np.ndarray:
    if not cols:
        return np.zeros((len(frame), 1), dtype=float)
    x = frame[cols].astype(float)
    return ((x - center[cols]) / scale[cols].replace(0, 1.0)).fillna(0.0).to_numpy(dtype=float)


def weighted_radii(
    cal_frame: pd.DataFrame,
    target_frame: pd.DataFrame,
    cal_scores: np.ndarray,
    cols: list[str],
    bandwidth: float,
) -> np.ndarray:
    center = cal_frame[cols].astype(float).mean() if cols else pd.Series(dtype=float)
    scale = cal_frame[cols].astype(float).std(ddof=0).replace(0, 1.0) if cols else pd.Series(dtype=float)
    cal_x = scaled_matrix(cal_frame, cols, center, scale)
    target_x = scaled_matrix(target_frame, cols, center, scale)
    q_level = np.ceil((len(cal_scores) + 1) * base.TARGET) / max(len(cal_scores), 1)
    q_level = min(float(q_level), 1.0)
    if np.isinf(bandwidth):
        qhat = base.conformal_q(cal_scores, alpha=1 - base.TARGET)
        return np.full(len(target_frame), qhat, dtype=float)
    radii = []
    denom = max(float(bandwidth) ** 2, 1e-12)
    for row in target_x:
        dist2 = np.mean((cal_x - row) ** 2, axis=1)
        weights = np.exp(-0.5 * dist2 / denom) + 1e-12
        radii.append(weighted_quantile(cal_scores, weights, q_level))
    return np.asarray(radii, dtype=float)


def interval_metrics_with_utility(
    frame: pd.DataFrame,
    y: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    center: np.ndarray,
    seed: int,
    reps: int,
    min_denominator: int,
    family_n: int,
) -> dict:
    utility = hard.decision_utility(frame, y, lower, upper, seed, reps, min_denominator, family_n)
    covered = (y >= lower) & (y <= upper)
    return {
        **base.interval_metrics(frame, y, lower, upper, center, seed, reps),
        "decision_utility_ci": utility,
        "decision_cost_curve": hard.cost_curve(utility),
        "double_coverage": {
            "marginal_coverage": float(np.mean(covered)) if len(covered) else 0.0,
            "cell_reliability": rel.cell_reliability(frame, covered),
        },
    }


def fit_cqr_models(train: pd.DataFrame, cal: pd.DataFrame, fcols: list[str], seed: int) -> dict:
    y_train = train["soh"].to_numpy()
    y_cal = cal["soh"].to_numpy()
    lower_model, upper_model, center_model = base.fit_gb_quantiles(train[fcols], y_train, seed)
    cal_lower = lower_model.predict(cal[fcols])
    cal_upper = upper_model.predict(cal[fcols])
    cal_low = np.minimum(cal_lower, cal_upper)
    cal_high = np.maximum(cal_lower, cal_upper)
    cal_scores = np.maximum.reduce([cal_low - y_cal, y_cal - cal_high, np.zeros_like(y_cal)])
    return {
        "lower_model": lower_model,
        "upper_model": upper_model,
        "center_model": center_model,
        "cal_scores": cal_scores,
        "standard_qhat": base.conformal_q(cal_scores, alpha=1 - base.TARGET),
    }


def predict_base_interval(models: dict, frame: pd.DataFrame, fcols: list[str], radius: np.ndarray | float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    low_pred = models["lower_model"].predict(frame[fcols])
    high_pred = models["upper_model"].predict(frame[fcols])
    center = models["center_model"].predict(frame[fcols])
    low = np.minimum(low_pred, high_pred) - radius
    high = np.maximum(low_pred, high_pred) + radius
    return low, high, center


def select_bandwidth(
    models: dict,
    cal: pd.DataFrame,
    val: pd.DataFrame,
    fcols: list[str],
    shift_cols: list[str],
    seed: int,
    reps: int,
) -> dict:
    if len(val) == 0:
        return {
            "bandwidth": float("inf"),
            "selection_trace": [],
            "selection_rule": "No validation rows; fallback to standard unweighted CQR radius.",
        }
    y_val = val["soh"].to_numpy()
    best_bw = float("inf")
    best_score = float("inf")
    trace = []
    for bw in BANDWIDTH_GRID:
        radii = weighted_radii(cal, val, models["cal_scores"], shift_cols, bw)
        low, high, center = predict_base_interval(models, val, fcols, radii)
        metrics = base.interval_metrics(val, y_val, low, high, center, seed, reps)
        score = base.exp001_compatible_selection_score(metrics)
        row = {
            "bandwidth": "inf" if np.isinf(bw) else float(bw),
            "validation_coverage": float(metrics["coverage"]),
            "validation_mean_width": float(metrics["mean_width"]),
            "selection_score": float(score),
        }
        trace.append(row)
        if score < best_score:
            best_score = score
            best_bw = bw
    return {
        "bandwidth": "inf" if np.isinf(best_bw) else float(best_bw),
        "selection_trace": trace,
        "selection_rule": "validation-only coverage-first width objective; test metrics are not used for bandwidth selection",
    }


def evaluate_task(
    df: pd.DataFrame,
    task_name: str,
    indices: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]],
    seed: int,
    reps: int,
    min_denominator: int,
    family_n: int,
) -> dict:
    train_idx, cal_idx, val_idx, test_idx, fcols = indices
    train = df.loc[train_idx].copy()
    cal = df.loc[cal_idx].copy()
    val = df.loc[val_idx].copy()
    test = df.loc[test_idx].copy()
    if min(len(train), len(cal), len(test)) == 0:
        return {"skipped": True, "reason": "empty train/cal/test split"}

    models = fit_cqr_models(train, cal, fcols, seed)
    y_test = test["soh"].to_numpy()
    methods = {}

    standard_low, standard_high, center = predict_base_interval(models, test, fcols, models["standard_qhat"])
    methods["cqr_gradient_boosting_standard"] = {
        **interval_metrics_with_utility(test, y_test, standard_low, standard_high, center, seed, reps, min_denominator, family_n),
        "qhat": float(models["standard_qhat"]),
        "comparator_role": "non_shift_adaptive_reference",
    }

    shift_cols = shift_features(df, fcols)
    selected = select_bandwidth(models, cal, val, fcols, shift_cols, seed, max(200, min(reps, 500)))
    bw_value = float("inf") if selected["bandwidth"] == "inf" else float(selected["bandwidth"])
    weighted_radius = weighted_radii(cal, test, models["cal_scores"], shift_cols, bw_value)
    weighted_low, weighted_high, weighted_center = predict_base_interval(models, test, fcols, weighted_radius)
    methods["weighted_cqr_shift_adaptive"] = {
        **interval_metrics_with_utility(test, y_test, weighted_low, weighted_high, weighted_center, seed, reps, min_denominator, family_n),
        "adaptive_rule": "heuristic localized-residual CQR with validation-selected Gaussian-kernel bandwidth",
        "shift_features": shift_cols,
        "selected_bandwidth": selected["bandwidth"],
        "bandwidth_selection_trace": selected["selection_trace"],
        "selection_rule": selected["selection_rule"],
        "comparator_role": "localized_residual_diagnostic_without_covariate_shift_coverage_guarantee",
    }

    return {
        "task": task_name,
        "n_train": int(len(train)),
        "n_cal": int(len(cal)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "features": fcols,
        "shift_features": shift_cols,
        "methods": methods,
        "shift_diagnostics": rel.shift_diagnostics(cal, test, shift_cols),
    }


def comparator_summary(tasks: dict) -> dict:
    rows = []
    for task_name, task in tasks.items():
        if task.get("skipped"):
            continue
        standard = task["methods"]["cqr_gradient_boosting_standard"]
        adaptive = task["methods"]["weighted_cqr_shift_adaptive"]
        rows.append({
            "task": task_name,
            "standard_coverage": standard["coverage"],
            "adaptive_coverage": adaptive["coverage"],
            "coverage_delta_adaptive_minus_standard": float(adaptive["coverage"] - standard["coverage"]),
            "standard_cell_ci_low": standard["cell_block_ci_low"],
            "adaptive_cell_ci_low": adaptive["cell_block_ci_low"],
            "standard_mean_width": standard["mean_width"],
            "adaptive_mean_width": adaptive["mean_width"],
            "width_ratio_adaptive_vs_standard": float(adaptive["mean_width"] / max(standard["mean_width"], 1e-12)),
            "adaptive_meets_target": bool(adaptive["coverage"] >= base.TARGET and adaptive["cell_block_ci_low"] >= base.CELL_CI_FLOOR),
            "interpretation": "recovery_candidate" if adaptive["coverage"] >= base.TARGET else "failure_boundary",
        })
    return {
        "comparison_policy": "No method-superiority claim; report whether shift-adaptive CP recovers, partially recovers, or fails under protocol shift.",
        "rows": rows,
        "tasks_recovered_by_adaptive": [row["task"] for row in rows if row["adaptive_meets_target"]],
        "tasks_not_recovered_by_adaptive": [row["task"] for row in rows if not row["adaptive_meets_target"]],
    }


def decision_utility_export(tasks: dict) -> dict:
    return {
        task_name: {
            method_name: method["decision_utility_ci"]
            for method_name, method in task.get("methods", {}).items()
            if not method.get("skipped")
        }
        for task_name, task in tasks.items()
        if not task.get("skipped")
    }


def multiplicity_summary(tasks: dict) -> dict:
    rows = []
    for task_name, task in tasks.items():
        if task.get("skipped"):
            continue
        for method_name, method in task["methods"].items():
            for threshold_key, utility in method["decision_utility_ci"].items():
                fs = utility["false_safe_per_actual_unsafe"]
                rows.append({
                    "task": task_name,
                    "method": method_name,
                    "threshold": threshold_key,
                    "false_safe_rate": fs["rate"],
                    "false_safe_ci_high": fs["ci_high"],
                    "false_safe_bonferroni_ci_high": fs.get("bonferroni_ci_high"),
                    "interpretation": fs["interpretation"],
                    "effective_cell_count": fs["effective_cell_count"],
                    "denominator_n": fs["denominator_n"],
                })
    return {
        "family_n": len(rows),
        "policy": "False-safe claims must use denominator suppression and report effective cell counts.",
        "all_false_safe_tests": rows,
    }


def write_report(exp_dir: Path, metrics: dict) -> None:
    lines = [
        "# exp012_shift_adaptive_cp_comparator Report",
        "",
        "**Status**: pending_review",
        "",
        "## Results Summary",
        "",
        "This experiment tests whether weighted shift-adaptive conformal CQR recovers reliability under the existing real-data protocol-shift tasks.",
        "",
        "| Task | Standard cov | Adaptive cov | Adaptive CI low | Width ratio | Interpretation |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in metrics["comparator_summary"]["rows"]:
        lines.append(
            f"| {row['task']} | {row['standard_coverage']:.4f} | {row['adaptive_coverage']:.4f} | "
            f"{row['adaptive_cell_ci_low']:.4f} | {row['width_ratio_adaptive_vs_standard']:.3f} | {row['interpretation']} |"
        )
    lines.extend([
        "",
        "Synthetic data was not used.",
        "",
        "## Claim Boundary",
        "",
        metrics["claim_boundary"],
    ])
    (exp_dir / "report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-exp", default=OUT_EXP)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--min-decision-denominator", type=int, default=5)
    args = parser.parse_args()

    if not base.PROCESSED.exists() or not base.SPLITS.exists():
        raise SystemExit("Missing processed real data or split manifest. Run scripts/preprocess_real_battery.py first.")

    df = pd.read_csv(base.PROCESSED)
    splits = base.read_json(base.SPLITS)
    tasks = base.build_tasks(df, splits)
    family_n = len(tasks) * 2 * len(THRESHOLDS) * 2
    tasks_out = {
        task_name: evaluate_task(
            df,
            task_name,
            indices,
            args.seed,
            args.bootstrap_reps,
            args.min_decision_denominator,
            family_n,
        )
        for task_name, indices in tasks.items()
    }

    exp_dir = ROOT / "experiments" / args.output_exp
    run_manifest = {
        "generated_at": datetime.now().isoformat(),
        "script": "scripts/run_shift_adaptive_cp_comparator.py",
        "argv": sys.argv,
        "experiment_id": args.output_exp,
        "seed": args.seed,
        "bootstrap_reps": args.bootstrap_reps,
        "min_decision_denominator": args.min_decision_denominator,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "runtime_packages": base.runtime_packages(),
        "git_commit": base.git_commit(),
        "synthetic_data_used": False,
        "target_journal": "Reliability Engineering & System Safety",
        "article_type": "Short Communication / Case Study",
        "deterministic_regeneration_command": (
            "python scripts/run_shift_adaptive_cp_comparator.py "
            f"--output-exp {args.output_exp} --seed {args.seed} "
            f"--bootstrap-reps {args.bootstrap_reps} "
            f"--min-decision-denominator {args.min_decision_denominator}"
        ),
        "fpa_source": "docs/reports/20260531_121759_20260531_121759_fpa_chain_summary.md",
    }
    metrics = {
        "target_coverage": base.TARGET,
        "cell_ci_floor": base.CELL_CI_FLOOR,
        "claim_boundary": "RESS reliability / measurement-validity diagnostic only; the localized-residual comparator has no covariate-shift conformal coverage guarantee and supports no method-superiority, broad-transfer, deployment, Neural-ODE, or NEX-CP claim.",
        "data_policy": "real_data_only",
        "synthetic_data_used": False,
        "tasks": tasks_out,
        "comparator_summary": comparator_summary(tasks_out),
        "decision_utility_ci": decision_utility_export(tasks_out),
        "multiplicity_control": multiplicity_summary(tasks_out),
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
    write_json(exp_dir / "results" / "comparator_summary.json", metrics["comparator_summary"])
    write_json(exp_dir / "results" / "decision_utility_ci.json", metrics["decision_utility_ci"])
    write_json(exp_dir / "results" / "multiplicity_control.json", metrics["multiplicity_control"])
    write_json(exp_dir / "results" / "run_manifest.json", run_manifest)
    write_json(exp_dir / "results" / "split_manifest.json", metrics["split_manifest"])
    write_report(exp_dir, metrics)
    print(json.dumps({"status": "ok", "metrics": str(exp_dir / "results" / "metrics.json")}, indent=2))


if __name__ == "__main__":
    main()
