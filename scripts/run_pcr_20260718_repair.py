#!/usr/bin/env python3
"""Deterministically rerun experiments affected by PCR-2026-07-18-01."""

from __future__ import annotations

import subprocess
import sys
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"

COMMANDS = (
    (
        "scripts/run_fpa_repair_experiment.py",
        "--output-exp", "exp007_fpa_round2_repair",
        "--seed", "42", "--bootstrap-reps", "1000", "--include-ngboost",
    ),
    (
        "scripts/run_reliability_audit_experiment.py",
        "--output-exp", "exp008_reliability_audit",
        "--seed", "42", "--bootstrap-reps", "1000",
        "--min-decision-denominator", "5", "--include-ngboost",
    ),
    (
        "scripts/run_reliability_audit_experiment.py",
        "--output-exp", "exp009_fpa_round4_repair",
        "--seed", "42", "--bootstrap-reps", "1000",
        "--min-decision-denominator", "5", "--include-ngboost",
        "--add-harmonized-leave-nasa",
    ),
    (
        "scripts/run_hard_regime_audit_experiment.py",
        "--output-exp", "exp010_hard_regime_audit",
        "--seed", "42", "--bootstrap-reps", "1000",
        "--min-decision-denominator", "5", "--horizons", "0,5,20",
    ),
    (
        "scripts/run_original_paper_substance_experiment.py",
        "--output-exp", "exp011_original_paper_substance",
        "--seed", "42", "--bootstrap-reps", "1000",
        "--min-decision-denominator", "5",
    ),
    (
        "scripts/run_shift_adaptive_cp_comparator.py",
        "--output-exp", "exp012_shift_adaptive_cp_comparator",
        "--seed", "42", "--bootstrap-reps", "1000",
        "--min-decision-denominator", "5",
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-at", type=int, default=7, choices=range(7, 13))
    args = parser.parse_args()
    if not PYTHON.exists():
        raise SystemExit("Project .venv is missing; run research preflight first.")
    for experiment_number, command_args in zip(range(7, 13), COMMANDS):
        if experiment_number < args.start_at:
            continue
        command = [str(PYTHON), *command_args]
        print(f"RUN {' '.join(command_args)}", flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    print("PCR-2026-07-18-01 rerun complete", flush=True)


if __name__ == "__main__":
    main()
