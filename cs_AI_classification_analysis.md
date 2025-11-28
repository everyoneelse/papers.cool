# cs.AI 分类系统分析

## 1. cs.AI 是否有子分类系统？

**cs.AI 本身没有子分类系统。** arXiv 的分类系统是**扁平的（flat）**，没有层级结构。

### 1.1 arXiv 分类结构

- **cs.AI** 是 arXiv 的一个顶级分类（top-level category）
- 所有 arXiv 分类都是同一层级的，没有父子关系
- cs.AI 的定义：覆盖除 Vision、Robotics、Machine Learning、Multiagent Systems 和 Computation and Language (NLP) 之外的所有 AI 领域

### 1.2 论文的多分类标签

虽然 cs.AI 没有子分类，但**一篇论文可以有多个分类标签（subjects）**：

示例（来自 cs.AI 列表页）：
- `Artificial Intelligence (cs.AI)` - 主分类
- `Artificial Intelligence (cs.AI); Machine Learning (cs.LG)` - 主分类 + 其他分类
- `Artificial Intelligence (cs.AI); Computation and Language (cs.CL); Human-Computer Interaction (cs.HC); Machine Learning (cs.LG)` - 主分类 + 多个其他分类

每篇论文有：
- **Primary Subject（主分类）**：论文的主要分类，如 `cs.AI`
- **Additional Subjects（附加分类）**：论文可能属于的其他分类，如 `cs.LG`、`cs.CL` 等

## 2. 更细粒度的分类系统

虽然 cs.AI 本身没有子分类，但 arXiv 支持两种更细粒度的分类系统：

### 2.1 ACM 分类（ACM Classification）

- 计算机科学领域的标准分类系统
- 可以在 arXiv 搜索中使用 `acm_class` 字段进行搜索
- 例如：`I.2.0`（人工智能）、`I.2.1`（应用和专家系统）等

### 2.2 MSC 分类（Mathematics Subject Classification）

- 数学领域的标准分类系统
- 可以在 arXiv 搜索中使用 `msc_class` 字段进行搜索
- 主要用于数学相关的论文

## 3. Cool Papers 中的处理

在 `Zotero/CoolPapers.js` 中（第48-50行）：
```javascript
const subject = paper.querySelector("p.subjects a");
if (doc.body.id == "arxiv") {
    item.extra = subject.href.split("/").at(-1) + " - arXiv";
}
```

代码只提取了主分类（primary subject），没有处理多个分类或子分类。

## 总结

1. **cs.AI 没有子分类系统**：arXiv 的分类是扁平的，所有分类都在同一层级
2. **论文可以有多个分类**：一篇论文可以同时属于 cs.AI、cs.LG、cs.CL 等多个分类
3. **更细粒度的分类**：arXiv 支持 ACM 和 MSC 分类系统，但这些是独立的分类体系，不是 cs.AI 的子分类
4. **Cool Papers 当前实现**：只提取并显示论文的主分类（primary subject）
