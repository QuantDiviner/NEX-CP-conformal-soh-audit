#!/usr/bin/env python3
"""
论文图表生成脚本模板

用途：从 paper/data/ 读取数据，生成论文图表
使用：python paper/scripts/generate_figures.py

说明：
    这是一个模板，请根据项目需求实现具体的图表生成函数。
    下面提供了学术期刊通用的样式配置。
"""

import json
from pathlib import Path

# 可选依赖
# import matplotlib.pyplot as plt
# import pandas as pd


ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "paper" / "data"
FIGURES_DIR = ROOT_DIR / "paper" / "figures"


# 学术期刊图表样式配置
FIGURE_STYLE = {
    # 尺寸（英寸）
    "single_column": 3.5,
    "double_column": 7.0,
    "dpi": 300,

    # 字体
    "font_family": "serif",
    "font_size": 10,

    # 色盲友好配色
    "colors": ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#F0E442"],
}


def setup_style():
    """配置 matplotlib 样式"""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": FIGURE_STYLE["font_family"],
        "font.size": FIGURE_STYLE["font_size"],
        "figure.dpi": FIGURE_STYLE["dpi"],
        "savefig.dpi": FIGURE_STYLE["dpi"],
        "savefig.bbox": "tight",
    })


def load_metrics() -> dict:
    """加载 metrics.json"""
    path = DATA_DIR / "metrics.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def main():
    """主函数 - 在此添加图表生成代码"""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("论文图表生成脚本")
    print(f"输出目录: {FIGURES_DIR}")

    # 示例：
    # metrics = load_metrics()
    # setup_style()
    #
    # import matplotlib.pyplot as plt
    # fig, ax = plt.subplots(figsize=(FIGURE_STYLE["single_column"], 3))
    # ax.bar(["A", "B"], [metrics.get("a", 0), metrics.get("b", 0)])
    # plt.savefig(FIGURES_DIR / "comparison.pdf")

    print("\n请在此脚本中实现具体的图表生成逻辑")


if __name__ == "__main__":
    main()
