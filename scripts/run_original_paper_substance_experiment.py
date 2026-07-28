#!/usr/bin/env python3
"""Run exp011 supplemental schema-to-decision audit for RESS Original Paper."""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from datetime import datetime
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

import run_fpa_repair_experiment as base
import run_hard_regime_audit_experiment as hard
import run_reliability_audit_experiment as rel


ROOT = Path(__file__).resolve().parents[1]
OUT_EXP = "exp011_original_paper_substance"
BOOKKEEPING_FEATURES = {"source_row_id", "target_cycle_index", "target_soh"}
COMMON_NO_RECENT = ("cycle_index", "log_cycle_index")
COMMON_WITH_PREV_SOH = ("cycle_index", "log_cycle_index", "prev_soh")
THRESHOLDS = (0.90, 0.85, 0.80, 0.75, 0.70, 0.65)
NEGATIVE_CONTROL_FEATURE = "__negative_control_zero__"
ARTIFACT_DELTA_MIN_ABS = 0.03


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def finite_float(value: float) -> float | None:
    value = float(value)
    return value if np.isfinite(value) else None


def se_ci(observed: float, boot: list, alpha: float, lo_clip: float, hi_clip: float) -> dict:
    """Normal-approximation interval: observed +/- z * bootstrap standard error.

    Reported instead of percentile intervals because the Bonferroni-corrected
    schema/artifact family uses alpha ~ 2e-4, whose tail quantiles cannot be
    resolved by B=1000 percentile bootstrap (finest resolvable quantile = 1/B).
    A zero bootstrap SE is retained as boundary evidence and is evaluated with
    an exact paired-cell sign test rather than discarded.
    """
    if not boot:
        return {"ci_low": observed, "ci_high": observed, "se": 0.0, "degenerate": False}
    se = float(np.std(boot, ddof=1)) if len(boot) > 1 else 0.0
    z = NormalDist().inv_cdf(1 - alpha / 2)
    lo = max(lo_clip, observed - z * se)
    hi = min(hi_clip, observed + z * se)
    return {"ci_low": finite_float(lo), "ci_high": finite_float(hi), "se": se, "degenerate": se == 0.0}


def external_dataset_inventory() -> dict:
    raw = ROOT / "data" / "raw"
    rows = []
    for path in sorted(raw.glob("*")):
        item = {
            "entry": str(path.relative_to(ROOT)),
            "is_symlink": path.is_symlink(),
            "exists": path.exists(),
            "resolved_path": str(path.resolve(strict=False)) if path.is_symlink() else str(path),
            "qa_usable_now": False,
            "reason": "",
        }
        if not path.exists():
            item["reason"] = "path_missing_or_unmounted"
        elif path.name in {"CALCE", "NASA", "Oxford"}:
            item["qa_usable_now"] = True
            item["reason"] = "already_in_real_battery_preprocess_manifest"
        else:
            files = [p for p in path.rglob("*") if p.is_file()]
            item["file_count_depth_unbounded"] = len(files)
            item["reason"] = "present_but_not_integrated_by_current_qa_preprocessor"
        rows.append(item)
    return {
        "policy": "External datasets may only be used after the real-data QA preprocessor accepts them; no synthetic or hand-fabricated rows are allowed.",
        "entries": rows,
        "additional_qa_usable_dataset_available": any(
            row["qa_usable_now"] and not row["entry"].endswith(("CALCE", "NASA", "Oxford"))
            for row in rows
        ),
    }


def clean_original_features(features: list[str]) -> list[str]:
    return [
        c for c in features
        if c not in BOOKKEEPING_FEATURES and c != NEGATIVE_CONTROL_FEATURE
    ]


def feature_schemas(frame: pd.DataFrame, task_features: list[str]) -> dict[str, list[str]]:
    schemas = {
        "as_used_exp010_schema": [c for c in task_features if c in frame.columns],
        "clean_original_no_recent_schema": [c for c in clean_original_features(task_features) if c in frame.columns],
        "common_cycle_no_recent_schema": [c for c in COMMON_NO_RECENT if c in frame.columns],
        "common_cycle_prev_soh_reference_schema": [c for c in COMMON_WITH_PREV_SOH if c in frame.columns],
    }
    clean = schemas["clean_original_no_recent_schema"]
    if clean and NEGATIVE_CONTROL_FEATURE in frame.columns:
        schemas["clean_original_negative_control_schema"] = clean + [NEGATIVE_CONTROL_FEATURE]
    return {name: cols for name, cols in schemas.items() if cols}


def cqr_interval(train: pd.DataFrame, cal: pd.DataFrame, test: pd.DataFrame, features: list[str], seed: int) -> dict:
    y_train = train["target_soh"].to_numpy()
    y_cal = cal["target_soh"].to_numpy()
    y_test = test["target_soh"].to_numpy()
    lower_model, upper_model, center_model = base.fit_gb_quantiles(train[features], y_train, seed)
    cal_lower = lower_model.predict(cal[features])
    cal_upper = upper_model.predict(cal[features])
    cal_low = np.minimum(cal_lower, cal_upper)
    cal_high = np.maximum(cal_lower, cal_upper)
    scores = np.maximum.reduce([cal_low - y_cal, y_cal - cal_high, np.zeros_like(y_cal)])
    qhat = base.conformal_q(scores, alpha=1 - base.TARGET)
    test_lower = lower_model.predict(test[features])
    test_upper = upper_model.predict(test[features])
    low = np.minimum(test_lower, test_upper) - qhat
    high = np.maximum(test_lower, test_upper) + qhat
    center = center_model.predict(test[features])
    return {
        "frame": test,
        "y": y_test,
        "lower": low,
        "upper": high,
        "center": center,
        "covered": (y_test >= low) & (y_test <= high),
        "qhat": float(qhat),
    }


def decision_rates(frame: pd.DataFrame, y: np.ndarray, lower: np.ndarray, upper: np.ndarray, seed: int, reps: int, min_denominator: int, family_n: int) -> dict:
    return hard.decision_utility(frame, y, lower, upper, seed, reps, min_denominator, family_n)


def method_summary(interval: dict, seed: int, reps: int, min_denominator: int, family_n: int) -> dict:
    frame = interval["frame"]
    y = interval["y"]
    lower = interval["lower"]
    upper = interval["upper"]
    center = interval["center"]
    metrics = base.interval_metrics(frame, y, lower, upper, center, seed, reps)
    utility = decision_rates(frame, y, lower, upper, seed, reps, min_denominator, family_n)
    return {
        **metrics,
        "qhat": interval["qhat"],
        "decision_utility_ci": utility,
        "mae": float(mean_absolute_error(y, center)),
        "rmse": float(mean_squared_error(y, center) ** 0.5),
    }


def block_bootstrap_delta(frame: pd.DataFrame, a: np.ndarray, b: np.ndarray, seed: int, reps: int, alpha: float, group_col: str = "cell_id") -> dict:
    groups = frame[group_col].astype(str).to_numpy()
    unique, inverse = np.unique(groups, return_inverse=True)
    observed = float(np.mean(a) - np.mean(b)) if len(a) else 0.0
    if len(unique) < 2:
        return {"delta": observed, "ci_low": observed, "ci_high": observed, "alpha": alpha, "group_col": group_col, "groups": int(len(unique))}
    rng = np.random.default_rng(seed)
    group_n = np.bincount(inverse, minlength=len(unique)).astype(float)
    group_a = np.bincount(inverse, weights=np.asarray(a, dtype=float), minlength=len(unique))
    group_b = np.bincount(inverse, weights=np.asarray(b, dtype=float), minlength=len(unique))
    boot = []
    for _ in range(reps):
        sampled = rng.integers(0, len(unique), size=len(unique))
        denominator = float(np.sum(group_n[sampled]))
        if denominator > 0:
            boot.append(float((np.sum(group_a[sampled]) - np.sum(group_b[sampled])) / denominator))
    ci = se_ci(observed, boot, alpha, -1.0, 1.0)
    return {
        "delta": observed,
        "ci_low": ci["ci_low"],
        "ci_high": ci["ci_high"],
        "se": ci["se"],
        "alpha": alpha,
        "ci_method": "normal_approx",
        "group_col": group_col,
        "groups": int(len(unique)),
    }


def false_safe_arrays(y: np.ndarray, lower: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray]:
    actual_unsafe = y < threshold
    predicted_safe = lower >= threshold
    return predicted_safe & actual_unsafe, actual_unsafe


def rate_delta_by_cell(frame: pd.DataFrame, num_a: np.ndarray, num_b: np.ndarray, den: np.ndarray, seed: int, reps: int, alpha: float, min_denominator: int) -> dict:
    if not np.any(den):
        return {"delta": 0.0, "ci_low": 0.0, "ci_high": 0.0, "alpha": alpha, "denominator_n": 0, "interpretation": "suppressed_no_denominator"}
    den_n = int(np.sum(den))
    observed = float(np.sum(num_a & den) / np.sum(den) - np.sum(num_b & den) / np.sum(den))
    groups = frame["cell_id"].astype(str).to_numpy()
    unique = np.unique(groups[den])
    if den_n < min_denominator or len(unique) < 2:
        # Small-denominator suppression: a sub-floor cell is exploratory and must not
        # drive a headline artifact-positive verdict (consistent with the decision-cell floor).
        return {"delta": observed, "ci_low": observed, "ci_high": observed, "alpha": alpha, "denominator_n": den_n, "effective_cell_count": int(len(unique)), "interpretation": "suppressed_low_denominator_or_cells"}
    cell_den = np.asarray([np.sum(den & (groups == cell)) for cell in unique], dtype=float)
    cell_a = np.asarray([np.sum(num_a & den & (groups == cell)) for cell in unique], dtype=float)
    cell_b = np.asarray([np.sum(num_b & den & (groups == cell)) for cell in unique], dtype=float)
    cell_delta = cell_a / cell_den - cell_b / cell_den
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(reps):
        sampled = rng.integers(0, len(unique), size=len(unique))
        denominator = float(np.sum(cell_den[sampled]))
        if denominator > 0:
            boot.append(float((np.sum(cell_a[sampled]) - np.sum(cell_b[sampled])) / denominator))
    ci = se_ci(observed, boot, alpha, -1.0, 1.0)
    nonzero = cell_delta[~np.isclose(cell_delta, 0.0)]
    if len(nonzero):
        positive = int(np.sum(nonzero > 0))
        k = min(positive, int(len(nonzero) - positive))
        sign_p = min(1.0, 2.0 * sum(math.comb(len(nonzero), j) for j in range(k + 1)) / (2 ** len(nonzero)))
    else:
        sign_p = 1.0
    boundary_exact = bool(ci["degenerate"] and abs(observed) > 0 and sign_p <= alpha)
    return {
        "delta": observed,
        "ci_low": ci["ci_low"],
        "ci_high": ci["ci_high"],
        "se": ci["se"],
        "alpha": alpha,
        "ci_method": "normal_approx",
        "denominator_n": den_n,
        "effective_cell_count": int(len(unique)),
        "paired_cell_sign_pvalue": float(sign_p),
        "paired_cell_nonzero_count": int(len(nonzero)),
        "boundary_exact_significant": boundary_exact,
        "interpretation": "boundary_exact" if boundary_exact else ("zero_se_non_significant" if ci["degenerate"] else "interpretable"),
    }


def schema_deltas(task_result: dict, seed: int, reps: int, family_n: int, min_denominator: int) -> dict:
    intervals = task_result["_intervals"]
    frame = next(iter(intervals.values()))["frame"]
    alpha = 0.05 / max(family_n, 1)
    out = {}
    comparisons = [
        ("artifact_bookkeeping_as_used_minus_clean_original", "as_used_exp010_schema", "clean_original_no_recent_schema", "bookkeeping_artifact"),
        ("negative_control_clean_original_minus_zero_control", "clean_original_no_recent_schema", "clean_original_negative_control_schema", "negative_control"),
        ("legitimate_feature_richness_clean_original_minus_common_no_recent", "clean_original_no_recent_schema", "common_cycle_no_recent_schema", "legitimate_feature_set_sensitivity"),
        ("recent_label_reference_common_no_recent_minus_prev_soh_reference", "common_cycle_no_recent_schema", "common_cycle_prev_soh_reference_schema", "reference_only_recent_label_sensitivity"),
        ("as_used_vs_common_no_recent", "as_used_exp010_schema", "common_cycle_no_recent_schema"),
    ]
    for comparison in comparisons:
        label, a_name, b_name = comparison[:3]
        interpretation_class = comparison[3] if len(comparison) > 3 else "legacy_summary"
        if a_name not in intervals or b_name not in intervals:
            continue
        a = intervals[a_name]
        b = intervals[b_name]
        item = {
            "interpretation_class": interpretation_class,
            "multiplicity_adjustment": "Bonferroni across all preregistered coverage and false-safe schema-delta tests",
            "multiplicity_family_n": family_n,
            "coverage_delta_a_minus_b": block_bootstrap_delta(frame, a["covered"], b["covered"], seed, reps, alpha),
            "mean_width_delta_a_minus_b": float(np.mean(a["upper"] - a["lower"]) - np.mean(b["upper"] - b["lower"])),
            "mae_delta_a_minus_b": float(mean_absolute_error(a["y"], a["center"]) - mean_absolute_error(b["y"], b["center"])),
            "false_safe_rate_delta_a_minus_b": {},
        }
        for idx, threshold in enumerate(THRESHOLDS):
            num_a, den = false_safe_arrays(a["y"], a["lower"], threshold)
            num_b, _ = false_safe_arrays(b["y"], b["lower"], threshold)
            item["false_safe_rate_delta_a_minus_b"][f"soh_threshold_{threshold:.2f}"] = rate_delta_by_cell(
                frame,
                num_a,
                num_b,
                den,
                seed + 101 + idx,
                reps,
                alpha,
                min_denominator,
            )
        out[label] = item
    return out


def evaluate_task(frame: pd.DataFrame, task_name: str, indices: tuple, seed: int, reps: int, min_denominator: int, family_n: int) -> dict:
    train_idx, cal_idx, _val_idx, test_idx, task_features = indices
    schemas = feature_schemas(frame, task_features)
    required_cols = sorted({col for cols in schemas.values() for col in cols} | {"target_soh"})
    valid_mask = frame[required_cols].notna().all(axis=1)
    train_idx = np.asarray([idx for idx in train_idx if bool(valid_mask.loc[idx])], dtype=int)
    cal_idx = np.asarray([idx for idx in cal_idx if bool(valid_mask.loc[idx])], dtype=int)
    test_idx = np.asarray([idx for idx in test_idx if bool(valid_mask.loc[idx])], dtype=int)
    train = frame.loc[train_idx].copy()
    cal = frame.loc[cal_idx].copy()
    test = frame.loc[test_idx].copy()
    if min(len(train), len(cal), len(test)) == 0:
        return {"skipped": True, "reason": "empty train/cal/test split after shared row-alignment mask"}
    intervals = {}
    summaries = {}
    for schema_name, features in schemas.items():
        interval = cqr_interval(train, cal, test, features, seed)
        intervals[schema_name] = interval
        summaries[schema_name] = {
            "features": features,
            "n_features": len(features),
            "metrics": method_summary(interval, seed, reps, min_denominator, family_n),
            "shift_diagnostics": rel.shift_diagnostics(cal, test, features),
        }
    result = {
        "task": task_name,
        "n_train": int(len(train)),
        "n_cal": int(len(cal)),
        "n_test": int(len(test)),
        "row_alignment": {
            "rule": "All schemas in this task use the same train/cal/test rows after intersecting non-null feature requirements.",
            "required_columns": required_cols,
        },
        "schemas": summaries,
        "_intervals": intervals,
    }
    result["schema_deltas"] = schema_deltas(result, seed, reps, family_n, min_denominator)
    result.pop("_intervals", None)
    return result


def ci_excludes_zero(item: dict) -> bool:
    return bool(item["ci_low"] > 0 or item["ci_high"] < 0)


def inferentially_significant(item: dict) -> bool:
    return bool(ci_excludes_zero(item) or item.get("boundary_exact_significant", False))


def decision_rules(tasks: dict) -> dict:
    rows = []
    artifact_positive = []          # coverage-lens artifact (the robust, headline criterion)
    fs_safety_degrading = []        # diagnostic: artifact significantly RAISES false-safe (more dangerous)
    fs_safety_improving = []        # diagnostic: artifact significantly LOWERS false-safe (safer)
    fs_degenerate_tasks = []        # diagnostic: degenerate false-safe cell (boundary 0<->1 flip)
    negative_control_failures = []
    for task_name, task in tasks.items():
        if task.get("skipped"):
            continue
        deltas = task.get("schema_deltas", {})
        artifact = deltas.get("artifact_bookkeeping_as_used_minus_clean_original")
        if artifact:
            cov = artifact["coverage_delta_a_minus_b"]
            # HEADLINE artifact verdict = coverage lens only (robust): CI excludes 0 and |delta| >= 3pp.
            coverage_positive = bool(ci_excludes_zero(cov) and abs(cov["delta"]) >= ARTIFACT_DELTA_MIN_ABS)
            # False-safe reported as a SIGNED diagnostic, not a headline trigger.
            fs_cells = artifact["false_safe_rate_delta_a_minus_b"]
            sig = [(k, v) for k, v in fs_cells.items()
                   if v.get("interpretation") in {"interpretable", "boundary_exact"} and inferentially_significant(v)]
            degenerate = sorted(k for k, v in fs_cells.items() if v.get("interpretation") == "zero_se_non_significant")
            fs_key, fs = (None, None)
            if sig:
                fs_key, fs = max(sig, key=lambda kv: abs(kv[1]["delta"]))
            fs_direction = "none"
            if fs is not None:
                if fs["delta"] > 0:
                    fs_direction = "more_dangerous"
                    fs_safety_degrading.append(task_name)
                else:
                    fs_direction = "safer"
                    fs_safety_improving.append(task_name)
            if degenerate:
                fs_degenerate_tasks.append(task_name)
            rows.append({
                "task": task_name,
                "rule": "coverage artifact requires CI exclusion and abs(delta)>=3pp; false-safe evidence uses a multiplicity-adjusted CI or boundary-safe exact paired-cell sign test",
                "coverage_delta": cov["delta"],
                "coverage_ci_low": cov["ci_low"],
                "coverage_ci_high": cov["ci_high"],
                "coverage_artifact_positive": coverage_positive,
                "fs_threshold": fs_key,
                "fs_delta": fs["delta"] if fs else None,
                "fs_ci_low": fs["ci_low"] if fs else None,
                "fs_ci_high": fs["ci_high"] if fs else None,
                "fs_denominator_n": fs["denominator_n"] if fs else None,
                "fs_exact_pvalue": fs.get("paired_cell_sign_pvalue") if fs else None,
                "fs_direction": fs_direction,
                "fs_degenerate_thresholds": degenerate,
                "artifact_positive": coverage_positive,
            })
            if coverage_positive:
                artifact_positive.append(task_name)
        neg = deltas.get("negative_control_clean_original_minus_zero_control")
        if neg:
            cov = neg["coverage_delta_a_minus_b"]
            if ci_excludes_zero(cov) or any(inferentially_significant(v) for v in neg["false_safe_rate_delta_a_minus_b"].values() if v.get("interpretation") in {"interpretable", "boundary_exact"}):
                negative_control_failures.append(task_name)
    return {
        "artifact_delta_min_abs": ARTIFACT_DELTA_MIN_ABS,
        "artifact_positive_tasks": artifact_positive,
        "fs_safety_degrading_tasks": fs_safety_degrading,
        "fs_safety_improving_tasks": fs_safety_improving,
        "fs_degenerate_tasks": fs_degenerate_tasks,
        "negative_control_failures": negative_control_failures,
        "claim_allowed": bool(artifact_positive and not negative_control_failures),
        "rows": rows,
        "exp010_integrity_action": (
            "If artifact_positive_tasks is non-empty, exp010 no-recent-label hard-regime conclusions that used bookkeeping features must be downgraded or explicitly labeled contaminated."
        ),
    }


def compact_delta_summary(tasks: dict) -> dict:
    rows = []
    for task_name, task in tasks.items():
        if task.get("skipped"):
            continue
        for comparison, delta in task["schema_deltas"].items():
            cov = delta["coverage_delta_a_minus_b"]
            rows.append({
                "task": task_name,
                "comparison": comparison,
                "interpretation_class": delta.get("interpretation_class"),
                "coverage_delta": cov["delta"],
                "coverage_ci_low": cov["ci_low"],
                "coverage_ci_high": cov["ci_high"],
                "coverage_ci_alpha": cov.get("alpha"),
                "mean_width_delta": delta["mean_width_delta_a_minus_b"],
                "mae_delta": delta["mae_delta_a_minus_b"],
            })
    return {
        "interpretation": "Positive delta means schema A has larger metric than schema B on identical test rows.",
        "rows": rows,
        "largest_abs_coverage_delta": max(rows, key=lambda r: abs(r["coverage_delta"])) if rows else None,
    }


def multiplicity_control(tasks: dict, family_n: int) -> dict:
    return {
        "family_definition": "For each task and preregistered schema comparison, one coverage-delta test plus one false-safe-rate delta test per SOH threshold.",
        "family_n": family_n,
        "alpha": 0.05,
        "bonferroni_alpha": 0.05 / max(family_n, 1),
        "comparisons": [
            "artifact_bookkeeping_as_used_minus_clean_original",
            "negative_control_clean_original_minus_zero_control",
            "legitimate_feature_richness_clean_original_minus_common_no_recent",
            "recent_label_reference_common_no_recent_minus_prev_soh_reference",
            "as_used_vs_common_no_recent",
        ],
        "thresholds": list(THRESHOLDS),
        "note": "Reported delta CIs in schema_delta_summary use the Bonferroni-adjusted alpha.",
    }


def write_report(exp_dir: Path, metrics: dict) -> None:
    lines = [
        "# exp011_original_paper_substance Report",
        "",
        "**Status**: pending_review",
        "",
        "## Results Summary",
        "",
        "This experiment supplies user-approved new substance for a RESS Original Paper route.",
        "It audits whether schema choices change interval reliability and safety-decision metrics on identical real-data task splits.",
        "",
        "| Task | Comparison | Coverage delta | 95% block CI | Width delta | MAE delta |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in metrics["schema_delta_summary"]["rows"]:
        lines.append(
            f"| {row['task']} | {row['comparison']} | {row['coverage_delta']:.4f} | "
            f"[{row['coverage_ci_low']:.4f}, {row['coverage_ci_high']:.4f}] | "
            f"{row['mean_width_delta']:.4f} | {row['mae_delta']:.4f} |"
        )
    inv = metrics["external_dataset_inventory"]
    lines.extend([
        "",
        "## External Dataset Inventory",
        "",
        f"Additional QA-usable external dataset available now: {inv['additional_qa_usable_dataset_available']}.",
        "",
        "## Data Policy",
        "",
        "Synthetic data was not used. Any external dataset must pass the same real-data QA preprocessor before it can support a claim.",
    ])
    (exp_dir / "report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-exp", default=OUT_EXP)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--min-decision-denominator", type=int, default=5)
    args = parser.parse_args()

    df = pd.read_csv(base.PROCESSED)
    splits = base.read_json(base.SPLITS)
    frame = hard.prepare_horizon_frame(df, 0)
    rng = np.random.default_rng(args.seed + 991)
    frame[NEGATIVE_CONTROL_FEATURE] = rng.permutation(
        frame["log_cycle_index"].to_numpy(dtype=float)
    )
    tasks = hard.build_hard_tasks(frame, splits)
    family_n = len(tasks) * 5 * (1 + len(THRESHOLDS))
    exp_dir = ROOT / "experiments" / args.output_exp

    task_out = {}
    for task_name, indices in tasks.items():
        task_out[task_name] = evaluate_task(
            frame,
            task_name,
            indices,
            args.seed,
            args.bootstrap_reps,
            args.min_decision_denominator,
            family_n,
        )

    run_manifest = {
        "generated_at": datetime.now().isoformat(),
        "script": "scripts/run_original_paper_substance_experiment.py",
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
        "user_direction_gate": "Round 8 option 2: approve new substance for RESS Original Paper",
        "deterministic_regeneration_command": (
            "python scripts/run_original_paper_substance_experiment.py "
            f"--output-exp {args.output_exp} --seed {args.seed} "
            f"--bootstrap-reps {args.bootstrap_reps} "
            f"--min-decision-denominator {args.min_decision_denominator}"
        ),
    }
    metrics = {
        "target_coverage": base.TARGET,
        "cell_ci_floor": base.CELL_CI_FLOOR,
        "horizon_cycles": 0,
        "schema_policy": {
            "as_used_exp010_schema": "Contaminated condition under test: reproduces the exp010 task feature list, including any bookkeeping features that prior scripts allowed.",
            "clean_original_no_recent_schema": "Removes source_row_id, target_cycle_index, target_soh, prev_soh, and prev_soh_missing from the no-recent-label feature list.",
            "common_cycle_no_recent_schema": list(COMMON_NO_RECENT),
            "common_cycle_prev_soh_reference_schema": "Reference-only schema with prev_soh; not a no-recent-label decision policy.",
            "clean_original_negative_control_schema": "Negative control: independently refitted clean-original pipeline plus a fixed-seed permuted log-cycle feature on the shared row-alignment mask.",
        },
        "tasks": task_out,
        "schema_delta_summary": compact_delta_summary(task_out),
        "multiplicity_control": multiplicity_control(task_out, family_n),
        "decision_rules": decision_rules(task_out),
        "external_dataset_inventory": external_dataset_inventory(),
        "split_manifest": {
            "processed_data": str(base.PROCESSED.relative_to(ROOT)),
            "processed_data_sha256": base.sha256(base.PROCESSED),
            "split_manifest": str(base.SPLITS.relative_to(ROOT)),
            "split_manifest_sha256": base.sha256(base.SPLITS),
            "split_counts": {k: len(v) for k, v in splits.items()},
        },
        "run_manifest": run_manifest,
    }

    write_json(exp_dir / "results" / "metrics.json", metrics)
    write_json(exp_dir / "results" / "schema_delta_summary.json", metrics["schema_delta_summary"])
    write_json(exp_dir / "results" / "multiplicity_control.json", metrics["multiplicity_control"])
    write_json(exp_dir / "results" / "external_dataset_inventory.json", metrics["external_dataset_inventory"])
    write_json(exp_dir / "results" / "run_manifest.json", run_manifest)
    write_json(exp_dir / "results" / "split_manifest.json", metrics["split_manifest"])
    write_report(exp_dir, metrics)
    print(json.dumps({"status": "ok", "metrics": str(exp_dir / "results" / "metrics.json")}, indent=2))


if __name__ == "__main__":
    main()
