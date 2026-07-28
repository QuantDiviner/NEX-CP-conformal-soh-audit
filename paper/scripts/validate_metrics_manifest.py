#!/usr/bin/env python3
"""Validate the paper metrics semantic manifest."""

import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "paper" / "data"
METRICS_PATH = DATA_DIR / "metrics.json"
MANIFEST_PATH = DATA_DIR / "metrics_manifest.yaml"

REQUIRED_KEY_FIELDS = {
    "key",
    "value_type",
    "aggregation_method",
    "semantic_unit",
    "source_raw",
    "source_expression",
    "allowed_words",
    "forbidden_words",
}
ALLOWED_AGGREGATIONS = {
    "copied_from_experiment",
    "role_prefixed_copy",
    "derived",
    "metadata",
    "not_aggregated",
}


def load_json_yaml_subset(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} must be JSON-compatible YAML: {exc}") from exc


def main() -> int:
    problems: list[str] = []
    if not METRICS_PATH.exists():
        problems.append(f"missing {METRICS_PATH.relative_to(ROOT_DIR)}")
    if not MANIFEST_PATH.exists():
        problems.append(f"missing {MANIFEST_PATH.relative_to(ROOT_DIR)}")
    if problems:
        print("\n".join(problems))
        return 1

    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    manifest = load_json_yaml_subset(MANIFEST_PATH)

    for field in ("schema_version", "project_name", "unregistered_policy", "keys", "method_claims"):
        if field not in manifest:
            problems.append(f"manifest missing required field: {field}")

    manifest_keys = manifest.get("keys", [])
    if not isinstance(manifest_keys, list):
        problems.append("manifest keys must be a list")
        manifest_keys = []

    registered = set()
    allow_list = set(manifest.get("unregistered_allow_list", []))
    for idx, entry in enumerate(manifest_keys):
        missing = REQUIRED_KEY_FIELDS - set(entry)
        if missing:
            problems.append(f"keys[{idx}] missing fields: {sorted(missing)}")
        key = entry.get("key")
        if key in registered:
            problems.append(f"duplicate manifest key: {key}")
        if key:
            registered.add(key)
        aggregation = entry.get("aggregation_method")
        if aggregation not in ALLOWED_AGGREGATIONS:
            problems.append(f"{key}: invalid aggregation_method {aggregation!r}")
        if not isinstance(entry.get("allowed_words", []), list):
            problems.append(f"{key}: allowed_words must be a list")
        if not isinstance(entry.get("forbidden_words", []), list):
            problems.append(f"{key}: forbidden_words must be a list")

    top_keys = {key for key in metrics if not key.startswith("_")}
    unregistered = sorted(top_keys - registered - allow_list)
    if unregistered:
        problems.append(f"unregistered metrics keys: {', '.join(unregistered[:30])}")
        if len(unregistered) > 30:
            problems.append(f"... plus {len(unregistered) - 30} more")

    missing_metrics = sorted(registered - top_keys)
    if missing_metrics:
        problems.append(f"manifest keys missing from metrics.json: {', '.join(missing_metrics[:30])}")

    if problems:
        print("Metrics manifest validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(f"Metrics manifest validation passed: {len(registered)} keys registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
