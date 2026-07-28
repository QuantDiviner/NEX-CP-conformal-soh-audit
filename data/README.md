# 数据目录

此目录存放项目的**原始数据**和**预处理数据**。

## 目录结构

```
data/
├── README.md           # 本文件
├── raw/                # 原始数据（NAS 符号链接，不复制大文件）
│   ├── MIT_Stanford_Toyota -> /Volumes/Public/研究数据/电池原始数据/Stanford
│   ├── CALCE -> /Volumes/Public/研究数据/电池原始数据/CALCE
│   ├── NASA -> /Volumes/Public/研究数据/电池原始数据/NASA
│   ├── Oxford -> /Volumes/Public/研究数据/电池原始数据/Oxford
│   └── DATASETS.md -> /Volumes/Public/研究数据/电池原始数据/DATASETS.md
├── processed/          # 预处理后的数据（清洗、转换、分割后）
│   └── .gitkeep
└── splits/             # 数据分割索引（确保可复现）
    └── .gitkeep
```

## 与其他数据目录的区别

| 目录 | 用途 | 内容示例 |
|------|------|---------|
| **`data/`** (本目录) | 输入数据 | 数据集 CSV、HDF5、图像 |
| `experiments/expXXX/results/` | 实验输出 | 模型预测、metrics.json |
| `paper/data/` | 论文引用 (SSOT) | 聚合后的指标 |

## 数据流

```
外部来源 (下载/采集)
         ↓
data/raw/              # 原始数据 (不修改)
         ↓ 预处理脚本
data/processed/        # 处理后数据
         ↓ 分割脚本
data/splits/           # train/val/test 索引
         ↓ 训练/评估脚本
experiments/expXXX/    # 实验结果
         ↓ collect_results.py
paper/data/            # 论文引用 (SSOT)
```

---

## 数据来源记录

### MIT-Stanford-Toyota / Stanford Severson2019

| 项目 | 内容 |
|------|------|
| **来源** | data.matr.io / Toyota Research Institute |
| **本项目用途** | primary, 124 LFP cells |
| **许可证** | CC BY 4.0 |
| **大小** | ~7.7 GB |
| **格式** | MATLAB `.mat` |
| **存放位置** | `data/raw/MIT_Stanford_Toyota` |
| **真实位置** | `/Volumes/Public/研究数据/电池原始数据/Stanford` |

### CALCE Battery Dataset

| 项目 | 内容 |
|------|------|
| **来源** | CALCE, University of Maryland |
| **本项目用途** | cross-protocol / chemistry audit |
| **格式** | Excel `.xlsx`、文本、压缩包 |
| **存放位置** | `data/raw/CALCE` |
| **真实位置** | `/Volumes/Public/研究数据/电池原始数据/CALCE` |

### NASA Li-ion Battery Dataset

| 项目 | 内容 |
|------|------|
| **来源** | NASA PCoE / cleaned dataset |
| **本项目用途** | cross-profile / historical baseline |
| **格式** | `.mat`、CSV、metadata |
| **存放位置** | `data/raw/NASA` |
| **真实位置** | `/Volumes/Public/研究数据/电池原始数据/NASA` |

### Oxford Battery Degradation Dataset 1

| 项目 | 内容 |
|------|------|
| **来源** | Oxford Research Archive |
| **本项目用途** | diagnostic cross-chemistry, 8 NMC cells |
| **许可证** | ODbL |
| **大小** | ~254 MB |
| **格式** | MATLAB `.mat` |
| **存放位置** | `data/raw/Oxford` |
| **真实位置** | `/Volumes/Public/研究数据/电池原始数据/Oxford` |

完整 NAS 数据清单见 `data/raw/DATASETS.md`。

---

## 预处理记录

### 预处理步骤

1. **数据清洗**
   - 脚本: `scripts/preprocess/01_clean.py`
   - 输入: `data/raw/`
   - 输出: `data/processed/cleaned/`
   - 处理: [描述处理内容]

2. **特征工程**
   - 脚本: `scripts/preprocess/02_features.py`
   - 输入: `data/processed/cleaned/`
   - 输出: `data/processed/features/`
   - 处理: [描述处理内容]

3. **数据分割**
   - 脚本: `scripts/preprocess/03_split.py`
   - 输出: `data/splits/`
   - 分割比例: train:val:test = 8:1:1
   - 随机种子: 42

### 运行所有预处理

```bash
# 一键运行所有预处理步骤
./scripts/preprocess/run_all.sh

# 或分步运行
python scripts/preprocess/01_clean.py
python scripts/preprocess/02_features.py
python scripts/preprocess/03_split.py --seed 42
```

---

## 数据分割

### 分割信息

```yaml
# data/splits/split_info.yaml
split:
  method: "random"        # random / stratified / temporal
  seed: 42
  ratios:
    train: 0.8
    val: 0.1
    test: 0.1

counts:
  train: XXXX
  val: XXXX
  test: XXXX
```

### 分割文件

- `data/splits/train_indices.npy` - 训练集索引
- `data/splits/val_indices.npy` - 验证集索引
- `data/splits/test_indices.npy` - 测试集索引

---

## Git 管理

### 大文件处理

大文件不提交到 Git。在 `.gitignore` 中已配置：

```gitignore
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep
!data/README.md
```

### 推荐方案

1. **小型数据集**: 直接提交或使用 Git LFS
2. **大型数据集**: 使用外部存储，在 README 中记录下载方式
3. **敏感数据**: 不提交，仅记录获取方式

---

## 数据验证清单

- [x] 原始数据已在 NAS 中准备并通过符号链接挂载到 `data/raw/`
- [x] 数据来源和版本已记录
- [x] 许可证已确认（详见 `data/raw/DATASETS.md`）
- [ ] 预处理脚本已创建并测试
- [ ] 数据分割已完成，种子已固定
- [ ] 分割信息已记录
- [ ] 处理后的数据可以正确加载

---

**最后更新**: 2026-05-20
