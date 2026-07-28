#!/usr/bin/env python3
"""
硬编码数字检查脚本

用途：检查 QMD 文件正文中的数字，提醒使用动态引用
使用：python paper/scripts/check_hardcoded_numbers.py

注意：这是一个辅助工具，需要人工判断哪些数字应该动态引用
"""

import json
import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent.parent
QMD_DIR = ROOT_DIR / "paper" / "source"
ENTRYPOINT = QMD_DIR / "paper.qmd"
WHITELIST = Path(__file__).parent / ".hardcoded_whitelist.yaml"


def load_whitelist() -> list[str]:
    if not WHITELIST.exists():
        return []
    text = WHITELIST.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        return data.get("line_allow_regex", [])
    except json.JSONDecodeError:
        patterns = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("- "):
                patterns.append(line[2:].strip().strip('"'))
        return patterns


def governed_qmd_files() -> list[Path]:
    if not ENTRYPOINT.exists():
        return sorted(QMD_DIR.glob("*.qmd"))
    files = [ENTRYPOINT]
    include_re = re.compile(r"\{\{<\s*include\s+([^>\s]+)\s*>\}\}")
    for line in ENTRYPOINT.read_text(encoding="utf-8").splitlines():
        match = include_re.search(line)
        if match:
            files.append(QMD_DIR / match.group(1))
    return [path for path in files if path.exists()]


def is_in_code_block(lines: list, line_num: int) -> bool:
    """检查某行是否在代码块内"""
    in_block = False
    for i in range(line_num):
        if lines[i].strip().startswith("```"):
            in_block = not in_block
    return in_block


def check_file(filepath: Path) -> list:
    """检查单个 QMD 文件"""
    issues = []

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    whitelist = [re.compile(pattern) for pattern in load_whitelist()]

    for i, line in enumerate(lines):
        # 跳过代码块
        if is_in_code_block(lines, i):
            continue

        # 跳过 YAML/注释/标题
        stripped = line.strip()
        if stripped.startswith(("---", "#", "<!--", "```", "#|")):
            continue
        if not stripped:
            continue
        if "{{< include " in stripped:
            continue
        if "`{python}" in line:
            continue
        if re.match(r"^\d+\.\s+\S", stripped):
            line = re.sub(r"^\d+\.\s+", "", line)
            stripped = line.strip()
        if "http://" in line or "https://" in line:
            continue
        if any(pattern.search(line) for pattern in whitelist):
            continue

        # 查找数字（包含小数、百分比）
        # 排除：引用 [@xxx]、年份、小整数 0-2
        for match in re.finditer(r'\b(\d+\.?\d*)\s*(%|°C|ms|s|min)?', line):
            num_str = match.group(1)
            try:
                num = float(num_str)
                # 跳过小数字和年份
                if num < 3 or (1900 <= num <= 2100):
                    continue

                issues.append((i + 1, stripped[:60], num_str))
            except ValueError:
                continue

    return issues


def main():
    print("=" * 50)
    print("硬编码数字检查")
    print("=" * 50)

    if not QMD_DIR.exists():
        print(f"目录不存在: {QMD_DIR}")
        sys.exit(0)

    total = 0
    for qmd_file in governed_qmd_files():
        issues = check_file(qmd_file)
        if issues:
            print(f"\n📄 {qmd_file.name}")
            for line_num, content, num in issues:
                print(f"  行 {line_num}: \"{num}\" - {content}...")
            total += len(issues)

    print("\n" + "=" * 50)
    if total == 0:
        print("✓ 未发现明显的硬编码数字")
    else:
        print(f"发现 {total} 个可能的硬编码数字")
        print("\n建议使用动态引用: `{python} metrics['key']`")
        print("注意：需要人工判断哪些确实需要动态引用")

    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
