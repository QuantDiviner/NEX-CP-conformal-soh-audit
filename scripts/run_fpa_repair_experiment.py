#!/usr/bin/env python3
"""Run the exp006 FPA repair analysis on real battery data only."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed" / "real_battery_cycle_level_features.csv"
SPLITS = ROOT / "data" / "splits" / "real_battery_splits.json"
TARGET = 0.90
CELL_CI_FLOOR = 0.85
Z90 = 1.6448536269514722
TARGET_TRAIN_MAX = 0.20
TARGET_CAL_MAX = 0.35
TARGET_VAL_MAX = 0.55


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def runtime_packages() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }


def feature_columns(df: pd.DataFrame) -> list[str]:
    blocked = {"soh", "capacity_ah", "source_file", "cell_id", "domain", "calibration_group", "split_progress"}
    return [c for c in df.columns if c not in blocked and pd.api.types.is_numeric_dtype(df[c])]


def cross_domain_feature_columns(df: pd.DataFrame) -> list[str]:
    return [
        c for c in feature_columns(df)
        if not c.startswith("dataset_") and not c.startswith("chemistry_") and not c.startswith("protocol_")
    ]


def conformal_q(scores: np.ndarray, alpha: float = 0.10) -> float:
    if len(scores) == 0:
        return float("nan")
    q = np.ceil((len(scores) + 1) * (1 - alpha)) / len(scores)
    return float(np.quantile(scores, min(q, 1.0), method="higher"))


def block_bootstrap_ci(
    frame: pd.DataFrame,
    covered: np.ndarray,
    group_col: str,
    seed: int,
    reps: int,
) -> tuple[float, float]:
    if group_col not in frame.columns or len(covered) == 0:
        return float("nan"), float("nan")
    groups = frame[group_col].astype(str).to_numpy()
    unique, inverse = np.unique(groups, return_inverse=True)
    if len(unique) < 2:
        p = float(np.mean(covered))
        return p, p
    rng = np.random.default_rng(seed)
    group_n = np.bincount(inverse, minlength=len(unique)).astype(float)
    group_covered = np.bincount(
        inverse, weights=np.asarray(covered, dtype=float), minlength=len(unique)
    )
    boot = []
    for _ in range(reps):
        sampled = rng.integers(0, len(unique), size=len(unique))
        denominator = float(np.sum(group_n[sampled]))
        if denominator > 0:
            boot.append(float(np.sum(group_covered[sampled]) / denominator))
    if not boot:
        return float("nan"), float("nan")
    return float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def target_recalibrated_indices(
    df: pd.DataFrame, target_domain: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return disjoint source/target train, calibration, validation, and test rows."""
    source = df["domain"].ne(target_domain)
    target = df["domain"].eq(target_domain)
    progress = df["split_progress"]
    train_idx = df.index[
        source | (target & (progress <= TARGET_TRAIN_MAX))
    ].to_numpy()
    cal_idx = df.index[
        target & (progress > TARGET_TRAIN_MAX) & (progress <= TARGET_CAL_MAX)
    ].to_numpy()
    val_idx = df.index[
        target & (progress > TARGET_CAL_MAX) & (progress <= TARGET_VAL_MAX)
    ].to_numpy()
    test_idx = df.index[target & (progress > TARGET_VAL_MAX)].to_numpy()
    split_sets = [set(map(int, x)) for x in (train_idx, cal_idx, val_idx, test_idx)]
    for i, left in enumerate(split_sets):
        for right in split_sets[i + 1 :]:
            if left & right:
                raise AssertionError(
                    f"target-recalibrated split overlap for {target_domain}"
                )
    return train_idx, cal_idx, val_idx, test_idx


def coverage_first_score(m: dict[str, float]) -> float:
    score = float(m["mean_width"])
    score += max(0.0, TARGET - float(m["coverage"])) * 1000.0
    score += max(0.0, CELL_CI_FLOOR - float(m["cell_block_ci_low"])) * 1000.0
    return score


def exp001_compatible_selection_score(m: dict[str, float]) -> float:
    score = float(m["mean_width"])
    score += max(0.0, TARGET - float(m["coverage"])) * 1000.0
    return score


def interval_metrics(
    frame: pd.DataFrame,
    y: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    center: np.ndarray,
    seed: int,
    reps: int,
) -> dict:
    covered = (y >= lower) & (y <= upper)
    width = upper - lower
    cell_low, cell_high = block_bootstrap_ci(frame, covered, "cell_id", seed, reps)
    domain_low, domain_high = block_bootstrap_ci(frame, covered, "domain", seed + 17, reps)
    return {
        "coverage": float(np.mean(covered)),
        "cell_block_ci_low": cell_low,
        "cell_block_ci_high": cell_high,
        "domain_block_ci_low": domain_low,
        "domain_block_ci_high": domain_high,
        "mean_width": float(np.mean(width)),
        "median_width": float(np.median(width)),
        "soh_normalized_mean_width": float(np.mean(width) / max(float(np.nanmean(np.abs(y))), 1e-12)),
        "mae": float(mean_absolute_error(y, center)),
        "rmse": float(mean_squared_error(y, center) ** 0.5),
        "n": int(len(y)),
    }


def decision_utility(y: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict:
    out = {}
    for threshold in (0.80, 0.70):
        actual_unsafe = y < threshold
        actual_safe = ~actual_unsafe
        predicted_safe = lower >= threshold
        predicted_unsafe = upper < threshold
        uncertain = ~(predicted_safe | predicted_unsafe)
        false_safe = predicted_safe & actual_unsafe
        false_alarm = predicted_unsafe & actual_safe
        out[f"soh_threshold_{threshold:.2f}"] = {
            "threshold": float(threshold),
            "false_safe_rate_per_actual_unsafe": float(np.mean(false_safe[actual_unsafe])) if np.any(actual_unsafe) else 0.0,
            "false_alarm_rate_per_actual_safe": float(np.mean(false_alarm[actual_safe])) if np.any(actual_safe) else 0.0,
            "uncertain_rate": float(np.mean(uncertain)),
            "predicted_safe_rate": float(np.mean(predicted_safe)),
            "predicted_unsafe_rate": float(np.mean(predicted_unsafe)),
            "n_actual_unsafe": int(np.sum(actual_unsafe)),
            "n_actual_safe": int(np.sum(actual_safe)),
        }
    return out


def group_audit(frame: pd.DataFrame, y: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict:
    covered = (y >= lower) & (y <= upper)
    out = {}
    for col in ("domain", "calibration_group", "cell_id"):
        rows = {}
        for key, g in frame.groupby(col):
            idx = frame.index.isin(g.index)
            if col == "cell_id" and int(np.sum(idx)) < 20:
                continue
            rows[str(key)] = {
                "coverage": float(np.mean(covered[idx])),
                "n": int(np.sum(idx)),
            }
        out[col] = rows
    return out


def residual_diagnostics(frame: pd.DataFrame, y: np.ndarray, center: np.ndarray, covered: np.ndarray) -> dict:
    tmp = frame[["domain", "cell_id", "split_progress"]].copy()
    tmp["abs_residual"] = np.abs(y - center)
    tmp["covered"] = covered
    tmp["stage"] = pd.qcut(tmp["split_progress"], q=4, duplicates="drop").astype(str)
    out = {"by_domain": {}, "by_stage": {}}
    for domain, g in tmp.groupby("domain"):
        out["by_domain"][str(domain)] = {
            "mean_abs_residual": float(g["abs_residual"].mean()),
            "coverage": float(g["covered"].mean()),
            "n": int(len(g)),
        }
    for stage, g in tmp.groupby("stage"):
        out["by_stage"][str(stage)] = {
            "mean_abs_residual": float(g["abs_residual"].mean()),
            "coverage": float(g["covered"].mean()),
            "n": int(len(g)),
        }
    return out


def fit_gb_quantiles(x_train: pd.DataFrame, y_train: np.ndarray, seed: int) -> tuple:
    common = {"random_state": seed, "max_depth": 3, "n_estimators": 250, "learning_rate": 0.035}
    lower = GradientBoostingRegressor(loss="quantile", alpha=0.05, **common)
    upper = GradientBoostingRegressor(loss="quantile", alpha=0.95, **common)
    mean = GradientBoostingRegressor(loss="squared_error", **common)
    lower.fit(x_train, y_train)
    upper.fit(x_train, y_train)
    mean.fit(x_train, y_train)
    return lower, upper, mean


def mondrian_radius(cal: pd.DataFrame, resid: np.ndarray, target_groups: pd.Series, q_level: float) -> np.ndarray:
    global_q = float(np.quantile(resid, q_level, method="higher"))
    radii = []
    cal_groups = cal["calibration_group"].astype(str).to_numpy()
    for group in target_groups.astype(str):
        local = resid[cal_groups == group]
        radii.append(float(np.quantile(local, q_level, method="higher")) if len(local) >= 20 else global_q)
    return np.asarray(radii)


def evaluate_task(
    name: str,
    df: pd.DataFrame,
    train_idx: np.ndarray,
    cal_idx: np.ndarray,
    val_idx: np.ndarray,
    test_idx: np.ndarray,
    fcols: list[str],
    seed: int,
    reps: int,
    include_ngboost: bool,
) -> dict:
    train = df.loc[train_idx].copy()
    cal = df.loc[cal_idx].copy()
    val = df.loc[val_idx].copy()
    test = df.loc[test_idx].copy()
    y_train = train["soh"].to_numpy()
    y_cal = cal["soh"].to_numpy()
    y_test = test["soh"].to_numpy()
    methods = {}

    # Persistence-anchor protocol Mondrian CP.
    cal_resid = np.abs(y_cal - cal["prev_soh"].to_numpy())
    val_y = val["soh"].to_numpy()
    val_pred = val["prev_soh"].to_numpy()
    best_q = TARGET
    best_score = float("inf")
    for q_level in (0.90, 0.93, 0.95, 0.97, 0.99, 1.00):
        if len(val):
            val_radius = mondrian_radius(cal, cal_resid, val["calibration_group"], q_level)
            val_m = interval_metrics(val, val_y, val_pred - val_radius, val_pred + val_radius, val_pred, seed, reps)
            score = exp001_compatible_selection_score(val_m)
            if score < best_score:
                best_q, best_score = q_level, score
    test_center = test["prev_soh"].to_numpy()
    test_radius = mondrian_radius(cal, cal_resid, test["calibration_group"], best_q)
    lower = test_center - test_radius
    upper = test_center + test_radius
    covered = (y_test >= lower) & (y_test <= upper)
    methods["persistence_anchor_protocol_mondrian_cp"] = {
        **interval_metrics(test, y_test, lower, upper, test_center, seed, reps),
        "q_level": float(best_q),
        "selection_rule": "validation coverage-first width minimization; block CIs are reported but not used for q tuning",
        "decision_utility": decision_utility(y_test, lower, upper),
        "group_audit": group_audit(test, y_test, lower, upper),
        "residual_diagnostics": residual_diagnostics(test, y_test, test_center, covered),
    }

    # Quantile regression and CQR baselines.
    lower_model, upper_model, center_model = fit_gb_quantiles(train[fcols], y_train, seed)
    cal_lower = lower_model.predict(cal[fcols])
    cal_upper = upper_model.predict(cal[fcols])
    test_lower = lower_model.predict(test[fcols])
    test_upper = upper_model.predict(test[fcols])
    test_center = center_model.predict(test[fcols])

    lower = np.minimum(test_lower, test_upper)
    upper = np.maximum(test_lower, test_upper)
    covered = (y_test >= lower) & (y_test <= upper)
    methods["qr_gradient_boosting"] = {
        **interval_metrics(test, y_test, lower, upper, test_center, seed, reps),
        "decision_utility": decision_utility(y_test, lower, upper),
        "group_audit": group_audit(test, y_test, lower, upper),
        "residual_diagnostics": residual_diagnostics(test, y_test, test_center, covered),
    }

    cal_low = np.minimum(cal_lower, cal_upper)
    cal_high = np.maximum(cal_lower, cal_upper)
    scores = np.maximum.reduce([cal_low - y_cal, y_cal - cal_high, np.zeros_like(y_cal)])
    qhat = conformal_q(scores, alpha=1 - TARGET)
    lower = np.minimum(test_lower, test_upper) - qhat
    upper = np.maximum(test_lower, test_upper) + qhat
    covered = (y_test >= lower) & (y_test <= upper)
    methods["cqr_gradient_boosting"] = {
        **interval_metrics(test, y_test, lower, upper, test_center, seed, reps),
        "qhat": float(qhat),
        "decision_utility": decision_utility(y_test, lower, upper),
        "group_audit": group_audit(test, y_test, lower, upper),
        "residual_diagnostics": residual_diagnostics(test, y_test, test_center, covered),
    }

    if include_ngboost:
        try:
            from ngboost import NGBRegressor
            from ngboost.distns import Normal

            ngb = NGBRegressor(
                Dist=Normal,
                n_estimators=300,
                learning_rate=0.03,
                random_state=seed,
                verbose=False,
            )
            ngb.fit(train[fcols], y_train)
            cal_dist = ngb.pred_dist(cal[fcols])
            test_dist = ngb.pred_dist(test[fcols])
            cal_center = np.asarray(cal_dist.params["loc"], dtype=float)
            cal_scale = np.maximum(np.asarray(cal_dist.params["scale"], dtype=float), 1e-8)
            test_center = np.asarray(test_dist.params["loc"], dtype=float)
            test_scale = np.maximum(np.asarray(test_dist.params["scale"], dtype=float), 1e-8)
            cal_lower = cal_center - Z90 * cal_scale
            cal_upper = cal_center + Z90 * cal_scale
            scores = np.maximum.reduce([cal_lower - y_cal, y_cal - cal_upper, np.zeros_like(y_cal)])
            qhat = conformal_q(scores, alpha=1 - TARGET)
            lower = test_center - Z90 * test_scale - qhat
            upper = test_center + Z90 * test_scale + qhat
            covered = (y_test >= lower) & (y_test <= upper)
            methods["ngboost_normal_cqr"] = {
                **interval_metrics(test, y_test, lower, upper, test_center, seed, reps),
                "qhat": float(qhat),
                "baseline_family": "NGBoost probabilistic Normal distribution with conformalized interval",
                "decision_utility": decision_utility(y_test, lower, upper),
                "group_audit": group_audit(test, y_test, lower, upper),
                "residual_diagnostics": residual_diagnostics(test, y_test, test_center, covered),
            }
        except Exception as exc:
            methods["ngboost_normal_cqr"] = {
                "skipped": True,
                "reason": f"{type(exc).__name__}: {exc}",
                "baseline_family": "NGBoost probabilistic Normal distribution with conformalized interval",
            }

    return {
        "task": name,
        "n_train": int(len(train_idx)),
        "n_cal": int(len(cal_idx)),
        "n_val": int(len(val_idx)),
        "n_test": int(len(test_idx)),
        "features": fcols,
        "methods": methods,
    }


def build_tasks(df: pd.DataFrame, splits: dict[str, list[int]]) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]]:
    train_idx = np.array(splits["train"], dtype=int)
    cal_idx = np.array(splits["cal"], dtype=int)
    val_idx = np.array(splits["val"], dtype=int)
    test_idx = np.array(splits["test"], dtype=int)
    tasks = {
        "main_heldout": (train_idx, cal_idx, val_idx, test_idx, feature_columns(df)),
    }
    for domain in sorted(df["domain"].unique()):
        source = df["domain"].ne(domain)
        target = df["domain"].eq(domain)
        tasks[f"leave_{domain}_out"] = (
            train_idx[source.loc[train_idx].to_numpy()],
            cal_idx[source.loc[cal_idx].to_numpy()],
            val_idx[source.loc[val_idx].to_numpy()],
            df.index[target].to_numpy(),
            cross_domain_feature_columns(df),
        )
        tr_idx, ca_idx, va_idx, te_idx = target_recalibrated_indices(df, domain)
        tasks[f"target_recalibrated_{domain}"] = (
            tr_idx,
            ca_idx,
            va_idx,
            te_idx,
            cross_domain_feature_columns(df),
        )
    return tasks


def main_split_design(df: pd.DataFrame, splits: dict[str, list[int]], seed: int) -> dict:
    """Return manuscript-facing, deterministic Main split and label timing metadata."""
    partitions = {}
    for name in ("train", "cal", "val", "test"):
        frame = df.loc[np.asarray(splits[name], dtype=int)]
        partitions[name] = {
            "n_rows": int(len(frame)),
            "n_cells": int(frame["cell_id"].nunique()),
            "domain_rows": {
                str(key): int(value)
                for key, value in frame["domain"].value_counts().sort_index().items()
            },
            "cell_ids": sorted(frame["cell_id"].astype(str).unique().tolist()),
            "progress_min": float(frame["split_progress"].min()),
            "progress_max": float(frame["split_progress"].max()),
        }
    return {
        "name": "domain-stratified cell-disjoint mixed-domain held-out split",
        "seed": int(seed),
        "source_cycle_rows": int(len(df) + df["cell_id"].nunique()),
        "eligible_cycle_rows": int(len(df)),
        "excluded_first_rows": int(df["cell_id"].nunique()),
        "eligible_domain_rows": {
            str(key): int(value)
            for key, value in df["domain"].value_counts().sort_index().items()
        },
        "allocation": "within each domain, shuffled cells are assigned 55% train, 20% calibration, 10% validation, remainder test; calibration retains progress <=0.55 and test retains progress >=0.35",
        "cell_disjoint": True,
        "test_cells_contribute_to_fit_or_calibration": False,
        "partitions": partitions,
        "recent_label": {
            "definition": "prev_soh(i,t) = soh(i,t-1), the immediately preceding recorded cycle for the same cell after sorting by dataset, cell_id, and cycle_index",
            "prediction_timeline": "SOH at cycle t-1 must have been measured before predicting SOH at cycle t",
            "eligibility": "the first record of every cell is excluded before split construction; no current-row SOH imputation is used",
        },
    }


def contribution_verdict(tasks: dict) -> dict:
    main = tasks["main_heldout"]["methods"]
    persistence = main["persistence_anchor_protocol_mondrian_cp"]
    baselines = {
        k: v for k, v in main.items()
        if k != "persistence_anchor_protocol_mondrian_cp" and not v.get("skipped")
    }
    p_score = coverage_first_score(persistence)
    b_scores = {k: coverage_first_score(v) for k, v in baselines.items()}
    best_baseline = min(b_scores, key=b_scores.get)
    if p_score <= b_scores[best_baseline]:
        verdict = "scoped_positive_method_claim_allowed"
    else:
        verdict = "negative_diagnostic_positioning_required"
    return {
        "verdict": verdict,
        "rule": "persistence score must be no worse than the best CQR/QR baseline under coverage-first scoring",
        "persistence_score": float(p_score),
        "best_baseline": best_baseline,
        "best_baseline_score": float(b_scores[best_baseline]),
    }


def failure_list(tasks: dict) -> list[dict]:
    failures = []
    for task_name, task in tasks.items():
        for method_name, method in task["methods"].items():
            if method.get("skipped"):
                continue
            if method["cell_block_ci_low"] < CELL_CI_FLOOR:
                failures.append({
                    "task": task_name,
                    "method": method_name,
                    "level": "task",
                    "coverage": method["coverage"],
                    "cell_block_ci_low": method["cell_block_ci_low"],
                })
            for cell, row in method.get("group_audit", {}).get("cell_id", {}).items():
                if row["coverage"] < CELL_CI_FLOOR:
                    failures.append({
                        "task": task_name,
                        "method": method_name,
                        "level": "cell",
                        "cell_id": cell,
                        "coverage": row["coverage"],
                        "n": row["n"],
                    })
    return failures


def write_report(exp_dir: Path, exp_id: str, metrics_obj: dict) -> None:
    lines = [
        f"# {exp_id} Report",
        "",
        "**Status**: pending_review",
        "",
        f"**Generated**: {metrics_obj['run_manifest']['generated_at']}",
        "",
        "## Results Summary",
        "",
        f"Contribution-positioning verdict: `{metrics_obj['contribution_positioning']['verdict']}`.",
        "",
        "| Task | Method | Coverage | Cell-block CI low | Mean width | RMSE |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for task_name, task in metrics_obj["tasks"].items():
        for method_name, method in task["methods"].items():
            if method.get("skipped"):
                lines.append(f"| {task_name} | {method_name} | skipped | skipped | skipped | skipped |")
                continue
            lines.append(
                f"| {task_name} | {method_name} | {method['coverage']:.4f} | "
                f"{method['cell_block_ci_low']:.4f} | {method['mean_width']:.4f} | {method['rmse']:.4f} |"
            )
    lines.extend([
        "",
        "## FPA Repair Coverage",
        "",
        "- Same-split CQR/QR baselines: complete.",
        "- Dependence-aware cell-block bootstrap CIs: complete.",
        "- Cross-protocol failure diagnostics: complete.",
        "- Run and split manifests: complete.",
        "",
        "Synthetic data was not used.",
    ])
    (exp_dir / "report.md").write_text("\n".join(lines) + "\n")


def legacy_manifests(exp_dir: Path, seed: int) -> dict:
    manifests = {}
    for exp_id in ("exp001_main", "exp002_ablation", "exp003_cross_protocol", "exp004_stress_failure"):
        metrics_path = ROOT / "experiments" / exp_id / "results" / "metrics.json"
        metadata_path = ROOT / "experiments" / exp_id / "metadata.json"
        manifest = {
            "experiment_id": exp_id,
            "reconstructed_at": datetime.now().isoformat(),
            "seed": seed,
            "metrics_path": str(metrics_path.relative_to(ROOT)),
            "metrics_sha256": sha256(metrics_path) if metrics_path.exists() else None,
            "metadata_path": str(metadata_path.relative_to(ROOT)) if metadata_path.exists() else None,
            "metadata_sha256": sha256(metadata_path) if metadata_path.exists() else None,
            "split_manifest": str(SPLITS.relative_to(ROOT)),
            "split_manifest_sha256": sha256(SPLITS) if SPLITS.exists() else None,
            "processed_data": str(PROCESSED.relative_to(ROOT)),
            "processed_data_sha256": sha256(PROCESSED) if PROCESSED.exists() else None,
            "provenance_limitation": "Reconstructed after the original run from current metrics, metadata, processed data, and split manifest; exact historical shell environment may be unavailable.",
        }
        out_path = exp_dir / "results" / "legacy_manifests" / f"{exp_id}_manifest.json"
        write_json(out_path, manifest)
        manifests[exp_id] = str(out_path.relative_to(ROOT))
    return manifests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--output-exp", default="exp006_fpa_repair")
    parser.add_argument("--include-ngboost", action="store_true")
    args = parser.parse_args()
    exp_dir = ROOT / "experiments" / args.output_exp

    if not PROCESSED.exists() or not SPLITS.exists():
        raise SystemExit("Missing processed real data or split manifest. Run scripts/preprocess_real_battery.py first.")
    df = pd.read_csv(PROCESSED)
    splits = read_json(SPLITS)

    tasks_out = {}
    for task_name, (train_idx, cal_idx, val_idx, test_idx, fcols) in build_tasks(df, splits).items():
        if len(train_idx) == 0 or len(cal_idx) == 0 or len(test_idx) == 0:
            tasks_out[task_name] = {"skipped": True, "reason": "empty train/cal/test split"}
            continue
        tasks_out[task_name] = evaluate_task(
            task_name,
            df,
            train_idx,
            cal_idx,
            val_idx,
            test_idx,
            fcols,
            args.seed,
            args.bootstrap_reps,
            args.include_ngboost,
        )

    split_manifest = {
        "processed_data": str(PROCESSED.relative_to(ROOT)),
        "processed_data_sha256": sha256(PROCESSED),
        "split_manifest": str(SPLITS.relative_to(ROOT)),
        "split_manifest_sha256": sha256(SPLITS),
        "split_counts": {k: len(v) for k, v in splits.items()},
    }
    run_manifest = {
        "generated_at": datetime.now().isoformat(),
        "script": "scripts/run_fpa_repair_experiment.py",
        "argv": sys.argv,
        "output_experiment": args.output_exp,
        "seed": args.seed,
        "bootstrap_reps": args.bootstrap_reps,
        "include_ngboost": bool(args.include_ngboost),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "runtime_packages": runtime_packages(),
        "git_commit": git_commit(),
        "synthetic_data_used": False,
        "target_journal": "Reliability Engineering & System Safety",
    }
    metrics_obj = {
        "target_coverage": TARGET,
        "cell_ci_floor": CELL_CI_FLOOR,
        "selection_rule": "validation coverage-first width minimization; dependence-aware CIs are reported for inference but not used to tune q",
        "tasks": tasks_out,
        "main_split_design": main_split_design(df, splits, args.seed),
        "contribution_positioning": contribution_verdict(tasks_out),
        "failure_list": failure_list(tasks_out),
        "split_manifest": split_manifest,
        "run_manifest": run_manifest,
    }
    if args.output_exp == "exp007_fpa_round2_repair":
        metrics_obj["legacy_manifest_paths"] = legacy_manifests(exp_dir, args.seed)

    write_json(exp_dir / "results" / "metrics.json", metrics_obj)
    write_json(exp_dir / "results" / "run_manifest.json", run_manifest)
    write_json(exp_dir / "results" / "split_manifest.json", split_manifest)
    write_report(exp_dir, args.output_exp, metrics_obj)
    print(json.dumps({"status": "ok", "metrics": str(exp_dir / "results" / "metrics.json")}, indent=2))


if __name__ == "__main__":
    main()
