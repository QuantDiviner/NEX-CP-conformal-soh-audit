#!/usr/bin/env python3
"""Project wrapper for the bundled paper-writing core manuscript linter.

The bundled linter intentionally supports .tex files for projects that author
manuscripts directly in LaTeX. This project authors the manuscript in Quarto and
keeps Pandoc's generated index.tex in paper/source for Elsevier packaging, so
linting that generated file produces false hardcoded-number errors. This wrapper
keeps the bundled checks but limits manuscript-source enumeration to authored
QMD/Markdown files.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLED = ROOT / ".codex/skills/paper-writing-workflow/scripts/core_manuscript_lint.py"


def _load_bundled():
    spec = importlib.util.spec_from_file_location("bundled_core_manuscript_lint", BUNDLED)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load bundled linter: {BUNDLED}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _project_source_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.exists():
        return []
    authored_exts = {".qmd", ".md"}
    ignored_names = {
        "PROGRESS.md",
        "_generated_metadata.yml",
    }
    ignored_parts = {"_freeze", "output", ".quarto", "__pycache__", "index_files"}
    files: list[Path] = []
    for path in source.rglob("*"):
        if path.suffix.lower() not in authored_exts:
            continue
        if path.name in ignored_names:
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    module = _load_bundled()
    module.iter_source_files = _project_source_files
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
