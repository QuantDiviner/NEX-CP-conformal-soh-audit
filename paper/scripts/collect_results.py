#!/usr/bin/env python3
"""
实验结果收集脚本

用途：从 experiments/ 目录收集实验结果，聚合到 paper/data/metrics.json
使用：python paper/scripts/collect_results.py

数据流：
    experiments/expXXX/results/metrics.json
                     ↓
    paper/data/metrics.json (SSOT - 论文唯一数据源)
                     ↓
    paper/source/*.qmd (动态引用)

溯源信息：
    生成的 metrics.json 包含完整溯源信息，便于追踪和验证：
    - 收集时间
    - Git commit hash
    - 源文件时间戳
    - 实验角色映射
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


# === 配置 ===

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# 实验目录
EXPERIMENTS_DIR = ROOT_DIR / "experiments"

# 输出目录
OUTPUT_DIR = ROOT_DIR / "paper" / "data"

# 实验角色映射（从 PROJECT_CHARTER.md 复制）
# 使用角色而非硬编码实验ID，方便版本切换
EXPERIMENT_ROLES = {
    "main_baseline": "exp001_main",
    "ablation_study": "exp002_ablation",
    "cross_protocol_diagnostic": "exp003_cross_protocol",
    "stress_failure_probe": "exp004_stress_failure",
    "edge_compute_probe": "exp005_edge",
    "fpa_repair_negative_diagnostic": "exp006_fpa_repair",
    "scoped_method_repair": "exp007_fpa_round2_repair",
    "reliability_audit": "exp008_reliability_audit",
    "round4_schema_repair": "exp009_fpa_round4_repair",
    "hard_regime_audit": "exp010_hard_regime_audit",
    "original_paper_substance": "exp011_original_paper_substance",
    "shift_adaptive_comparator": "exp012_shift_adaptive_cp_comparator",
}


# === 溯源函数 ===

def get_git_commit() -> Optional[str]:
    """获取当前 Git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()[:8]  # 短 hash
    except Exception:
        return None


def get_git_dirty() -> bool:
    """检查是否有未提交的修改"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def get_file_mtime(filepath: Path) -> Optional[str]:
    """获取文件修改时间"""
    if filepath.exists():
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        return mtime.isoformat()
    return None


def build_traceability_info() -> dict:
    """
    构建完整的溯源信息

    这些信息帮助：
    1. 追踪数据来源
    2. 验证数据是否过期
    3. 复现结果
    """
    git_commit = get_git_commit()
    git_dirty = get_git_dirty()

    return {
        "collected_at": datetime.now().isoformat(),
        "collector_script": "paper/scripts/collect_results.py",
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "warning": "代码有未提交修改，结果可能不可复现" if git_dirty else None,
        "source_experiments": {},
        "source_files": {},
    }


# === 收集函数 ===

def load_experiment_metrics(exp_dir: Path) -> dict:
    """
    从单个实验目录加载指标

    Args:
        exp_dir: 实验目录路径

    Returns:
        dict: 实验指标，如果文件不存在返回空字典
    """
    metrics_file = exp_dir / "results" / "metrics.json"

    if not metrics_file.exists():
        print(f"  ⚠️  未找到: {metrics_file}")
        return {}

    with open(metrics_file) as f:
        metrics = json.load(f)
        print(f"  ✓ 加载: {metrics_file.relative_to(ROOT_DIR)}")
        return metrics


def collect_all_metrics() -> dict:
    """
    收集所有实验的指标

    Returns:
        dict: 聚合后的指标，包含完整溯源信息
    """
    # 构建带溯源信息的聚合结果
    aggregated = {
        "_meta": build_traceability_info()
    }

    # 检查配置
    if not EXPERIMENT_ROLES:
        print("⚠️  EXPERIMENT_ROLES 为空！")
        print("请在脚本中配置实验角色映射，或在 PROJECT_CHARTER.md 中定义后复制到此处。")
        print("\n示例配置:")
        print('''
EXPERIMENT_ROLES = {
    "main_experiment": "exp001_main",
    "ablation_study": "exp002_ablation",
}
''')
        return aggregated

    # 收集每个角色的实验结果
    for role, exp_name in EXPERIMENT_ROLES.items():
        print(f"\n--- {role} ({exp_name}) ---")

        exp_dir = EXPERIMENTS_DIR / exp_name

        if not exp_dir.exists():
            print(f"  ❌ 实验目录不存在: {exp_dir}")
            continue

        metrics = load_experiment_metrics(exp_dir)

        if metrics:
            # 将实验指标添加到聚合结果
            # 可以选择：
            # 1. 按角色分组: aggregated[role] = metrics
            # 2. 扁平化: aggregated.update({f"{role}_{k}": v for k, v in metrics.items()})

            # 默认：扁平化，便于在 Quarto 中直接引用
            for key, value in metrics.items():
                if not key.startswith("_"):  # 跳过元数据
                    flat_key = f"{role}_{key}" if len(EXPERIMENT_ROLES) > 1 else key
                    aggregated[flat_key] = value

            # 记录来源和时间戳（用于溯源和新鲜度检查）
            metrics_file = exp_dir / "results" / "metrics.json"
            aggregated["_meta"]["source_experiments"][role] = exp_name
            aggregated["_meta"]["source_files"][role] = {
                "path": str(metrics_file.relative_to(ROOT_DIR)),
                "mtime": get_file_mtime(metrics_file),
            }

    return aggregated


def calculate_derived_metrics(metrics: dict) -> dict:
    """
    计算派生指标（如性能提升百分比）

    Args:
        metrics: 原始指标

    Returns:
        dict: 添加派生指标后的字典
    """
    # 示例：计算性能提升
    # if "proposed_accuracy" in metrics and "baseline_accuracy" in metrics:
    #     proposed = metrics["proposed_accuracy"]
    #     baseline = metrics["baseline_accuracy"]
    #     metrics["improvement_pct"] = (proposed - baseline) / baseline * 100

    return metrics


def save_metrics(metrics: dict, output_path: Path):
    """保存指标到 JSON 文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 保存到: {output_path.relative_to(ROOT_DIR)}")


def main():
    """主函数"""
    print("=" * 60)
    print("实验结果收集脚本")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 60)

    # 收集指标
    metrics = collect_all_metrics()

    # 计算派生指标
    metrics = calculate_derived_metrics(metrics)

    # 保存
    output_path = OUTPUT_DIR / "metrics.json"
    save_metrics(metrics, output_path)

    # 总结
    metric_count = len([k for k in metrics.keys() if not k.startswith("_")])
    print(f"\n共收集 {metric_count} 个指标")

    print("\n下一步:")
    print("1. 验证 paper/data/metrics.json 中的数值")
    print("2. 在 paper/source/*.qmd 中使用动态引用")
    print("3. 运行 quarto render paper/source/ 生成论文")


if __name__ == "__main__":
    main()
