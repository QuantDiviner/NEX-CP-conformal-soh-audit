#!/usr/bin/env python3
"""Validate external fact registry against governed manuscript text."""

import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "paper" / "data"
SOURCE_DIR = ROOT_DIR / "paper" / "source"
FACTS_PATH = DATA_DIR / "external_facts.yaml"


def load_json_yaml_subset(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} must be JSON-compatible YAML: {exc}") from exc


def governed_text() -> str:
    entry = SOURCE_DIR / "paper.qmd"
    if not entry.exists():
        return "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_DIR.glob("*.qmd"))
    parts = [entry.read_text(encoding="utf-8")]
    for line in parts[0].splitlines():
        line = line.strip()
        if line.startswith("{{< include "):
            include = line.removeprefix("{{< include ").removesuffix(">}}").strip()
            path = SOURCE_DIR / include
            if path.exists():
                parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def main() -> int:
    if not FACTS_PATH.exists():
        print(f"missing {FACTS_PATH.relative_to(ROOT_DIR)}")
        return 1

    registry = load_json_yaml_subset(FACTS_PATH)
    problems: list[str] = []
    facts = registry.get("facts", [])
    if registry.get("schema_version") is None:
        problems.append("external_facts missing schema_version")
    if not isinstance(facts, list) or not facts:
        problems.append("external_facts facts must be a non-empty list")
        facts = []

    manuscript = governed_text().lower()
    seen = set()
    for idx, fact in enumerate(facts):
        fact_id = fact.get("fact_id")
        if not fact_id:
            problems.append(f"facts[{idx}] missing fact_id")
        elif fact_id in seen:
            problems.append(f"duplicate fact_id: {fact_id}")
        seen.add(fact_id)
        for field in ("fact_type", "statement", "source_url_or_doi", "verified_date", "anti_claims"):
            if field not in fact:
                problems.append(f"{fact_id or idx}: missing {field}")
        if not str(fact.get("source_url_or_doi", "")).strip():
            problems.append(f"{fact_id or idx}: empty source_url_or_doi")
        anti_claims = fact.get("anti_claims", [])
        if not isinstance(anti_claims, list):
            problems.append(f"{fact_id or idx}: anti_claims must be a list")
            anti_claims = []
        for anti_claim in anti_claims:
            if str(anti_claim).lower() in manuscript:
                problems.append(f"{fact_id or idx}: anti-claim appears in manuscript: {anti_claim}")

    if problems:
        print("External fact validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(f"External fact validation passed: {len(facts)} facts registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
