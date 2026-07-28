# 实验目录

此目录管理所有实验。

## 目录结构

```
experiments/
├── README.md               # 本文件
├── EXPERIMENT_LOG.md       # 实验日志（按时间记录）
│
├── exp001_baseline/        # 正式实验
│   ├── config.yaml         # 实验配置
│   ├── metadata.json       # 元数据
│   ├── README.md           # 实验说明
│   ├── logs/               # 训练日志
│   ├── checkpoints/        # 模型检查点
│   └── results/
│       ├── metrics.json    # 评估指标
│       └── figures/        # 结果图表
│
├── exp002_our_method/
│   └── ...
│
├── _archived/              # 已归档实验（不删除）
│   └── ARCHIVE_INDEX.md    # 归档索引
│
└── _scratch/               # 临时实验（可删除）
    └── debug_xxx/
```

## 命名规则

- 正式实验: `expXXX_简短描述`
  - XXX: 三位数字编号 (001, 002, ...)
  - 简短描述: 使用下划线连接的英文描述

- 临时实验: `debug_xxx` 或 `test_xxx`
  - 放在 `_scratch/` 目录

## 创建新实验

### 1. 复制模板

```bash
cp -r experiments/_template experiments/exp001_my_experiment
```

### 2. 修改配置

编辑 `exp001_my_experiment/config.yaml`

### 3. 运行实验

```bash
python scripts/train.py --config experiments/exp001_my_experiment/config.yaml
```

### 4. 记录日志

在 `EXPERIMENT_LOG.md` 中添加记录

---

## 实验模板

每个实验目录应包含以下文件：

### config.yaml

```yaml
# 实验配置
# 继承默认配置，只写需要修改的参数

experiment:
  id: "exp001"
  name: "实验名称"
  description: "实验描述"

# 覆盖默认参数
training:
  epochs: 200
```

### metadata.json

```json
{
  "experiment_id": "exp001",
  "name": "实验名称",
  "status": "planned",
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "dependencies": {
    "parent_experiment": null,
    "frozen_parameters_version": "v1.0"
  },
  "outputs": {
    "paper_section": "Section X.X"
  }
}
```

### README.md

```markdown
# exp001: 实验名称

## 目的
[这个实验要验证什么]

## 方法
[使用什么方法]

## 结果
[主要结果]

## 结论
[得出的结论]
```

---

## 实验状态

| 状态 | 说明 |
|------|------|
| `planned` | 已计划，未开始 |
| `running` | 正在运行 |
| `completed` | 运行完成，待验证 |
| `validated` | 验证通过 |
| `archived` | 已归档 |

---

## 归档规则

1. **不要删除实验**，移动到 `_archived/`
2. 在 `_archived/ARCHIVE_INDEX.md` 记录归档原因
3. 保留完整的配置和结果文件

---

## 实验角色映射

见 `PROJECT_CHARTER.md` 中的 `experiment_roles` 定义。

使用角色而非硬编码实验ID，方便切换版本：

```yaml
# PROJECT_CHARTER.md
experiment_roles:
  main_experiment: exp003      # 可以随时更新
  ablation_study: exp004
  baseline_comparison: exp005
```
