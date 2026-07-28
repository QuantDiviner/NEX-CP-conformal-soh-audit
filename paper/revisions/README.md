# 审稿修订管理

本目录用于管理论文投稿后的审稿意见和修订过程。

## 目录结构

```
revisions/
├── README.md                    # 本文件
├── round_1/                     # 第一轮审稿
│   ├── reviews/                 # 审稿意见
│   │   ├── reviewer_1.md
│   │   ├── reviewer_2.md
│   │   └── editor.md
│   ├── response/                # 回复
│   │   └── response_letter.md
│   ├── diff/                    # 修改对比
│   │   └── changes.pdf
│   └── manuscript_r1.pdf        # 修订后稿件
├── round_2/                     # 第二轮审稿（如有）
│   └── ...
└── final/                       # 最终接收版本
    └── accepted_manuscript.pdf
```

## 修订流程

### 1. 收到审稿意见

1. 创建 `round_N/` 目录
2. 将审稿意见复制到 `reviews/`
3. 逐条分析审稿意见

### 2. 准备回复

使用 `response_letter.md` 模板，逐条回复：

```markdown
## Reviewer 1

### Comment 1.1
> [原文引用审稿意见]

**Response:**
[你的回复]

**Changes made:**
- [具体修改，包括页码/行号]

### Comment 1.2
...
```

### 3. 修改稿件

- 使用 Word 修订模式或 latexdiff 标记修改
- 生成修改对比文档 `diff/changes.pdf`
- 确保所有修改都在回复信中说明

### 4. 提交修订

- 修订稿件
- 回复信 (Response to Reviewers)
- 修改标记版本 (Track Changes / Diff)

## 回复信模板

```markdown
# Response to Reviewers

Dear Editor and Reviewers,

Thank you for your valuable comments and suggestions on our manuscript entitled "[Title]" (Manuscript ID: XXX). We have carefully considered all the comments and revised our manuscript accordingly. Below, we provide point-by-point responses to each comment.

Changes in the revised manuscript are highlighted in [yellow/red/track changes].

---

## Response to Editor

[回复编辑意见]

---

## Response to Reviewer 1

[逐条回复]

---

## Response to Reviewer 2

[逐条回复]

---

We hope that the revised manuscript now meets the standards for publication in [Journal Name]. Thank you again for your time and consideration.

Sincerely,
[Corresponding Author]
```

## 技巧

### 积极回应

- 感谢审稿人的意见
- 对每条意见都给出具体回应
- 即使不同意，也要礼貌解释原因

### 清晰标记修改

- 明确指出修改位置（页码、行号、段落）
- 使用引用格式展示新增/修改的文字
- 提供修改对比文档

### 处理无法满足的要求

如果某条意见无法或不应满足：

```markdown
**Response:**
We thank the reviewer for this suggestion. However, [原因].
We respectfully believe that [解释]. Nevertheless, we have
added a discussion of this limitation in Section X (Page Y,
Lines Z-W).
```

## 版本控制建议

- 每轮修订在 Git 中打 tag: `v1.0-submitted`, `v1.1-r1`, `v1.2-r2`
- 保留所有版本的 PDF
- 记录修改历史
