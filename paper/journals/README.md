# 期刊投稿版本

本目录存放适配不同期刊格式的论文版本。

## 目录结构

```
journals/
├── README.md             # 本文件
├── nature/               # Nature 格式版本
│   ├── main.tex
│   └── figures/
├── ieee/                 # IEEE 格式版本
│   ├── main.tex
│   └── figures/
└── arxiv/                # arXiv 预印本版本
    └── main.tex
```

## 工作流

1. 在 `paper/source/` 中完成 Quarto 版本
2. 确定目标期刊后，创建对应目录
3. 从 Quarto 输出转换为期刊要求的格式
4. 根据期刊模板调整格式

## 期刊模板资源

- **IEEE**: [IEEE Author Center](https://www.ieee.org/publications/authors/author-center.html)
- **Nature**: [Nature Author Guidelines](https://www.nature.com/nature/for-authors)
- **Elsevier**: [Elsevier LaTeX](https://www.elsevier.com/authors/policies-and-guidelines/latex-instructions)
- **ACM**: [ACM Primary Article Template](https://www.acm.org/publications/proceedings-template)

## 检查清单

投稿前检查：

- [ ] 格式符合期刊模板要求
- [ ] 字数/页数限制符合要求
- [ ] 图片格式和分辨率符合要求
- [ ] 参考文献格式正确
- [ ] 作者信息、机构正确
- [ ] 补充材料准备就绪
- [ ] Cover letter 已准备

## Cover Letter 模板

见 `cover_letter_template.md`
