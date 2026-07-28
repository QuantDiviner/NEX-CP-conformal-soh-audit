# 补充材料

此目录存放论文的补充材料（Supplementary Material）。

## 内容

补充材料通常包括：

1. **额外实验结果**
   - 更详细的消融实验
   - 额外的可视化
   - 完整的结果表格

2. **实现细节**
   - 详细的算法伪代码
   - 超参数搜索过程
   - 训练细节

3. **数据集详情**
   - 数据集统计信息
   - 数据预处理步骤
   - 数据样例

4. **理论证明**
   - 定理证明
   - 推导过程

## 目录结构

```
supplementary/
├── README.md           # 本文件
├── supplementary.qmd   # 主文件
├── sections/
│   ├── A_additional_experiments.qmd
│   ├── B_implementation_details.qmd
│   ├── C_dataset_details.qmd
│   └── D_proofs.qmd
└── figures/
    └── ...
```

## 注意事项

1. **独立性**: 补充材料应能独立阅读
2. **引用**: 使用与主文一致的编号 (Figure S1, Table S1)
3. **数据一致**: 仍然使用 `paper/data/` 作为数据源
4. **格式**: 遵循期刊的补充材料格式要求
