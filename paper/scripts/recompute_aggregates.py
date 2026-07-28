#!/usr/bin/env python3
"""Recompute paper metrics from raw experiment files and compare with SSOT."""

import importlib.util
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent.parent
COLLECTOR_PATH = ROOT_DIR / "paper" / "scripts" / "collect_results.py"
METRICS_PATH = ROOT_DIR / "paper" / "data" / "metrics.json"


def load_collector():
    spec = importlib.util.spec_from_file_location("collect_results", COLLECTOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load collect_results.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def comparable(metrics: dict) -> dict:
    return {key: value for key, value in metrics.items() if not key.startswith("_")}


def main() -> int:
    if not METRICS_PATH.exists():
        print(f"missing {METRICS_PATH.relative_to(ROOT_DIR)}")
        return 1
    collector = load_collector()
    current = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    recomputed = collector.collect_all_metrics()

    current_cmp = comparable(current)
    recomputed_cmp = comparable(recomputed)
    if current_cmp != recomputed_cmp:
        current_keys = set(current_cmp)
        recomputed_keys = set(recomputed_cmp)
        print("Aggregate recomputation failed:")
        missing = sorted(recomputed_keys - current_keys)
        extra = sorted(current_keys - recomputed_keys)
        changed = sorted(key for key in current_keys & recomputed_keys if current_cmp[key] != recomputed_cmp[key])
        if missing:
            print(f"- missing in current metrics.json: {missing[:20]}")
        if extra:
            print(f"- extra in current metrics.json: {extra[:20]}")
        if changed:
            print(f"- changed values: {changed[:20]}")
        return 1

    print(f"Aggregate recomputation passed: {len(current_cmp)} top-level metrics match raw experiment files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
