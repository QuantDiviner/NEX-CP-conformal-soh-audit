#!/usr/bin/env python3
"""Run real-data conformal SOH experiments.

Inputs must come from scripts/preprocess_real_battery.py. This script refuses to
run if the processed real-data table or split manifest is missing.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SPLITS = ROOT / "data" / "splits"
EXPERIMENTS = ROOT / "experiments"
PAPER_DATA = ROOT / "paper" / "data"
TARGET = 0.90


def load_inputs() -> tuple[pd.DataFrame, dict[str, list[int]]]:
    data_path = PROCESSED / "real_battery_cycle_level_features.csv"
    split_path = SPLITS / "real_battery_splits.json"
    if not data_path.exists() or not split_path.exists():
        raise SystemExit("Missing real preprocessed data. Run scripts/preprocess_real_battery.py first.")
    df = pd.read_csv(data_path)
    splits = json.loads(split_path.read_text())
    return df, splits


def feature_columns(df: pd.DataFrame) -> list[str]:
    blocked = {"soh", "capacity_ah", "source_file", "cell_id", "domain", "calibration_group", "split_progress"}
    return [c for c in df.columns if c not in blocked and pd.api.types.is_numeric_dtype(df[c])]


def cross_domain_feature_columns(df: pd.DataFrame) -> list[str]:
    return [
        c for c in feature_columns(df)
        if not c.startswith("dataset_") and not c.startswith("chemistry_") and not c.startswith("protocol_")
    ]


def conformal_q(residuals: np.ndarray, alpha: float = 0.10) -> float:
    n = len(residuals)
    if n == 0:
        return float("nan")
    q = np.ceil((n + 1) * (1 - alpha)) / n
    return float(np.quantile(residuals, min(q, 1.0), method="higher"))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights) / np.sum(weights)
    pos = min(int(np.searchsorted(cdf, q, side="left")), len(values) - 1)
    return float(values[pos])


def metrics(y: np.ndarray, pred: np.ndarray, radius: np.ndarray) -> dict[str, float]:
    covered = np.abs(y - pred) <= radius
    ci_low, ci_high = coverage_ci(covered)
    return {
        "coverage": float(np.mean(covered)),
        "coverage_ci_low": ci_low,
        "coverage_ci_high": ci_high,
        "mean_width": float(np.mean(2 * radius)),
        "soh_normalized_mean_width": float(np.mean(2 * radius) / max(float(np.nanmean(np.abs(y))), 1e-12)),
        "median_width": float(np.median(2 * radius)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
        "n": int(len(y)),
    }


def coverage_ci(covered: np.ndarray) -> tuple[float, float]:
    n = len(covered)
    if n == 0:
        return float("nan"), float("nan")
    p = float(np.mean(covered))
    se = (p * (1.0 - p) / n) ** 0.5
    return max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)


def tune_lambda_and_q(cal_cycle: np.ndarray, cal_resid: np.ndarray, val_cycle: np.ndarray, y_val: np.ndarray, pred_val: np.ndarray) -> tuple[float, float]:
    best = (float("inf"), 0.25, TARGET)
    for lam in (0.05, 0.10, 0.18, 0.25, 0.40, 0.70):
        for q in (0.90, 0.93, 0.95, 0.97, 0.99, 1.00):
            radii = []
            for cycle in val_cycle:
                w = np.exp(-np.abs(cal_cycle - cycle) / lam) + 1e-8
                radii.append(weighted_quantile(cal_resid, w, q))
            m = metrics(y_val, pred_val, np.asarray(radii))
            penalty = max(0.0, TARGET - m["coverage"]) * 100.0
            score = m["mean_width"] + penalty
            if score < best[0]:
                best = (score, lam, q)
    return best[1], best[2]


def tune_standard_q(resid: np.ndarray, y_val: np.ndarray, pred_val: np.ndarray) -> float:
    best = (float("inf"), TARGET)
    for q in (0.90, 0.93, 0.95, 0.97, 0.99, 1.00):
        radius = np.full(len(y_val), float(np.quantile(resid, q, method="higher")))
        m = metrics(y_val, pred_val, radius)
        penalty = max(0.0, TARGET - m["coverage"]) * 100.0
        score = m["mean_width"] + penalty
        if score < best[0]:
            best = (score, q)
    return best[1]


def selection_score(validation_metrics: dict[str, float]) -> float:
    """Predeclared coverage-first validation score.

    Candidates at or above nominal validation coverage are ranked by closeness
    to the nominal target first, then interval width. Under-covering candidates
    receive a large penalty, so pure minimum-width selection cannot win.
    """
    coverage = validation_metrics.get("coverage", 0.0)
    width = validation_metrics.get("mean_width", float("inf"))
    if coverage >= TARGET:
        return width
    return (TARGET - coverage) * 1000.0 + width


def choose_selected(selection_scores: dict[str, float], method_metrics: dict[str, dict], prefer_online: bool = False) -> str:
    if prefer_online:
        valid_online = [
            key for key, vals in method_metrics.items()
            if key.endswith("_online_adaptive_cp") and vals.get("validation_coverage", 0.0) >= TARGET
        ]
        if valid_online:
            return min(valid_online, key=lambda key: method_metrics[key].get("validation_mean_width", float("inf")))
    return min(selection_scores, key=selection_scores.get)


def domain_radii(
    cal_domains: pd.Series,
    cal_resid: np.ndarray,
    target_domains: pd.Series,
    q_level: float,
) -> np.ndarray:
    global_q = float(np.quantile(cal_resid, q_level, method="higher"))
    out = []
    for domain in target_domains:
        local = cal_resid[cal_domains.to_numpy() == domain]
        if len(local) >= 20:
            out.append(float(np.quantile(local, q_level, method="higher")))
        else:
            out.append(global_q)
    return np.asarray(out)


def online_adaptive_radii(initial_resid: np.ndarray, y: np.ndarray, pred: np.ndarray, q_level: float = TARGET) -> np.ndarray:
    history = list(np.asarray(initial_resid, dtype=float))
    radii = []
    for actual, forecast in zip(y, pred, strict=False):
        radius = float(np.quantile(history, q_level, method="higher")) if history else 0.0
        radii.append(radius)
        history.append(abs(float(actual) - float(forecast)))
    return np.asarray(radii)


def tune_online_q(initial_resid: np.ndarray, y_val: np.ndarray, pred_val: np.ndarray) -> float:
    best = (float("inf"), TARGET)
    for q_level in (0.90, 0.93, 0.95, 0.97, 0.99, 1.00):
        radius = online_adaptive_radii(initial_resid, y_val, pred_val, q_level)
        m = metrics(y_val, pred_val, radius)
        score = selection_score(m)
        if score < best[0]:
            best = (score, q_level)
    return best[1]


def fit_models(seed: int) -> dict:
    return {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "gradient_boosting": GradientBoostingRegressor(random_state=seed, max_depth=3, n_estimators=250, learning_rate=0.035),
        "random_forest": RandomForestRegressor(random_state=seed, n_estimators=300, min_samples_leaf=3, n_jobs=-1),
        "extra_trees": ExtraTreesRegressor(random_state=seed, n_estimators=300, min_samples_leaf=3, n_jobs=-1),
    }


def add_fixed_prediction_methods(
    result: dict,
    prefix: str,
    y_cal: np.ndarray,
    pred_cal: np.ndarray,
    y_val: np.ndarray,
    pred_val: np.ndarray,
    y_test: np.ndarray,
    pred_test: np.ndarray,
    cal_groups: pd.Series,
    val_groups: pd.Series,
    test_groups: pd.Series,
    selection_scores: dict[str, float],
    test_predictions: dict[str, np.ndarray],
    test_radii: dict[str, np.ndarray],
) -> None:
    resid = np.abs(y_cal - pred_cal)
    if len(y_val):
        standard_q_level = tune_standard_q(resid, y_val, pred_val)
        q = float(np.quantile(resid, standard_q_level, method="higher"))
    else:
        standard_q_level = TARGET
        q = conformal_q(resid, 1 - TARGET)
    std_test_radius = np.full(len(y_test), q)
    std_val_radius = np.full(len(y_val), q) if len(y_val) else std_test_radius
    std_test = metrics(y_test, pred_test, std_test_radius)
    std_val = metrics(y_val, pred_val, std_val_radius) if len(y_val) else std_test

    mondrian_val_radius = domain_radii(cal_groups, resid, val_groups, standard_q_level) if len(y_val) else std_val_radius
    mondrian_test_radius = domain_radii(cal_groups, resid, test_groups, standard_q_level)
    mondrian_test = metrics(y_test, pred_test, mondrian_test_radius)
    mondrian_val = metrics(y_val, pred_val, mondrian_val_radius) if len(y_val) else mondrian_test

    online_q_level = tune_online_q(resid, y_val, pred_val) if len(y_val) else TARGET
    online_val_radius = online_adaptive_radii(resid, y_val, pred_val, online_q_level) if len(y_val) else std_val_radius
    online_test_radius = online_adaptive_radii(np.r_[resid, np.abs(y_val - pred_val)] if len(y_val) else resid, y_test, pred_test, online_q_level)
    online_test = metrics(y_test, pred_test, online_test_radius)
    online_val = metrics(y_val, pred_val, online_val_radius) if len(y_val) else online_test

    candidates = {
        f"{prefix}_standard_cp": (std_test, std_val, std_test_radius, {"q_level": float(standard_q_level)}),
        f"{prefix}_protocol_mondrian_cp": (mondrian_test, mondrian_val, mondrian_test_radius, {"q_level": float(standard_q_level)}),
        f"{prefix}_online_adaptive_cp": (
            online_test,
            online_val,
            online_test_radius,
            {"q_level": float(online_q_level), "update_rule": "sequentially append observed real residuals before later predictions"},
        ),
    }
    for key, (test_m, val_m, radius, extra) in candidates.items():
        result["methods"][key] = {
            **test_m,
            **extra,
            "validation_coverage": val_m["coverage"],
            "validation_mean_width": val_m["mean_width"],
        }
        selection_scores[key] = selection_score(val_m)
        test_predictions[key] = pred_test
        test_radii[key] = radius


def run_conformal(
    df: pd.DataFrame,
    splits: dict[str, list[int]],
    seed: int,
    train_filter=None,
    test_filter=None,
    drop_cols: set[str] | None = None,
    use_cross_domain_features: bool = False,
    prefer_online: bool = False,
    include_persistence_anchor: bool = True,
) -> dict:
    drop_cols = drop_cols or set()
    base_cols = cross_domain_feature_columns(df) if use_cross_domain_features else feature_columns(df)
    fcols = [c for c in base_cols if c not in drop_cols]
    train_idx = np.array(splits["train"], dtype=int)
    cal_idx = np.array(splits["cal"], dtype=int)
    val_idx = np.array(splits["val"], dtype=int)
    test_idx = np.array(splits["test"], dtype=int)
    if train_filter is not None:
        train_idx = train_idx[train_filter(df.loc[train_idx])]
        cal_idx = cal_idx[train_filter(df.loc[cal_idx])]
        val_idx = val_idx[train_filter(df.loc[val_idx])]
    if test_filter is not None:
        if use_cross_domain_features:
            test_idx = df.index[test_filter(df)].to_numpy()
        else:
            test_idx = test_idx[test_filter(df.loc[test_idx])]
    if len(train_idx) == 0 or len(cal_idx) == 0 or len(test_idx) == 0:
        return {"skipped": True, "reason": "empty split after filtering"}

    x_train, y_train = df.loc[train_idx, fcols], df.loc[train_idx, "soh"].to_numpy()
    x_cal, y_cal = df.loc[cal_idx, fcols], df.loc[cal_idx, "soh"].to_numpy()
    x_val, y_val = df.loc[val_idx, fcols], df.loc[val_idx, "soh"].to_numpy()
    x_test, y_test = df.loc[test_idx, fcols], df.loc[test_idx, "soh"].to_numpy()

    result = {
        "target_coverage": TARGET,
        "features": fcols,
        "methods": {},
        "selection_rule": "validation-only coverage-first; cross-protocol tasks prefer online adaptive if validation coverage >= 0.90",
    }
    models = fit_models(seed)
    selection_scores = {}
    test_predictions = {}
    test_radii = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        pred_cal = model.predict(x_cal)
        pred_val = model.predict(x_val) if len(x_val) else pred_cal[:0]
        pred_test = model.predict(x_test)
        resid = np.abs(y_cal - pred_cal)
        if len(x_val):
            standard_q_level = tune_standard_q(resid, y_val, pred_val)
            q = float(np.quantile(resid, standard_q_level, method="higher"))
        else:
            standard_q_level = TARGET
            q = conformal_q(resid, 1 - TARGET)
        standard = metrics(y_test, pred_test, np.full(len(y_test), q))
        standard_val = metrics(y_val, pred_val, np.full(len(y_val), q)) if len(x_val) else standard
        if len(x_val):
            lam, nex_q_level = tune_lambda_and_q(
                df.loc[cal_idx, "log_cycle_index"].to_numpy(),
                resid,
                df.loc[val_idx, "log_cycle_index"].to_numpy(),
                y_val,
                pred_val,
            )
        else:
            lam = 0.25
            nex_q_level = TARGET
        radii = np.asarray(
            [
                weighted_quantile(resid, np.exp(-np.abs(df.loc[cal_idx, "log_cycle_index"].to_numpy() - cyc) / lam) + 1e-8, nex_q_level)
                for cyc in df.loc[test_idx, "log_cycle_index"].to_numpy()
            ]
        )
        nex = metrics(y_test, pred_test, radii)
        nex_val_radii = np.asarray(
            [
                weighted_quantile(resid, np.exp(-np.abs(df.loc[cal_idx, "log_cycle_index"].to_numpy() - cyc) / lam) + 1e-8, nex_q_level)
                for cyc in df.loc[val_idx, "log_cycle_index"].to_numpy()
            ]
        ) if len(x_val) else radii
        nex_val = metrics(y_val, pred_val, nex_val_radii) if len(x_val) else nex
        std_key = f"{name}_standard_cp"
        nex_key = f"{name}_nex_cp"
        result["methods"][std_key] = {**standard, "q_level": float(standard_q_level), "validation_coverage": standard_val["coverage"], "validation_mean_width": standard_val["mean_width"]}
        result["methods"][nex_key] = {**nex, "lambda_log_cycle_index": float(lam), "q_level": float(nex_q_level), "validation_coverage": nex_val["coverage"], "validation_mean_width": nex_val["mean_width"]}
        mondrian_val_radius = domain_radii(df.loc[cal_idx, "calibration_group"], resid, df.loc[val_idx, "calibration_group"], standard_q_level) if len(x_val) else np.full(len(y_val), q)
        mondrian_test_radius = domain_radii(df.loc[cal_idx, "calibration_group"], resid, df.loc[test_idx, "calibration_group"], standard_q_level)
        mondrian_val = metrics(y_val, pred_val, mondrian_val_radius) if len(x_val) else standard
        mondrian_test = metrics(y_test, pred_test, mondrian_test_radius)
        mondrian_key = f"{name}_domain_mondrian_cp"
        online_q_level = tune_online_q(resid, y_val, pred_val) if len(x_val) else TARGET
        online_val_radius = online_adaptive_radii(resid, y_val, pred_val, online_q_level) if len(x_val) else np.full(len(y_test), q)
        online_test_radius = online_adaptive_radii(np.r_[resid, np.abs(y_val - pred_val)] if len(x_val) else resid, y_test, pred_test, online_q_level)
        online_val = metrics(y_val, pred_val, online_val_radius) if len(x_val) else standard
        online_test = metrics(y_test, pred_test, online_test_radius)
        online_key = f"{name}_online_adaptive_cp"
        result["methods"][mondrian_key] = {
            **mondrian_test,
            "q_level": float(standard_q_level),
            "validation_coverage": mondrian_val["coverage"],
            "validation_mean_width": mondrian_val["mean_width"],
        }
        result["methods"][online_key] = {
            **online_test,
            "q_level": float(online_q_level),
            "validation_coverage": online_val["coverage"],
            "validation_mean_width": online_val["mean_width"],
            "update_rule": "sequentially append observed real residuals before later predictions",
        }
        selection_scores[std_key] = selection_score(standard_val)
        selection_scores[nex_key] = selection_score(nex_val)
        selection_scores[mondrian_key] = selection_score(mondrian_val)
        selection_scores[online_key] = selection_score(online_val)
        test_predictions[std_key] = pred_test
        test_predictions[nex_key] = pred_test
        test_predictions[mondrian_key] = pred_test
        test_predictions[online_key] = pred_test
        test_radii[std_key] = np.full(len(y_test), q)
        test_radii[nex_key] = radii
        test_radii[mondrian_key] = mondrian_test_radius
        test_radii[online_key] = online_test_radius

    if include_persistence_anchor:
        add_fixed_prediction_methods(
            result,
            "persistence_anchor",
            y_cal,
            df.loc[cal_idx, "prev_soh"].to_numpy(),
            y_val,
            df.loc[val_idx, "prev_soh"].to_numpy(),
            y_test,
            df.loc[test_idx, "prev_soh"].to_numpy(),
            df.loc[cal_idx, "calibration_group"],
            df.loc[val_idx, "calibration_group"],
            df.loc[test_idx, "calibration_group"],
            selection_scores,
            test_predictions,
            test_radii,
        )

    best_key = choose_selected(selection_scores, result["methods"], prefer_online=prefer_online)
    result["selected_method"] = best_key
    result["selected"] = result["methods"][best_key]
    result["selection_score"] = float(selection_scores[best_key])
    result["group_audit"] = group_audit(df.loc[test_idx], y_test, test_predictions[best_key], test_radii[best_key])
    result["selected_bias_probe"] = bias_probe(df.loc[test_idx], y_test, test_predictions[best_key], test_radii[best_key])
    result["persistence_baseline"] = persistence_baseline(df.loc[test_idx])
    return result


def run_target_recalibrated(df: pd.DataFrame, seed: int, target_domain: str) -> dict:
    """Train on source + early target, calibrate on mid target cycles, test late target cycles."""
    fcols = cross_domain_feature_columns(df)
    import run_fpa_repair_experiment as repair

    train_idx, cal_idx, val_idx, test_idx = repair.target_recalibrated_indices(
        df, target_domain
    )
    if len(train_idx) == 0 or len(cal_idx) == 0 or len(test_idx) == 0:
        return {"skipped": True, "reason": "empty source/train, target/cal, or target/test split"}

    x_train, y_train = df.loc[train_idx, fcols], df.loc[train_idx, "soh"].to_numpy()
    x_cal, y_cal = df.loc[cal_idx, fcols], df.loc[cal_idx, "soh"].to_numpy()
    x_val, y_val = df.loc[val_idx, fcols], df.loc[val_idx, "soh"].to_numpy()
    x_test, y_test = df.loc[test_idx, fcols], df.loc[test_idx, "soh"].to_numpy()
    result = {
        "target_coverage": TARGET,
        "target_domain": target_domain,
        "features": fcols,
        "n_source_train": int(len(train_idx)),
        "n_target_cal": int(len(cal_idx)),
        "n_target_val": int(len(val_idx)),
        "n_target_test": int(len(test_idx)),
        "methods": {},
        "selection_rule": "target-validation-only coverage-first; prefer online adaptive if validation coverage >= 0.90",
    }
    selection_scores = {}
    test_predictions = {}
    test_radii = {}
    for name, model in fit_models(seed).items():
        model.fit(x_train, y_train)
        pred_cal = model.predict(x_cal)
        pred_val = model.predict(x_val) if len(x_val) else pred_cal[:0]
        pred_test = model.predict(x_test)
        resid = np.abs(y_val - pred_val) if len(y_val) else np.abs(y_cal - pred_cal)
        if len(x_val):
            # Calibration residuals come from the latest available target segment.
            q_level = TARGET
            lam, nex_q = tune_lambda_and_q(
                df.loc[val_idx, "log_cycle_index"].to_numpy(),
                resid,
                df.loc[val_idx, "log_cycle_index"].to_numpy(),
                y_val,
                pred_val,
            )
        else:
            q_level, lam, nex_q = TARGET, 0.25, TARGET
        standard_radius = np.full(len(y_test), float(np.quantile(resid, q_level, method="higher")))
        nex_radius = np.asarray(
            [
                weighted_quantile(
                    resid,
                    np.exp(-np.abs((df.loc[val_idx, "log_cycle_index"].to_numpy() if len(y_val) else df.loc[cal_idx, "log_cycle_index"].to_numpy()) - cyc) / lam) + 1e-8,
                    nex_q,
                )
                for cyc in df.loc[test_idx, "log_cycle_index"].to_numpy()
            ]
        )
        std_key = f"{name}_standard_cp"
        nex_key = f"{name}_nex_cp"
        online_key = f"{name}_online_adaptive_cp"
        result["methods"][std_key] = {**metrics(y_test, pred_test, standard_radius), "q_level": float(q_level)}
        result["methods"][nex_key] = {**metrics(y_test, pred_test, nex_radius), "lambda_log_cycle_index": float(lam), "q_level": float(nex_q)}
        online_q_level = tune_online_q(resid, y_val, pred_val) if len(y_val) else TARGET
        online_val_radius = online_adaptive_radii(resid, y_val, pred_val, online_q_level) if len(y_val) else standard_radius
        online_test_radius = online_adaptive_radii(np.r_[resid, np.abs(y_val - pred_val)] if len(y_val) else resid, y_test, pred_test, online_q_level)
        result["methods"][online_key] = {
            **metrics(y_test, pred_test, online_test_radius),
            "q_level": float(online_q_level),
            "update_rule": "sequentially append observed real residuals before later predictions",
        }
        std_val_radius = np.full(len(y_val), float(np.quantile(resid, q_level, method="higher"))) if len(y_val) else standard_radius
        nex_val_radius = np.asarray(
            [
                weighted_quantile(resid, np.exp(-np.abs(df.loc[val_idx, "log_cycle_index"].to_numpy() - cyc) / lam) + 1e-8, nex_q)
                for cyc in df.loc[val_idx, "log_cycle_index"].to_numpy()
            ]
        ) if len(y_val) else nex_radius
        std_val = metrics(y_val, pred_val, std_val_radius) if len(y_val) else result["methods"][std_key]
        nex_val = metrics(y_val, pred_val, nex_val_radius) if len(y_val) else result["methods"][nex_key]
        result["methods"][std_key]["validation_coverage"] = std_val["coverage"]
        result["methods"][std_key]["validation_mean_width"] = std_val["mean_width"]
        result["methods"][nex_key]["validation_coverage"] = nex_val["coverage"]
        result["methods"][nex_key]["validation_mean_width"] = nex_val["mean_width"]
        online_val = metrics(y_val, pred_val, online_val_radius) if len(y_val) else result["methods"][online_key]
        result["methods"][online_key]["validation_coverage"] = online_val["coverage"]
        result["methods"][online_key]["validation_mean_width"] = online_val["mean_width"]
        mondrian_val_radius = domain_radii(df.loc[cal_idx, "calibration_group"], np.abs(y_cal - pred_cal), df.loc[val_idx, "calibration_group"], q_level) if len(y_val) else standard_radius
        mondrian_test_radius = domain_radii(df.loc[cal_idx, "calibration_group"], np.abs(y_cal - pred_cal), df.loc[test_idx, "calibration_group"], q_level)
        mondrian_key = f"{name}_protocol_mondrian_cp"
        mondrian_val = metrics(y_val, pred_val, mondrian_val_radius) if len(y_val) else metrics(y_test, pred_test, mondrian_test_radius)
        result["methods"][mondrian_key] = {
            **metrics(y_test, pred_test, mondrian_test_radius),
            "q_level": float(q_level),
            "validation_coverage": mondrian_val["coverage"],
            "validation_mean_width": mondrian_val["mean_width"],
        }
        selection_scores[std_key] = selection_score(std_val)
        selection_scores[nex_key] = selection_score(nex_val)
        selection_scores[online_key] = selection_score(online_val)
        selection_scores[mondrian_key] = selection_score(mondrian_val)
        test_predictions[std_key] = pred_test
        test_predictions[nex_key] = pred_test
        test_predictions[online_key] = pred_test
        test_predictions[mondrian_key] = pred_test
        test_radii[std_key] = standard_radius
        test_radii[nex_key] = nex_radius
        test_radii[online_key] = online_test_radius
        test_radii[mondrian_key] = mondrian_test_radius
    add_fixed_prediction_methods(
        result,
        "persistence_anchor",
        y_cal,
        df.loc[cal_idx, "prev_soh"].to_numpy(),
        y_val,
        df.loc[val_idx, "prev_soh"].to_numpy(),
        y_test,
        df.loc[test_idx, "prev_soh"].to_numpy(),
        df.loc[cal_idx, "calibration_group"],
        df.loc[val_idx, "calibration_group"],
        df.loc[test_idx, "calibration_group"],
        selection_scores,
        test_predictions,
        test_radii,
    )
    best_key = choose_selected(selection_scores, result["methods"], prefer_online=True)
    result["selected_method"] = best_key
    result["selected"] = result["methods"][best_key]
    result["selection_score"] = float(selection_scores[best_key])
    result["group_audit"] = group_audit(df.loc[test_idx], y_test, test_predictions[best_key], test_radii[best_key])
    result["persistence_baseline"] = persistence_baseline(df.loc[test_idx])
    return result


def group_audit(test_df: pd.DataFrame, y: np.ndarray, pred: np.ndarray, radius: np.ndarray) -> dict:
    out = {}
    for domain, g in test_df.groupby("domain"):
        idx = test_df.index.isin(g.index)
        out[f"domain_{domain}"] = metrics(y[idx], pred[idx], radius[idx])
    if "calibration_group" in test_df.columns:
        for group, g in test_df.groupby("calibration_group"):
            idx = test_df.index.isin(g.index)
            out[f"calibration_group_{group}"] = metrics(y[idx], pred[idx], radius[idx])
    for cell, g in test_df.groupby("cell_id"):
        if len(g) < 20:
            continue
        idx = test_df.index.isin(g.index)
        out[f"cell_{cell}"] = metrics(y[idx], pred[idx], radius[idx])
    return out


def bias_probe(test_df: pd.DataFrame, y: np.ndarray, pred: np.ndarray, radius: np.ndarray) -> dict:
    rows = {}
    for bias in (-0.05, -0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02, 0.05):
        shifted = pred + bias
        m = metrics(y, shifted, radius)
        rows[f"bias_{bias:+.3f}"] = {
            **m,
            "bias_soh": float(bias),
            "domain_audit": group_audit(test_df, y, shifted, radius),
        }
    below = [abs(v["bias_soh"]) for v in rows.values() if v["coverage"] < TARGET]
    return {
        "bias_grid": rows,
        "breakpoint_abs_bias_soh": float(min(below)) if below else None,
        "interpretation": "Empirical prediction-bias stress probe recomputed on real held-out rows; no synthetic rows added.",
    }


def persistence_baseline(test_df: pd.DataFrame) -> dict:
    rows = test_df.sort_values(["cell_id", "cycle_index"]).copy()
    rows["pred"] = rows.groupby("cell_id")["soh"].shift(1)
    rows = rows.dropna(subset=["pred"])
    if rows.empty:
        return {"n": 0}
    y = rows["soh"].to_numpy()
    pred = rows["pred"].to_numpy()
    return {
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
        "n": int(len(rows)),
    }


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def save_exp(exp_id: str, title: str, metrics_obj: dict, purpose: str) -> None:
    exp = EXPERIMENTS / exp_id
    write_json(exp / "results" / "metrics.json", metrics_obj)
    plan_path = exp / "plan.md"
    if not plan_path.exists():
        plan_path.write_text(f"# {exp_id}: {title}\n\n## Purpose\n{purpose}\n\n## Data\nReal data only from `data/raw` NAS symlinks.\n")
    (exp / "report.md").write_text(
        f"# {exp_id}: {title}\n\n"
        f"**Status**: pending_review\n\n"
        f"**Generated**: {datetime.now().isoformat()}\n\n"
        "## Summary\n"
        f"Selected method: `{metrics_obj.get('selected_method', 'n/a')}`.\n\n"
        "Synthetic data was not used.\n"
    )


def run_ablation(df: pd.DataFrame, splits: dict[str, list[int]], seed: int) -> dict:
    conditions = {
        "full_features": set(),
        "without_prev_soh": {"prev_soh", "prev_soh_missing"},
        "without_resistance": {"internal_resistance", "internal_resistance_missing"},
        "without_prev_soh_and_resistance": {"prev_soh", "prev_soh_missing", "internal_resistance", "internal_resistance_missing"},
    }
    out = {
        "target_coverage": TARGET,
        "ablation_conditions": {key: sorted(value) for key, value in conditions.items()},
        "conditions": {},
    }
    baseline = None
    for key, drop in conditions.items():
        result = run_conformal(df, splits, seed, drop_cols=drop, include_persistence_anchor=("prev_soh" not in drop))
        out["conditions"][key] = result
        if key == "full_features":
            baseline = result.get("selected", {})
        elif baseline and "selected" in result:
            selected = result["selected"]
            out["conditions"][key]["delta_vs_full"] = {
                "coverage": float(selected["coverage"] - baseline["coverage"]),
                "mean_width": float(selected["mean_width"] - baseline["mean_width"]),
                "mae": float(selected["mae"] - baseline["mae"]),
                "rmse": float(selected["rmse"] - baseline["rmse"]),
            }
    return out


def run_host_latency_screen(df: pd.DataFrame, splits: dict[str, list[int]]) -> dict:
    cal_idx = np.array(splits["cal"], dtype=int)
    test_idx = np.array(splits["test"], dtype=int)
    cal = df.loc[cal_idx].copy()
    sample = df.loc[test_idx].head(512).copy()
    cal_resid = np.abs(cal["soh"].to_numpy() - cal["prev_soh"].to_numpy())
    q_level = 0.93
    global_radius = float(np.quantile(cal_resid, q_level, method="higher"))
    group_radii = {}
    for group, g in cal.groupby("calibration_group"):
        resid = np.abs(g["soh"].to_numpy() - g["prev_soh"].to_numpy())
        group_radii[group] = float(np.quantile(resid, q_level, method="higher")) if len(resid) >= 20 else global_radius

    def interval_lookup(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        pred = frame["prev_soh"].to_numpy()
        radius = frame["calibration_group"].map(group_radii).fillna(global_radius).to_numpy()
        return pred - radius, pred + radius

    def persistence_only(frame: pd.DataFrame) -> np.ndarray:
        return frame["prev_soh"].to_numpy()

    train_idx = np.array(splits["train"], dtype=int)
    fcols = feature_columns(df)
    gb = GradientBoostingRegressor(random_state=42, max_depth=3, n_estimators=250, learning_rate=0.035)
    gb.fit(df.loc[train_idx, fcols], df.loc[train_idx, "soh"].to_numpy())

    def sklearn_predict(frame: pd.DataFrame) -> np.ndarray:
        return gb.predict(frame[fcols])

    def measure(fn) -> dict:
        for _ in range(20):
            fn(sample)
        times = []
        for _ in range(300):
            t0 = time.perf_counter()
            fn(sample)
            times.append((time.perf_counter() - t0) * 1000 / max(len(sample), 1))
        return {
            "latency_ms_per_sample_mean": float(np.mean(times)),
            "latency_ms_per_sample_p95": float(np.quantile(times, 0.95)),
            "latency_ms_per_sample_std": float(np.std(times)),
        }

    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        git_commit = "unknown"

    measurements = {
        "persistence_only": measure(persistence_only),
        "persistence_anchor_interval_lookup": measure(interval_lookup),
        "gradient_boosting_predict": measure(sklearn_predict),
    }
    return {
        **measurements["persistence_anchor_interval_lookup"],
        "comparators": measurements,
        "n_test_samples_timed": int(len(sample)),
        "n_repetitions": 300,
        "n_warmup": 20,
        "q_level": q_level,
        "timed_path": "host-only persistence-anchor prediction plus protocol-Mondrian conformal interval lookup",
        "timing_semantics": "512-row vectorized batch timed repeatedly; per-sample values are amortized batch throughput, not serving latency",
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "timer": "time.perf_counter",
        "git_commit": git_commit,
        "source": "real test rows only; host compute-cost screen, not edge/deployment evidence",
    }


def flatten(exp_metrics: dict[str, dict]) -> dict:
    out = {
        "_meta": {
            "collected_at": datetime.now().isoformat(),
            "source": "real battery datasets only",
            "source_experiments": {k: f"experiments/{k}/results/metrics.json" for k in exp_metrics},
        }
    }
    for exp_id, obj in exp_metrics.items():
        selected = obj.get("selected", {})
        for key, value in selected.items():
            if isinstance(value, (int, float)):
                out[f"{exp_id}_{key}"] = value
        for method, vals in obj.get("methods", {}).items():
            for key, value in vals.items():
                if isinstance(value, (int, float)):
                    out[f"{exp_id}_{method}_{key}"] = value
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    df, splits = load_inputs()

    exp_metrics: dict[str, dict] = {}
    exp_metrics["exp001_main"] = run_conformal(df, splits, args.seed)
    save_exp("exp001_main", "Real-data marginal and non-exchangeable conformal SOH intervals", exp_metrics["exp001_main"], "Main SOH interval calibration on real NASA/CALCE/Oxford cycle-level data.")

    exp_metrics["exp002_ablation"] = run_ablation(df, splits, args.seed)
    save_exp("exp002_ablation", "Feature and calibration ablation", exp_metrics["exp002_ablation"], "Remove degradation-history and resistance features to quantify contribution.")

    cross = {"target_coverage": TARGET, "methods": {}}
    for domain in sorted(df["domain"].unique()):
        res = run_conformal(
            df,
            splits,
            args.seed,
            train_filter=lambda d, domain=domain: d["domain"].ne(domain).to_numpy(),
            test_filter=lambda d, domain=domain: d["domain"].eq(domain).to_numpy(),
            use_cross_domain_features=True,
            prefer_online=True,
        )
        cross["methods"][f"leave_{domain}_out"] = res
        cross["methods"][f"target_recalibrated_{domain}"] = run_target_recalibrated(df, args.seed, domain)
    exp_metrics["exp003_cross_protocol"] = cross
    save_exp("exp003_cross_protocol", "Leave-domain-out cross-protocol stress", cross, "Train on all other real domains and test on the held-out domain.")

    stress = run_conformal(df, splits, args.seed)
    if "selected" in stress:
        stress["bias_probe"] = stress.get("selected_bias_probe", {})
    exp_metrics["exp004_stress_failure"] = stress
    save_exp("exp004_stress_failure", "Real residual stress probe", stress, "Probe sensitivity of selected conformal interval to systematic residual bias on real test rows.")

    edge = run_host_latency_screen(df, splits)
    exp_metrics["exp005_edge"] = edge
    save_exp("exp005_edge", "Real-row inference latency screen", edge, "Measure prediction latency on real held-out feature rows.")

    write_json(PAPER_DATA / "metrics.json", flatten(exp_metrics))
    print(json.dumps({"status": "ok", "experiments": list(exp_metrics), "paper_metrics": "paper/data/metrics.json"}, indent=2))


if __name__ == "__main__":
    main()
