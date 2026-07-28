#!/usr/bin/env python3
"""Preprocess real battery datasets into a cycle-level SOH table.

No synthetic rows are generated here. Every output row is derived from files
under data/raw, which are expected to be symlinks to the NAS datasets.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.io import loadmat


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SPLITS = ROOT / "data" / "splits"


def _clean_capacity(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan)
    return values


def _finalize_cell(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["capacity_ah"]).copy()
    df = df[df["capacity_ah"] > 0]
    if df.empty:
        return df
    df = df.sort_values(["dataset", "cell_id", "cycle_index"])
    refs = {}
    qa_rows = []
    for (dataset, cell), group in df.groupby(["dataset", "cell_id"], sort=False):
        early_n = max(3, min(10, int(np.ceil(len(group) * 0.2))))
        early = group.head(early_n)["capacity_ah"].to_numpy(dtype=float)
        reference = float(np.nanmax(early))
        refs[(dataset, cell)] = reference
        soh_values = group["capacity_ah"].to_numpy(dtype=float) / reference
        qa_rows.append(
            {
                "dataset": dataset,
                "cell_id": cell,
                "n_cycles": int(len(group)),
                "reference_capacity_ah": reference,
                "min_soh": float(np.nanmin(soh_values)),
                "max_soh": float(np.nanmax(soh_values)),
                "monotonic_violation_rate": float(np.mean(np.diff(soh_values) > 0.01)) if len(soh_values) > 1 else 0.0,
                "qa_pass": bool(len(group) >= 20 and np.nanmax(soh_values) <= 1.05),
            }
        )
    ref_series = df.apply(lambda r: refs[(r["dataset"], r["cell_id"])], axis=1)
    df["soh"] = df["capacity_ah"] / ref_series
    qa = pd.DataFrame(qa_rows)
    failed_cells = set(qa.loc[~qa["qa_pass"], "cell_id"].astype(str))
    df = df[~df["cell_id"].astype(str).isin(failed_cells)]
    df = df[(df["soh"] > 0.4) & (df["soh"] <= 1.05)]
    df.attrs["qa"] = qa
    return df


def load_nasa() -> pd.DataFrame:
    meta_path = RAW / "NASA" / "cleaned_dataset" / "metadata.csv"
    if not meta_path.exists():
        return pd.DataFrame()
    meta = pd.read_csv(meta_path)
    dis = meta[meta["type"].astype(str).str.lower() == "discharge"].copy()
    dis["capacity_ah"] = _clean_capacity(dis["Capacity"])
    dis["re_ohm"] = _clean_capacity(dis.get("Re", pd.Series(index=dis.index, dtype=float)))
    dis["rct_ohm"] = _clean_capacity(dis.get("Rct", pd.Series(index=dis.index, dtype=float)))
    dis["ambient_temperature"] = pd.to_numeric(dis["ambient_temperature"], errors="coerce")
    dis = dis.sort_values(["battery_id", "test_id"])
    dis["cycle_index"] = dis.groupby("battery_id").cumcount() + 1
    out = pd.DataFrame(
        {
            "dataset": "NASA",
            "domain": "NASA",
            "chemistry": "Li-ion",
            "protocol": "NASA",
            "cell_id": "NASA_" + dis["battery_id"].astype(str),
            "cycle_index": dis["cycle_index"],
            "capacity_ah": dis["capacity_ah"],
            "ambient_temperature": dis["ambient_temperature"],
            "internal_resistance": dis[["re_ohm", "rct_ohm"]].mean(axis=1),
            "source_file": str(meta_path.relative_to(ROOT)),
        }
    )
    return out


def load_calce(limit_files: int | None = None) -> pd.DataFrame:
    rows = []
    skipped = []
    files = sorted((RAW / "CALCE").glob("**/*.xlsx"))
    if limit_files:
        files = files[:limit_files]
    for path in files:
        try:
            xl = pd.ExcelFile(path)
        except Exception as exc:
            skipped.append({"file": str(path), "reason": f"open_failed:{exc}"})
            continue
        stat_sheets = [s for s in xl.sheet_names if s.lower().startswith("statistics")]
        for sheet in stat_sheets:
            try:
                df = pd.read_excel(path, sheet_name=sheet, usecols=lambda c: c in {
                    "Cycle_Index",
                    "Discharge_Capacity(Ah)",
                    "Internal_Resistance(Ohm)",
                    "Date_Time",
                })
            except Exception as exc:
                skipped.append({"file": str(path), "sheet": sheet, "reason": f"read_failed:{exc}"})
                continue
            if "Discharge_Capacity(Ah)" not in df or "Cycle_Index" not in df:
                skipped.append({"file": str(path), "sheet": sheet, "reason": "missing_required_columns"})
                continue
            name_match = re.search(r"(CS2_\d+|CX2_\d+)", str(path))
            if name_match:
                cell_name = name_match.group(1)
                protocol = cell_name.split("_")[0]
            else:
                channel = sheet.replace("Channel_", "")
                stem = re.sub(r"-?\d{8}$", "", path.stem)
                cell_name = f"{stem}_{channel}"
                protocol = "A123"
            df = df.copy()
            df["Cycle_Index"] = pd.to_numeric(df["Cycle_Index"], errors="coerce")
            df["Discharge_Capacity(Ah)"] = _clean_capacity(df["Discharge_Capacity(Ah)"])
            df["Internal_Resistance(Ohm)"] = pd.to_numeric(
                df.get("Internal_Resistance(Ohm)", pd.Series(np.nan, index=df.index)),
                errors="coerce",
            )
            df["ambient_temperature"] = np.nan
            df["Date_Time"] = pd.to_datetime(df.get("Date_Time"), errors="coerce")
            df = df.dropna(subset=["Cycle_Index", "Discharge_Capacity(Ah)"])
            if df.empty:
                skipped.append({"file": str(path), "sheet": sheet, "reason": "no_valid_cycles"})
                continue
            grouped = df.sort_values(["Date_Time", "Cycle_Index"]).copy()
            raw_cap = grouped["Discharge_Capacity(Ah)"].to_numpy(dtype=float)
            delta_cap = np.diff(np.r_[0.0, raw_cap])
            valid_delta = (delta_cap > 0.05) & (delta_cap < np.nanpercentile(raw_cap, 95) * 1.2)
            grouped["capacity_ah"] = np.where(valid_delta, delta_cap, raw_cap)
            for _, row in grouped.iterrows():
                rows.append(
                    {
                        "dataset": "CALCE",
                        "domain": "CALCE",
                        "chemistry": "LCO/NMC",
                        "protocol": protocol,
                        "cell_id": f"CALCE_{cell_name}",
                        "cycle_index": row["Cycle_Index"],
                        "source_order": row["Date_Time"].isoformat() if pd.notna(row["Date_Time"]) else "",
                        "capacity_ah": row["capacity_ah"],
                        "ambient_temperature": row["ambient_temperature"],
                        "internal_resistance": row["Internal_Resistance(Ohm)"],
                        "source_file": str(path.relative_to(ROOT)),
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.dropna(subset=["capacity_ah", "cycle_index"]).copy()
    out = out.sort_values(["cell_id", "source_order", "cycle_index", "source_file"])
    out["cycle_index"] = out.groupby("cell_id").cumcount() + 1
    out = out.drop(columns=["source_order"])
    out.attrs["skipped"] = skipped
    return out


def load_oxford() -> pd.DataFrame:
    path = RAW / "Oxford" / "Oxford_Battery_Degradation_Dataset_1.mat"
    if not path.exists():
        return pd.DataFrame()
    mat = loadmat(path, simplify_cells=True)
    rows = []
    for cell_name, cell_data in mat.items():
        if not cell_name.startswith("Cell") or not isinstance(cell_data, dict):
            continue
        for key in sorted(k for k in cell_data if k.startswith("cyc")):
            cycle_data = cell_data[key]
            if not isinstance(cycle_data, dict) or "C1dc" not in cycle_data:
                continue
            dc = cycle_data["C1dc"]
            q = np.asarray(dc.get("q", []), dtype=float)
            temp = np.asarray(dc.get("T", []), dtype=float)
            if q.size == 0:
                continue
            capacity_ah = abs(float(np.nanmin(q))) / 1000.0
            cycle_index = int(key.replace("cyc", "")) + 1
            rows.append(
                {
                    "dataset": "Oxford",
                    "domain": "Oxford",
                    "chemistry": "NMC",
                    "protocol": "Oxford",
                    "cell_id": f"Oxford_{cell_name}",
                    "cycle_index": cycle_index,
                    "capacity_ah": capacity_ah,
                    "ambient_temperature": float(np.nanmean(temp)) if temp.size else np.nan,
                    "internal_resistance": np.nan,
                    "source_file": str(path.relative_to(ROOT)),
                }
            )
    return pd.DataFrame(rows)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["dataset", "cell_id", "cycle_index"]).copy()
    df["calibration_group"] = np.where(
        df["domain"].eq("CALCE"),
        "CALCE_" + df["protocol"].astype(str),
        df["domain"].astype(str),
    )
    df["split_progress"] = df.groupby("cell_id")["cycle_index"].transform(lambda s: s / max(float(s.max()), 1.0))
    df["log_cycle_index"] = np.log1p(df["cycle_index"].astype(float))
    df["prev_soh"] = df.groupby("cell_id")["soh"].shift(1)
    df["prev_soh_missing"] = df["prev_soh"].isna().astype(int)
    # A recent-label feature is valid only when a strictly earlier same-cell
    # capacity measurement exists. Exclude each cell's first record instead of
    # filling it from the current target, which would introduce same-row label
    # leakage into fitting, calibration, validation, or testing.
    df = df.loc[df["prev_soh_missing"].eq(0)].copy()
    df["ambient_temperature_missing"] = df["ambient_temperature"].isna().astype(int)
    df["internal_resistance_missing"] = df["internal_resistance"].isna().astype(int)
    df["ambient_temperature"] = df["ambient_temperature"].fillna(df["ambient_temperature"].median())
    df["internal_resistance"] = df["internal_resistance"].fillna(df["internal_resistance"].median())
    if df["internal_resistance"].isna().all():
        df["internal_resistance"] = 0.0
    df = pd.get_dummies(df, columns=["dataset", "chemistry", "protocol"], drop_first=False)
    return df


def make_splits(df: pd.DataFrame, seed: int) -> dict[str, list[int]]:
    rng = np.random.default_rng(seed)
    splits = {"train": [], "cal": [], "val": [], "test": []}
    cells = np.array(sorted(df["cell_id"].unique()))
    for domain in sorted(df["domain"].unique()):
        domain_cells = np.array(sorted(df.loc[df["domain"] == domain, "cell_id"].unique()))
        rng.shuffle(domain_cells)
        n = len(domain_cells)
        if n < 4:
            train_cells, cal_cells, val_cells, test_cells = domain_cells[:1], domain_cells[:1], domain_cells[:1], domain_cells[1:]
        else:
            n_train = max(1, int(0.55 * n))
            n_cal = max(1, int(0.20 * n))
            n_val = max(1, int(0.10 * n))
            train_cells = domain_cells[:n_train]
            cal_cells = domain_cells[n_train : n_train + n_cal]
            val_cells = domain_cells[n_train + n_cal : n_train + n_cal + n_val]
            test_cells = domain_cells[n_train + n_cal + n_val :]
        for name, selected in {
            "train": train_cells,
            "cal": cal_cells,
            "val": val_cells,
            "test": test_cells,
        }.items():
            mask = df["cell_id"].isin(selected)
            if name == "cal":
                mask &= df["split_progress"] <= 0.55
            if name == "test":
                mask &= df["split_progress"] >= 0.35
            splits[name].extend(df.index[mask].astype(int).tolist())
    return splits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--calce-limit-files", type=int, default=None)
    args = parser.parse_args()

    frames = [load_nasa(), load_calce(args.calce_limit_files), load_oxford()]
    skipped = []
    for frame in frames:
        skipped.extend(frame.attrs.get("skipped", []))
    raw = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    if raw.empty:
        raise SystemExit("No real battery rows found under data/raw.")
    raw = _finalize_cell(raw).reset_index(drop=True)
    qa_frames = []
    if isinstance(raw.attrs.get("qa"), pd.DataFrame):
        qa_frames.append(raw.attrs["qa"])
    for qa in qa_frames:
        for _, row in qa.loc[~qa["qa_pass"]].iterrows():
            skipped.append(
                {
                    "cell_id": row["cell_id"],
                    "dataset": row["dataset"],
                    "reason": "qa_failed",
                    "n_cycles": int(row["n_cycles"]),
                    "max_soh": float(row["max_soh"]),
                    "min_soh": float(row["min_soh"]),
                }
            )
    featured = add_features(raw).reset_index(drop=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    SPLITS.mkdir(parents=True, exist_ok=True)
    raw_path = PROCESSED / "real_battery_cycle_level_raw.csv"
    feature_path = PROCESSED / "real_battery_cycle_level_features.csv"
    raw.to_csv(raw_path, index=False)
    featured.to_csv(feature_path, index=False)
    qa_path = SPLITS / "real_battery_preprocess_qa.csv"
    if qa_frames:
        pd.concat(qa_frames, ignore_index=True).drop_duplicates(["dataset", "cell_id"]).to_csv(qa_path, index=False)
    skipped_path = SPLITS / "real_battery_skipped_sources.json"
    skipped_path.write_text(json.dumps(skipped, indent=2, ensure_ascii=False) + "\n")
    splits = make_splits(featured, args.seed)
    (SPLITS / "real_battery_splits.json").write_text(json.dumps(splits, indent=2) + "\n")
    manifest = {
        "created_at": datetime.now().isoformat(),
        "seed": args.seed,
        "raw_rows": int(len(raw)),
        "feature_rows": int(len(featured)),
        "cells": int(raw["cell_id"].nunique()),
        "domains": sorted(raw["domain"].unique().tolist()),
        "source": "real data only: data/raw symlinks to NAS battery datasets",
        "runtime_packages": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "outputs": [
            str(raw_path.relative_to(ROOT)),
            str(feature_path.relative_to(ROOT)),
            "data/splits/real_battery_splits.json",
            "data/splits/real_battery_preprocess_qa.csv",
            "data/splits/real_battery_skipped_sources.json",
        ],
    }
    (SPLITS / "real_battery_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
