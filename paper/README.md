# 论文目录

此目录管理论文撰写的所有内容。

## 目录结构

```
paper/
├── README.md               # 本文件
│
├── data/                   # 论文数据层 (SSOT)
│   ├── metrics.json        # 核心指标（从实验聚合）
│   ├── tables/             # 表格数据
│   └── provenance.json     # 数据血缘追踪
│
├── source/                 # Quarto 源文件（主草稿）
│   ├── _quarto.yml         # Quarto 配置
│   ├── index.qmd           # 主文件
│   ├── 01-introduction.qmd
│   ├── 02-related-work.qmd
│   ├── 03-method.qmd
│   ├── 04-experiments.qmd
│   ├── 05-results.qmd
│   ├── 06-discussion.qmd
│   ├── 07-conclusion.qmd
│   └── references.bib      # 参考文献
│
├── figures/                # 论文图表
│   ├── fig1_overview.pdf
│   └── ...
│
├── scripts/                # 论文相关脚本
│   ├── collect_results.py      # 数据聚合
│   ├── check_hardcoded_numbers.py  # 硬编码检查
│   └── generate_figures.py     # 图表生成
│
├── journals/               # 期刊特定版本
│   └── journal_a/
│       ├── source/         # 期刊版 QMD
│       ├── figures/        # 期刊规格图表
│       └── output/         # 编译输出
│
└── supplementary/          # 补充材料
    └── README.md
```

## 数据流

```
experiments/expXXX/results/
         ↓ scripts/collect_results.py
paper/data/metrics.json (SSOT)
         ↓ Quarto 动态引用
paper/source/*.qmd
         ↓ quarto render
paper/source/_site/ 或 *.pdf
```

## 核心原则

### 1. 数据单一来源 (SSOT)

- 所有论文引用的数值都来自 `paper/data/metrics.json`
- **禁止**在 QMD 中硬编码数字
- **禁止**手动编辑 `paper/data/metrics.json`

### 2. 动态引用

在 QMD 中使用 Python 代码引用数据：

```markdown
Our method achieves `{python} f"{metrics['accuracy']:.1f}"`% accuracy.
```

### 3. 图表从数据生成

```python
# paper/scripts/generate_figures.py
import json
import matplotlib.pyplot as plt

with open("paper/data/metrics.json") as f:
    metrics = json.load(f)

# 生成图表
plt.bar(...)
plt.savefig("paper/figures/fig1.pdf")
```

## 常用命令

```bash
# 聚合实验数据
python paper/scripts/collect_results.py

# 检查硬编码数字
python paper/scripts/check_hardcoded_numbers.py

# 生成图表
python paper/scripts/generate_figures.py

# 渲染论文
cd paper/source && quarto render

# 渲染期刊版本
cd paper/journals/journal_a/source && quarto render
```

## 审核清单

渲染后检查：

- [ ] 摘要数值与正文一致
- [ ] 表格数值与正文一致
- [ ] 图表数值与正文一致
- [ ] 无硬编码数字
- [ ] 参考文献格式正确

## 期刊投稿

1. 在 `journals/` 创建期刊目录
2. 复制 `source/` 到期刊目录
3. 调整格式和页数
4. 确保数据路径指向 `../../data/`
5. 生成期刊规格图表
