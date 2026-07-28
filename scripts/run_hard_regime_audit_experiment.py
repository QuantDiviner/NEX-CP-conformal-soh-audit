#!/usr/bin/env python3
"""Run hard-regime reliability/safety audit without recent SOH labels."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

import run_fpa_repair_experiment as base
import run_reliability_audit_experiment as rel


ROOT = Path(__file__).resolve().parents[1]
OUT_EXP = "exp010_hard_regime_audit"
Q_GRID = (0.90, 0.93, 0.95, 0.97, 0.99, 1.00)
THRESHOLDS = (0.90, 0.85, 0.80, 0.75, 0.70, 0.65)
COST_RATIOS = (1, 2, 5, 10, 20)
FALSE_SAFE_TOLERANCE = 0.05
NO_RECENT_LABEL_DROP = {"prev_soh", "prev_soh_missing"}
COMMON_HARD_SCHEMA = ["cycle_index", "log_cycle_index"]


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def hard_feature_columns(df: pd.DataFrame, *, cross_domain: bool = False) -> list[str]:
    cols = base.cross_domain_feature_columns(df) if cross_domain else base.feature_columns(df)
    return [c for c in cols if c not in NO_RECENT_LABEL_DROP and c != "target_soh"]


def prepare_horizon_frame(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    frame = df.copy()
    frame["source_row_id"] = frame.index.astype(int)
    frame = frame.sort_values(["cell_id", "cycle_index", "source_row_id"])
    if horizon == 0:
        frame["target_soh"] = frame["soh"]
        frame["target_cycle_index"] = frame["cycle_index"]
    else:
        frame["target_soh"] = frame.groupby("cell_id")["soh"].shift(-horizon)
        frame["target_cycle_index"] = frame.groupby("cell_id")["cycle_index"].shift(-horizon)
    frame = frame.dropna(subset=["target_soh"]).copy()
    frame.index = np.arange(len(frame))
    return frame


def by_source_split(frame: pd.DataFrame, split_ids: list[int]) -> np.ndarray:
    ids = set(int(v) for v in split_ids)
    return frame.index[frame["source_row_id"].astype(int).isin(ids)].to_numpy()


def build_hard_tasks(frame: pd.DataFrame, splits: dict[str, list[int]]) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]]:
    train_idx = by_source_split(frame, splits["train"])
    cal_idx = by_source_split(frame, splits["cal"])
    val_idx = by_source_split(frame, splits["val"])
    test_idx = by_source_split(frame, splits["test"])
    tasks = {
        "main_heldout": (train_idx, cal_idx, val_idx, test_idx, hard_feature_columns(frame)),
    }
    for domain in sorted(frame["domain"].unique()):
        source = frame["domain"].ne(domain)
        target = frame["domain"].eq(domain)
        tasks[f"leave_{domain}_out"] = (
            train_idx[source.loc[train_idx].to_numpy()],
            cal_idx[source.loc[cal_idx].to_numpy()],
            val_idx[source.loc[val_idx].to_numpy()],
            frame.index[target].to_numpy(),
            hard_feature_columns(frame, cross_domain=True),
        )
        tr_idx, ca_idx, va_idx, te_idx = base.target_recalibrated_indices(frame, domain)
        tasks[f"target_recalibrated_{domain}"] = (
            tr_idx,
            ca_idx,
            va_idx,
            te_idx,
            hard_feature_columns(frame, cross_domain=True),
        )
    return tasks


def conformal_interval_from_model(
    train: pd.DataFrame,
    cal: pd.DataFrame,
    test: pd.DataFrame,
    fcols: list[str],
    seed: int,
    *,
    method: str,
) -> dict:
    y_train = train["target_soh"].to_numpy()
    y_cal = cal["target_soh"].to_numpy()
    y_test = test["target_soh"].to_numpy()
    lower_model, upper_model, center_model = base.fit_gb_quantiles(train[fcols], y_train, seed)
    center = center_model.predict(test[fcols])
    if method == "qr_gradient_boosting":
        lower = lower_model.predict(test[fcols])
        upper = upper_model.predict(test[fcols])
        return {"frame": test, "y": y_test, "lower": np.minimum(lower, upper), "upper": np.maximum(lower, upper), "center": center}
    cal_lower = lower_model.predict(cal[fcols])
    cal_upper = upper_model.predict(cal[fcols])
    cal_low = np.minimum(cal_lower, cal_upper)
    cal_high = np.maximum(cal_lower, cal_upper)
    scores = np.maximum.reduce([cal_low - y_cal, y_cal - cal_high, np.zeros_like(y_cal)])
    test_lower = lower_model.predict(test[fcols])
    test_upper = upper_model.predict(test[fcols])
    low = np.minimum(test_lower, test_upper)
    high = np.maximum(test_lower, test_upper)
    if method == "cqr_gradient_boosting":
        qhat = base.conformal_q(scores, alpha=1 - base.TARGET)
        return {"frame": test, "y": y_test, "lower": low - qhat, "upper": high + qhat, "center": center, "qhat": float(qhat)}
    raise ValueError(f"unknown method: {method}")


def stage_labels(frame: pd.DataFrame) -> pd.Series:
    progress = frame["split_progress"].clip(0, 1)
    return pd.cut(progress, bins=[-0.001, 0.35, 0.70, 1.001], labels=["early", "mid", "late"]).astype(str)


def grouped_radius(cal_scores: np.ndarray, cal_groups: pd.Series, target_groups: pd.Series, q_level: float) -> np.ndarray:
    global_q = float(np.quantile(cal_scores, q_level, method="higher"))
    out = []
    cal_group_values = cal_groups.astype(str).to_numpy()
    for group in target_groups.astype(str):
        local = cal_scores[cal_group_values == group]
        out.append(float(np.quantile(local, q_level, method="higher")) if len(local) >= 20 else global_q)
    return np.asarray(out)


def stage_mondrian_cqr(train: pd.DataFrame, cal: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, fcols: list[str], seed: int) -> dict:
    y_train = train["target_soh"].to_numpy()
    y_cal = cal["target_soh"].to_numpy()
    y_val = val["target_soh"].to_numpy()
    y_test = test["target_soh"].to_numpy()
    lower_model, upper_model, center_model = base.fit_gb_quantiles(train[fcols], y_train, seed + 101)
    cal_low = np.minimum(lower_model.predict(cal[fcols]), upper_model.predict(cal[fcols]))
    cal_high = np.maximum(lower_model.predict(cal[fcols]), upper_model.predict(cal[fcols]))
    cal_scores = np.maximum.reduce([cal_low - y_cal, y_cal - cal_high, np.zeros_like(y_cal)])
    val_low = np.minimum(lower_model.predict(val[fcols]), upper_model.predict(val[fcols])) if len(val) else np.array([])
    val_high = np.maximum(lower_model.predict(val[fcols]), upper_model.predict(val[fcols])) if len(val) else np.array([])
    best_q = base.TARGET
    best_score = float("inf")
    trace = []
    for q_level in Q_GRID:
        if len(val):
            radius = grouped_radius(cal_scores, stage_labels(cal), stage_labels(val), q_level)
            center = center_model.predict(val[fcols])
            m = base.interval_metrics(val, y_val, val_low - radius, val_high + radius, center, seed, 200)
            score = base.exp001_compatible_selection_score(m)
            trace.append({
                "q_level": float(q_level),
                "validation_coverage": float(m["coverage"]),
                "validation_mean_width": float(m["mean_width"]),
                "selection_score": float(score),
            })
            if score < best_score:
                best_q, best_score = q_level, score
    test_low = np.minimum(lower_model.predict(test[fcols]), upper_model.predict(test[fcols]))
    test_high = np.maximum(lower_model.predict(test[fcols]), upper_model.predict(test[fcols]))
    radius = grouped_radius(cal_scores, stage_labels(cal), stage_labels(test), best_q)
    center = center_model.predict(test[fcols])
    return {
        "frame": test,
        "y": y_test,
        "lower": test_low - radius,
        "upper": test_high + radius,
        "center": center,
        "q_level": float(best_q),
        "q_selection_trace": trace,
        "adaptive_rule": "stage-Mondrian CQR; q selected on validation coverage-first width objective",
    }


def rate_ci_by_cell(
    frame: pd.DataFrame,
    numerator: np.ndarray,
    denominator: np.ndarray,
    seed: int,
    reps: int,
    min_denominator: int,
    alpha: float,
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
    return {
        "rate": rate,
        "ci_low": float(np.quantile(boot, alpha / 2)) if boot else rate,
        "ci_high": float(np.quantile(boot, 1 - alpha / 2)) if boot else rate,
        "denominator_n": int(np.sum(denominator)),
        "effective_cell_count": int(len(den_cells)),
        "interpretation": interpretation,
    }


def decision_utility(frame: pd.DataFrame, y: np.ndarray, lower: np.ndarray, upper: np.ndarray, seed: int, reps: int, min_denominator: int, family_n: int) -> dict:
    out = {}
    alpha = 0.05
    bonf_alpha = alpha / max(family_n, 1)
    for threshold in THRESHOLDS:
        actual_unsafe = y < threshold
        actual_safe = ~actual_unsafe
        predicted_safe = lower >= threshold
        predicted_unsafe = upper < threshold
        uncertain = ~(predicted_safe | predicted_unsafe)
        false_safe = predicted_safe & actual_unsafe
        false_alarm = predicted_unsafe & actual_safe
        fs = rate_ci_by_cell(frame, false_safe, actual_unsafe, seed, reps, min_denominator, alpha)
        fa = rate_ci_by_cell(frame, false_alarm, actual_safe, seed + 11, reps, min_denominator, alpha)
        unc = rate_ci_by_cell(frame, uncertain, np.ones(len(y), dtype=bool), seed + 23, reps, min_denominator, alpha)
        fs_bonf = rate_ci_by_cell(frame, false_safe, actual_unsafe, seed + 31, reps, min_denominator, bonf_alpha)
        fa_bonf = rate_ci_by_cell(frame, false_alarm, actual_safe, seed + 41, reps, min_denominator, bonf_alpha)
        out[f"soh_threshold_{threshold:.2f}"] = {
            "false_safe_per_actual_unsafe": {
                **fs,
                "bonferroni_ci_high": fs_bonf["ci_high"],
                "survives_false_safe_tolerance_unadjusted": bool(fs["interpretation"] == "interpretable" and fs["ci_high"] <= FALSE_SAFE_TOLERANCE),
                "survives_false_safe_tolerance_bonferroni": bool(fs["interpretation"] == "interpretable" and fs_bonf["ci_high"] <= FALSE_SAFE_TOLERANCE),
            },
            "false_alarm_per_actual_safe": {**fa, "bonferroni_ci_high": fa_bonf["ci_high"]},
            "uncertain_rate": unc,
            "predicted_safe_rate": float(np.mean(predicted_safe)),
            "predicted_unsafe_rate": float(np.mean(predicted_unsafe)),
            "multiplicity_family_n": int(family_n),
            "multiplicity_methods": ["Bonferroni simultaneous CI", "BH-style ranking summary in multiplicity_control.json"],
        }
    return out


def cost_curve(utility: dict) -> dict:
    out = {}
    for threshold_key, item in utility.items():
        fs = item["false_safe_per_actual_unsafe"]["rate"]
        fa = item["false_alarm_per_actual_safe"]["rate"]
        unc = item["uncertain_rate"]["rate"]
        out[threshold_key] = {f"false_safe_cost_ratio_{ratio}": float(ratio * fs + fa + 0.25 * unc) for ratio in COST_RATIOS}
    return out


def summarize(interval: dict, seed: int, reps: int, min_denominator: int, family_n: int) -> dict:
    frame = interval["frame"]
    y = interval["y"]
    lower = interval["lower"]
    upper = interval["upper"]
    center = interval["center"]
    covered = (y >= lower) & (y <= upper)
    utility = decision_utility(frame, y, lower, upper, seed, reps, min_denominator, family_n)
    item = {
        **base.interval_metrics(frame, y, lower, upper, center, seed, reps),
        "decision_utility_ci": utility,
        "decision_cost_curve": cost_curve(utility),
        "double_coverage": {
            "marginal_coverage": float(np.mean(covered)),
            "cell_reliability": rel.cell_reliability(frame, covered),
        },
    }
    for key in ("qhat", "q_level", "q_selection_trace", "adaptive_rule"):
        if key in interval:
            item[key] = interval[key]
    return item


def residual_shift(cal: pd.DataFrame, test: pd.DataFrame, method: dict) -> dict:
    y = method["y"]
    center = method["center"]
    test_resid = np.abs(y - center)
    cal_resid = np.abs(cal["target_soh"].to_numpy() - np.nanmedian(cal["target_soh"].to_numpy()))
    pooled = float(np.sqrt(0.5 * (np.nanvar(cal_resid) + np.nanvar(test_resid))))
    smd = 0.0 if pooled <= 1e-12 else float((np.nanmean(test_resid) - np.nanmean(cal_resid)) / pooled)
    return {
        "cal_reference": "absolute deviation from calibration median target SOH",
        "test_reference": "absolute residual of selected model center",
        "cal_abs_residual_mean": float(np.nanmean(cal_resid)),
        "test_abs_residual_mean": float(np.nanmean(test_resid)),
        "residual_smd": smd,
    }


def evaluate_task(frame: pd.DataFrame, task_name: str, indices: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]], seed: int, reps: int, min_denominator: int, family_n: int) -> dict:
    train_idx, cal_idx, val_idx, test_idx, fcols = indices
    train = frame.loc[train_idx].copy()
    cal = frame.loc[cal_idx].copy()
    val = frame.loc[val_idx].copy()
    test = frame.loc[test_idx].copy()
    if min(len(train), len(cal), len(test)) == 0:
        return {"skipped": True, "reason": "empty train/cal/test split"}
    intervals = {
        "qr_gradient_boosting_no_recent_label": conformal_interval_from_model(train, cal, test, fcols, seed, method="qr_gradient_boosting"),
        "cqr_gradient_boosting_no_recent_label": conformal_interval_from_model(train, cal, test, fcols, seed, method="cqr_gradient_boosting"),
        "stage_mondrian_cqr_no_recent_label": stage_mondrian_cqr(train, cal, val, test, fcols, seed),
    }
    methods = {name: summarize(interval, seed, reps, min_denominator, family_n) for name, interval in intervals.items()}
    selected = methods["stage_mondrian_cqr_no_recent_label"]
    selected_interval = intervals["stage_mondrian_cqr_no_recent_label"]
    common_cols = [c for c in COMMON_HARD_SCHEMA if c in frame.columns]
    return {
        "task": task_name,
        "n_train": int(len(train)),
        "n_cal": int(len(cal)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "features": fcols,
        "hard_regime": "no_recent_soh_label",
        "methods": methods,
        "selected_recovery_method": "stage_mondrian_cqr_no_recent_label",
        "usable_trust_envelope": {
            "coverage_target_met": bool(selected["coverage"] >= base.TARGET),
            "cell_ci_floor_met": bool(selected["cell_block_ci_low"] >= base.CELL_CI_FLOOR),
            "false_safe_bonferroni_any_survives": any(
                cell["false_safe_per_actual_unsafe"]["survives_false_safe_tolerance_bonferroni"]
                for cell in selected["decision_utility_ci"].values()
            ),
        },
        "shift_diagnostics": {
            "original_schema": rel.shift_diagnostics(cal, test, fcols),
            "common_hard_schema": rel.shift_diagnostics(cal, test, common_cols),
            "residual_shift": residual_shift(cal, test, selected_interval),
        },
    }


def multiplicity_summary(tasks: dict) -> dict:
    rows = []
    for horizon_name, horizon in tasks.items():
        for task_name, task in horizon["tasks"].items():
            if task.get("skipped"):
                continue
            for method_name, method in task["methods"].items():
                for threshold_key, utility in method["decision_utility_ci"].items():
                    fs = utility["false_safe_per_actual_unsafe"]
                    rows.append({
                        "horizon": horizon_name,
                        "task": task_name,
                        "method": method_name,
                        "threshold": threshold_key,
                        "rate": fs["rate"],
                        "ci_high": fs["ci_high"],
                        "bonferroni_ci_high": fs["bonferroni_ci_high"],
                        "interpretation": fs["interpretation"],
                        "survives_bonferroni": fs["survives_false_safe_tolerance_bonferroni"],
                    })
    ranked = sorted(rows, key=lambda row: row["ci_high"])
    for rank, row in enumerate(ranked, start=1):
        row["bh_rank"] = rank
        row["bh_style_pass"] = bool(row["interpretation"] == "interpretable" and row["ci_high"] <= FALSE_SAFE_TOLERANCE * rank / max(len(ranked), 1))
    return {
        "family_n": len(rows),
        "false_safe_tolerance": FALSE_SAFE_TOLERANCE,
        "bonferroni_survivors": [row for row in rows if row["survives_bonferroni"]],
        "bh_style_survivors": [row for row in ranked if row["bh_style_pass"]],
        "all_false_safe_tests": rows,
    }


def write_report(exp_dir: Path, metrics: dict) -> None:
    lines = [
        "# exp010_hard_regime_audit Report",
        "",
        "**Status**: pending_review",
        "",
        "## Results Summary",
        "",
        "This experiment audits SOH interval reliability without using a recent SOH label.",
        "It includes current-cycle no-label estimation and 5/20-cycle-ahead targets.",
        "",
        "| Horizon | Task | Selected method | Coverage | Cell CI low | Width | Usable envelope? |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for horizon_name, horizon in metrics["horizons"].items():
        for task_name, task in horizon["tasks"].items():
            if task.get("skipped"):
                lines.append(f"| {horizon_name} | {task_name} | skipped | skipped | skipped | skipped | no |")
                continue
            method_name = task["selected_recovery_method"]
            method = task["methods"][method_name]
            usable = task["usable_trust_envelope"]
            ok = usable["coverage_target_met"] and usable["cell_ci_floor_met"]
            lines.append(
                f"| {horizon_name} | {task_name} | {method_name} | {method['coverage']:.4f} | "
                f"{method['cell_block_ci_low']:.4f} | {method['mean_width']:.4f} | {'yes' if ok else 'no'} |"
            )
    lines.extend([
        "",
        "## Multiplicity",
        "",
        f"False-safe family size: {metrics['multiplicity_control']['family_n']}.",
        f"Bonferroni survivors: {len(metrics['multiplicity_control']['bonferroni_survivors'])}.",
        f"BH-style survivors: {len(metrics['multiplicity_control']['bh_style_survivors'])}.",
        "",
        "## External Dataset Status",
        "",
        metrics["external_dataset_status"]["status"],
        "",
        "Synthetic data was not used.",
    ])
    (exp_dir / "report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-exp", default=OUT_EXP)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    parser.add_argument("--min-decision-denominator", type=int, default=5)
    parser.add_argument("--horizons", default="0,5,20")
    args = parser.parse_args()

    df = pd.read_csv(base.PROCESSED)
    splits = base.read_json(base.SPLITS)
    horizons = [int(item.strip()) for item in args.horizons.split(",") if item.strip()]
    exp_dir = ROOT / "experiments" / args.output_exp
    family_n = len(horizons) * 7 * 3 * len(THRESHOLDS) * 2

    horizon_out = {}
    for horizon in horizons:
        frame = prepare_horizon_frame(df, horizon)
        tasks = build_hard_tasks(frame, splits)
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
        horizon_out[f"horizon_{horizon}"] = {
            "horizon_cycles": horizon,
            "n_rows": int(len(frame)),
            "tasks": task_out,
        }

    run_manifest = {
        "generated_at": datetime.now().isoformat(),
        "script": "scripts/run_hard_regime_audit_experiment.py",
        "argv": sys.argv,
        "experiment_id": args.output_exp,
        "seed": args.seed,
        "bootstrap_reps": args.bootstrap_reps,
        "min_decision_denominator": args.min_decision_denominator,
        "horizons": horizons,
        "thresholds": list(THRESHOLDS),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "runtime_packages": base.runtime_packages(),
        "git_commit": base.git_commit(),
        "synthetic_data_used": False,
        "target_journal": "Reliability Engineering & System Safety",
        "deterministic_regeneration_command": (
            "python scripts/run_hard_regime_audit_experiment.py "
            f"--output-exp {args.output_exp} --seed {args.seed} "
            f"--bootstrap-reps {args.bootstrap_reps} "
            f"--min-decision-denominator {args.min_decision_denominator} "
            f"--horizons {args.horizons}"
        ),
        "fpa_revision_plan": "docs/reports/20260530_215915_fpa_revision_20260530_215247_revision_plan.md",
    }
    metrics = {
        "target_coverage": base.TARGET,
        "cell_ci_floor": base.CELL_CI_FLOOR,
        "hard_regime_policy": "No method may use prev_soh or prev_soh_missing as a feature.",
        "feature_drop": sorted(NO_RECENT_LABEL_DROP),
        "thresholds": list(THRESHOLDS),
        "horizons": horizon_out,
        "multiplicity_control": None,
        "external_dataset_status": {
            "status": "No additional QA-compatible modern battery dataset is available under data/raw in the current local evidence base; this run records the conditional external-validity gap rather than fabricating or synthesizing data.",
            "data_raw_entries": sorted(str(path.relative_to(ROOT)) for path in (ROOT / "data" / "raw").glob("*")),
        },
        "split_manifest": {
            "processed_data": str(base.PROCESSED.relative_to(ROOT)),
            "processed_data_sha256": base.sha256(base.PROCESSED),
            "split_manifest": str(base.SPLITS.relative_to(ROOT)),
            "split_manifest_sha256": base.sha256(base.SPLITS),
            "split_counts": {k: len(v) for k, v in splits.items()},
        },
        "run_manifest": run_manifest,
    }
    metrics["multiplicity_control"] = multiplicity_summary(horizon_out)

    write_json(exp_dir / "results" / "metrics.json", metrics)
    write_json(exp_dir / "results" / "multiplicity_control.json", metrics["multiplicity_control"])
    write_json(exp_dir / "results" / "run_manifest.json", run_manifest)
    write_json(exp_dir / "results" / "split_manifest.json", metrics["split_manifest"])
    write_report(exp_dir, metrics)
    print(json.dumps({"status": "ok", "metrics": str(exp_dir / "results" / "metrics.json")}, indent=2))


if __name__ == "__main__":
    main()
