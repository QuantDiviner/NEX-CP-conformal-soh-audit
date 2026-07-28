# 实验模板

复制此目录创建新实验：

```bash
cp -r experiments/_template experiments/exp001_description
```

## 目录结构

```
expXXX_description/
├── config.yaml          # 实验配置（从 configs/default.yaml 派生）
├── README.md            # 实验说明（复制本文件后修改）
├── logs/                # 训练日志
│   └── .gitkeep
├── checkpoints/         # 模型检查点（建议 .gitignore）
│   └── .gitkeep
├── results/             # 实验结果
│   ├── metrics.json     # 核心指标（用于论文引用）
│   └── figures/         # 实验生成的图表
└── analysis/            # 分析脚本和笔记
    └── .gitkeep
```

## 快速开始

1. **复制模板**
   ```bash
   cp -r experiments/_template experiments/exp001_baseline
   ```

2. **修改配置**
   ```bash
   # 从默认配置派生
   cp configs/default.yaml experiments/exp001_baseline/config.yaml
   # 编辑实验特定参数
   ```

3. **记录实验目的**
   编辑本 README.md，填写下方模板

4. **运行实验**
   ```bash
   python scripts/train.py --config experiments/exp001_baseline/config.yaml
   ```

5. **记录结果**
   实验完成后，确保 `results/metrics.json` 已生成

---

## 实验信息（填写此部分）

### 实验ID
`expXXX`

### 实验目的
[简述本实验要验证什么假设或回答什么问题]

### 与基准的差异
[相比默认配置或其他实验，本实验改变了什么]

| 参数 | 基准值 | 本实验值 | 原因 |
|------|--------|----------|------|
| param_1 | value_1 | new_value | 理由 |

### 预期结果
[你期望看到什么结果？]

### 实际结果
[实验完成后填写]

- **状态**: ⏳ 待运行 / 🔄 运行中 / ✅ 完成 / ❌ 失败
- **运行时间**:
- **关键指标**:
  - metric_1:
  - metric_2:

### 结论
[这个实验告诉我们什么？]

### 后续行动
- [ ] 行动1
- [ ] 行动2
